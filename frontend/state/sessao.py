import streamlit as st

PADROES = {
    "analise_atual": None,
    "entrada_atual": None,
    "historico": [],
    "ultimo_protocolo": None,
    "texto_grande": False,
    "erro_envio": None,
}


def iniciar() -> None:
    for chave, valor in PADROES.items():
        if chave not in st.session_state:
            st.session_state[chave] = list(valor) if isinstance(valor, list) else valor


def guardar_analise(entrada: dict, analise: dict) -> None:
    st.session_state.entrada_atual = entrada
    st.session_state.analise_atual = analise
    st.session_state.ultimo_protocolo = None


def descartar_analise() -> None:
    st.session_state.entrada_atual = None
    st.session_state.analise_atual = None


def registrar_envio(solicitacao: dict, resumo: str) -> None:
    st.session_state.historico.insert(0, {**solicitacao, "resumo": resumo})
    st.session_state.ultimo_protocolo = solicitacao["protocolo"]
    descartar_analise()


def registrar_avaliacao(protocolo: str, avaliacao: str) -> None:
    for item in st.session_state.historico:
        if item["protocolo"] == protocolo:
            item["avaliacao"] = avaliacao


def meus_protocolos() -> set[str]:
    return {item["protocolo"] for item in st.session_state.historico}
