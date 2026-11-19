import hashlib
from datetime import datetime

from ..catalogo import secretaria_e_prazo
from ..providers import repositorio
from ..schemas.solicitacoes import Solicitacao, SolicitacaoConfirmacao


def _protocolo(dados: SolicitacaoConfirmacao, agora: datetime) -> str:
    base = f"{dados.texto_mascarado}|{dados.cep}|{agora.isoformat()}"
    return f"PRT-{agora:%Y%m%d}-{hashlib.sha1(base.encode()).hexdigest()[:6].upper()}"


def registrar(dados: SolicitacaoConfirmacao) -> Solicitacao:
    agora = datetime.now().replace(microsecond=0)
    secretaria, prazo = secretaria_e_prazo(dados.categoria_confirmada, dados.urgencia)
    registro = {
        "protocolo": _protocolo(dados, agora), "criada_em": agora.isoformat(),
        "categoria_sugerida": dados.categoria_sugerida, "categoria_confirmada": dados.categoria_confirmada,
        "corrigida_pelo_cidadao": int(dados.categoria_sugerida != dados.categoria_confirmada),
        "urgencia": dados.urgencia, "secretaria": secretaria, "prazo_dias": prazo,
        "bairro": dados.bairro or "não informado", "fonte": dados.fonte,
        "texto_mascarado": dados.texto_mascarado, "cep": dados.cep, "numero": dados.numero,
    }
    repositorio.inserir(registro)
    return Solicitacao(**{k: v for k, v in registro.items() if k in Solicitacao.model_fields},
                       avaliacao=None)


def listar() -> list[Solicitacao]:
    return [Solicitacao(**l) for l in repositorio.listar()]


def avaliar(protocolo: str, avaliacao: str) -> bool:
    return repositorio.avaliar(protocolo, avaliacao)
