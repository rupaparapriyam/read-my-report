"""Make the Hindi glossary once, from the English one, and keep every source.

Run deliberately, not per request:
    python3 backend/translate_glossary.py

Only our own sourced English sentences are translated. No new medical fact is
introduced, the source URL and review date travel with each entry unchanged, and the
result is committed to the repository so a reader can check it.
"""
import json
import os
import pathlib

import boto3

HERE = pathlib.Path(__file__).resolve().parent
MODEL = os.environ.get("BEDROCK_MODEL_ID", "au.anthropic.claude-haiku-4-5-20251001-v1:0")

ASK = """Translate these sentences from an Indian lab-report explainer into simple Hindi
a 10th-standard student reads easily.

Rules:
- Translate meaning, not word for word. Keep it plain and calm.
- Keep the hedging exactly as hedged: "can be a sign of" must not become "is".
- Do not add, remove or soften any medical fact.
- Keep well-known test names in Latin script where that is how people say them
  (TSH, HbA1c, LDL, HDL, MCV, RDW).
- Return ONLY a JSON object with the same keys, values translated. No other text.

{payload}"""


def main():
    english = json.loads((HERE / "glossary.json").read_text(encoding="utf-8"))
    client = boto3.client("bedrock-runtime")
    out = {"_about": "Hindi of glossary.json, translated once by Bedrock from our own "
                     "sourced English sentences. Sources and dates are unchanged. No "
                     "medical fact was added in translation."}
    for slug, entry in english.items():
        if slug.startswith("_"):
            continue
        payload = {k: entry[k] for k in ("what", "high", "low", "ask") if entry.get(k)}
        body = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 1500,
                "temperature": 0,
                "messages": [{"role": "user",
                              "content": ASK.format(payload=json.dumps(payload, ensure_ascii=False, indent=1))}]}
        answer = client.invoke_model(modelId=MODEL, body=json.dumps(body))
        text = json.loads(answer["body"].read())["content"][0]["text"].strip()
        text = text[text.index("{"):text.rindex("}") + 1]
        hindi = json.loads(text)
        hindi["source"] = entry["source"]          # unchanged, on purpose
        out[slug] = hindi
        print(f"  {slug}")
    (HERE / "glossary.hi.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nwrote glossary.hi.json, {len(out) - 1} tests")


if __name__ == "__main__":
    main()
