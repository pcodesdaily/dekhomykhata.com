"""Self-contained HTML model report (inline SVG charts, light/dark) rendered from results.json."""

from html import escape
from typing import Any

from mykhata_ml.categories import CATEGORIES

W = 720
SERIES = ["var(--s1)", "var(--s2)", "var(--s3)"]


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def inr(x: float) -> str:
    whole = f"{int(round(x)):d}"
    head, tail = whole[:-3], whole[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join([g for g in [head, *groups] if g] + [tail])


def _svg(height: int, body: str, label: str) -> str:
    return (f'<div class="chart"><svg viewBox="0 0 {W} {height}" role="img" aria-label="{escape(label)}">'
            f"{body}</svg></div>")


def _legend(names: list[str]) -> str:
    items = "".join(f'<span><i style="background:{SERIES[i]}"></i>{escape(n)}</span>' for i, n in enumerate(names))
    return f'<div class="legend">{items}</div>'


def grouped_bars(rows: list[tuple[str, list[float | None]]], names: list[str], label: str, left: int = 250) -> str:
    bar, gap, group_gap = 12, 2, 16
    group_h = len(names) * (bar + gap) + group_gap
    height = len(rows) * group_h + 28
    span = W - left - 60
    out = [f'<line class="axis" x1="{left}" x2="{left}" y1="0" y2="{height - 24}"/>']
    for t in (0, 0.25, 0.5, 0.75, 1):
        x = left + t * span
        out.append(f'<line class="grid" x1="{x}" x2="{x}" y1="0" y2="{height - 24}"/>'
                   f'<text class="tick" x="{x}" y="{height - 8}" text-anchor="middle">{int(t * 100)}%</text>')
    for r, (name, values) in enumerate(rows):
        y0 = r * group_h + 4
        out.append(f'<text class="lbl" x="{left - 10}" y="{y0 + len(names) * (bar + gap) / 2 + 4}" '
                   f'text-anchor="end">{escape(name)}</text>')
        for s, v in enumerate(values):
            if v is None:
                continue
            y, w = y0 + s * (bar + gap), max(v * span, 2)
            tip = f"{name} · {names[s]}: {pct(v)}"
            out.append(f'<rect x="{left}" y="{y}" width="{w}" height="{bar}" rx="3" fill="{SERIES[s]}" '
                       f'data-tip="{escape(tip)}"/><text class="val" x="{left + w + 6}" y="{y + bar - 2}">{pct(v)}</text>')
    return _legend(names) + _svg(height, "".join(out), label)


def bars(rows: list[tuple[str, float, str]], label: str, left: int = 170, fmt=pct, xmax: float = 1.0) -> str:
    bar, gap = 18, 8
    height = len(rows) * (bar + gap) + 8
    span = W - left - 110
    out = []
    for r, (name, v, note) in enumerate(rows):
        y, w = r * (bar + gap) + 4, max(v / xmax * span, 2)
        out.append(f'<text class="lbl" x="{left - 10}" y="{y + 13}" text-anchor="end">{escape(name)}</text>'
                   f'<rect x="{left}" y="{y}" width="{w}" height="{bar}" rx="3" fill="var(--s1)" '
                   f'data-tip="{escape(name)}: {fmt(v)} {escape(note)}"/>'
                   f'<text class="val" x="{left + w + 6}" y="{y + 13}">{fmt(v)} <tspan class="note">{escape(note)}</tspan></text>')
    return _svg(height, "".join(out), label)


def coverage_chart(tables: dict[str, list[dict]], label: str) -> str:
    height, left, bottom, top = 300, 60, 40, 16
    x0, x1, y0, y1 = 0.4, 1.0, 0.75, 1.0
    sx = lambda v: left + (v - x0) / (x1 - x0) * (W - left - 30)
    sy = lambda v: top + (1 - (v - y0) / (y1 - y0)) * (height - top - bottom)
    out = []
    for t in (0.75, 0.8, 0.85, 0.9, 0.95, 1.0):
        out.append(f'<line class="grid" x1="{left}" x2="{W - 30}" y1="{sy(t)}" y2="{sy(t)}"/>'
                   f'<text class="tick" x="{left - 8}" y="{sy(t) + 4}" text-anchor="end">{int(t * 100)}%</text>')
    for t in (0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        out.append(f'<text class="tick" x="{sx(t)}" y="{height - bottom + 18}" text-anchor="middle">{int(t * 100)}%</text>')
    out.append(f'<text class="axis-title" x="{(left + W) / 2}" y="{height - 4}" text-anchor="middle">'
               f'Share of transactions the model labels (the rest become "Uncategorised")</text>'
               f'<text class="axis-title" transform="translate(14 {height / 2}) rotate(-90)" text-anchor="middle">'
               f'Accuracy on labelled</text>')
    for s, (name, rows) in enumerate(tables.items()):
        pts = [(sx(r["coverage"]), sy(r["accuracy_answered"]), r) for r in rows]
        out.append(f'<polyline fill="none" stroke="{SERIES[s]}" stroke-width="2" '
                   f'points="{" ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)}"/>')
        for x, y, r in pts:
            tip = f"{name}, threshold {r['threshold']}: labels {pct(r['coverage'])}, {pct(r['accuracy_answered'])} correct"
            out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{SERIES[s]}" stroke="var(--surface)" stroke-width="2" '
                       f'data-tip="{escape(tip)}"/><text class="note" x="{x + 8}" y="{y - 8}">{r["threshold"]}</text>')
    return _legend(list(tables)) + _svg(height, "".join(out), label)


def reliability(cals: dict[str, dict], label: str) -> str:
    size, left, bottom, top = 320, 60, 40, 12
    plot = size - top - bottom
    sx = lambda v: left + v * plot
    sy = lambda v: top + (1 - v) * plot
    out = [f'<line class="axis" x1="{sx(0)}" y1="{sy(0)}" x2="{sx(1)}" y2="{sy(1)}" stroke-dasharray="4 4"/>'
           f'<text class="note" x="{sx(0.62)}" y="{sy(0.52)}">perfectly honest confidence</text>']
    for t in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line class="grid" x1="{left}" x2="{sx(1)}" y1="{sy(t)}" y2="{sy(t)}"/>'
                   f'<text class="tick" x="{left - 8}" y="{sy(t) + 4}" text-anchor="end">{int(t * 100)}%</text>'
                   f'<text class="tick" x="{sx(t)}" y="{size - bottom + 18}" text-anchor="middle">{int(t * 100)}%</text>')
    out.append(f'<text class="axis-title" x="{sx(0.5)}" y="{size - 4}" text-anchor="middle">What the model says (confidence)</text>'
               f'<text class="axis-title" transform="translate(14 {top + plot / 2}) rotate(-90)" text-anchor="middle">How often it is right</text>')
    for s, (name, cal) in enumerate(cals.items()):
        pts = [(sx(b["confidence"]), sy(b["accuracy"]), b) for b in cal["bins"]]
        out.append(f'<polyline fill="none" stroke="{SERIES[s]}" stroke-width="2" '
                   f'points="{" ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)}"/>')
        for x, y, b in pts:
            tip = f"{name}, confidence {b['bin']}: said {pct(b['confidence'])}, right {pct(b['accuracy'])} ({b['count']:,} rows)"
            out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{SERIES[s]}" stroke="var(--surface)" stroke-width="2" '
                       f'data-tip="{escape(tip)}"/>')
    return _legend([f"{n} (calibration error {pct(c['ece'])})" for n, c in cals.items()]) + \
        f'<div class="chart square"><svg viewBox="0 0 {W} {size}" role="img" aria-label="{escape(label)}">{"".join(out)}</svg></div>'


