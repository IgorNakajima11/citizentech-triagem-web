import streamlit as st

from providers import api
from state import sessao
from ui import componentes as ui

ROTULO_AVALIACAO = {"util": "Você marcou como útil", "incorreta": "Você marcou como incorreta"}


def mostrar() -> None:
    historico = st.session_state.historico
    if not historico:
        ui.estado_vazio("Você ainda não enviou nenhuma solicitação nesta sessão.",
                        "Use a aba Fazer um relato. Os pedidos enviados aparecem aqui com o protocolo.")
        return
    nomes = {c["codigo"]: c["nome"] for c in api.categorias()}
    st.caption(f"{len(historico)} solicitação(ões) enviada(s) nesta sessão.")
    for item in historico:
        linhas = [("Protocolo", item["protocolo"]), ("Enviado para", item["secretaria"]),
                  ("Prazo estimado", f"até {item['prazo_dias']} dia(s)"), ("Resumo", item.get("resumo", ""))]
        if item["corrigida_pelo_cidadao"]:
            linhas.append(("Assunto", f"corrigido por você para {nomes.get(item['categoria_confirmada'])}"))
        ui.cartao_solicitacao(nomes.get(item["categoria_confirmada"], item["categoria_confirmada"]), item["urgencia"], linhas)
        if item.get("avaliacao"):
            st.caption(ROTULO_AVALIACAO[item["avaliacao"]] + ". Obrigado pelo retorno.")
            continue
        st.caption("A análise da inteligência artificial ajudou?")
        c1, c2, _ = st.columns([1, 1, 3])
        for coluna, valor, rotulo in ((c1, "util", "Foi útil"), (c2, "incorreta", "Estava incorreta")):
            if coluna.button(rotulo, key=f"{valor}_{item['protocolo']}", width="stretch"):
                try:
                    api.avaliar(item["protocolo"], valor)
                    sessao.registrar_avaliacao(item["protocolo"], valor)
                    st.rerun()
                except api.ErroApi as e:
                    ui.mensagem_erro(e.mensagem)
