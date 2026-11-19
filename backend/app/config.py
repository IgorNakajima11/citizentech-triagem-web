import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ_BACKEND = Path(__file__).resolve().parent.parent


def _carregar_env(caminho: Path) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


_carregar_env(RAIZ_BACKEND / ".env")


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


@dataclass(frozen=True)
class Configuracao:
    groq_api_key: str = field(default_factory=lambda: os.environ.get("GROQ_API_KEY", ""))
    groq_modelo: str = field(default_factory=lambda: os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"))
    groq_url: str = field(default_factory=lambda: os.environ.get(
        "GROQ_URL", "https://api.groq.com/openai/v1/chat/completions"))
    llm_timeout_s: float = field(default_factory=lambda: float(os.environ.get("LLM_TIMEOUT_S", "20")))
    viacep_url: str = field(default_factory=lambda: os.environ.get("VIACEP_URL", "https://viacep.com.br/ws/{cep}/json/"))
    viacep_timeout_s: float = field(default_factory=lambda: float(os.environ.get("VIACEP_TIMEOUT_S", "5")))
    origens_permitidas: list[str] = field(default_factory=lambda: _lista(
        os.environ.get("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501")))
    caminho_banco: Path = field(default_factory=lambda: Path(
        os.environ.get("DB_PATH", str(RAIZ_BACKEND / "dados" / "solicitacoes.db"))))
    caminho_treino: Path = RAIZ_BACKEND / "app" / "dados" / "solicitacoes_treino.csv"

    @property
    def llm_configurado(self) -> bool:
        return bool(self.groq_api_key)


configuracao = Configuracao()
