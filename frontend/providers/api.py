import os

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT_CONEXAO_S = 3
TIMEOUT_RESPOSTA_S = 45


class ErroApi(Exception):
    def __init__(self, mensagem: str, campos: list[dict] | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.campos = campos or []


@st.cache_resource
def _sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _requisitar(metodo: str, caminho: str, **kwargs):
    try:
        resp = _sessao().request(metodo, f"{API_URL}{caminho}", timeout=(TIMEOUT_CONEXAO_S, TIMEOUT_RESPOSTA_S), **kwargs)
    except requests.Timeout as e:
        raise ErroApi("O serviço demorou demais para responder. Tente de novo em alguns instantes.") from e
    except requests.ConnectionError as e:
        raise ErroApi("Não conseguimos falar com o serviço da prefeitura agora. Tente de novo em alguns minutos.") from e
    if resp.status_code == 422:
        try:
            campos = resp.json().get("campos", [])
        except ValueError:
            campos = []
        raise ErroApi("Alguns dados precisam ser corrigidos.", campos)
    if resp.status_code == 404:
        raise ErroApi("Não encontramos esse protocolo.")
    if resp.status_code >= 400:
        raise ErroApi("Tivemos um problema ao processar seu pedido. Ele não foi perdido: tente enviar de novo.")
    if resp.status_code == 204:
        return None
    try:
        return resp.json()
    except ValueError as e:
        raise ErroApi("Recebemos uma resposta inesperada do serviço. Tente de novo.") from e


@st.cache_data(ttl=30, show_spinner=False)
def saude() -> dict | None:
    try:
        return _requisitar("GET", "/api/saude")
    except ErroApi:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def categorias() -> list[dict]:
    return _requisitar("GET", "/api/categorias")


@st.cache_data(ttl=20, show_spinner=False)
def listar_solicitacoes() -> list[dict]:
    return _requisitar("GET", "/api/solicitacoes")


def analisar(texto: str, cep: str, numero: str) -> dict:
    return _requisitar("POST", "/api/triagem/analisar", json={"texto": texto, "cep": cep, "numero": numero or None})


def confirmar(dados: dict) -> dict:
    resultado = _requisitar("POST", "/api/solicitacoes", json=dados)
    listar_solicitacoes.clear()
    return resultado


def avaliar(protocolo: str, avaliacao: str) -> None:
    _requisitar("POST", f"/api/solicitacoes/{protocolo}/avaliacao", json={"avaliacao": avaliacao})
    listar_solicitacoes.clear()
