"""The AWS Lambda behind the page.

POST /read   body: a report (PDF, or a photo of one)
             -> {counts, outside[], normal[], summary}

**Why there is no Amazon Textract here.** Textract was the obvious choice and the first
version used it. This account is on the AWS free plan, and the free plan denies Textract
outright: the call comes back "not authorized to perform: textract:DetectDocumentText
with an explicit deny in a service control policy". Rather than ask for a paid upgrade to
read a page of text, the job is split:

  * a PDF is read with **pypdf**, pure Python, no system libraries, which is what the
    lab actually emails the patient;
  * a photo is read by **Bedrock**, the same model that writes the explanation, because
    it accepts images. One model, two jobs, no second service to pay for.

The uploaded file is held in memory for the length of the request and never stored.
"""
import base64
import io
import json
import os
import sys

# pypdf is vendored beside this file rather than installed from a requirements file:
# pure Python, no build step, and the package ships complete in the deployment zip.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

from ask import answer as niqo_answer
from explain import DISCLAIMER, build_brief, with_bedrock
from parse import parse

MAX_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 6 * 1024 * 1024))
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "au.anthropic.claude-haiku-4-5-20251001-v1:0")

# What the model is asked when it is handed a photograph of a report.
READ_IMAGE = """Read this lab report photograph and type out its results table, one test
per line, exactly as printed and in this order:

  test name | result | unit | reference range

Copy the numbers exactly. Do not convert units, do not round, do not add tests that are
not there, and do not say anything that is not on the page. If a row has no reference
range printed, leave that column empty. No other text."""


def _pdf_text(blob):
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(blob))
    return "\n".join(page.extract_text(extraction_mode="layout") or "" for page in reader.pages)


def _image_text(blob, media_type):
    import boto3
    client = boto3.client("bedrock-runtime")
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1200,
        "temperature": 0,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                         "data": base64.b64encode(blob).decode()}},
            {"type": "text", "text": READ_IMAGE}]}],
    }
    answer = client.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
    rows = json.loads(answer["body"].read())["content"][0]["text"]
    # Turn "name | value | unit | range" into the spaced columns the parser expects.
    lines = []
    for row in rows.splitlines():
        parts = [c.strip() for c in row.split("|")]
        if len(parts) >= 3 and parts[0] and not set(parts[0]) <= set("-: "):
            lines.append("  ".join(p for p in parts if p).replace("  ", "    "))
    return "\n".join(lines)


def text_from_bytes(blob, content_type=""):
    """Returns (text, how it was read). Never raises: an unreadable file is an answer."""
    kind = (content_type or "").lower()
    looks_pdf = blob[:5] == b"%PDF-" or "pdf" in kind
    if looks_pdf:
        try:
            return _pdf_text(blob), "pypdf"
        except Exception:                               # noqa: BLE001
            return "", "unreadable"
    media = "image/png" if blob[:8].startswith(b"\x89PNG") else "image/jpeg"
    try:
        return _image_text(blob, media), f"Amazon Bedrock vision ({MODEL_ID})"
    except Exception:                                   # noqa: BLE001
        return "", "unreadable"


def read_report(blob, content_type="application/pdf", language="English"):
    if len(blob) > MAX_BYTES:
        raise ValueError(f"file is larger than {MAX_BYTES // (1024 * 1024)} MB")
    text, engine = text_from_bytes(blob, content_type)
    results = parse(text)
    brief = build_brief(results, language=language)
    brief["read_by"] = engine
    if not results:
        brief["note"] = ("No test results could be read from this file. A clearer photo, "
                         "or the PDF the lab emailed rather than a picture of the "
                         "printout, usually works.")
        return brief
    return with_bedrock(brief, language=language)


def lambda_handler(event, context=None):
    try:
        path = (event.get("path") or event.get("rawPath") or "").rstrip("/")
        if path.endswith("/ask"):
            return _ask(event)
        body = event.get("body") or ""
        blob = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode()
        params = event.get("queryStringParameters") or {}
        headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
        brief = read_report(blob, content_type=headers.get("content-type", ""),
                            language=params.get("language", "English"))
        return _response(200, brief)
    except ValueError as exc:
        return _response(400, {"error": str(exc), "disclaimer": DISCLAIMER})
    except Exception as exc:                            # noqa: BLE001
        return _response(500, {"error": f"{type(exc).__name__}: {exc}",
                               "disclaimer": DISCLAIMER})


def _ask(event):
    """Niqo answers one follow-up question about the report already on screen.

    The brief comes back from the browser rather than from a store, because nothing is
    stored. It is the same JSON we sent it a moment ago.
    """
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    payload = json.loads(raw)
    brief = payload.get("brief") or {}
    out = niqo_answer(brief, payload.get("question", ""),
                      language=payload.get("language", "English"))
    return _response(200, out)


def _response(status, payload):
    return {"statusCode": status,
            "headers": {"Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "no-store"},
            "body": json.dumps(payload, ensure_ascii=False)}
