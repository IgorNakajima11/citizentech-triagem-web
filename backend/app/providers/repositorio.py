import sqlite3
import threading
from datetime import datetime

from ..config import configuracao

_trava = threading.Lock()
_COLUNAS = ["protocolo", "criada_em", "categoria_sugerida", "categoria_confirmada", "corrigida_pelo_cidadao",
            "urgencia", "secretaria", "prazo_dias", "bairro", "fonte", "avaliacao"]


def _conexao() -> sqlite3.Connection:
    configuracao.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(configuracao.caminho_banco)
    con.execute(
        "CREATE TABLE IF NOT EXISTS solicitacoes ("
        " protocolo TEXT PRIMARY KEY, criada_em TEXT NOT NULL, categoria_sugerida TEXT NOT NULL,"
        " categoria_confirmada TEXT NOT NULL, corrigida_pelo_cidadao INTEGER NOT NULL, urgencia TEXT NOT NULL,"
        " secretaria TEXT NOT NULL, prazo_dias INTEGER NOT NULL, bairro TEXT NOT NULL, fonte TEXT NOT NULL,"
        " avaliacao TEXT, texto_mascarado TEXT NOT NULL, cep TEXT NOT NULL, numero TEXT)")
    return con


def inserir(registro: dict) -> None:
    with _trava, _conexao() as con:
        con.execute(
            "INSERT INTO solicitacoes VALUES (:protocolo, :criada_em, :categoria_sugerida, :categoria_confirmada,"
            " :corrigida_pelo_cidadao, :urgencia, :secretaria, :prazo_dias, :bairro, :fonte, NULL,"
            " :texto_mascarado, :cep, :numero)", registro)


def listar() -> list[dict]:
    with _trava, _conexao() as con:
        cur = con.execute(f"SELECT {', '.join(_COLUNAS)} FROM solicitacoes ORDER BY criada_em DESC")
        linhas = [dict(zip(_COLUNAS, l)) for l in cur.fetchall()]
    for l in linhas:
        l["criada_em"] = datetime.fromisoformat(l["criada_em"])
        l["corrigida_pelo_cidadao"] = bool(l["corrigida_pelo_cidadao"])
    return linhas


def avaliar(protocolo: str, avaliacao: str) -> bool:
    with _trava, _conexao() as con:
        cur = con.execute("UPDATE solicitacoes SET avaliacao = ? WHERE protocolo = ?", (avaliacao, protocolo))
        return cur.rowcount == 1
