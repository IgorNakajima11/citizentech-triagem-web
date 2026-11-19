import logging
import re
import unicodedata

from pydantic import ValidationError

from ..catalogo import CATEGORIAS, secretaria_e_prazo
from ..providers import llm_groq, modelo_local, viacep
from ..schemas.triagem import AnaliseIA, AnaliseResultado, RelatoEntrada
from .privacidade import mascarar

log = logging.getLogger("triagem")

PROMPT_SISTEMA = """Você é o assistente de triagem da central de atendimento de uma prefeitura brasileira.
Recebe o relato de um cidadão sobre um problema na rua e devolve SOMENTE um objeto JSON com estes campos:
- "categoria": uma de {categorias}. Postes, lâmpadas e fios da rede elétrica na rua são "iluminacao_publica".
  Pedidos de plantio ou de remoção de árvores são "poda_arvore". Use "outro" só se o relato não for de zeladoria urbana.
- "urgencia": "alta" se houver risco imediato à vida ou à segurança (fio elétrico exposto, árvore ou poste caindo,
  cratera, alagamento, semáforo apagado em cruzamento, acidente); "media" se atrapalha o dia a dia mas sem risco
  imediato; "baixa" para pedidos, sugestões ou incômodos leves.
- "resumo": uma frase curta e neutra do problema, sem dados pessoais (máximo 200 caracteres).
- "orientacao": orientação ao cidadão em linguagem simples, sem jargão (máximo 3 frases). Se houver risco, diga
  primeiro o que fazer para se proteger (por exemplo, não se aproximar do fio e ligar para os bombeiros no 193 ou a
  Defesa Civil no 199 em emergência). O relato já está sendo registrado na prefeitura por este canal: não peça para
  o cidadão registrar em outro lugar.
- "sinais_de_risco": lista curta (até 5) dos trechos do relato que indicam risco; lista vazia se não houver.
- "confianca": número de 0 a 1 indicando sua certeza sobre a categoria.
Não invente informações que não estão no relato. Não prometa prazos. Responda apenas com o JSON."""

_RISCOS = [
    (r"\bfios?\b.*\b(solto|caido|chao|expost|pendurad)", "fio elétrico exposto"),
    (r"\b(choque|eletrocut|faisca)", "risco de choque"),
    (r"\b(acidente|atropel|bateu|batida|capotou)", "acidente ou risco de acidente"),
    (r"\b(caiu|desabou|despencou|tombou|caindo)\b", "queda de estrutura"),
    (r"\b(cratera|afundou|desmoron)", "afundamento de via"),
    (r"\b(alag|inund|enchente)", "alagamento"),
    (r"\b(semaforo|farol)\b.*\b(apagado|desligado|quebrado|nao funciona|piscando)", "semáforo sem funcionar"),
]


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def _analise_por_regras(texto: str) -> AnaliseIA:
    categoria, conf = modelo_local.classificar(texto)
    if conf < 0.45:
        categoria = "outro"
    t = _sem_acento(texto)
    sinais = [m for p, m in _RISCOS if re.search(p, t)]
    urgencia = "alta" if sinais else "media"
    nome = CATEGORIAS[categoria][0]
    orientacao = ("Seu relato foi registrado e será analisado pela equipe responsável."
                  if not sinais else
                  "Se houver perigo imediato, afaste-se do local e ligue 193 (bombeiros) ou 199 (Defesa Civil). "
                  "Seu relato foi marcado como urgente.")
    return AnaliseIA(categoria=categoria, urgencia=urgencia, resumo=f"Relato classificado como: {nome}.",
                     orientacao=orientacao, sinais_de_risco=sinais[:5], confianca=round(conf, 2))


def _analise_por_llm(texto_mascarado: str) -> AnaliseIA:
    sistema = PROMPT_SISTEMA.format(categorias=", ".join(f'"{c}"' for c in CATEGORIAS))
    ultimo_erro = None
    for _ in range(2):
        try:
            dados = llm_groq.chamar_json(sistema, f"Relato do cidadão:\n{texto_mascarado}")
            return AnaliseIA.model_validate(dados)
        except (llm_groq.LLMRespostaInvalida, ValidationError) as e:
            ultimo_erro = e
            log.warning("resposta do LLM inválida, tentando de novo: %s", type(e).__name__)
    raise llm_groq.LLMRespostaInvalida(str(ultimo_erro))


def analisar(entrada: RelatoEntrada) -> AnaliseResultado:
    texto_mascarado = mascarar(entrada.texto)
    aviso = None
    try:
        analise = _analise_por_llm(texto_mascarado)
        fonte = "llm"
    except (llm_groq.LLMIndisponivel, llm_groq.LLMRespostaInvalida) as e:
        log.warning("LLM indisponível (%s); usando o modelo próprio", e)
        analise = _analise_por_regras(texto_mascarado)
        fonte = "modelo_local"
        aviso = "A análise detalhada está indisponível no momento. Usamos uma classificação automática mais simples."

    segunda, conf_segunda = modelo_local.classificar(texto_mascarado)
    divergente = fonte == "llm" and analise.categoria != "outro" and conf_segunda >= 0.6 and segunda != analise.categoria
    endereco = viacep.consultar(entrada.cep)
    secretaria, prazo = secretaria_e_prazo(analise.categoria, analise.urgencia)
    revisao = divergente or analise.confianca < 0.6 or analise.categoria == "outro" or not endereco.validado
    return AnaliseResultado(
        analise=analise, fonte=fonte, secretaria=secretaria, prazo_dias=prazo, endereco=endereco,
        segunda_opiniao=segunda if divergente else None, revisao_sugerida=revisao, aviso=aviso,
        texto_mascarado=texto_mascarado)
