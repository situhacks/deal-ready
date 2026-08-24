"""Verify every published number, offline, from committed artifacts.

    python run_checks.py

No network. No model. No API key. If this is green on a fresh clone, every figure in
the README and in `reports/` is reproducible by someone who has never run a GPU.

That property is deliberate and it is doing real work. The expensive parts of this
pipeline - reading pages with a vision model - are slow and hardware-dependent, so a
reviewer who had to re-run them in order to trust the numbers would simply not check.
Committing the raw model outputs and recomputing the *scoring* from them separates two
things that usually get tangled:

    reproducing the measurement   - offline, deterministic, checked here
    regenerating the raw outputs  - needs local models, and is not required to verify

Where a check cannot run - Tesseract absent, no vision cache - it reports SKIP with a
reason. A skipped check is never counted as a pass. Knowing what was not verified is
the point of running this at all.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"
results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str = "") -> None:
    results.append((name, status, detail))
    mark = {PASS: "ok  ", FAIL: "FAIL", SKIP: "skip"}[status]
    print(f"  [{mark}] {name}" + (f"  - {detail}" if detail else ""))


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


# --------------------------------------------------------------------------------
def check_corpus_deterministic() -> None:
    """Regenerating must reproduce the same ground truth, byte for byte.

    A generator whose output drifts between runs makes every downstream number
    unfalsifiable - you could never tell a real regression from a reroll.
    """
    gt_path = DATA / "ground_truth.json"
    before = gt_path.read_text(encoding="utf-8") if gt_path.exists() else None
    if before is None:
        check("corpus is deterministic", SKIP, "no ground_truth.json - run generate.py")
        return
    proc = subprocess.run([sys.executable, str(ROOT / "generate.py")],
                          capture_output=True, text=True, cwd=ROOT)
    if proc.returncode != 0:
        check("corpus is deterministic", FAIL, "generate.py failed (leak check?)")
        return
    after = gt_path.read_text(encoding="utf-8")
    check("corpus is deterministic", PASS if before == after else FAIL,
          "regenerating reproduces identical ground truth")


def check_no_chart_leaks() -> None:
    """The experiment's control: chart-only values absent from every text layer."""
    from deal_ready.parse import textlayer
    gt = load(DATA / "ground_truth.json")
    if not gt:
        check("chart values absent from text layer", SKIP, "no ground truth")
        return
    from deal_ready.values import value_present
    by = defaultdict(list)
    for r in gt:
        by[r["target_id"]].append(r)
    leaks = []
    for pdf in sorted(DATA.glob("*.pdf")):
        doc = textlayer.parse(pdf)
        for r in by[pdf.name.split("_")[0]]:
            if r["carrier"] == "chart" and value_present(doc.text, r["metric"], r["value"]):
                leaks.append(f"{r['target_id']}/{r['metric']}")
    check("chart values absent from text layer",
          PASS if not leaks else FAIL,
          "no leaks across 5 decks" if not leaks else f"leaked: {leaks}")


def check_textlayer_layer_p() -> None:
    """The published Layer P text-layer row: 100% prose, 100% table, 0% chart."""
    from collections import defaultdict as dd

    from deal_ready.parse import textlayer
    from eval.recoverability import aggregate, load_ground_truth, score_document
    gt = load_ground_truth()
    by = dd(list)
    for r in gt:
        by[r["target_id"]].append(r)
    rows = []
    for pdf in sorted(DATA.glob("*.pdf")):
        rows += score_document(textlayer.parse(pdf), by[pdf.name.split("_")[0]])
    agg = aggregate(rows)
    expect = {"prose": 100.0, "table": 100.0, "chart": 0.0}
    bad = []
    for carrier, want in expect.items():
        got = agg.get(f"textlayer|{carrier}", {}).get("attributed_pct")
        if got != want:
            bad.append(f"{carrier}: {got} != {want}")
    check("Layer P text-layer row reproduces",
          PASS if not bad else FAIL,
          "prose 100%, table 100%, chart 0%" if not bad else "; ".join(bad))


