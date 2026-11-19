import re

import streamlit as st

from providers import api
from state import sessao
from ui import componentes as ui

TAMANHO_MINIMO = 15
TAMANHO_MAXIMO = 1000


def _validar(texto: str, cep: str, numero: str) -> list[str]:
    erros = []
    if not texto.strip():
        erros.append("Descreva o problema: o campo está vazio.")
    elif len(texto.strip()) < TAMANHO_MINIMO:
        erros.append(f"Conte um pouco mais: a descrição precisa ter pelo menos {TAMANHO_MINIMO} letras.")
    if not re.fullmatch(r"\d{5}-?\d{3}", cep.strip()):
        erros.append("Informe o CEP com 8 números, por exemplo 01310-100.")
    if numero and not re.fullmatch(r"[0-9A-Za-z/ -]{1,10}", numero.strip()):
        erros.append("O número do imóvel pode ter no máximo 10 caracteres.")
    return erros


def _formulario() -> None:
    with st.form("form_relato", clear_on_submit=False):
        texto = st.text_area(
            "Descreva o problema", max_chars=TAMANHO_MAXIMO, height=130,
            placeholder="Exemplo: O poste em frente ao número 120 está apagado há uma semana e a rua fica escura.",
            help="Conte o que aconteceu e onde. Não é preciso escrever seu CPF ou telefone.")
        col1, col2 = st.columns([2, 1])
        cep = col1.text_input("CEP do local", max_chars=9, placeholder="01310-100",
                              help="Se não souber, procure o CEP da rua no site dos Correios.")
        numero = col2.text_input("Número (opcional)", max_chars=10, placeholder="120")
        enviado = st.form_submit_button("Analisar meu relato", type="primary", width="stretch")

    if not enviado:
        return
    erros = _validar(texto, cep, numero)
    if erros:
        st.error("Antes de continuar:\n" + "".join(f"\n- {e}" for e in erros))
        return
    entrada = {"texto": texto.strip(), "cep": re.sub(r"\D", "", cep), "numero": numero.strip()}
    try:
        with st.spinner("Analisando seu relato. Isso costuma levar alguns segundos..."):
            analise = api.analisar(**entrada)
    except api.ErroApi as e:
        ui.mensagem_erro(e.mensagem, e.campos)
        return
    sessao.guardar_analise(entrada, analise)
    st.rerun()


def _resultado() -> None:
    r = st.session_state.analise_atual
    entrada = st.session_state.entrada_atual
    a = r["analise"]
    nomes = {c["codigo"]: c["nome"] for c in api.categorias()}

    st.subheader("Confira a análise antes de enviar")
    if r.get("aviso"):
        st.warning(r["aviso"])
    ui.selo_urgencia(a["urgencia"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Assunto identificado:** {nomes.get(a['categoria'], a['categoria'])}")
        st.markdown(f"**Vai para:** {r['secretaria']}")
        st.markdown(f"**Prazo estimado:** até {r['prazo_dias']} dia(s)")
    with col2:
        end = r["endereco"]
        if end["validado"]:
            numero = f", {entrada['numero']}" if entrada.get("numero") else ""
            st.markdown(f"**Local:** {end['logradouro']}{numero} - {end['bairro']}, {end['cidade']}/{end['uf']}")
        else:
            st.markdown(f"**Local:** CEP {entrada['cep']} (não confirmado)")
            st.caption(end.get("aviso") or "")
        st.markdown(f"**Resumo:** {a['resumo']}")

    st.info(f"**O que fazer agora:** {a['orientacao']}")
    if a["sinais_de_risco"]:
        st.markdown("**Sinais de risco no seu relato:** " + "; ".join(a["sinais_de_risco"]))
    if r.get("revisao_sugerida"):
        st.caption("Um atendente vai conferir este pedido antes do encaminhamento final.")

    st.markdown("---")
    st.markdown("**O assunto está certo?** Se não estiver, escolha o correto. Sua correção ajuda a melhorar o sistema.")
    codigos = [c["codigo"] for c in api.categorias()]
    escolhida = st.selectbox("Assunto do pedido", codigos, index=codigos.index(a["categoria"]),
                             format_func=lambda c: nomes.get(c, c), key="categoria_confirmada")
    if r.get("segunda_opiniao") and r["segunda_opiniao"] != a["categoria"]:
        st.caption(f"Nosso modelo próprio sugeriu outro assunto: {nomes.get(r['segunda_opiniao'])}.")
    confirmo = st.checkbox("Confirmo que as informações estão corretas e quero enviar o pedido", key="confirmo")

    col_a, col_b = st.columns(2)
    if col_a.button("Enviar solicitação", type="primary", disabled=not confirmo, width="stretch"):
        dados = {
            "texto_mascarado": r["texto_mascarado"], "cep": entrada["cep"], "numero": entrada.get("numero") or None,
            "bairro": r["endereco"].get("bairro", ""), "categoria_sugerida": a["categoria"],
            "categoria_confirmada": escolhida, "urgencia": a["urgencia"], "fonte": r["fonte"],
        }
        try:
            with st.spinner("Enviando..."):
                solicitacao = api.confirmar(dados)
        except api.ErroApi as e:
            ui.mensagem_erro(e.mensagem, e.campos)
            return
        sessao.registrar_envio(solicitacao, a["resumo"])
        st.rerun()
    if col_b.button("Descartar e escrever de novo", width="stretch"):
        sessao.descartar_analise()
        st.rerun()


def mostrar() -> None:
    if st.session_state.ultimo_protocolo:
        st.success(f"Pedido enviado. Seu protocolo é **{st.session_state.ultimo_protocolo}**. "
                   "Acompanhe na aba Minhas solicitações.")
    if st.session_state.analise_atual:
        _resultado()
    else:
        st.markdown("Conte o problema com suas palavras. A inteligência artificial identifica o assunto, a urgência "
                    "e para onde enviar. **Você confere tudo antes de enviar.**")
        _formulario()
