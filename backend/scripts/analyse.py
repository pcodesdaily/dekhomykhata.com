"""Statement (PDF or CSV) -> categorised transactions + spending insights (JSON)."""

import argparse
import json
from pathlib import Path

from mykhata_ml import export, insights
from mykhata_ml.config import load_config, path


def budget(item: str) -> tuple[str, float]:
    category, _, amount = item.partition("=")
    return category.strip().upper(), float(amount)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("statement", type=Path)
    ap.add_argument("--password", help="statement PDF password, if any")
    ap.add_argument("--budget", type=budget, action="append", default=[], metavar="CATEGORY=AMOUNT",
                    help="monthly budget, e.g. --budget FOOD_DINING=6000 (repeatable)")
    ap.add_argument("--out", type=Path, help="write the report JSON here (default: print)")
    args = ap.parse_args()

    cfg = load_config()
    pipe = export.load(path(cfg["output"]["artifacts"]))
    tx = export.categorise_statement(pipe, args.statement, cfg["default_threshold"], args.password)
    report = insights.report(tx, cfg["insights"], dict(args.budget) or None)
    report["transactions"] = tx.assign(date=tx["date"].dt.strftime("%Y-%m-%d")).to_dict(orient="records")
    text = json.dumps(report, indent=2, default=float)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
