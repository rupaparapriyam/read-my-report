"""Niqo: answers a follow-up question about the report already on the screen.

Niqo is our assistant, and this is the narrowest possible version of it. It is handed
three things and nothing else: the results read off this person's report, the sourced
notes for those results, and their question. It may use nothing else.

The guardrails are the same as the rest of the project, said again because a free-text
box is where they get tested: explain, never diagnose, never name a medicine or a dose,
never invent a number, and say plainly when the answer is not in what it was given.
"""
import json
import os
import re

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "au.anthropic.claude-haiku-4-5-20251001-v1:0")
MAX_QUESTION = 300

REFUSE = {
    "English": "That is a question for your doctor. I can only explain what is printed "
               "on this report.",
    "Hindi": "यह सवाल आपके डॉक्टर के लिए है। मैं सिर्फ़ वही समझा सकता हूँ जो इस रिपोर्ट में लिखा है।",
}

SYSTEM = """You are Niqo, answering one question about the blood test report this person
has just uploaded. Answer in {language}.

You may use ONLY what is in THEIR RESULTS and NOTES below. That is the whole of your
knowledge. You have no other medical knowledge for this conversation.

Hard rules:
- Never say what condition they have. Never confirm or rule one out.
- Never mention a medicine, a dose, a diet, a supplement or any treatment.
- Never invent a number, a range or a test that is not listed below.
- If the answer is not in what you were given, say so in one sentence and tell them to
  ask their doctor. Do not guess, and do not fill the gap from general knowledge.
- No headings, no bullets, no bold, no Markdown. Plain sentences.
- At most 70 words. Finish your last sentence.
- Be calm. Do not frighten them, and do not reassure them about something you were not
  told.

THEIR RESULTS:
{findings}

NOTES (the only medical facts you may use):
{notes}
"""


def _context(brief):
    findings, notes = [], []
    for item in brief.get("outside", []):
        r = item["result"]
        findings.append(f"- {r['test']}: {r['raw_value']} {r['unit']}, the lab's range is "
                        f"{r['reference']}, so it is {r['status']}")
        note = item.get("note") or {}
        line = " ".join(x for x in (note.get("what"), note.get("means")) if x)
        if line:
            notes.append(f"- {r['test']}: {line}")
    for r in brief.get("normal", []):
        findings.append(f"- {r['test']}: {r['raw_value']} {r['unit']}, inside the lab's "
                        f"range of {r['reference']}")
    return "\n".join(findings) or "(none)", "\n".join(notes) or "(none)"


def answer(brief, question, language="English", client=None):
    question = (question or "").strip()[:MAX_QUESTION]
    if not question:
        return {"answer": None, "error": "no question"}
    if not brief.get("outside") and not brief.get("normal"):
        return {"answer": REFUSE.get(language, REFUSE["English"])}

    findings, notes = _context(brief)
    try:
        import boto3
        client = client or boto3.client("bedrock-runtime")
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "temperature": 0.1,
            "system": SYSTEM.format(language=language, findings=findings, notes=notes),
            "messages": [{"role": "user", "content": question}],
        }
        out = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        text = json.loads(out["body"].read())["content"][0]["text"].strip()
        text = re.sub(r"^#+\s*", "", text, flags=re.M)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"^[-*]\s+", "", text, flags=re.M)
        return {"answer": text.strip(), "answered_by": f"Niqo on Amazon Bedrock, {MODEL_ID}"}
    except Exception as exc:                        # noqa: BLE001
        return {"answer": None, "error": f"{type(exc).__name__}"}
