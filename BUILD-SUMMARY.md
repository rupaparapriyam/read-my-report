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
| **Amazon Bedrock** (Claude Haiku 4.5) | Two jobs: reads a photographed report, and writes the plain-language paragraph in English or Hindi | One service doing both is what the free plan allowed, and it turned out to be the better design. It keeps a medical document inside our own AWS account instead of sending it to a third-party API, and the same model that reads the page also explains it. Haiku is the cheapest Claude tier. |
| **AWS Lambda** (arm64) | Reads the PDF, runs the parser, calls Bedrock | A person reads a report once and then not for months, so the traffic is spiky and paying per request is the honest shape. arm64 is cheaper per millisecond. 512 MB, 30 s timeout, measured at 89 MB used. |
| **Amazon API Gateway** (REST) | The `/read` endpoint | Handles binary upload (`BinaryMediaTypes`) and, more importantly, gives a **hard throttle of 10 requests a second**, so neither a bug nor a bad actor can run up a bill on a student account. |
| **Amazon S3** | Two buckets: the page, and a scratch bucket | Both block all public access. The scratch bucket expires objects after a day; reports are handled in memory and nothing is meant to persist, so the rule is a backstop. |
| **Amazon CloudFront** | Serves the page over HTTPS | S3 alone cannot serve a private bucket over HTTPS. Origin Access Control keeps the bucket closed to everything but CloudFront. |
| **AWS CloudFormation / SAM** | The whole stack as one file | `infra/template.yaml` is the entire system. One command deploys it, one removes it, and a judge can read exactly what exists. |

### Two constraints the free plan imposed, and what we did about them

These are worth stating plainly, because they shaped the build.

**Amazon Textract is denied outright.** It was our first choice for reading the page, and
the first version used it. On this account the call returns *"not authorized to perform:
textract:DetectDocumentText with an explicit deny in a service control policy"*. The AWS
free plan simply does not include it. Rather than ask for a paid upgrade to read a page
of text, we split the job: a PDF is read in-process with **pypdf**, pure Python and
vendored into the deployment package, which is what the lab actually emails the patient;
a photograph is read by **Bedrock**, which accepts images. We lost a service and gained a
simpler system with one less thing to pay for.

**The account is pinned to one region.** AWS's new free plan assigns a project to a
single region, ours being ap-southeast-2; the console offers Mumbai only behind "upgrade
your plan first". We stayed in Sydney rather than spend money to improve a latency
number on a prototype. Moving is one flag at deploy time.

A third, smaller one: in this region Claude models are served only through **inference
profiles**, not bare model ids, and a profile can route a call to a neighbouring region.
That means the IAM policy has to allow the profile in-region *and* the underlying model
across regions — allowing only one fails with AccessDenied. The template does both, with
a comment saying why.

## How the request flows

```
browser ──POST /read──> API Gateway ──> Lambda
                                         ├── pypdf          a PDF  -> text
                                         │   or Bedrock     a photo -> text
                                         ├── parse.py       text -> test, value, unit, range
                                         ├── glossary.json  sourced note per flagged test
                                         └── Bedrock        notes + numbers -> paragraph
                                         ──> JSON back to the browser
```

## Choices worth defending

**The reference range comes from the patient's report, not from us.** Ranges differ by
lab, method and machine. Reading the lab's own printed interval means we never tell
someone they are abnormal when their lab says otherwise, and it keeps medical claims
out of our code.

**Hindi is a real translation, not a live one.** The sourced notes exist in Hindi as a
committed file, `backend/glossary.hi.json`, translated once from our own English
sentences by `backend/translate_glossary.py` and checked in so anyone can read it.
Nothing is translated per request: the hedging is preserved deliberately ("can be a sign
of" stays "संकेत हो सकता है", never "is"), each entry keeps the English source's URL and
review date because that is the page that was actually read, and no medical fact was
introduced in translation. Switching the page to Hindi changes the whole answer — the
paragraph, what each test measures, what the result can suggest, and the question to ask
— not only the labels.

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

**Cost control was designed in, not added.** API Gateway throttled at 10 requests a
second, arm64 Lambda, the cheapest Claude tier, `PriceClass_100` CloudFront, a one-day
expiry on the only bucket that can fill up, and a zero-spend budget alert created on the
account *before* any of this existed. Reading one report costs a fraction of a rupee.

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

Read the whole report rather than only rows with a printed numeric range; have the Hindi
output checked by a clinician; and widen the glossary past thirteen tests, which is a
sourcing job rather than an engineering one. If the account were ever upgraded, Textract
would handle creased and badly lit photographs better than a vision model does.
