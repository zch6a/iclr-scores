// iclr-scores: the page. Reads data/iclr.json (built by `iclr-scores build`) and draws every chart as SVG with its
// numbers also in a table, so nothing is only a picture.

import { ENOUGH, MAX_SCORES, odds, parseScores, wilson } from "./odds.js";

const $ = (id) => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";
const state = { doc: null, year: "" };

/** @param {string} tag @param {Record<string, any>} attrs @param {...(Node|string)} kids */
function el(tag, attrs = {}, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "on") for (const [ev, f] of Object.entries(v)) e.addEventListener(ev, f);
    else if (v !== false && v !== undefined) e.setAttribute(k, String(v));
  }
  e.append(...kids);
  return e;
}
/** @param {string} tag @param {Record<string, any>} attrs */
function svg(tag, attrs = {}, text = "") {
  const e = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, String(v));
  if (text) e.textContent = text;
  return e;
}
const pct = (x) => `${Math.round(x * 100)}%`;
const num = (x) => Number(x).toLocaleString("en");
const range = (edges, i) => `${edges[i].toFixed(1)}–${edges[i + 1].toFixed(1)}`;

/**
 * A bar chart with its table. Each series is {name, cls, values: [{value, n, text}]}; values are rates (0..1) when
 * `rate`, else counts. Bars of fewer than ENOUGH papers are drawn faint.
 */
function chart(box, { labels, series, rate = true, caption, marker = null, edges = null }) {
  // drawn at the box's own width, so that its text stays readable on a phone
  const W = Math.max(300, Math.min(760, box.clientWidth || 720)), H = W < 500 ? 200 : 220, L = 40, B = 34, T = 10, R = 10;
  const top = Math.max(1, ...series.flatMap((s) => s.values.map((v) => v.value)));
  const step = 10 ** Math.floor(Math.log10(top));
  const max = rate ? 1 : [1, 1.25, 2, 2.5, 5, 10].map((m) => m * step).find((m) => m >= top) || top; // a round top for the counts
  const g = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": caption, class: "bars" });
  const iw = (W - L - R) / labels.length, bw = (iw * 0.8) / series.length;
  for (const f of [0, 0.25, 0.5, 0.75, 1]) {
    const y = T + (1 - f) * (H - T - B);
    g.append(svg("line", { x1: L, x2: W - R, y1: y, y2: y, class: "grid" }));
    g.append(svg("text", { x: L - 4, y: y + 4, class: "axis", "text-anchor": "end" }, rate ? pct(f) : num(Math.round(f * max))));
  }
  labels.forEach((lab, i) => {
    const x0 = L + i * iw + iw * 0.1;
    series.forEach((s, j) => {
      const v = s.values[i];
      if (!v || !v.n) return;
      const h = (v.value / max) * (H - T - B);
      const r = svg("rect", { x: x0 + j * bw, y: T + (H - T - B) - h, width: Math.max(1, bw - 1), height: h, class: `${s.cls}${rate && v.n < ENOUGH ? " few" : ""}` });
      r.append(svg("title", {}, `${s.name}, ${lab}: ${v.text}`));
      g.append(r);
    });
    const every = Math.ceil(28 / iw); // a label every so many groups, so that they do not run into each other
    if (!edges && i % every === 0) g.append(svg("text", { x: x0 + iw * 0.4, y: H - B + 14, class: "axis", "text-anchor": "middle" }, lab));
  });
  if (edges) {
    // the groups' edges under their boundaries: a bar between 5.5 and 6.0 sits between those two numbers
    const every = Math.ceil(28 / iw);
    edges.forEach((e, i) => {
      if (i % every === 0) g.append(svg("text", { x: L + i * iw, y: H - B + 14, class: "axis", "text-anchor": "middle" }, Number.isInteger(e) ? String(e) : e.toFixed(1)));
    });
  }
  if (marker !== null) {
    const x = L + marker.at * iw;
    g.append(svg("line", { x1: x, x2: x, y1: T, y2: H - B, class: "marker" }));
    // left of the line, where the bars before it are short
    g.append(svg("text", { x: x - 5, y: T + (H - T - B) * 0.4, class: "axis marker-text", "text-anchor": "end" }, marker.text));
  }
  const table = el("table", {}, el("thead", {}, el("tr", {}, el("th", {}, caption.split(":")[0]), ...series.map((s) => el("th", {}, s.name)))));
  const body = el("tbody");
  labels.forEach((lab, i) => body.append(el("tr", {}, el("th", {}, lab), ...series.map((s) => el("td", {}, s.values[i]?.n ? s.values[i].text : "–")))));
  table.append(body);
  const legend = el("p", { class: "legend" }, ...series.map((s) => el("span", { class: `key ${s.cls}` }, s.name)));
  box.replaceChildren(g, series.length > 1 ? legend : "", el("details", {}, el("summary", {}, "The numbers"), table));
}

// ------------------------------------------------------------------ the year's charts

