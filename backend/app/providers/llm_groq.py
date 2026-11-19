import json

import httpx

from ..config import configuracao


class LLMIndisponivel(Exception):
    pass


class LLMRespostaInvalida(Exception):
    pass


def chamar_json(sistema: str, usuario: str) -> dict:
    if not configuracao.llm_configurado:
        raise LLMIndisponivel("GROQ_API_KEY não configurada")
    corpo = {
        "model": configuracao.groq_modelo,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}],
    }
    cabecalhos = {"Authorization": f"Bearer {configuracao.groq_api_key}"}
    try:
        resp = httpx.post(configuracao.groq_url, json=corpo, headers=cabecalhos, timeout=configuracao.llm_timeout_s)
    except httpx.TimeoutException as e:
        raise LLMIndisponivel("tempo esgotado") from e
    except httpx.HTTPError as e:
        raise LLMIndisponivel(f"falha de conexão: {type(e).__name__}") from e
    if resp.status_code >= 400:
        raise LLMIndisponivel(f"HTTP {resp.status_code}")
    try:
        conteudo = resp.json()["choices"][0]["message"]["content"]
        return json.loads(conteudo)
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise LLMRespostaInvalida("resposta sem JSON válido") from e