def check_rules_catch_seeded_defects() -> None:
    """Coverage, not a true-positive rate.

    These rules are tested against defects this repo planted, so a TPR would be
    circular - the answer key and the exam share an author. What is claimable is
    whether each rule caught the classes it says it catches.
    """
    from deal_ready.generator.profiles import ALL_PROFILES
    from deal_ready.scorer import rules
    gt = load(DATA / "ground_truth.json")
    if not gt:
        check("seeded defects caught", SKIP, "no ground truth")
        return
    vals = defaultdict(dict)
    for r in gt:
        vals[r["target_id"]][r["metric"]] = r["value"]
    crit = rules.load_criteria()

    # Defect class -> the rule that must fire. Some seeded classes are narrative
    # (key-person, legacy stack) and are deliberately NOT deterministic rules; they
    # are the judgement layer's job and are excluded rather than quietly passed.
    RULE_FOR = {
        "top1_concentration_breach": "top1_concentration_breach",
        "top5_concentration_breach": "top5_concentration_breach",
        "recurring_below_floor": "recurring_below_floor",
        "ebitda_negative": "ebitda_negative",
        "grr_below_floor": "grr_below_floor",
    }
    NOT_DETERMINISTIC = {"key_person_dependency", "legacy_stack_rewrite_risk",
                         "services_revenue_in_arr", "rule_of_40_fail"}

    missed = []
    checked = 0
    for prof in ALL_PROFILES:
        fired = {f.rule_id for f in rules.evaluate(vals[prof["target_id"]], crit)}
        for defect in prof["seeded_defects"]:
            if defect in NOT_DETERMINISTIC:
                continue
            want = RULE_FOR.get(defect)
            if not want:
                continue
            checked += 1
            if want not in fired:
                missed.append(f"{prof['target_id']}/{defect}")
    check("seeded defects caught by rules",
          PASS if not missed else FAIL,
          f"{checked - len(missed)}/{checked} classes" if not missed else f"missed {missed}")


def check_clean_baseline_silent() -> None:
    """A validator that fires on a healthy company is worse than none.

    People learn to ignore it, and then it is worse than none for the one deal that
    mattered. This is the check most tools skip.
    """
    from deal_ready.scorer import rules
    gt = load(DATA / "ground_truth.json")
    if not gt:
        check("clean baseline is silent", SKIP, "no ground truth")
        return
    clean = {r["metric"]: r["value"] for r in gt if r["target_id"] == "T01"}
    findings = rules.evaluate(clean, rules.load_criteria())
    noisy = [f.rule_id for f in findings if f.severity in ("blocker", "warning")]
    check("clean baseline is silent",
          PASS if not noisy else FAIL,
          "0 blocker/warning findings on the clean target"
          if not noisy else f"fired: {noisy}")


def check_vision_cache_is_successes_only() -> None:
    """No cached failure may masquerade as a read.

    This exists because it happened: a 300s timeout under GPU contention wrote an
    empty result that scored as a miss. Downstream, that is indistinguishable from a
    model that looked and found nothing.
    """
    cache = DATA / "vision_cache"
    files = sorted(cache.glob("*.json")) if cache.exists() else []
    if not files:
        check("vision cache holds only successes", SKIP, "no vision cache committed")
        return
    bad = []
    for f in files:
        d = load(f)
        if not d["meta"].get("ok") or not d["text"].strip():
            bad.append(f.name)
    check("vision cache holds only successes",
          PASS if not bad else FAIL,
          f"{len(files)} cached pages, all non-empty successes"
          if not bad else f"{len(bad)} empty/failed: {bad[:3]}")


def check_reports_match_artifacts() -> None:
    """Published Layer P must recompute from the committed rows, not be hand-typed."""
    from eval.recoverability import aggregate
    rep = load(REPORTS / "layer_p.json")
    if not rep:
        check("Layer P report matches its rows", SKIP, "run parse_corpus.py first")
        return
    recomputed = aggregate(rep["rows"])
    check("Layer P report matches its rows",
          PASS if recomputed == rep["aggregate"] else FAIL,
          f"{len(rep['rows'])} scored fields recompute to the published aggregate")


