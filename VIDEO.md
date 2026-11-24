# AWS demo video — under 3 minutes

Screen recording of the live site, one voice over it. Record at 1080p. They score
**Demo and Storytelling at 20%**, and the brief asks the video to cover the problem,
who it helps, how it works, the impact, and why most people should care — so say all
five, plainly.

Record against the **live AWS URL**, not localhost. The judges will notice.

---

### 0:00–0:25 — the problem, shown not described

**On screen:** a lab report PDF open, scrolled slowly. No app yet.

> "This is a blood test report. If you have had a test done in India, you have been
> handed one of these. Twenty abbreviations, twenty numbers, and a column of ranges in
> the same small print.
>
> Most people look for red ink, find none, and assume they are fine. Or find one and
> assume the worst. The three things they actually need are not on this page: which
> numbers are outside the range, what each one measures, and what to ask the doctor."

### 0:25–1:15 — the thing working

**On screen:** the live site. Upload the same report. Let the real wait happen — don't cut it.

> "So we built this. Upload the report your lab gave you — the PDF, or just a photo of
> the printout, which is what most people actually have.
>
> Textract reads the page. Our parser pulls out every row: the test, the value, the
> unit, and the range. Then it compares them."

**Let the results appear.** Scroll to one card, slowly.

> "Six values outside range. For each one: what the test measures, what a high result
> can suggest, and one question to ask the doctor — with the source and the date it was
> last reviewed, because this is someone's health and they should be able to check us.
>
> It explains. It never diagnoses, it never names a medicine, and every answer ends by
> pointing at a doctor."

### 1:15–1:40 — the decision to be proud of

**On screen:** zoom on the line that reads "your lab: 0.55 – 4.78".

> "Here is the choice we care most about. We do not store reference ranges. We read the
> range off the patient's own report.
>
> Ranges genuinely differ between labs, machines and methods. An app with its own table
> will eventually tell someone they are abnormal when their own lab says they are fine.
> Reading the lab's printed range means the judgement belongs to the lab — our part is
> arithmetic."

### 1:40–2:10 — Hindi, and what is under it

**On screen:** press हिंदी. Then briefly show the architecture diagram or the template file.

> "Same report, in Hindi.
>
> Underneath: API Gateway to Lambda, Textract to read the page, and Bedrock to write
> the paragraph. Bedrock is handed sourced notes and told to use no fact of its own. If
> Bedrock is down, the page still works and shows the sourced notes. It degrades to
> plain, never to silent.
>
> Nothing is stored. The report lives in memory for one request."

### 2:10–2:40 — why us, and why it matters

> "We build Kliniqo, a pathology lab product that is live today — it is the kind of
> system that prints reports like this one, so we know their layouts and their quirks.
> This tool exists because it is the question labs get asked after handing the report
> over, and a lab has no time to answer it.
>
> If you can afford a follow-up consultation the same week, a confusing report costs
> you nothing. If you cannot, that sheet of paper is the only medical information you
> will have for months. That is who this is for.
>
> It turns an unreadable page into three sensible questions. Team Clauduss."

---

## Before recording

- Deploy and open the live URL; click through both samples once so nothing is cold.
- Use the **sugar & cholesterol** sample: six values outside range reads well on camera.
- Say the team name once. Don't read numbers off a slide — let the page show them.
- Keep it under 3:00. The cut above runs about 2:40.
