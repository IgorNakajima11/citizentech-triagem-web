import re

_PADROES = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[EMAIL]"),
    (re.compile(r"(?:\(?\b\d{2}\)?\s?)?\b9?\d{4}-?\d{4}\b"), "[TELEFONE]"),
]


def mascarar(texto: str) -> str:
    for padrao, troca in _PADROES:
        texto = padrao.sub(troca, texto)
    return texto
