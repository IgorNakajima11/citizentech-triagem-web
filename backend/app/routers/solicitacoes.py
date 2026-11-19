from fastapi import APIRouter, HTTPException

from ..pipelines import solicitacoes
from ..schemas.solicitacoes import Avaliacao, Solicitacao, SolicitacaoConfirmacao

router = APIRouter(prefix="/api/solicitacoes", tags=["solicitacoes"])


@router.post("", response_model=Solicitacao, status_code=201)
def confirmar(dados: SolicitacaoConfirmacao) -> Solicitacao:
    return solicitacoes.registrar(dados)


@router.get("", response_model=list[Solicitacao])
def listar() -> list[Solicitacao]:
    return solicitacoes.listar()


@router.post("/{protocolo}/avaliacao", status_code=204)
def avaliar(protocolo: str, dados: Avaliacao) -> None:
    if not solicitacoes.avaliar(protocolo, dados.avaliacao):
        raise HTTPException(status_code=404, detail="protocolo não encontrado")
