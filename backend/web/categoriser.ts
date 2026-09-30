// MyKhata transaction categoriser: dependency-free runtime for .mkm models (see src/mykhata_ml/web.py).
// Meant to run server-side (e.g. a Cloudflare Worker) so the model file is never sent to browsers.

export type TxType = "DEBIT" | "CREDIT";

export interface Transaction {
  narration: string;
  type: TxType;
  amount: number;
}

export interface Prediction {
  category: string;
  label: string;
  bucket: string;
  confidence: number;
}

interface Header {
  version: number;
  classes: string[];
  threshold: number;
  fallback: string;
  categories: Record<string, { label: string; bucket: string }>;
  char: { ngram: [number, number]; size: number; bytes: number };
  word: { ngram: [number, number]; size: number; bytes: number; token_pattern: string };
  scale: number[];
  intercept: number[];
  sha256: string;
}

const MAX_NARRATION = 512;
const MAX_AMOUNT = 1e12;
const TYPE_TOKEN: Record<TxType, string> = { DEBIT: "txdebit", CREDIT: "txcredit" };

export function normalize(narration: string): string {
  return narration.toLowerCase().replace(/\p{Nd}+/gu, "0").replace(/\s+/g, " ").trim();
}

export function modelText(tx: Transaction): string {
  const amt = Math.floor(Math.log2(Math.max(tx.amount, 1)));
  return `${TYPE_TOKEN[tx.type]} amt${amt} ${normalize(tx.narration)}`;
}

export function charWbNgrams(text: string, lo: number, hi: number): string[] {
  const grams: string[] = [];
  for (const word of text.split(/\s+/)) {
    if (!word) continue;
    const w = Array.from(` ${word} `);
    for (let n = lo; n <= hi; n++) {
      for (let i = 0; i < Math.max(w.length - n + 1, 1); i++) grams.push(w.slice(i, i + n).join(""));
      if (w.length <= n) break;
    }
  }
  return grams;
}

export function wordNgrams(text: string, pattern: RegExp, lo: number, hi: number): string[] {
  const tokens = text.match(pattern) ?? [];
  const grams: string[] = [];
  for (let n = lo; n <= hi; n++) {
    for (let i = 0; i + n <= tokens.length; i++) grams.push(tokens.slice(i, i + n).join(" "));
  }
  return grams;
}

function validate(tx: Transaction): Transaction {
  if (tx === null || typeof tx !== "object") throw new TypeError("transaction must be an object");
  if (typeof tx.narration !== "string") throw new TypeError("narration must be a string");
  if (tx.type !== "DEBIT" && tx.type !== "CREDIT") throw new TypeError("type must be DEBIT or CREDIT");
  if (typeof tx.amount !== "number" || !Number.isFinite(tx.amount) || tx.amount < 0 || tx.amount > MAX_AMOUNT) {
    throw new RangeError("amount must be a finite number between 0 and 1e12");
  }
  return { narration: tx.narration.slice(0, MAX_NARRATION), type: tx.type, amount: tx.amount };
}

async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(digest, (b) => b.toString(16).padStart(2, "0")).join("");
}

export class Categoriser {
  readonly header: Header;
  readonly threshold: number;
  #charVocab: Map<string, number>;
  #wordVocab: Map<string, number>;
  #idf: Float32Array;
  #quant: Int8Array;
  #pattern: RegExp;

  constructor(header: Header, payload: Uint8Array) {
    const { char, word, classes } = header;
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const vocab = (bytes: Uint8Array) => new Map(decoder.decode(bytes).split("\0").map((t, i) => [t, i] as const));
    this.header = header;
    this.threshold = header.threshold;
    this.#charVocab = vocab(payload.subarray(0, char.bytes));
    this.#wordVocab = vocab(payload.subarray(char.bytes, char.bytes + word.bytes));
    const features = char.size + word.size;
    const at = char.bytes + word.bytes;
    const view = new DataView(payload.buffer, payload.byteOffset + at, features * 4);
    this.#idf = Float32Array.from({ length: features }, (_, i) => view.getFloat32(i * 4, true));
    this.#quant = new Int8Array(payload.buffer.slice(
      payload.byteOffset + at + features * 4, payload.byteOffset + at + features * 4 + features * classes.length));
    this.#pattern = new RegExp(word.token_pattern, "g");
  }

  #block(grams: string[], vocab: Map<string, number>, offset: number, scores: Float64Array): void {
    const counts = new Map<number, number>();
    for (const g of grams) {
      const i = vocab.get(g);
      if (i !== undefined) counts.set(i + offset, (counts.get(i + offset) ?? 0) + 1);
    }
    const values = new Map<number, number>();
    let norm = 0;
    for (const [f, c] of counts) {
      const v = (1 + Math.log(c)) * this.#idf[f];
      values.set(f, v);
      norm += v * v;
    }
    norm = Math.sqrt(norm) || 1;
    const k = this.header.classes.length;
    for (const [f, v] of values) {
      for (let c = 0; c < k; c++) scores[c] += (v / norm) * this.#quant[f * k + c] * this.header.scale[c];
    }
  }

  #probabilities(tx: Transaction): Float64Array {
    const { char, word, intercept } = this.header;
    const text = modelText(validate(tx));
    const scores = Float64Array.from(intercept);
    this.#block(charWbNgrams(text, char.ngram[0], char.ngram[1]), this.#charVocab, 0, scores);
    this.#block(wordNgrams(text, this.#pattern, word.ngram[0], word.ngram[1]), this.#wordVocab, char.size, scores);
    const max = Math.max(...scores);
    let sum = 0;
    for (let c = 0; c < scores.length; c++) sum += scores[c] = Math.exp(scores[c] - max);
    return scores.map((s) => s / sum);
  }

  categorise(tx: Transaction): Prediction {
    const proba = this.#probabilities(tx);
    let best = 0;
    for (let c = 1; c < proba.length; c++) if (proba[c] > proba[best]) best = c;
    const confident = proba[best] >= this.threshold;
    const category = confident ? this.header.classes[best] : this.header.fallback;
    const meta = this.header.categories[category];
    return { category, label: meta.label, bucket: meta.bucket, confidence: Math.round(proba[best] * 100) / 100 };
  }
}

export async function loadModel(data: ArrayBuffer | Uint8Array): Promise<Categoriser> {
  const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
  if (bytes.length < 8 || new TextDecoder().decode(bytes.subarray(0, 4)) !== "MKHM") {
    throw new Error("not a MyKhata model file");
  }
  const size = new DataView(bytes.buffer, bytes.byteOffset + 4, 4).getUint32(0, true);
  const header: Header = JSON.parse(new TextDecoder().decode(bytes.subarray(8, 8 + size)));
  const payload = bytes.subarray(8 + size);
  if ((await sha256(payload)) !== header.sha256) throw new Error("model file failed its integrity check");
  return new Categoriser(header, payload);
}
