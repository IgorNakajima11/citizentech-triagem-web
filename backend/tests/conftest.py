import os
import sys
import tempfile
from pathlib import Path

os.environ["DB_PATH"] = str(Path(tempfile.mkdtemp()) / "teste.db")
os.environ["GROQ_API_KEY"] = "chave-de-teste"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.providers import viacep
from app.schemas.triagem import Endereco


@pytest.fixture(autouse=True)
def cep_falso(monkeypatch):
    def consultar(cep):
        if cep == "99999999":
            return Endereco(validado=False, aviso="Não encontramos esse CEP.")
        return Endereco(validado=True, logradouro="Avenida Paulista", bairro="Bela Vista", cidade="São Paulo", uf="SP")
    monkeypatch.setattr(viacep, "consultar", consultar)