def check_axis_values_remeasure() -> None:
    """The axis-read column re-measures offline, from committed pixels.

    The tiered text for an unlabelled chart ends in values code measured from the
    document's own embedded image, calibrated by tick glyphs the model read once
    (cached). Both halves are committed, so the measurement - and with it the
    published axis column - is verifiable by anyone, on any machine, with no GPU
    and no model. This is the same property the arithmetic rules have always had,
    extended to the last model-read numbers in the pipeline.
    """
    import re as _re

    from deal_ready.parse import chart_measure, tiered, vision
    from deal_ready.values import value_present
    gt = load(DATA / "ground_truth.json")
    rows = [r for r in gt if r["carrier"] == "chart" and not r["labelled_in_chart"]]
    if not rows:
        check("axis values re-measure offline", SKIP, "no chart ground truth")
        return
    strong = _re.sub(r"[:/]", "-", tiered.STRONG_MODEL)
    bad, checked, xchecked = [], 0, 0
    for r in rows:
        pdfs = list(DATA.glob(f"{r['target_id']}_*.pdf"))
        if not pdfs:
            bad.append(f"{r['target_id']}: no PDF")
            continue
        pdf = pdfs[0]
        stem = pdf.stem
        crop = load(DATA / "vision_cache" / f"{stem}__p{r['page']:02d}__{strong}__crop.json")
        tickrec = load(DATA / "vision_cache" / f"{stem}__p{r['page']:02d}__{strong}__ticks0.json")
        if not crop or not tickrec:
            bad.append(f"{r['target_id']} p{r['page']}: missing committed crop/ticks")
            continue
        png = vision.page_embedded_images(pdf, r["page"])[0]
        rgb = chart_measure._rgb(png)
        grid = chart_measure.find_gridlines(rgb)
        ticks = sorted(tickrec["ticks"], reverse=True)
        if len(grid) != len(ticks):
            bad.append(f"{r['target_id']} p{r['page']}: {len(grid)} gridlines vs "
                       f"{len(ticks)} ticks")
            continue
        values = []
        for color in chart_measure.find_series(rgb):
            ep = chart_measure.find_endpoint(rgb, color)
            if ep is None:
                break
            y = chart_measure.line_fit_y(rgb, color, ep[1], ep[0]) or ep[0]
            values.append(round(chart_measure.interpolate(y, grid, ticks), 1))
        block = chart_measure.measured_block(crop["text"], values)
        if not block or not value_present(block, r["metric"], r["value"]):
            bad.append(f"{r['target_id']}/{r['metric']}: measured {values or 'nothing'} "
                       f"does not recover {r['value']}")
            continue
        # The cross-check claim, when published: the committed independent read
        # must still agree with the re-measured value, offline.
        verify = _re.sub(r"[:/]", "-", tiered.VERIFY_MODEL)
        readrec = load(DATA / "vision_cache" /
                       f"{stem}__p{r['page']:02d}__{verify}__read0.json")
        if readrec:
            pairs = chart_measure.measured_pairs(crop["text"], values)
            recs = chart_measure.crosscheck(
                pairs, [(x["label"], x["value"]) for x in readrec["reads"]])
            if not recs or not all(x["agree"] for x in recs):
                bad.append(f"{r['target_id']}/{r['metric']}: cross-check read does "
                           f"not agree offline")
                continue
            xchecked += 1
        checked += 1
    check("axis values re-measure offline",
          PASS if not bad else FAIL,
          f"{checked} axis-read values re-measure from committed pixels, no GPU"
          + (f"; {xchecked} cross-checked against committed independent reads"
             if xchecked else "; cross-check reads not committed")
          if not bad else "; ".join(bad[:3]))


def check_deterministic_path_needs_no_model() -> None:
    """screen.py --no-vision must complete with nothing installed."""
    proc = subprocess.run(
        [sys.executable, str(ROOT / "screen.py"), str(DATA), "--no-vision"],
        capture_output=True, text=True, cwd=ROOT)
    # exit 1 is correct here: blocker findings exist in this corpus.
    ok = proc.returncode in (0, 1) and "Traceback" not in proc.stderr
    check("deterministic path runs with no model",
          PASS if ok else FAIL,
          "screen.py --no-vision completed" if ok else proc.stderr.strip()[-160:])


def check_correction_records() -> None:
    """Correction records must be well-formed and fully triaged.

    An untriaged correction teaches nothing reliably, and a correction pointing at
    a call-out that does not exist means the diff attribution drifted. Both break
    the loop silently if nobody checks.

    Session anchors resolve against the call-outs *of the draft that was reviewed*.
    When a later version regenerates a target's call-outs, the reviewed set is
    frozen to `callouts_<target>_session<N>.json` - history is not rewritten to
    match the present, and the present is not forbidden from improving.
    """
    files = sorted((DATA / "corrections").glob("*_session*.json")) \
        if (DATA / "corrections").exists() else []
    if not files:
        check("correction records are consistent", SKIP,
              "no committed review sessions")
        return
    problems = []
    for f in files:
        rec = load(f)
        frozen = REPORTS / f"callouts_{f.stem}.json"
        src = frozen if frozen.exists() \
            else REPORTS / f"callouts_{rec['target_id']}.json"
        callouts = {c["id"] for c in (load(src) or {}).get("callouts", [])}
        for c in rec["corrections"]:
            if c["reason_category"] == "needs_triage":
                problems.append(f"{f.name}: untriaged correction")
            if not c["blind_spot"]:
                if c["callout_id"] not in callouts:
                    problems.append(f"{f.name}: {c['callout_id']} not in callouts")
            elif c["callout_id"] is not None:
                problems.append(f"{f.name}: blind spot with an id")
    check("correction records are consistent",
          PASS if not problems else FAIL,
          f"{len(files)} session(s), all triaged, all anchors resolve"
          if not problems else "; ".join(problems[:3]))


