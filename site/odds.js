// The odds for a set of scores, as src/iclr_scores/odds.py computes them: the page's calculator runs this, and
// test/odds.test.js checks it against the Python results in tests/fixtures/odds.json.

export const ENOUGH = 30; // papers at least in the window of mean scores
export const MAX_SCORES = 12; // more reviews than any ICLR paper had

/** The Wilson 95% interval of a rate k/n. @returns {[number, number]} */
export function wilson(k, n, z = 1.96) {
  if (!n) return [0, 1];
  const p = k / n, d = 1 + (z * z) / n, c = (p + (z * z) / (2 * n)) / d;
  const h = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
  // none or all accepted: the interval ends at 0 or 1 exactly (the formula gives 2.8e-17 or 0.9999999999999999)
  return [k === 0 ? 0 : Math.max(0, c - h), k === n ? 1 : Math.min(1, c + h)];
}

/**
 * The scores typed, and what could not be read as one: whole numbers from 0 to 10, apart by spaces, commas,
 * semicolons or slashes.
 * @param {string} text @returns {{scores: number[], bad: string[]}}
 */
export function parseScores(text) {
  const scores = [], bad = [];
  for (const t of text.split(/[\s,;/]+/).filter(Boolean)) {
    if (/^\d{1,2}$/.test(t) && Number(t) <= 10) scores.push(Number(t));
    else bad.push(t);
  }
  return { scores, bad };
}

/**
 * @param {{by_mean: number[][], scale: number[], model?: number[]}} year one year of data/iclr.json
 * @param {number[]} scores
 */
export function odds(year, scores) {
  if (!scores.length) throw new Error("no scores given");
  const m = scores.reduce((a, b) => a + b, 0) / scores.length;
  const spread = Math.sqrt(scores.reduce((a, b) => a + (b - m) ** 2, 0) / scores.length);
  let window = 0.25, papers = 0, accepted = 0;
  for (;;) {
    const cells = year.by_mean.filter((c) => Math.abs(c[0] - m) <= window + 1e-5); // means are stored to 6 decimals
    papers = cells.reduce((a, c) => a + c[1], 0);
    accepted = cells.reduce((a, c) => a + c[2], 0);
    if (papers >= ENOUGH || window >= 2) break;
    window += 0.25;
  }
  const out = {
    mean: m, spread, window, papers, accepted,
    rate: papers ? accepted / papers : null,
    interval: papers ? wilson(accepted, papers) : null,
    off_scale: [...new Set(scores.filter((s) => year.scale.length && !year.scale.includes(s)))].sort((a, b) => a - b),
    model: null,
  };
  if (year.model) {
    const [b0, b1, b2, b3] = year.model, z = b0 + b1 * m + b2 * spread + b3 * Math.min(...scores);
    out.model = 1 / (1 + Math.exp(-Math.max(-30, Math.min(30, z))));
  }
  return out;
}