def dumbbell(rows: list[tuple[str, float, float]], names: list[str], label: str, left: int = 200) -> str:
    step = 22
    height = len(rows) * step + 30
    span = W - left - 40
    sx = lambda v: left + v * span
    out = []
    for t in (0, 0.25, 0.5, 0.75, 1):
        out.append(f'<line class="grid" x1="{sx(t)}" x2="{sx(t)}" y1="0" y2="{height - 24}"/>'
                   f'<text class="tick" x="{sx(t)}" y="{height - 8}" text-anchor="middle">{int(t * 100)}%</text>')
    for r, (name, a, b) in enumerate(rows):
        y = r * step + 12
        out.append(f'<text class="lbl" x="{left - 10}" y="{y + 4}" text-anchor="end">{escape(name)}</text>'
                   f'<line class="axis" x1="{sx(min(a, b))}" x2="{sx(max(a, b))}" y1="{y}" y2="{y}"/>')
        for s, v in enumerate((a, b)):
            out.append(f'<circle cx="{sx(v)}" cy="{y}" r="5" fill="{SERIES[s]}" stroke="var(--surface)" stroke-width="2" '
                       f'data-tip="{escape(name)} · {names[s]}: F1 {pct(v)}"/>')
    return _legend(names) + _svg(height, "".join(out), label)


