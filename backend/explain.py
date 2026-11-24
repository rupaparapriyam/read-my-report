"""Turn parsed results into plain words a patient can act on.

Two rules shape this file.

**It explains, it never diagnoses.** Every sentence describes what a test measures or
what an out-of-range value *can* suggest, and ends by pointing at a doctor. Nothing
here tells anyone they have a condition or what to take for it.

**Nothing medical is invented.** The short notes come from `glossary.json`, which
carries a source URL and review date for every line. Amazon Bedrock is given those
notes and the patient's own numbers and asked only to join them into readable
sentences in the chosen language -- it is not asked to supply the medical content. If
Bedrock is unavailable the glossary text is shown as it stands, so the app degrades to
"plain and sourced" rather than to "silent".
"""
import json
import os
import pathlib

GLOSSARY_PATH = pathlib.Path(__file__).with_name("glossary.json")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0")

DISCLAIMER = ("This explains your report in plain words. It is not a diagnosis and not "
              "medical advice. Only your doctor can tell you what these results mean "
              "for you.")

# Matching a printed test name to a glossary entry. Labs name the same test many ways.
ALIASES = {
    "haemoglobin": "haemoglobin", "hemoglobin": "haemoglobin", "hb": "haemoglobin",
    "packed cell volume": "packed_cell_volume", "pcv": "packed_cell_volume",
    "haematocrit": "packed_cell_volume", "hematocrit": "packed_cell_volume", "hct": "packed_cell_volume",
    "mean corpuscular volume": "mcv", "mcv": "mcv",
    "red cell distribution width": "rdw", "rdw": "rdw", "rdw-cv": "rdw", "rdw cv": "rdw",
    "total leucocyte count": "total_leucocyte_count", "total leukocyte count": "total_leucocyte_count",
    "tlc": "total_leucocyte_count", "wbc count": "total_leucocyte_count",
    "white blood cell count": "total_leucocyte_count", "leucocyte count": "total_leucocyte_count",
    "wbc": "total_leucocyte_count",
    "platelet count": "platelet_count", "platelets": "platelet_count",
    "tsh": "tsh", "thyroid stimulating hormone": "tsh",
    "free t3": "free_t3", "ft3": "free_t3", "triiodothyronine free": "free_t3",
    "free t4": "free_t4", "ft4": "free_t4", "thyroxine free": "free_t4",
    "fasting blood sugar": "fasting_blood_sugar", "fasting plasma glucose": "fasting_blood_sugar",
    "fasting glucose": "fasting_blood_sugar", "fbs": "fasting_blood_sugar",
    "glucose fasting": "fasting_blood_sugar", "blood sugar fasting": "fasting_blood_sugar",
    "hba1c": "hba1c", "glycated haemoglobin": "hba1c", "glycosylated haemoglobin": "hba1c",
    "total cholesterol": "total_cholesterol", "cholesterol total": "total_cholesterol",
    "ldl cholesterol": "ldl_cholesterol", "ldl": "ldl_cholesterol",
    "hdl cholesterol": "hdl_cholesterol", "hdl": "hdl_cholesterol",
    "triglycerides": "triglycerides", "serum triglycerides": "triglycerides",
    "serum creatinine": "serum_creatinine", "creatinine": "serum_creatinine",
}


def load_glossary(path=GLOSSARY_PATH):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def match(test_name, glossary):
    """Find the glossary entry for a printed test name, or None."""
    key = " ".join(test_name.lower().replace(".", "").split())
    slug = ALIASES.get(key)
    if slug is None:
        for alias, candidate in ALIASES.items():
            if alias in key:
                slug = candidate
                break
    return (slug, glossary.get(slug)) if slug else (None, None)


def note_for(result, glossary):
    """The sourced line for one result, chosen by whether it is high or low."""
    slug, entry = match(result.test, glossary)
    if not entry:
        return None
    src = entry.get("source") or {}
    note = {"slug": slug, "what": entry.get("what"), "ask": entry.get("ask"),
            "source": (f"{src.get('publisher')} — {src.get('url')} "
                       f"(updated {src.get('last_updated')})") if src else None}
    if result.status == "high":
        note["means"] = entry.get("high")
    elif result.status == "low":
        note["means"] = entry.get("low")
    return note


def build_brief(results, language="English"):
    """Everything the page needs, with no AI involved. Always works."""
    glossary = load_glossary()
    outside = [r for r in results if r.status in ("high", "low")]
    outside.sort(key=lambda r: -r.distance)
    items = []
    for r in outside:
        note = note_for(r, glossary)
        items.append({"result": r.as_dict(), "note": note})
    normal = [r.as_dict() for r in results if r.status == "normal"]
    return {"language": language, "disclaimer": DISCLAIMER,
            "counts": {"total": len(results), "outside": len(outside),
                       "normal": len(normal)},
            "outside": items, "normal": normal,
            "unreadable": [r.as_dict() for r in results if r.status == "unknown"]}


# --------------------------------------------------------------------- Bedrock
PROMPT = """You are helping a patient in India read their own blood test report.

Write a short, calm explanation in {language}. Rules you must follow:
- Use ONLY the facts in NOTES below. Do not add any medical fact of your own.
- Do not diagnose. Do not name a disease as theirs. Do not mention any medicine,
  dose, diet or treatment.
- Do not repeat the numbers more than once each.
- Short sentences. No jargon unless the notes define it.
- End with one line telling them to take the report to their doctor.
- 120 words or fewer.

THEIR RESULTS THAT ARE OUTSIDE THE LAB'S OWN RANGE:
{findings}

NOTES (the only medical facts you may use):
{notes}
"""


def with_bedrock(brief, client=None, language="English"):
    """Add a joined-up paragraph from Bedrock. Returns the brief unchanged on failure."""
    if not brief["outside"]:
        return brief
    try:
        import boto3
        client = client or boto3.client("bedrock-runtime")
        findings = "\n".join(
            f"- {i['result']['test']}: {i['result']['raw_value']} {i['result']['unit']}, "
            f"the lab's range is {i['result']['reference']}, so it is {i['result']['status']}"
            for i in brief["outside"])
        notes = "\n".join(
            f"- {i['result']['test']}: {i['note']['what']} {i['note'].get('means') or ''}"
            for i in brief["outside"] if i.get("note"))
        body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 400,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": PROMPT.format(
                    language=language, findings=findings, notes=notes or "(none)")}]}
        answer = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        payload = json.loads(answer["body"].read())
        brief["summary"] = payload["content"][0]["text"].strip()
        brief["summary_by"] = f"Amazon Bedrock, {MODEL_ID}"
    except Exception as exc:                      # noqa: BLE001 - never break the page
        brief["summary"] = None
        brief["summary_error"] = f"{type(exc).__name__}: {exc}"
    return brief
