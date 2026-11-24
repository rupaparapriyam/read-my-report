"""The AWS Lambda behind the page.

POST /read   multipart or base64 body: a report (PDF or photo)
             -> {counts, outside[], normal[], summary}

In production the text comes from Amazon Textract. Running locally with no AWS
credentials, it comes from pdftotext instead, so the same code path can be developed
and demonstrated offline.

The uploaded file is held in memory for the length of the request and written to S3
only under a key that expires. No report is kept after the answer is returned.
"""
import base64
import json
import os

from explain import DISCLAIMER, build_brief, with_bedrock
from parse import parse

MAX_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 6 * 1024 * 1024))
ALLOWED = {"application/pdf", "image/jpeg", "image/png"}


def text_from_bytes(blob, content_type):
    """Textract on AWS; pdftotext on a laptop. Same text either way."""
    if os.environ.get("USE_TEXTRACT", "1") == "1":
        try:
            import boto3
            client = boto3.client("textract")
            answer = client.detect_document_text(Document={"Bytes": blob})
            lines = [b["Text"] for b in answer["Blocks"] if b["BlockType"] == "LINE"]
            return "\n".join(lines), "Amazon Textract"
        except Exception:                          # noqa: BLE001
            pass
    import tempfile
    from extract_local import pdf_to_text
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as fh:
            fh.write(blob)
            fh.flush()
            return pdf_to_text(fh.name), "pdftotext (local)"
    except Exception:                              # noqa: BLE001
        # Not a readable document. Say so kindly rather than failing the request.
        return "", "unreadable"


def read_report(blob, content_type="application/pdf", language="English"):
    if len(blob) > MAX_BYTES:
        raise ValueError(f"file is larger than {MAX_BYTES // (1024*1024)} MB")
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
        body = event.get("body") or ""
        blob = base64.b64decode(body) if event.get("isBase64Encoded") else body.encode()
        params = event.get("queryStringParameters") or {}
        brief = read_report(blob, language=params.get("language", "English"))
        return _response(200, brief)
    except ValueError as exc:
        return _response(400, {"error": str(exc), "disclaimer": DISCLAIMER})
    except Exception as exc:                        # noqa: BLE001
        return _response(500, {"error": f"{type(exc).__name__}", "disclaimer": DISCLAIMER})


def _response(status, payload):
    return {"statusCode": status,
            "headers": {"Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "no-store"},
            "body": json.dumps(payload, ensure_ascii=False)}