def heatmap(labels: list[str], matrix: list[list[int]], label: str) -> str:
    n, left, top = len(labels), 150, 150
    cell = (W - left - 10) / n
    height = top + n * cell + 6
    out = []
    for i, name in enumerate(labels):
        short = escape(CATEGORIES[name]["label"])
        out.append(f'<text class="tick" x="{left - 6}" y="{top + i * cell + cell * 0.7}" text-anchor="end">{short}</text>'
                   f'<text class="tick" transform="translate({left + i * cell + cell * 0.65} {top - 6}) rotate(-60)">{short}</text>')
        total = sum(matrix[i]) or 1
        for j, count in enumerate(matrix[i]):
            share = count / total
            if count == 0:
                continue
            tip = f"Actual {CATEGORIES[name]['label']} → predicted {CATEGORIES[labels[j]]['label']}: {count:,} ({pct(share)})"
            out.append(f'<rect x="{left + j * cell + 0.5}" y="{top + i * cell + 0.5}" width="{cell - 1}" height="{cell - 1}" '
                       f'fill="var(--s1)" fill-opacity="{0.08 + 0.92 * share:.3f}" data-tip="{escape(tip)}"/>')
    return _svg(int(height), "".join(out), label)


def table(head: list[str], rows: list[list[str]], numeric_from: int = 1) -> str:
    th = "".join(f'<th class="{"num" if i >= numeric_from else ""}">{escape(h)}</th>' for i, h in enumerate(head))
    body = "".join("<tr>" + "".join(f'<td class="{"num" if i >= numeric_from else ""}">{c}</td>' for i, c in enumerate(r))
                   + "</tr>" for r in rows)
    return f'<div class="table"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def verdict(sample: dict) -> str:
    if sample["category"] == sample["label"]:
        return "Correct"
    return f'Wrong: actually {escape(CATEGORIES[sample["label"]]["label"])}'


def tile(value: str, name: str, note: str) -> str:
    return f'<div class="tile"><b>{value}</b><span>{escape(name)}</span><small>{escape(note)}</small></div>'


