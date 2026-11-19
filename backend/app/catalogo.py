CATEGORIAS = {
    "iluminacao_publica": ("Iluminação pública", "Secretaria de Serviços Urbanos - Iluminação", 5),
    "buraco_pavimentacao": ("Buraco e pavimentação", "Secretaria de Obras - Pavimentação", 15),
    "coleta_lixo": ("Lixo e entulho", "Secretaria de Serviços Urbanos - Limpeza", 3),
    "poda_arvore": ("Árvores e poda", "Secretaria do Verde e Meio Ambiente", 20),
    "agua_esgoto": ("Água, esgoto e bueiros", "Saneamento - Água e Esgoto", 7),
    "transito_sinalizacao": ("Trânsito e sinalização", "Secretaria de Mobilidade e Trânsito", 10),
    "outro": ("Outro assunto", "Central de Atendimento (análise manual)", 10),
}
PRAZO_URGENTE_DIAS = 1


def secretaria_e_prazo(categoria: str, urgencia: str) -> tuple[str, int]:
    _, secretaria, prazo = CATEGORIAS[categoria]
    if urgencia == "alta":
        prazo = PRAZO_URGENTE_DIAS
    return secretaria, prazo
