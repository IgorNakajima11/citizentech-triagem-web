from fastapi.testclient import TestClient

from app.main import app
from app.providers import llm_groq

cliente = TestClient(app)

RESPOSTA_OK = {
    "categoria": "iluminacao_publica", "urgencia": "media", "resumo": "Poste apagado na rua.",
    "orientacao": "Seu pedido foi registrado.", "sinais_de_risco": [], "confianca": 0.93,
}
RELATO = {"texto": "O poste da minha rua está apagado há uma semana, fica tudo escuro", "cep": "01310-100", "numero": "900"}


def test_fluxo_completo_com_llm(monkeypatch):
    monkeypatch.setattr(llm_groq, "chamar_json", lambda s, u: RESPOSTA_OK)
    r = cliente.post("/api/triagem/analisar", json=RELATO)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["fonte"] == "llm"
    assert corpo["analise"]["categoria"] == "iluminacao_publica"
    assert corpo["secretaria"].startswith("Secretaria de Serviços Urbanos")
    assert corpo["endereco"]["validado"] is True

    confirmacao = {"texto_mascarado": corpo["texto_mascarado"], "cep": "01310100", "numero": "900",
                   "bairro": "Bela Vista", "categoria_sugerida": "iluminacao_publica",
                   "categoria_confirmada": "iluminacao_publica", "urgencia": "media", "fonte": "llm"}
    r2 = cliente.post("/api/solicitacoes", json=confirmacao)
    assert r2.status_code == 201
    protocolo = r2.json()["protocolo"]
    assert protocolo.startswith("PRT-")
    assert any(s["protocolo"] == protocolo for s in cliente.get("/api/solicitacoes").json())
    assert cliente.post(f"/api/solicitacoes/{protocolo}/avaliacao", json={"avaliacao": "util"}).status_code == 204


def test_llm_fora_do_ar_usa_modelo_proprio(monkeypatch):
    def falha(s, u):
        raise llm_groq.LLMIndisponivel("tempo esgotado")
    monkeypatch.setattr(llm_groq, "chamar_json", falha)
    r = cliente.post("/api/triagem/analisar", json=RELATO)
    assert r.status_code == 200
    assert r.json()["fonte"] == "modelo_local"
    assert r.json()["analise"]["categoria"] == "iluminacao_publica"
    assert r.json()["aviso"]


def test_resposta_invalida_do_llm_tenta_de_novo_e_cai_no_modelo_proprio(monkeypatch):
    chamadas = []

    def invalida(s, u):
        chamadas.append(1)
        return {"categoria": "inventada", "urgencia": "altissima"}
    monkeypatch.setattr(llm_groq, "chamar_json", invalida)
    r = cliente.post("/api/triagem/analisar", json=RELATO)
    assert r.status_code == 200
    assert r.json()["fonte"] == "modelo_local"
    assert len(chamadas) == 2


def test_fio_exposto_sem_llm_vira_urgencia_alta(monkeypatch):
    monkeypatch.setattr(llm_groq, "chamar_json", lambda s, u: (_ for _ in ()).throw(llm_groq.LLMIndisponivel("x")))
    r = cliente.post("/api/triagem/analisar", json={"texto": "Tem um fio solto caído no chão perto da escola", "cep": "01310100"})
    assert r.json()["analise"]["urgencia"] == "alta"
    assert r.json()["prazo_dias"] == 1


def test_validacao_de_entrada():
    r = cliente.post("/api/triagem/analisar", json={"texto": "curto", "cep": "123"})
    assert r.status_code == 422
    campos = {c["campo"] for c in r.json()["campos"]}
    assert campos == {"texto", "cep"}


def test_dados_pessoais_nao_vao_para_o_llm(monkeypatch):
    enviado = {}

    def captura(s, u):
        enviado["u"] = u
        return RESPOSTA_OK
    monkeypatch.setattr(llm_groq, "chamar_json", captura)
    cliente.post("/api/triagem/analisar", json={
        "texto": "Poste apagado, meu cpf 123.456.789-09 e telefone (11) 98888-7777", "cep": "01310100"})
    assert "123.456.789-09" not in enviado["u"] and "98888-7777" not in enviado["u"]
    assert "[CPF]" in enviado["u"] and "[TELEFONE]" in enviado["u"]


def test_cep_inexistente_pede_revisao(monkeypatch):
    monkeypatch.setattr(llm_groq, "chamar_json", lambda s, u: RESPOSTA_OK)
    r = cliente.post("/api/triagem/analisar", json={**RELATO, "cep": "99999999"})
    assert r.json()["endereco"]["validado"] is False
    assert r.json()["revisao_sugerida"] is True


def test_cors_restrito():
    r = cliente.options("/api/saude", headers={"Origin": "https://site-estranho.com", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") != "*"
    assert r.headers.get("access-control-allow-origin") != "https://site-estranho.com"