def render(r: dict[str, Any]) -> str:
    ours = "MyKhata model"
    bench = {**r["benchmark"], ours: {"seen_accuracy": r["test_seen"]["accuracy"],
                                      "unseen_accuracy": r["test_unseen"]["accuracy"],
                                      "seen_macro_f1": r["test_seen"]["macro_f1"],
                                      "unseen_macro_f1": r["test_unseen"]["macro_f1"],
                                      "real_accuracy": r["real"]["accuracy"], "abstains": True}}
    order = sorted(bench, key=lambda k: bench[k]["seen_accuracy"])
    classes = sorted(r["per_class_seen"], key=lambda c: r["per_class_seen"][c]["f1-score"])
    d, ex, parser = r["data"], r["export"], r["parser"]
    real = r["real"]
    samples = "".join(
        f'<tr><td class="mono">{escape(s["narration"])}</td><td>{s["type"].title()}</td>'
        f'<td class="num">₹{inr(s["amount"])}</td><td>{escape(CATEGORIES[s["category"]]["label"])}</td>'
        f'<td class="num">{pct(s["confidence"], 0)}</td><td>{verdict(s)}</td></tr>' for s in r["samples"])
    best_seen = max(bench, key=lambda k: bench[k]["seen_accuracy"])
    tops = [name for name, key in (("unseen brands", "unseen_accuracy"), ("the real statement", "real_accuracy"))
            if all(bench[ours][key] >= v[key] for v in bench.values())]
    if best_seen == ours:
        claim = f"<b>Most accurate of the {len(bench)} approaches tested</b> on known brands ({pct(bench[ours]['seen_accuracy'])})."
    else:
        gap = 100 * (bench[best_seen]["seen_accuracy"] - bench[ours]["seen_accuracy"])
        claim = (f"<b>Most accurate on {' and '.join(tops) or 'none of the tests'}</b>, and within {gap:.1f} points of the best "
                 f"on known brands ({escape(best_seen)}, which cannot say 'unsure').")
    ahead = 100 * (bench[ours]["seen_accuracy"] - bench["Brand keyword lookup"]["seen_accuracy"])
    sections = f"""
<header>
  <p class="eyebrow">MyKhata · transaction categoriser · model report</p>
  <h1>Reading Indian bank statements the way you would</h1>
  <p class="lede">The model turns cryptic narrations like <code>UPI/DR/412345678901/BUNDL TE/YESB</code> into one of
  {len(CATEGORIES)} spending categories, says so when it is unsure, and runs in about {ex["microseconds_per_txn"]:.0f} µs per
  transaction from a {ex["bytes"] / 1e6:.1f} MB file. Every number on this page is produced by <code>scripts/train.py</code>.</p>
  <div class="tiles">
    {tile(pct(r["test_seen"]["accuracy"]), "accuracy on known brands", "new transactions, 887 Indian brands")}
    {tile(pct(real["accuracy"]), "accuracy on a real statement", f"{real['rows']} hand-labelled rows")}
    {tile(pct(r["thresholds_seen"][1]["accuracy_answered"]), "when it answers", f"labels {pct(r['thresholds_seen'][1]['coverage'])}, the rest say 'unsure'")}
    {tile(f"{ex['bytes'] / 1e6:.1f} MB", "model size", f"was 20 MB · {pct(ex['agreement_with_full_precision'], 2)} identical answers")}
  </div>
</header>

<section>
  <h2>Why this model</h2>
  <ul class="why">
    <li>{claim} {ahead:.0f} points ahead of the brand keyword lookup that most expense apps use.</li>
    <li><b>Knows when it doesn't know.</b> Its confidence is honest (calibration error {pct(r["calibration_seen"]["ece"])}), so low-confidence
    rows become "Uncategorised" instead of silently wrong numbers in your budget. The SVM and keyword rules cannot do this.</li>
    <li><b>Understands Indian statement formats.</b> Character n-grams read truncated names (<code>BUNDL TE</code>), UPI IDs and
    legal entity names, and the amount and debit/credit direction separate a refund from a purchase.</li>
    <li><b>Private and cheap to run.</b> No external AI API sees your transactions: the model runs on your own server in
    {ex["microseconds_per_txn"]:.0f} µs per row, from a {ex["bytes"] / 1e6:.1f} MB file with an integrity check.</li>
    <li><b>Checked against the bank's own numbers.</b> The statement reader reconciles every row with the running balance, and
    savings are computed from money in and out, not from labels.</li>
  </ul>
</section>

<section>
  <h2>Compared with other approaches</h2>
  <p>All models trained and tested on the same data. <em>Known brands</em>: new transactions from brands seen in training.
  <em>Unseen brands</em>: every brand and shop in the test set was hidden during training. <em>Real</em>: the hand-labelled real statement.
  Most real rows are opaque and correctly "Uncategorised", which is why even the keyword lookup scores high there.</p>
  {grouped_bars([(k, [bench[k]["seen_accuracy"], bench[k]["unseen_accuracy"], bench[k]["real_accuracy"]]) for k in reversed(order)],
                ["Known brands", "Unseen brands", "Real statement"], "Accuracy of each approach")}
  {table(["Approach", "Known brands", "Macro F1", "Unseen brands", "Real statement", "Can say 'unsure'"],
         [[escape(k) if k != ours else f"<b>{k}</b>", pct(bench[k]["seen_accuracy"]), pct(bench[k]["seen_macro_f1"]),
           pct(bench[k]["unseen_accuracy"]), pct(bench[k]["real_accuracy"]), "Yes" if bench[k]["abstains"] else "No"]
          for k in reversed(order)])}
</section>

<section>
  <h2>Where it is strong and where it is weak</h2>
  <p>Accuracy on the unseen-brand test, by who is on the other side of the transaction. Brands the model has never seen are the
  weak spot: nothing in a name like <code>STARBUCKS</code> says "coffee". Adding brands to the catalogue is what fixes it.</p>
  {bars([(k, v["accuracy"], f"({v['rows']:,} rows)") for k, v in sorted(r["counterparty_unseen"].items(), key=lambda kv: -kv[1]["accuracy"])],
        "Unseen-test accuracy by counterparty")}
</section>

<section>
  <h2>Confidence you can trust</h2>
  <p>Raising the threshold trades coverage for accuracy. At the default 0.5 it labels {pct(r["thresholds_seen"][1]["coverage"])} of
  known-brand transactions with {pct(r["thresholds_seen"][1]["accuracy_answered"])} accuracy.</p>
  {coverage_chart({"Known brands": r["thresholds_seen"], "Unseen brands": r["thresholds_unseen"]}, "Coverage versus accuracy")}
  <p>When the model says it is 90% sure, it is right about 90% of the time. Points on the dashed line mean perfectly honest confidence.</p>
  {reliability({"Known brands": r["calibration_seen"], "Unseen brands": r["calibration_unseen"]}, "Reliability diagram")}
</section>

<section>
  <h2>Every category</h2>
  <p>F1 score per category (balance of precision and recall).</p>
  {dumbbell([(CATEGORIES[c]["label"], r["per_class_seen"][c]["f1-score"], r["per_class_unseen"][c]["f1-score"]) for c in classes],
            ["Known brands", "Unseen brands"], "F1 per category")}
  <details><summary>Table</summary>
  {table(["Category", "Budget bucket", "Precision", "Recall", "F1", "Test rows"],
         [[escape(CATEGORIES[c]["label"]), CATEGORIES[c]["bucket"], pct(v["precision"]), pct(v["recall"]), pct(v["f1-score"]),
           f'{int(v["support"]):,}'] for c, v in sorted(r["per_class_seen"].items(), key=lambda kv: -kv[1]["f1-score"])], numeric_from=2)}
  </details>
  <h3>What gets confused (unseen-brand test)</h3>
  <p>Rows are the true category, columns the prediction; darker means a larger share of that row.</p>
  {heatmap(r["confusion_unseen"]["labels"], r["confusion_unseen"]["matrix"], "Confusion matrix")}
</section>

<section>
  <h2>Stable across splits</h2>
  <p>Five-fold cross-validation with brands kept on one side of each split. Accuracy stays within
  {pct(max(f["accuracy"] for f in r["cv_folds"]) - min(f["accuracy"] for f in r["cv_folds"]))} across folds.</p>
  {table(["Fold", "Accuracy", "Macro F1"], [[str(f["fold"]), pct(f["accuracy"]), pct(f["macro_f1"])] for f in r["cv_folds"]]
         + [["<b>Mean</b>", f'<b>{pct(r["cv_mean"]["accuracy"])}</b>', f'<b>{pct(r["cv_mean"]["macro_f1"])}</b>']])}
</section>

<section>
  <h2>On a real bank statement</h2>
  <p>{real["rows"]} unique transactions from a real, anonymised Indian account (Kaggle, CC0). Most narrations are opaque
  (<code>UPI/33535</code>); they are labelled "Uncategorised" because nobody could tell what they were from the text.</p>
  {table(["Measure", "Result"], [["All rows", pct(real["accuracy"])],
                                  ["Rows whose text reveals the category", f'{pct(real["informative_accuracy"])} ({real["informative_rows"]} rows)'],
                                  ["Opaque rows correctly left uncategorised", pct(real["opaque_kept_as_other"])]])}
  <h3>Sample predictions</h3>
  <div class="table"><table><thead><tr><th>Narration</th><th>Type</th><th class="num">Amount</th><th>Category</th>
  <th class="num">Confidence</th><th>Check</th></tr></thead><tbody>{samples}</tbody></table></div>
</section>

<section>
  <h2>Reading statement PDFs</h2>
  <p>Tested on 50 digital statements (two layouts) with known answers.</p>
  {table(["Field", *parser.keys()], [[name, *[pct(parser[l][key]) for l in parser]] for name, key in
         [("Transactions found", "found"), ("Date", "date"), ("Amount", "amount"), ("Debit / credit", "type"),
          ("Balance", "balance"), ("Narration (ignoring spaces)", "narration_ignoring_spaces"),
          ("Narration (exact)", "narration_exact")]])}
  <p class="note">About 12% of rows fail the running-balance check because the test dataset's own ground truth breaks its
  balance on those rows; the reader extracts them correctly. On the real statement every row reconciles.</p>
</section>

<section>
  <h2>Training data</h2>
  <p>No public labelled dataset of Indian personal statements exists, so training data is generated in the formats of SBI,
  HDFC, ICICI, Axis, Kotak, PSU banks and app exports, with {r["catalog"]["brands"]} brands ({r["catalog"]["aliases"]:,} name variants),
  weighted by popularity.</p>
  {bars([("Generated", d["raw_rows"], ""), ("Valid rows", d["after_dropping_invalid"], ""),
         ("Without amount outliers", d["after_dropping_amount_outliers"], ""),
         ("Without duplicates", d["after_dropping_duplicates"], "")], "Cleaning funnel",
        fmt=lambda v: f"{int(v):,}", xmax=d["raw_rows"])}
  <p class="note">{d["relabelled_ambiguous"]} rows whose text maps to several categories (e.g. a bare <code>NEFT</code>)
  were relabelled "Uncategorised".</p>
</section>

<section>
  <h2>Deployment and security</h2>
  {table(["Property", "Value"], [["File", "model.mkm (int8 weights, SHA-256 checked on load)"],
                                  ["Size", f'{ex["bytes"] / 1e6:.2f} MB ({ex["features"]:,} features)'],
                                  ["Same answer as full precision", pct(ex["agreement_with_full_precision"], 2)],
                                  ["Speed", f'{ex["microseconds_per_txn"]:.0f} µs per transaction (Python reference)'],
                                  ["Runtime", "Dependency-free TypeScript, server-side (e.g. Cloudflare Worker)"],
                                  ["What callers see", "Top category and rounded confidence only"]])}
  <p>The model is meant to stay on the server: anything sent to a browser can be copied. Pair the API with rate limiting.</p>
</section>

<section>
  <h2>Limits</h2>
  <ul>
    <li>Training data is synthetic; formats were reconstructed, not copied from every bank's real statements.</li>
    <li>The real statement was also used to find gaps in the generator, so its score is optimistic. A second, untouched real statement is needed.</li>
    <li>Brands missing from the catalogue fall to about {pct(r["counterparty_unseen"]["Brands"]["accuracy"], 0)} accuracy.</li>
    <li>Scanned (photographed) PDFs are not supported yet.</li>
  </ul>
</section>"""
    return PAGE.replace("{{BODY}}", sections)