function render() {
  const y = state.doc.years[state.year];
  for (const b of $("years").children) b.setAttribute("aria-pressed", String(b.dataset.year === state.year));
  const o = y.outcomes;
  $("summary").textContent = `ICLR ${state.year}: ${num(y.count)} submissions, ${num(y.accepted)} of the ${num(y.decided)} decided papers with scores accepted (${pct(y.accepted / y.decided)}); ${num(o.withdrawn)} withdrawn${o.workshop ? `, ${num(o.workshop)} invited to the workshop track` : ""}. Scores on a scale of ${y.scale.join(", ")}.`;
  $("scale").textContent = `${state.year}'s scale: ${y.scale.join(", ")}; most papers had ${Object.entries(y.reviews).sort((a, b) => b[1] - a[1])[0][0]} reviews.`;
  const edges = y.edges, labels = edges.slice(0, -1).map((_, i) => range(edges, i));
  const first = edges.findIndex((_, i) => i < edges.length - 1 && y.hist.accept[i] + y.hist.reject[i] + y.hist.withdrawn[i] > 0);
  const last = edges.length - 2 - [...edges.slice(0, -1).keys()].reverse().findIndex((i) => y.hist.accept[i] + y.hist.reject[i] + y.hist.withdrawn[i] > 0);
  const cut = (a) => a.slice(first, last + 1);
  const shown = cut(labels);
  const shownEdges = edges.slice(first, last + 2);

  const rate = shown.map((_, j) => {
    const i = first + j, n = y.hist.accept[i] + y.hist.reject[i], k = y.hist.accept[i];
    return { value: n ? k / n : 0, n, text: n ? `${pct(k / n)} of ${num(n)}` : "" };
  });
  const half = y.half;
  chart($("rate"), {
    labels: shown, edges: shownEdges, caption: `Accepted share by mean score, ICLR ${state.year}`, series: [{ name: "accepted", cls: "acc", values: rate }],
    marker: half ? { at: (half - edges[first]) / 0.5, text: `half accepted at ${half.toFixed(2)}` } : null,
  });
  chart($("hist"), {
    labels: shown, edges: shownEdges, rate: false, caption: `Papers by mean score, ICLR ${state.year}`,
    series: [
      { name: "accepted", cls: "acc", values: cut(y.hist.accept).map((v) => ({ value: v, n: v, text: num(v) })) },
      { name: "not accepted", cls: "rej", values: cut(y.hist.reject).map((v) => ({ value: v, n: v, text: num(v) })) },
      { name: "withdrawn", cls: "wd", values: cut(y.hist.withdrawn).map((v) => ({ value: v, n: v, text: num(v) })) },
    ],
  });
  $("agree-note").textContent = `In each group of mean scores, the share accepted when the reviewers' scores were close (a spread of at most ${y.spread_split.toFixed(2)}, the year's median) and when they were far apart.`;
  const agree = cut(y.agree);
  chart($("agree"), {
    labels: shown, edges: shownEdges, caption: `Accepted share by agreement, ICLR ${state.year}`,
    series: [
      { name: "reviewers agree", cls: "acc", values: agree.map(([n, k]) => ({ value: n ? k / n : 0, n, text: n ? `${pct(k / n)} of ${num(n)}` : "" })) },
      { name: "reviewers disagree", cls: "dis", values: agree.map(([, , n, k]) => ({ value: n ? k / n : 0, n, text: n ? `${pct(k / n)} of ${num(n)}` : "" })) },
    ],
  });
  chart($("withdraw"), {
    labels: shown, edges: shownEdges, caption: `Withdrawn share by mean score, ICLR ${state.year}`,
    series: [{ name: "withdrawn", cls: "wd", values: cut(y.withdraw).map(([n, k]) => ({ value: n ? k / n : 0, n, text: n ? `${pct(k / n)} of ${num(n)}` : "" })) }],
  });
  renderTopics();
  calc();
}

function renderTrend() {
  const years = Object.keys(state.doc.years).filter((k) => state.doc.years[k].decided);
  const ys = years.map((k) => state.doc.years[k]);
  chart($("trend"), {
    labels: years, caption: "Accepted share of the decided papers, by year",
    series: [{ name: "accepted", cls: "acc", values: ys.map((y) => ({ value: y.accepted / y.decided, n: y.decided, text: `${pct(y.accepted / y.decided)} of ${num(y.decided)}${y.half ? `; half accepted at a mean of ${y.half.toFixed(2)}` : ""}` })) }],
  });
}

