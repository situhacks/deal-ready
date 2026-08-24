"""Capture reviewer corrections from an edited memo. The loop's other half.

    python capture.py T05 --edited reports/memo_T05_reviewed.md
    python capture.py T05 --edited reports/memo_T05_reviewed.md --minutes 14 --reviewer "analyst A"

The reviewer edits the memo file they were handed - nothing new to learn. This
script diffs the edit against the draft and writes structured correction records to
data/corrections/<target>_session<N>.json, attributing each change to the call-out
it responded to where one exists.

Attribution is deliberately conservative:

- a change near a call-out anchor is credited to that call-out;
- a change with no anchor above it is a **blind spot** (callout_id: null) - the
  system missed it and the reviewer caught it anyway. Blind-spot count is the honest
  quality metric, because precision on flagged items flatters whatever the flagger
  already knows.

Categories: capture suggests; the reviewer triages. `factual_error` on a value or a
checkable claim, `judgement_call` on accepted-but-edited interpretation,
`preference` for style, `new_information` for material added from outside the
document. Anything left as `needs_triage` after a human pass does not fold back -
an untriaged correction teaches nothing reliably.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"
CORRECTIONS = ROOT / "data" / "corrections"

ANCHOR_RE = re.compile(r"<!--(co-[^>]+)-->")


def _clean(line: str) -> str:
    return re.sub(r"\s+", " ", ANCHOR_RE.sub("", line)).strip()


def _nearest_anchor(marked_lines: list[str], idx: int) -> str | None:
    """Last call-out id at or above this line in the marked draft."""
    for k in range(min(idx, len(marked_lines) - 1), -1, -1):
        m = ANCHOR_RE.search(marked_lines[k])
        if m:
            return m.group(1)
    return None


def _suggest(kind: str | None, before: str | None, after: str | None) -> str:
    if kind in ("axis_read", "label_read"):
        return "factual_error"
    if kind == "judgement":
        return "judgement_call" if after else "needs_triage"   # struck = signal, triage decides
    if before and not after:
        return "new_information"    # removed entirely without replacement
    if after and not before:
        return "new_information"    # added from outside the document
    return "needs_triage"


def diff_memo(draft_md: str, edited_md: str,
              callouts: list[dict]) -> list[dict]:
    by_id = {c["id"]: c for c in callouts}
    marked = draft_md.splitlines()
    dlines = [_clean(l) for l in marked]
    elines = [_clean(l) for l in edited_md.splitlines()]

    out: list[dict] = []

    def record(anchor: str | None, before: str | None, after: str | None):
        if before == after or (not before and not after):
            return
        # Pure additions are never credited to a call-out, however near one they
        # sit: an inserted line is content the system did not produce, which is
        # what blind-spot means. Triage may reassign by hand.
        if before is None:
            anchor = None
        c = by_id.get(anchor or "")
        out.append({
            "callout_id": anchor,
            "blind_spot": anchor is None,
            "field": c["metric"] if c else None,
            "kind": c["kind"] if c else None,
            "before": before,
            "after": after,
            "reason_category": _suggest(c["kind"] if c else None, before, after),
        })

    sm = difflib.SequenceMatcher(None, dlines, elines, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                before = dlines[i1 + k] if i1 + k < i2 else None
                after = elines[j1 + k] if j1 + k < j2 else None
                idx = i1 + k if i1 + k < i2 else i2 - 1   # deletions attribute above their line
                record(_nearest_anchor(marked, idx), before, after)
        elif tag == "delete":
            for k in range(i1, i2):
                record(_nearest_anchor(marked, k), dlines[k], None)
        elif tag == "insert":
            record(_nearest_anchor(marked, max(i1 - 1, 0)),
                   None, " ".join(elines[j1:j2]))
    return [r for r in out if (r["before"] or r["after"])]


def main() -> int:
    ap = argparse.ArgumentParser(description="Diff an edited memo into correction records.")
    ap.add_argument("target", help="target id, e.g. T05")
    ap.add_argument("--edited", required=True, help="the reviewer's edited memo file")
    ap.add_argument("--draft", help="draft memo (default reports/memo_<target>.md)")
    ap.add_argument("--minutes", type=int, default=0, help="reviewer minutes spent")
    ap.add_argument("--reviewer", default="unattributed")
    args = ap.parse_args()

    tid = args.target.upper()
    draft_path = Path(args.draft) if args.draft else REPORTS / f"memo_{tid}.md"
    edited_path = Path(args.edited)
    callouts_path = REPORTS / f"callouts_{tid}.json"
    for p in (draft_path, edited_path, callouts_path):
        if not p.exists():
            print(f"missing {p}")
            return 2

    corrections = diff_memo(draft_path.read_text(encoding="utf-8"),
                            edited_path.read_text(encoding="utf-8"),
                            json.loads(callouts_path.read_text(encoding="utf-8"))["callouts"])

    CORRECTIONS.mkdir(parents=True, exist_ok=True)
    session = 1 + len(list(CORRECTIONS.glob(f"{tid}_session*.json")))
    rec = {
        "target_id": tid,
        "session": session,
        "draft_version": "v2",
        "reviewer": args.reviewer,
        "minutes_spent": args.minutes,
        "corrections": corrections,
    }
    dest = CORRECTIONS / f"{tid}_session{session:02d}.json"
    dest.write_text(json.dumps(rec, indent=2), encoding="utf-8")

    blind = sum(1 for c in corrections if c["blind_spot"])
    print(f"{dest.name}: {len(corrections)} corrections "
          f"({blind} blind spot(s), "
          f"{sum(1 for c in corrections if c['reason_category'] == 'needs_triage')} to triage)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
