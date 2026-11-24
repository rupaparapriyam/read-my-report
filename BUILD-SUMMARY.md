# Build summary — the AWS services we used, and why

**Read My Report** · Team Clauduss · Campus to Cloud Hackathon, Techfest IIT Bombay 2026–27

Everything is in `infra/template.yaml`, deployed with AWS SAM in **ap-southeast-2
(Sydney)**. The whole stack is one command to deploy and one to remove.

**On the region, because it is fair to ask.** We wanted ap-south-1 (Mumbai) and wrote
the stack for it. AWS's new free plan assigns an account to exactly one region, and
ours is Sydney; the console says "Region Asia Pacific (Mumbai) unavailable… upgrade
your plan first." Upgrading means paying, and this is a student entry on the free
plan, so we stayed in Sydney rather than spend to improve a latency number. The region
is a single flag at deploy time: moving to Mumbai is one command the day the account
allows it, and nothing in the code changes.

| Service | What it does here | Why this one |
|---|---|---|
| **Amazon Textract** | Reads the uploaded report into lines of text | Most people photograph a printout rather than keep the lab's PDF. Textract handles a phone photo, including a slightly skewed one, which plain PDF text extraction cannot. `DetectDocumentText` is the cheapest call that gives us what we need; we do not need table or form analysis because we re-join rows ourselves. |
| **Amazon Bedrock** (Claude Haiku) | Writes the short plain-language paragraph, in English or Hindi | We need natural sentences in two languages without running a model ourselves. Haiku is the cheapest model that writes well, and Bedrock keeps the call inside our own AWS account rather than sending a medical document to a third-party API. We use **Claude Haiku 5.5** (`anthropic.claude-haiku-5-5`), taken from the Bedrock model catalogue in our region, where it is serverless and lists Hindi among its languages. It is given sourced notes and asked only to join them up. |
| **AWS Lambda** (arm64) | Runs the parser and joins the two services together | The traffic is spiky — a person reads a report once, then not again for months. Paying per request rather than for an idle server is the honest shape for that. arm64 is cheaper per millisecond. 512 MB, 30 s timeout. |
| **Amazon API Gateway** | The `/read` endpoint | Gives us binary upload handling (`BinaryMediaTypes`) and, more importantly, a **hard throttle of 10 requests a second**, so a mistake or a bad actor cannot run up a bill on a student account. |
| **Amazon S3** | Two buckets: the page, and a scratch bucket | Both block all public access. The scratch bucket has a one-day expiry rule; reports are processed in memory and nothing is meant to persist, so the rule is a backstop rather than a feature. |
| **Amazon CloudFront** | Serves the page over HTTPS | S3 alone cannot serve a private bucket over HTTPS. Origin Access Control means the bucket stays closed and only CloudFront can read it. `PriceClass_100` keeps it cheap. |

## How the request flows

```
browser ──POST /read──> API Gateway ──> Lambda
                                         ├── Textract      (page -> lines of text)
                                         ├── parse.py      (lines -> test, value, unit, range)
                                         ├── glossary.json (sourced note per test)
                                         └── Bedrock       (notes + numbers -> paragraph)
                                         ──> JSON back to the browser
```

## Choices worth defending

**The reference range comes from the patient's report, not from us.** Ranges differ by
lab, method and machine. Reading the lab's own printed interval means we never tell
someone they are abnormal when their lab says otherwise, and it keeps medical claims
out of our code.

**Bedrock is grounded, not trusted.** `glossary.json` holds the medical notes, each
with a source URL and the date that page was last updated — all thirteen from
MedlinePlus, the US National Library of Medicine. Bedrock receives those notes and the
patient's numbers, and is instructed to use no fact of its own. If Bedrock is
unavailable the page still works and shows the sourced notes as they stand. The app
degrades to plain and sourced, never to silent.

**Nothing is stored.** The report is held in memory for the length of one request. No
database, no user account, no analytics on the content. That is a deliberate
simplification: the moment reports are stored, the thing needs consent flows and a
retention policy it does not yet deserve.

**Cost control was designed in, not added.** API Gateway throttling, arm64 Lambda, the
cheapest Textract call, the cheapest Bedrock model, `PriceClass_100` CloudFront, a
one-day expiry on the only bucket that can fill up, and a budget alert set on the
account before any of this was created.

## What we reused from our own products, and what we did not

We already run two systems that touch this problem, and the brief asks for original
work, so it is worth being exact about where the line falls.

**Reused — the thinking.** Kliniqo, our pathology-lab product, is why we knew to read
the reference range off the report instead of storing our own: we have seen how
differently labs print them. Niqo, our AI assistant, is why this build grounds the
model in sourced notes rather than letting it answer from memory, caps what it can
spend, and keeps working when the model is unavailable. Those three habits came
straight from things we had already got wrong once.

**Not reused — the code.** None of Kliniqo's source is in this repository. It is a
commercial product, the repository here is public, and a hackathon entry is not the
place to publish it. Every file in this repo was written for this entry.

**Not reused — the data.** No real report and no patient's data is anywhere in this
project. The four sample reports are invented people, generated by
`samples/make_samples.py`, which is in the repo so anyone can see how they were made.

## What we would do next

Read the whole report rather than only rows with a numeric range; have the Hindi output
reviewed by a clinician; and widen the glossary past thirteen tests, which is a
sourcing job rather than an engineering one.