function renderTopics() {
  const all = $("all-years").checked;
  const rows = [];
  for (const [label, years] of Object.entries(state.doc.topics)) {
    let n = 0, k = 0;
    for (const [yr, [dn, dk]] of Object.entries(years)) if (all || yr === state.year) (n += dn), (k += dk);
    if (n) rows.push({ label, n, k, r: k / n, ci: wilson(k, n) });
  }
  // by rate, the topics with too few papers for a steady rate after the others
  rows.sort((a, b) => Number(a.n < ENOUGH) - Number(b.n < ENOUGH) || b.r - a.r);
  const table = el("table", { class: "topics" }, el("thead", {}, el("tr", {}, el("th", {}, "Topic"), el("th", {}, "Decided"), el("th", {}, "Accepted"), el("th", {}, "Rate (95% interval)"))));
  const body = el("tbody");
  for (const t of rows) {
    const bar = el("span", { class: "ci", "aria-hidden": "true" }, el("span", { class: "ci-range", style: false }), el("span", { class: "ci-dot" }));
    bar.firstChild.style.left = `${t.ci[0] * 100}%`;
    bar.firstChild.style.width = `${(t.ci[1] - t.ci[0]) * 100}%`;
    bar.lastChild.style.left = `${t.r * 100}%`;
    body.append(el("tr", { class: t.n < ENOUGH ? "few" : "" }, el("th", {}, t.label), el("td", {}, num(t.n)), el("td", {}, num(t.k)),
      el("td", {}, `${pct(t.r)} (${pct(t.ci[0])}–${pct(t.ci[1])}) `, bar)));
  }
  table.append(body);
  $("topics").replaceChildren(rows.length ? table : el("p", { class: "meta" }, "No topic labels this year."));
}

// ------------------------------------------------------------------ the odds

function calc() {
  const out = $("calc-out");
  const text = $("scores").value.trim();
  if (!text) return out.replaceChildren();
  const { scores, bad } = parseScores(text);
  const notes = [];
  if (bad.length) notes.push(el("p", { class: "meta warn" }, `Not read as scores: ${bad.slice(0, 5).join(" ")}${bad.length > 5 ? " …" : ""}. Scores are whole numbers from 0 to 10, e.g. 6 6 8 5.`));
  if (!scores.length) return out.replaceChildren(...(notes.length ? notes : [el("p", {}, "Scores are whole numbers from 0 to 10, e.g. 6 6 8 5.")]));
  if (scores.length > MAX_SCORES) return out.replaceChildren(el("p", { class: "meta warn" }, `${scores.length} scores: no ICLR paper had more than ${MAX_SCORES} reviews.`));
  const y = state.doc.years[state.year];
  const r = odds(y, scores);
  const parts = [el("p", { class: "big" }, r.papers ? pct(r.rate) : "–"), el("p", {}, r.papers
    ? `${num(r.accepted)} of the ${num(r.papers)} decided papers of ICLR ${state.year} with a mean score within ${r.window.toFixed(2)} of ${r.mean.toFixed(2)} were accepted (95% interval ${r.interval.map(pct).join("–")}).`
    : "No decided papers with a mean score near that.")];
  if (r.model !== null) parts.push(el("p", { class: "meta" }, `The year's model of the rate, from the mean, the spread (${r.spread.toFixed(2)}) and the lowest score: ${pct(r.model)}.`));
  if (scores.length < 3) parts.push(el("p", { class: "meta warn" }, `Almost every ICLR paper had 3 reviews or more (most had ${Object.entries(y.reviews).sort((a, b) => b[1] - a[1])[0][0]}); with ${scores.length === 1 ? "one score" : "two scores"} this compares with papers whose full set of reviews averaged the same.`));
  if (r.off_scale.length) parts.push(el("p", { class: "meta warn" }, `${r.off_scale.join(", ")} was not on ${state.year}'s scale (${y.scale.join(", ")}).`));
  out.replaceChildren(...notes, ...parts);
  const hash = `#${state.year}/${scores.join(",")}`;
  if (location.hash !== hash) history.replaceState(null, "", hash);
}

// ------------------------------------------------------------------ start

function pick(year) {
  state.year = year;
  const { scores } = parseScores($("scores").value);
  history.replaceState(null, "", `#${year}${scores.length ? `/${scores.join(",")}` : ""}`);
  render();
}

async function start() {
  try {
    const r = await fetch("data/iclr.json");
    if (!r.ok) throw new Error(`data/iclr.json: ${r.status}`);
    const doc = await r.json();
    if (doc.format !== "iclr-scores/1") throw new Error("statistics in a format this page does not read");
    state.doc = doc;
    const years = Object.keys(doc.years).filter((k) => doc.years[k].decided);
    for (const yr of years) $("years").append(el("button", { type: "button", "data-year": yr, "aria-pressed": "false", on: { click: () => pick(yr) } }, yr));
    let hash = "";
    try { hash = decodeURIComponent(location.hash.slice(1)); } catch { hash = ""; }
    const [hy, hs] = hash.split("/");
    if (hs) $("scores").value = parseScores(hs).scores.slice(0, MAX_SCORES).join(" ");
    state.year = years.includes(hy) ? hy : years[years.length - 1];
    const s = doc.source;
    $("source").replaceChildren("Data: the ", el("a", { href: s.url }, s.name), ` (${s.license}; scraped from ${s.origin}), built ${doc.built}. Please cite: ${s.cite}.`);
    $("calc-form").addEventListener("submit", (e) => { e.preventDefault(); calc(); });
    $("scores").addEventListener("input", calc);
    $("all-years").addEventListener("change", renderTopics);
    renderTrend();
    render();
    let timer = 0;
    window.addEventListener("resize", () => {
      clearTimeout(timer);
      timer = setTimeout(() => { renderTrend(); render(); }, 150); // the charts are drawn at their box's width
    });
  } catch (err) {
    $("summary").textContent = `Could not load the statistics: ${err instanceof Error ? err.message : err}`;
  }
}
start();
