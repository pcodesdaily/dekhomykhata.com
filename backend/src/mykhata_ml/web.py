"""Compact, dependency-free model format (.mkm) shared by Python and the TypeScript runtime in web/.

Layout (little-endian): b"MKHM" | u32 header length | header JSON | payload
payload = char vocab | word vocab (UTF-8, "\\0"-separated) | idf float32 | coef int8 [feature x class]
Coefficients are quantised per class (scale = max|coef| / 127). The header stores the payload's SHA-256.
"""

import hashlib
import json
import math
import re
import struct
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.pipeline import Pipeline

from mykhata_ml.categories import CATEGORIES

MAGIC = b"MKHM"
VERSION = 1


def write(pipe: Pipeline, file: Path, threshold: float) -> dict:
    (_, char), (_, word) = pipe.named_steps["features"].transformer_list
    clf = pipe.named_steps["clf"]
    vocab = [sorted(v.vocabulary_, key=v.vocabulary_.get) for v in (char, word)]
    blobs = ["\0".join(terms).encode("utf-8") for terms in vocab]
    idf = np.concatenate([char.idf_, word.idf_]).astype("<f4")
    scale = np.abs(clf.coef_).max(axis=1) / 127
    quant = np.round(clf.coef_ / scale[:, None]).astype(np.int8).T
    payload = blobs[0] + blobs[1] + idf.tobytes() + np.ascontiguousarray(quant).tobytes()
    header = {
        "version": VERSION, "classes": clf.classes_.tolist(), "threshold": threshold, "fallback": "OTHER",
        "categories": {c: CATEGORIES[c] for c in clf.classes_},
        "char": {"ngram": list(char.ngram_range), "size": len(vocab[0]), "bytes": len(blobs[0])},
        "word": {"ngram": list(word.ngram_range), "size": len(vocab[1]), "bytes": len(blobs[1]),
                 "token_pattern": word.token_pattern},
        "scale": scale.tolist(), "intercept": clf.intercept_.tolist(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    head = json.dumps(header, separators=(",", ":")).encode("utf-8")
    file.write_bytes(MAGIC + struct.pack("<I", len(head)) + head + payload)
    return header


def char_wb_ngrams(text: str, lo: int, hi: int) -> list[str]:
    grams = []
    for word in text.split():
        w = f" {word} "
        for n in range(lo, hi + 1):
            grams.extend(w[i:i + n] for i in range(max(len(w) - n + 1, 1)))
            if len(w) <= n:
                break
    return grams


def word_ngrams(text: str, pattern: re.Pattern, lo: int, hi: int) -> list[str]:
    tokens = pattern.findall(text)
    return [" ".join(tokens[i:i + n]) for n in range(lo, hi + 1) for i in range(len(tokens) - n + 1)]


class WebModel:
    """Pure-NumPy reader for .mkm files; mirrors web/categoriser.ts."""

    def __init__(self, file: Path):
        raw = Path(file).read_bytes()
        if raw[:4] != MAGIC:
            raise ValueError("not a MyKhata model file")
        size = struct.unpack("<I", raw[4:8])[0]
        self.header = h = json.loads(raw[8:8 + size])
        payload = raw[8 + size:]
        if hashlib.sha256(payload).hexdigest() != h["sha256"]:
            raise ValueError("model file failed its integrity check")
        cb, wb = h["char"]["bytes"], h["word"]["bytes"]
        n_char, n_word, n_cls = h["char"]["size"], h["word"]["size"], len(h["classes"])
        self.char_vocab = {t: i for i, t in enumerate(payload[:cb].decode("utf-8").split("\0"))}
        self.word_vocab = {t: i for i, t in enumerate(payload[cb:cb + wb].decode("utf-8").split("\0"))}
        at = cb + wb
        self.idf = np.frombuffer(payload, "<f4", n_char + n_word, at)
        quant = np.frombuffer(payload, np.int8, (n_char + n_word) * n_cls, at + 4 * (n_char + n_word))
        self.weights = quant.reshape(n_char + n_word, n_cls).astype(np.float32) * np.float32(h["scale"])
        self.intercept = np.array(h["intercept"], np.float32)
        self.classes_ = np.array(h["classes"])
        self.pattern = re.compile(h["word"]["token_pattern"])
        self.n_char = n_char

    def _block(self, grams: list[str], vocab: dict[str, int], offset: int) -> tuple[list[int], np.ndarray]:
        counts = Counter(g for g in grams if g in vocab)
        idx = [vocab[g] + offset for g in counts]
        vals = np.array([(1 + math.log(c)) for c in counts.values()], np.float32) * self.idf[idx]
        norm = np.linalg.norm(vals)
        return idx, vals / norm if norm else vals

    def features(self, text: str) -> tuple[list[int], np.ndarray]:
        h = self.header
        ci, cv = self._block(char_wb_ngrams(text, *h["char"]["ngram"]), self.char_vocab, 0)
        wi, wv = self._block(word_ngrams(text, self.pattern, *h["word"]["ngram"]), self.word_vocab, self.n_char)
        return ci + wi, np.concatenate([cv, wv])

    def predict_proba(self, texts) -> np.ndarray:
        out = np.empty((len(texts), len(self.classes_)), np.float32)
        for r, text in enumerate(texts):
            idx, vals = self.features(text)
            scores = self.intercept + vals @ self.weights[idx]
            exp = np.exp(scores - scores.max())
            out[r] = exp / exp.sum()
        return out
