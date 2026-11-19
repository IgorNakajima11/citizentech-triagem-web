from fastapi import APIRouter

from ..catalogo import CATEGORIAS
from ..config import configuracao
from ..pipelines import triagem
from ..schemas.triagem import AnaliseResultado, CategoriaInfo, RelatoEntrada

router = APIRouter(prefix="/api", tags=["triagem"])


@router.get("/saude")
def saude() -> dict:
    return {"status": "ok", "llm_configurado": configuracao.llm_configurado, "modelo": configuracao.groq_modelo}


@router.get("/categorias", response_model=list[CategoriaInfo])
def categorias() -> list[CategoriaInfo]:
    return [CategoriaInfo(codigo=c, nome=n, secretaria=s, prazo_dias=p) for c, (n, s, p) in CATEGORIAS.items()]


@router.post("/triagem/analisar", response_model=AnaliseResultado)
def analisar(entrada: RelatoEntrada) -> AnaliseResultado:
    return triagem.analisar(entrada)
