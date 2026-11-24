"""Write the sample answers the web page uses when there is no backend to call.

Run after changing the parser, the glossary or the samples:
    python3 backend/make_demo_json.py
"""
import json, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
os.environ.setdefault("USE_TEXTRACT", "0")
from handler import read_report                                    # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "samples"
OUT.mkdir(parents=True, exist_ok=True)

for pdf in sorted((ROOT / "samples").glob("*.pdf")):
    brief = read_report(pdf.read_bytes())
    brief.pop("summary_error", None)
    (OUT / f"{pdf.stem}.json").write_text(json.dumps(brief, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    notes = sum(1 for i in brief["outside"] if i.get("note"))
    print(f"  {pdf.stem:12} {brief['counts']['total']} read, "
          f"{brief['counts']['outside']} outside, {notes} with a sourced note")
