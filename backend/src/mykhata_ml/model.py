"""TF-IDF (char + word n-grams) -> multinomial logistic regression."""

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_union


def build(cfg: dict[str, Any], seed: int) -> Pipeline:
    features = make_union(
        TfidfVectorizer(analyzer="char_wb", ngram_range=tuple(cfg["char_ngrams"]),
                        max_features=cfg["max_char_features"], sublinear_tf=True, dtype=np.float32),
        TfidfVectorizer(analyzer="word", ngram_range=tuple(cfg["word_ngrams"]), token_pattern=r"[a-z0]+",
                        max_features=cfg["max_word_features"], sublinear_tf=True, dtype=np.float32),
    )
    clf = LogisticRegression(C=cfg["C"], solver="saga", tol=cfg["tol"], max_iter=cfg["max_iter"], random_state=seed)
    return Pipeline([("features", features), ("clf", clf)])


def train(texts: list[str], y, cfg: dict[str, Any], seed: int) -> Pipeline:
    return build(cfg, seed).fit(texts, y)