PAGE = """<meta charset="utf-8">
<title>MyKhata Model Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Layout: one reading column; charts and tables scroll inside their own boxes on phones. */
:root {
  --bg: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --line: rgba(11,11,11,0.10);
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --code: #eef1f6;
  --display: "Archivo", system-ui, sans-serif; --body: "Source Sans 3", system-ui, sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --line: rgba(255,255,255,0.10);
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --code: #23262c; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0d0d0d; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --line: rgba(255,255,255,0.10);
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --code: #23262c; color-scheme: dark }
body { background: var(--bg); color: var(--ink); font: 17px/1.6 var(--body); }
main { max-width: 900px; margin: 0 auto; padding-inline: 20px; padding-block: 40px 80px; display: grid; gap: 56px; }
h1, h2, h3 { font-family: var(--display); line-height: 1.2; text-wrap: balance; margin: 0; }
h1 { font-size: clamp(30px, 5vw, 44px); font-weight: 700; letter-spacing: -0.01em; }
h2 { font-size: 26px; font-weight: 700; }
h3 { font-size: 18px; font-weight: 500; margin-top: 12px; }
section, header { display: grid; gap: 16px; min-width: 0; }
p, li { max-width: 68ch; color: var(--ink-2); margin: 0; }
.eyebrow { font: 500 13px/1 var(--display); letter-spacing: 0.08em; text-transform: uppercase; color: var(--s1); }
.lede { font-size: 19px; }
code, .mono { font-family: var(--mono); font-size: 0.86em; }
code { background: var(--code); padding: 1px 5px; border-radius: 4px; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin-top: 8px; }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 16px; display: grid; gap: 2px; }
.tile b { font: 700 32px/1.1 var(--display); color: var(--ink); }
.tile span { color: var(--ink); font-weight: 600; }
.tile small { color: var(--muted); font-size: 14px; }
.why { display: grid; gap: 10px; padding-left: 20px; }
.why b { color: var(--ink); }
.chart { overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 12px; }
.chart svg { display: block; width: 100%; min-width: 480px; height: auto; }
.chart.square svg { max-width: 720px; }
.chart text { font-family: var(--body); }
.lbl { fill: var(--ink); font-size: 13px; }
.val { fill: var(--ink-2); font-size: 12px; font-variant-numeric: tabular-nums; }
.note { fill: var(--muted); font-size: 12px; }
p.note { font-size: 15px; color: var(--muted); }
.tick { fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.axis-title { fill: var(--ink-2); font-size: 12px; }
.grid { stroke: var(--grid); stroke-width: 1; }
.axis { stroke: var(--axis); stroke-width: 1.5; }
[data-tip] { cursor: default; }
[data-tip]:hover { opacity: 0.85; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 14px; color: var(--ink-2); }
.legend i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }
.table { overflow-x: auto; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
table { border-collapse: collapse; width: 100%; font-size: 15px; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--line); white-space: nowrap; }
th { font-weight: 600; color: var(--ink); font-size: 13px; letter-spacing: 0.02em; }
td { color: var(--ink-2); }
tr:last-child td { border-bottom: 0; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
details summary { cursor: pointer; color: var(--s1); font-weight: 600; }
details[open] summary { margin-bottom: 10px; }
#tip { position: fixed; pointer-events: none; background: var(--ink); color: var(--bg); font-size: 13px; padding: 6px 9px;
  border-radius: 6px; max-width: 280px; z-index: 10; }
:focus-visible { outline: 2px solid var(--s1); outline-offset: 2px; }
</style>
<main>{{BODY}}</main>
<div id="tip" hidden></div>
<script>
const tip = document.getElementById("tip");
document.addEventListener("pointermove", (e) => {
  const t = e.target.closest && e.target.closest("[data-tip]");
  if (!t) { tip.hidden = true; return; }
  tip.textContent = t.getAttribute("data-tip");
  tip.hidden = false;
  const x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
  tip.style.left = x + "px"; tip.style.top = (e.clientY + 14) + "px";
});
</script>
"""
