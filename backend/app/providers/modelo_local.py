import csv
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from ..config import configuracao


@lru_cache(maxsize=1)
def modelo() -> Pipeline:
    with configuracao.caminho_treino.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    atributos = FeatureUnion([
        ("palavras", TfidfVectorizer(strip_accents="unicode", ngram_range=(1, 2), sublinear_tf=True)),
        ("caracteres", TfidfVectorizer(strip_accents="unicode", analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    pipe = Pipeline([("atributos", atributos), ("classificador", LogisticRegression(max_iter=3000, C=4.0))])
    return pipe.fit([l["texto"] for l in linhas], [l["categoria"] for l in linhas])


def classificar(texto: str) -> tuple[str, float]:
    m = modelo()
    probs = m.predict_proba([texto])[0]
    i = probs.argmax()
    return str(m.classes_[i]), float(probs[i])
