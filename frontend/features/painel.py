from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from providers import api
from state import sessao
from ui import componentes as ui

PERIODOS = {"Últimos 7 dias": 7, "Últimos 30 dias": 30, "Todo o período": None}


def _dados() -> pd.DataFrame | None:
    try:
        registros = api.listar_solicitacoes()
    except api.ErroApi as e:
        ui.mensagem_erro(e.mensagem)
        return None
    if not registros:
        return pd.DataFrame()
    df = pd.DataFrame(registros)
    df["criada_em"] = pd.to_datetime(df["criada_em"])
    df["dia"] = df["criada_em"].dt.date
    nomes = {c["codigo"]: c["nome"] for c in api.categorias()}
    df["Assunto"] = df["categoria_confirmada"].map(nomes)
    df["Urgência"] = df["urgencia"].map(ui.NOMES_URGENCIA)
    return df


def mostrar() -> None:
    st.markdown("Pedidos registrados na cidade. Os gráficos são interativos: passe o mouse para ver os números "
                "e arraste para dar zoom.")
    df = _dados()
    if df is None:
        return
    if df.empty:
        ui.estado_vazio("Ainda não há pedidos registrados.", "Quando alguém enviar um relato, os números aparecem aqui.")
        return

    f1, f2, f3, f4 = st.columns([2, 2, 1.4, 1.2])
    assuntos = f1.multiselect("Assunto", sorted(df["Assunto"].unique()), placeholder="Todos os assuntos")
    urgencias = f2.multiselect("Urgência", ["Alta", "Média", "Baixa"], placeholder="Todas as urgências")
    periodo = f3.selectbox("Período", list(PERIODOS))
    so_meus = f4.toggle("Só os meus pedidos", help="Mostra apenas os pedidos enviados por você nesta sessão")

    filtrado = df
    if assuntos:
        filtrado = filtrado[filtrado["Assunto"].isin(assuntos)]
    if urgencias:
        filtrado = filtrado[filtrado["Urgência"].isin(urgencias)]
    if PERIODOS[periodo]:
        filtrado = filtrado[filtrado["dia"] >= date.today() - timedelta(days=PERIODOS[periodo])]
    if so_meus:
        filtrado = filtrado[filtrado["protocolo"].isin(sessao.meus_protocolos())]

    if filtrado.empty:
        ui.estado_vazio("Nenhum pedido com esses filtros.", "Remova algum filtro para ver mais resultados.")
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pedidos", len(filtrado))
    m2.metric("Urgência alta", int((filtrado["urgencia"] == "alta").sum()))
    m3.metric("Assunto corrigido pelo cidadão", f"{filtrado['corrigida_pelo_cidadao'].mean() * 100:.0f}%")
    avaliados = filtrado["avaliacao"].dropna()
    m4.metric("Análises avaliadas como úteis", f"{(avaliados == 'util').mean() * 100:.0f}%" if len(avaliados) else "sem avaliações")

    cores = {ui.NOMES_URGENCIA[u]: c for u, c in ui.CORES_URGENCIA.items()}
    contagem = filtrado.groupby(["Assunto", "Urgência"]).size().reset_index(name="Pedidos")
    fig = px.bar(contagem, y="Assunto", x="Pedidos", color="Urgência", orientation="h",
                 color_discrete_map=cores, category_orders={"Urgência": ["Alta", "Média", "Baixa"]},
                 title="Pedidos por assunto e urgência", pattern_shape="Urgência",
                 pattern_shape_map={"Alta": "x", "Média": "/", "Baixa": ""})
    fig.update_layout(legend_title_text="Urgência", yaxis_title=None, height=360, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, width="stretch")

    por_dia = filtrado.groupby(["dia", "Urgência"]).size().reset_index(name="Pedidos")
    fig2 = px.line(por_dia, x="dia", y="Pedidos", color="Urgência", markers=True, symbol="Urgência",
                   color_discrete_map=cores, title="Pedidos por dia")
    fig2.update_layout(xaxis_title=None, height=300, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig2, width="stretch")

    with st.expander("Ver a tabela de pedidos"):
        st.dataframe(filtrado[["protocolo", "criada_em", "Assunto", "Urgência", "secretaria", "bairro"]]
                     .rename(columns={"protocolo": "Protocolo", "criada_em": "Data", "secretaria": "Secretaria",
                                      "bairro": "Bairro"}), hide_index=True, width="stretch")
