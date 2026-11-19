import html

import streamlit as st

URGENCIA = {
    "alta": {"rotulo": "URGÊNCIA ALTA", "detalhe": "risco à segurança, atendimento prioritário",
             "simbolo": "!!!", "fundo": "#FDECEA", "borda": "#B3261E", "texto": "#7A1410"},
    "media": {"rotulo": "URGÊNCIA MÉDIA", "detalhe": "atrapalha o dia a dia, sem risco imediato",
              "simbolo": "!!", "fundo": "#FFF4E0", "borda": "#A35F00", "texto": "#6B3E00"},
    "baixa": {"rotulo": "URGÊNCIA BAIXA", "detalhe": "pedido ou incômodo leve",
              "simbolo": "!", "fundo": "#E8F5EC", "borda": "#1E6B34", "texto": "#14491F"},
}
CORES_URGENCIA = {u: v["borda"] for u, v in URGENCIA.items()}
NOMES_URGENCIA = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}


def aplicar_tema(texto_grande: bool) -> None:
    tamanho = "1.15rem" if texto_grande else "1rem"
    st.markdown(f"""<style>
    html, body, [class*="css"], .stMarkdown p, label, .stTextInput input, .stTextArea textarea {{ font-size: {tamanho}; }}
    .selo {{ display:inline-block; border-left: 6px solid; border-radius: 6px; padding: 6px 12px; margin: 2px 0 8px; }}
    .selo strong {{ letter-spacing: .02em; }}
    .cartao {{ border: 1px solid #C9CED6; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }}
    .cartao h4 {{ margin: 0 0 6px; }}
    </style>""", unsafe_allow_html=True)


def selo_urgencia(urgencia: str, compacto: bool = False) -> None:
    u = URGENCIA[urgencia]
    detalhe = "" if compacto else f" &middot; {u['detalhe']}"
    st.markdown(
        f'<div class="selo" role="status" aria-label="{u["rotulo"]}" '
        f'style="background:{u["fundo"]};border-color:{u["borda"]};color:{u["texto"]}">'
        f'<strong>[{u["simbolo"]}] {u["rotulo"]}</strong>{detalhe}</div>', unsafe_allow_html=True)


def cartao_solicitacao(titulo: str, urgencia: str, linhas: list[tuple[str, str]]) -> None:
    with st.container(border=True):
        st.markdown(f"#### {html.escape(titulo)}")
        selo_urgencia(urgencia, compacto=True)
        for rotulo, valor in linhas:
            st.markdown(f"**{rotulo}:** {html.escape(str(valor))}")


def estado_vazio(titulo: str, explicacao: str) -> None:
    with st.container(border=True):
        st.markdown(f"**{titulo}**")
        st.caption(explicacao)


def mensagem_erro(mensagem: str, campos: list[dict] | None = None) -> None:
    nomes = {"texto": "Descrição do problema", "cep": "CEP", "numero": "Número"}
    detalhes = "".join(f"\n- {nomes.get(c['campo'], c['campo'])}: {c['mensagem']}" for c in (campos or []))
    st.error(f"{mensagem}{detalhes}")