def check_fold_back_complete() -> None:
    """Accepted corrections must appear as examples; extraction gaps need a regression.

    This is the recursion's honesty check. A review session that changes nothing
    downstream was theatre - the corrections were received, but they did not teach.
    """
    sessions = sorted((DATA / "corrections").glob("*_session*.json")) \
        if (DATA / "corrections").exists() else []
    examples = load(ROOT / "eval" / "judgement_examples.json") or []
    regressions = load(ROOT / "eval" / "regressions.json") or []
    if not sessions:
        check("fold-back is complete", SKIP, "no committed review sessions")
        return
    import re as _re
    ex_keys = set()
    for e in examples:
        m = _re.match(r".*?([\w]+_session\d+\.json)#corrections\[(\d+)\]",
                      e.get("source", ""))
        if m:
            ex_keys.add((m.group(1), int(m.group(2))))
    problems = []
    for f in sessions:
        rec = load(f)
        for i, c in enumerate(rec["corrections"]):
            if (c["reason_category"] == "judgement_call"
                    and (f.name, i) not in ex_keys):
                problems.append(f"{f.name}[{i}]: accepted judgement never became an example")
            if (c["reason_category"] == "factual_error"
                    and not any(r.get("from", "").startswith(f"{rec['target_id']}_session")
                                for r in regressions)):
                problems.append(f"{f.name}[{i}]: factual error locked by no regression")
    check("fold-back is complete",
          PASS if not problems else FAIL,
          "every accepted correction teaches; every extraction gap is asserted"
          if not problems else "; ".join(problems[:3]))


def check_regressions_hold() -> None:
    """Each lesson learned from a reviewer must still be visible in current artifacts.

    These are assertions written after a human caught something the system missed.
    If one starts failing, the pipeline regressed past what a reviewer taught it -
    exactly the drift the changelog exists to prevent.
    """
    regs = load(ROOT / "eval" / "regressions.json") or []
    if not regs:
        check("reviewer regressions hold", SKIP, "no regressions recorded")
        return
    failures = []
    for r in regs:
        data = load(REPORTS / f"callouts_{r['target_id']}.json")
        if not data:
            failures.append(f"{r['id']}: no callouts for {r['target_id']}")
            continue
        hit = any(c.get("kind") == r["callout_kind"]
                  and (r.get("evidence_page") is None
                       or c.get("evidence_page") == r["evidence_page"])
                  and all(s in json.dumps(c) for s in r["must_contain"])
                  for c in data["callouts"])
        if not hit:
            failures.append(f"{r['id']}: {r['must_contain']} not found")
    check("reviewer regressions hold",
          PASS if not failures else FAIL,
          f"{len(regs)} lesson(s) still visible" if not failures else "; ".join(failures))


# --------------------------------------------------------------------------------
def main() -> int:
    print("\ndeal-ready checks - offline, no model, no network\n")
    check_corpus_deterministic()
    check_no_chart_leaks()
    check_textlayer_layer_p()
    check_rules_catch_seeded_defects()
    check_clean_baseline_silent()
    check_vision_cache_is_successes_only()
    check_reports_match_artifacts()
    check_axis_values_remeasure()
    check_deterministic_path_needs_no_model()
    check_correction_records()
    check_fold_back_complete()
    check_regressions_hold()

    n_pass = sum(1 for _, s, _ in results if s == PASS)
    n_fail = sum(1 for _, s, _ in results if s == FAIL)
    n_skip = sum(1 for _, s, _ in results if s == SKIP)
    print(f"\n  {n_pass} passed, {n_fail} failed, {n_skip} skipped "
          f"(skipped checks are NOT passes)\n")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
