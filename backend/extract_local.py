"""Get text out of a PDF on this machine, standing in for AWS Textract while developing.

Textract is what runs in production; this exists so the parser can be built and tested
without an AWS account, and so the demo works offline.
"""
import shutil
import subprocess


def pdf_to_text(path):
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext not found (install poppler), or use Textract")
    done = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip() or "pdftotext failed")
    return done.stdout
