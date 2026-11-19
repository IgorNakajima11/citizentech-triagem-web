import streamlit as st

from features import historico, painel, relato
from providers import api
from state import sessao
from ui import componentes as ui

st.set_page_config(page_title="Cidade Atende", layout="wide")
sessao.iniciar()

with st.sidebar:
    st.title("Cidade Atende")
    st.caption("Relate problemas da sua rua para a prefeitura em poucos passos.")
    st.toggle("Texto maior", key="texto_grande", help="Aumenta o tamanho das letras")
    st.markdown("**Como funciona**\n1. Você descreve o problema.\n2. A inteligência artificial identifica o assunto "
                "e a urgência.\n3. Você confere e envia.\n4. Recebe um protocolo.")
    st.markdown("**Emergência?** Não espere: ligue **193** (bombeiros) ou **199** (Defesa Civil).")
    situacao = api.saude()
    if situacao is None:
        st.error("Serviço da prefeitura fora do ar no momento. Você pode tentar de novo em alguns minutos.")
    elif not situacao.get("llm_configurado"):
        st.warning("Análise detalhada desligada: usando a classificação automática simples.")
    else:
        st.caption("Serviço funcionando normalmente.")

ui.aplicar_tema(st.session_state.texto_grande)

aba_relato, aba_minhas, aba_painel = st.tabs(["Fazer um relato", "Minhas solicitações", "Painel da cidade"])
with aba_relato:
    try:
        relato.mostrar()
    except api.ErroApi as e:
        ui.mensagem_erro(e.mensagem)
with aba_minhas:
    try:
        historico.mostrar()
    except api.ErroApi as e:
        ui.mensagem_erro(e.mensagem)
with aba_painel:
    painel.mostrar()
