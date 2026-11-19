from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .triagem import Categoria, Urgencia


class SolicitacaoConfirmacao(BaseModel):
    texto_mascarado: str = Field(min_length=15, max_length=1000)
    cep: str = Field(pattern=r"^\d{8}$")
    numero: str | None = Field(default=None, max_length=10)
    bairro: str = Field(default="", max_length=80)
    categoria_sugerida: Categoria
    categoria_confirmada: Categoria
    urgencia: Urgencia
    fonte: Literal["llm", "modelo_local"]


class Solicitacao(BaseModel):
    protocolo: str
    criada_em: datetime
    categoria_sugerida: Categoria
    categoria_confirmada: Categoria
    corrigida_pelo_cidadao: bool
    urgencia: Urgencia
    secretaria: str
    prazo_dias: int
    bairro: str
    fonte: Literal["llm", "modelo_local"]
    avaliacao: Literal["util", "incorreta"] | None = None


class Avaliacao(BaseModel):
    avaliacao: Literal["util", "incorreta"]
