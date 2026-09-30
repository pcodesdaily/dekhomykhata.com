// Checks the TypeScript runtime against Python's predictions (artifacts/golden.json, written by train.py).
// Run: node --test web/parity.test.ts

import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { loadModel, type Transaction } from "./categoriser.ts";

const artifacts = new URL("../artifacts/", import.meta.url);
const bytes = readFileSync(new URL("model.mkm", artifacts));
const golden: { input: Transaction; category: string; confidence: number }[] =
  JSON.parse(readFileSync(new URL("golden.json", artifacts), "utf-8"));

test("matches Python on every golden case", async () => {
  const model = await loadModel(bytes);
  let mismatches = 0;
  for (const g of golden) {
    const p = model.categorise(g.input);
    const borderline = Math.abs(g.confidence - model.threshold) < 0.001;
    if (!borderline && (p.category !== g.category || Math.abs(p.confidence - g.confidence) > 0.011)) mismatches++;
  }
  assert.equal(mismatches, 0, `${mismatches} of ${golden.length} predictions differ from Python`);
});

test("rejects a tampered model", async () => {
  const tampered = new Uint8Array(bytes);
  tampered[tampered.length - 1] ^= 0xff;
  await assert.rejects(loadModel(tampered), /integrity/);
});

test("validates input", async () => {
  const model = await loadModel(bytes);
  assert.throws(() => model.categorise({ narration: "AMZN", type: "BOTH" as never, amount: 10 }), /DEBIT or CREDIT/);
  assert.throws(() => model.categorise({ narration: "AMZN", type: "DEBIT", amount: Number.NaN }), /finite/);
  const long = model.categorise({ narration: "UPI/SWIGGY/".repeat(10_000), type: "DEBIT", amount: 250 });
  assert.equal(typeof long.category, "string");
});
