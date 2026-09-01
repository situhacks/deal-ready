"""Check a human-filled value set against the source document.

    python review.py data/T05_Ashgrove_CIM.pdf reports/asserted_T05.json
    python review.py data/T05_Ashgrove_CIM.pdf asserted.csv --no-vision
    python review.py data/T05_Ashgrove_CIM.pdf asserted.json --json

The screening path asks what the document says. This asks whether what *you* wrote is
supported by it - the human keeps the judgement, the machine checks. Output is three
buckets and a coverage number, never a verdict.

Accepts JSON (`{"grr_pct": 91.0}`) or two-column CSV (`metric,value`). Exit code is 1
when anything disagreed, so it composes in a pipeline; a run with disagreements is a
result, not a crash.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from deal_ready.review import check_one

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"


def load_asserted(path: Path) -> dict:
    """Read a value set. Numbers are coerced; anything unparseable is a hard error.

    Refusing a bad row rather than skipping it is deliberate: a silently dropped
    assertion would appear nowhere in the three buckets, which is exactly the kind of
    invisible gap this tool exists to prevent.
    """
    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in (".csv", ".tsv"):
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        raw = {}
        with path.open(encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh, delimiter=delim):
                if len(row) < 2 or not row[0].strip():
                    continue
                if row[0].strip().lower() in ("metric", "field", "name"):
                    continue
                raw[row[0].strip()] = row[1].strip()
    else:
        raise SystemExit(f"review: unsupported value file {path.suffix} "
                         "(use .json, .csv or .tsv)")

    out = {}
    for k, v in raw.items():
        if isinstance(v, (int, float)):
            out[k] = v
            continue
        s = str(v).strip().replace("$", "").replace(",", "").replace("%", "")
        try:
            out[k] = float(s) if "." in s else int(s)
        except ValueError:
            raise SystemExit(
                f"review: cannot read a number from {k!r} = {v!r}. "
                "Fix the row rather than removing it - a dropped assertion is "
                "invisible in the output.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path, help="the source document")
    ap.add_argument("asserted", type=Path, help="your values: .json, .csv or .tsv")
    ap.add_argument("--no-vision", action="store_true",
                    help="text layer only; chart-carried values will land in "
                         "could-not-check rather than being read")
    ap.add_argument("--top-k", type=int, default=1,
                    help="pages per metric sent to the reader when routing")
    ap.add_argument("--json", dest="as_json", action="store_true",
                    help="write reports/review_<TARGET>.json as well")
    args = ap.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"review: no such document: {args.pdf}")
    if not args.asserted.exists():
        raise SystemExit(f"review: no such value file: {args.asserted}")

    asserted = load_asserted(args.asserted)
    if not asserted:
        raise SystemExit("review: the value file is empty - nothing to check")

    result = check_one(args.pdf, asserted, use_vision=not args.no_vision,
                       top_k=args.top_k, verbose=True)

    if args.as_json:
        REPORTS.mkdir(exist_ok=True)
        tid = args.pdf.name.split("_")[0]
        out = REPORTS / f"review_{tid}.json"
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")

    return 1 if result["disagreed"] else 0


if __name__ == "__main__":
    sys.exit(main())
