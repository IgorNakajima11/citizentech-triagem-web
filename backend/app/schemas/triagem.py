from typing import Literal

from pydantic import BaseModel, Field, field_validator

Categoria = Literal[
    "iluminacao_publica", "buraco_pavimentacao", "coleta_lixo",
    "poda_arvore", "agua_esgoto", "transito_sinalizacao", "outro",
]
Urgencia = Literal["baixa", "media", "alta"]


class RelatoEntrada(BaseModel):
    texto: str = Field(min_length=15, max_length=1000, description="Relato do problema em linguagem livre")
    cep: str = Field(description="CEP do local, com ou sem traço")
    numero: str | None = Field(default=None, max_length=10)

    @field_validator("texto")
    @classmethod
    def texto_com_conteudo(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 15:
            raise ValueError("descreva o problema com pelo menos 15 caracteres")
        return v

    @field_validator("cep")
    @classmethod
    def cep_valido(cls, v: str) -> str:
        digitos = "".join(c for c in v if c.isdigit())
        if len(digitos) != 8:
            raise ValueError("o CEP precisa ter 8 números")
        return digitos


class AnaliseIA(BaseModel):
    categoria: Categoria
    urgencia: Urgencia
    resumo: str = Field(max_length=200)
    orientacao: str = Field(max_length=500)
    sinais_de_risco: list[str] = Field(default_factory=list, max_length=5)
    confianca: float = Field(ge=0, le=1)


class Endereco(BaseModel):
    validado: bool
    logradouro: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""
    aviso: str | None = None


class AnaliseResultado(BaseModel):
    analise: AnaliseIA
    fonte: Literal["llm", "modelo_local"]
    secretaria: str
    prazo_dias: int
    endereco: Endereco
    segunda_opiniao: Categoria | None = None
    revisao_sugerida: bool = False
    aviso: str | None = None
    texto_mascarado: str


class CategoriaInfo(BaseModel):
    codigo: Categoria
    nome: str
    secretaria: str
    prazo_dias: int
