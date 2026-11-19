from functools import lru_cache

import httpx

from ..config import configuracao
from ..schemas.triagem import Endereco


@lru_cache(maxsize=2048)
def consultar(cep: str) -> Endereco:
    try:
        resp = httpx.get(configuracao.viacep_url.format(cep=cep), timeout=configuracao.viacep_timeout_s)
        resp.raise_for_status()
        dados = resp.json()
    except (httpx.HTTPError, ValueError):
        consultar.cache_clear()
        return Endereco(validado=False, aviso="Não foi possível confirmar o endereço agora. Um atendente vai conferir.")
    if dados.get("erro"):
        return Endereco(validado=False, aviso="Não encontramos esse CEP. Confira o número ou um atendente vai verificar.")
    return Endereco(validado=True, logradouro=dados.get("logradouro", ""), bairro=dados.get("bairro", ""),
                    cidade=dados.get("localidade", ""), uf=dados.get("uf", ""))
