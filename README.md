# Read My Report

Upload a blood test report, see which values are outside **your own lab's** range, what
each measures, and what to ask your doctor. In English or Hindi.

Team Clauduss · Campus to Cloud Hackathon sponsored by AWS · Techfest IIT Bombay 2026–27

**Live: https://d1h56y4dqpwrm0.cloudfront.net**

It explains. It does not diagnose.

```bash
python3 samples/make_samples.py          # build the sample reports (needs Chrome)
python3 backend/make_demo_json.py        # rebuild the page's sample answers
cd web && python3 -m http.server 8731    # then open http://127.0.0.1:8731
```

| | |
|---|---|
| What it is and who for | [IDEA-BRIEF.md](IDEA-BRIEF.md) |
| AWS services and why | [BUILD-SUMMARY.md](BUILD-SUMMARY.md) |
| Deploying it | [infra/DEPLOY.md](infra/DEPLOY.md) |
| The demo video | [VIDEO.md](VIDEO.md) |

## The code

| File | Job |
|---|---|
| `backend/parse.py` | report text → test, value, unit, and **the range the lab printed**; decides high/low |
| `backend/explain.py` | picks the sourced note for each flagged value; asks Bedrock to join them up |
| `backend/glossary.json` | the only medical content, 13 tests, each with its source URL and review date |
| `backend/handler.py` | the Lambda: read the PDF with pypdf, or a photo with Bedrock → parse → explain |
| `backend/vendor/pypdf` | PDF reader, vendored so the Lambda needs no build step |
| `web/index.html` | the whole front end, one file, no framework |
| `infra/template.yaml` | the AWS stack: Lambda, API Gateway, Bedrock, S3, CloudFront |
| `samples/` | four invented patients, used to build and demo |

## Privacy

Reports are processed in memory for the length of one request and are not stored. There
is no account, no database and no analytics on report content. Every sample report in
this repository uses an invented patient; no real person's report is here.

## Medical content

`backend/glossary.json` is the only place a medical claim appears, and every line
carries the page it came from and that page's last-updated date — all from MedlinePlus,
the US National Library of Medicine, fetched 24 November 2026. Reference ranges are
deliberately **not** stored: they are read from each patient's own report, because they
differ by lab, method and machine.
