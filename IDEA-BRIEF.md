# Read My Report — idea brief

**Team Clauduss** · Team ID TM-BD39ACE6BC2 · Campus to Cloud Hackathon, Techfest IIT Bombay 2026–27
Priyam Rupapara (leader), Nivaan Shah, Ved Patel, Manan Nagar

## The problem

Every day, lakhs of Indians collect a blood test report and understand almost none of
it. The report is a grid of abbreviations, numbers and units — TSH, MCV, RDW — printed
in English, and the reference range sits in the next column in the same small type. The
patient looks for red ink, finds none, and assumes everything is fine. Or finds one and
assumes the worst.

What they actually need to know is small and simple: **which numbers are outside my
own lab's range, what does each one measure, and what should I ask my doctor?**

This matters most to the people with the least access. If you can afford a follow-up
consultation the same week, a confusing report costs you nothing. If you cannot, the
report is the only medical information you will have for months.

## Who it is for

Anyone handed a lab report they cannot read. In practice: patients at small-town and
semi-urban labs, people booking tests directly through a diagnostic chain with no
doctor in between, and the family member who ends up explaining the report to everyone
else.

## How it works

Upload the report — the PDF the lab emailed, or a photo of the printout.

1. The page is read into text: a PDF with **pypdf** inside the Lambda, a photograph by
   **Amazon Bedrock**, which accepts images. (Textract was the first choice and is denied
   on the AWS free plan, so the model does both jobs. See the build summary.)
2. Our parser pulls out each row: test name, value, unit, and **the reference range the
   lab printed on that same row**.
3. Each value is compared against *that lab's own range*. Nothing is compared to a
   table we wrote.
4. For every value outside range, the page shows what the test measures, what a high or
   low result can suggest, and one question worth asking the doctor — each line carrying
   the source it came from and the date that source was last updated.
5. **Amazon Bedrock** joins those sourced notes and the patient's own numbers into a
   short paragraph, in English or Hindi. It is given the facts; it is not asked to
   supply them.

It explains. It does not diagnose, it names no medicine, and every answer ends by
pointing at a doctor.

## The decision we are most sure about

**We read the reference range off the patient's report rather than storing our own.**

Ranges genuinely differ between labs, machines and methods, and between men, women and
children. An app that hardcodes them will tell somebody their result is abnormal when
their own lab says it is fine. Reading the lab's printed range means the comparison
belongs to the lab, and our part is arithmetic. It also keeps the medical claims in our
code down to zero, which is the right place for them to be.

## Why this team

We already build software for exactly this corner of Indian healthcare.

**Kliniqo** is our pathology-lab product, live in production today. It is the system
that produces reports like the ones this tool reads,
so we know their layouts, their quirks, and how a lab actually prints a reference
interval. That is the part a team without this background gets wrong.

**Niqo** is our AI assistant project, which taught us the discipline this needed:
grounding an AI in sourced material rather than letting it answer from memory, keeping
a hard cap on per-day spend, and falling back gracefully when the model is unavailable.
All three ideas are in this build.

We are not guessing about the problem either: it is the question labs get asked after
the report is handed over, and a lab has no time to answer it.

## Impact

For the patient: they arrive at the consultation knowing which two numbers matter and
what to ask, instead of handing over a sheet of paper and waiting.

For the lab: fewer calls asking what a number means.

The honest limit: this tool cannot tell anyone what is wrong with them, and should not.
Its ambition is to turn an unreadable page into three sensible questions.

## What is not built yet

- Only blood tests with a printed numeric range are read. Scans, cultures and
  descriptive findings are out of scope.
- Hindi is translated at the point of writing; we have not had the output checked by a
  native-speaking clinician.
- The sourced glossary covers thirteen common tests. Anything else is still flagged as
  high or low from the lab's own range, but without an explanation.
