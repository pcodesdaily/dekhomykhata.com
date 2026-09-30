"""Generate -> clean -> CV + tests + baselines -> final model -> compact export -> real + parser eval -> report."""

import json
import time

import numpy as np
import pandas as pd

from mykhata_ml import catalog, data, evaluate, export, report, statement
from mykhata_ml import model as mdl
from mykhata_ml.config import load_config, path


def fit_and_test(df, tr, te, cfg, seed):
    train, test = df.iloc[tr], df.iloc[te]
    pipe = mdl.train(data.texts(train), train["category"], cfg["model"], seed)
    proba = pipe.predict_proba(data.texts(test))
    return pipe, test, proba, pipe.classes_[proba.argmax(1)]


def parser_eval(pattern: str) -> dict[str, dict[str, float]]:
    rows = []
    for pdf in sorted(path(".").glob(pattern)):
        parsed = statement.parse(pdf)
        truth = data.load_statement_truth(pdf.with_suffix(".json"))
        scores = evaluate.parser_scores(parsed, truth)
        rows.append({"layout": pdf.parent.name.replace("digital_", "Layout ").replace("type", ""),
                     "found": min(scores["parsed_rows"], scores["truth_rows"]) / scores["truth_rows"],
                     "balance_check_pass": statement.balance_check(parsed).mean(), **scores})
    return pd.DataFrame(rows).groupby("layout").mean().to_dict(orient="index")


def main() -> None:
    cfg = load_config()
    seed, threshold, test_size = cfg["seed"], cfg["default_threshold"], cfg["split"]["test_size"]
    reports, artifacts = path(cfg["output"]["reports"]), path(cfg["output"]["artifacts"])
    reports.mkdir(parents=True, exist_ok=True)

    df, stats = data.clean(data.generate(cfg))
    splits = {"unseen": data.split(df, test_size, seed), "seen": data.random_split(df, test_size, seed)}
    stats |= {"train_rows": len(splits["unseen"][0]), "test_rows": len(splits["unseen"][1])}
    print(stats, flush=True)

    folds = evaluate.cross_validate(df.iloc[splits["unseen"][0]].reset_index(drop=True), cfg, seed)
    print("cv", folds, flush=True)

    results = {"data": stats, "class_counts": df["category"].value_counts().to_dict(), "cv_folds": folds,
               "cv_mean": {k: float(np.mean([f[k] for f in folds])) for k in folds[0] if k != "fold"},
               "catalog": {"brands": sum(len(v) for v in catalog.MERCHANTS.values()),
                           "aliases": sum(len(a) for v in catalog.MERCHANTS.values() for a in v)}}
    for name, (tr, te) in splits.items():
        pipe, test, proba, pred = fit_and_test(df, tr, te, cfg, seed)
        results[f"test_{name}"] = evaluate.metrics(test["category"], pred)
        results[f"per_class_{name}"] = evaluate.per_class(test["category"], pred)
        results[f"thresholds_{name}"] = evaluate.threshold_table(test["category"], proba, pipe.classes_, cfg["thresholds"])
        results[f"calibration_{name}"] = evaluate.calibration(test["category"], proba, pipe.classes_)
        results[f"counterparty_{name}"] = evaluate.by_counterparty(test, pred)
        if name == "unseen":
            labels = list(pipe.classes_)
            results["confusion_unseen"] = {"labels": labels, "matrix": evaluate.confusion(test["category"], pred, labels)}
        print(name, results[f"test_{name}"], flush=True)

    real = data.load_real(cfg)
    alias_map = {e[0]: [(a, cat) for a in e] for cat, entries in catalog.MERCHANTS.items() for e in entries}
    results["benchmark"] = evaluate.benchmark(df, splits, real, df["merchant_id"].map(alias_map))
    print("benchmark", results["benchmark"], flush=True)

    final = mdl.train(data.texts(df), df["category"], cfg["model"], seed)
    golden_rows = pd.concat([df.sample(1500, random_state=seed), real])[["narration", "type", "amount"]]
    header = export.save(final, artifacts, threshold, golden_rows)
    model = export.load(artifacts)
    check = df.sample(5000, random_state=seed + 1)
    start = time.perf_counter()
    shipped_pred = model.classes_[model.predict_proba(data.texts(check)).argmax(1)]
    results["export"] = {"bytes": (artifacts / export.MODEL_FILE).stat().st_size,
                         "features": header["char"]["size"] + header["word"]["size"],
                         "microseconds_per_txn": (time.perf_counter() - start) / len(check) * 1e6,
                         "agreement_with_full_precision": float((shipped_pred == final.predict(data.texts(check))).mean())}
    print("export", results["export"], flush=True)

    real_pred = export.categorise(model, real["narration"], real["type"], real["amount"], threshold)
    real_pred.insert(3, "label", real["category"].to_numpy())
    real_pred.to_csv(reports / "real_predictions.csv", index=False)
    results["real"] = evaluate.real(real["category"], real_pred["category"])
    shown = real_pred[real_pred["category"] != "OTHER"].drop_duplicates("category").head(6)
    opaque = real_pred[real_pred["category"] == "OTHER"].head(2)
    results["samples"] = pd.concat([shown, opaque])[["narration", "type", "amount", "category", "label", "confidence"]] \
        .to_dict(orient="records")
    print("real", results["real"], flush=True)

    results["parser"] = parser_eval(cfg["data"]["statements_glob"])
    print("parser", results["parser"], flush=True)

    (reports / "results.json").write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    (reports / "report.html").write_text(report.render(json.loads(json.dumps(results, default=float))), encoding="utf-8")
    print("done", flush=True)


if __name__ == "__main__":
    main()
