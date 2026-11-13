// The site's calculator gives the odds Python gives (tests/fixtures/odds.json, written by scripts/odds_fixture.py).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { MAX_SCORES, odds, parseScores, wilson } from "../site/odds.js";

const fixture = JSON.parse(readFileSync(new URL("../tests/fixtures/odds.json", import.meta.url), "utf8"));
const close = (a, b, label) => assert.ok(Math.abs(a - b) < 1e-9, `${label}: ${a} vs ${b}`);

for (const c of fixture.cases) {
  test(`same odds as Python for ${c.scores.join(" ")}`, () => {
    const r = odds(fixture.year, c.scores), p = c.odds;
    for (const k of ["window", "papers", "accepted"]) assert.equal(r[k], p[k], k);
    for (const k of ["rate", "model"]) close(r[k], p[k], k);
    for (const k of ["mean", "spread"]) assert.ok(Math.abs(r[k] - p[k]) < 6e-4, `${k}: ${r[k]} vs ${p[k]}`); // Python prints them to 3 decimals
    close(r.interval[0], p.interval[0], "interval");
    close(r.interval[1], p.interval[1], "interval");
    assert.deepEqual(r.off_scale, p.off_scale);
  });
}

test("what is not a score is said, not dropped silently", () => {
  assert.deepEqual(parseScores("6, 6;8/5"), { scores: [6, 6, 8, 5], bad: [] });
  assert.deepEqual(parseScores("6 x 11 5.5 -1 08"), { scores: [6, 8], bad: ["x", "11", "5.5", "-1"] });
  assert.deepEqual(parseScores(""), { scores: [], bad: [] });
  assert.ok(MAX_SCORES >= 12);
  assert.throws(() => odds(fixture.year, []));
});

test("a mean exactly on the window's edge counts on both sides", () => {
  // 29/6 and 35/6 are both 0.5 from 16/3 (as stored: six decimals)
  const year = { by_mean: [[4.833333, 20, 0], [5.833333, 20, 20]], scale: [4, 5, 6] };
  const r = odds(year, [5, 5, 6]);
  assert.deepEqual([r.window, r.papers, r.accepted], [0.5, 40, 20]);
});

test("none or all accepted: the interval ends at 0 or 1 exactly", () => {
  assert.equal(wilson(6, 6)[1], 1);
  assert.equal(wilson(0, 11)[0], 0);
  for (let n = 1; n < 300; n++) for (let k = 0; k <= n; k++) { const [lo, hi] = wilson(k, n); assert.ok(lo <= k / n && k / n <= hi, `${k}/${n}`); }
});
