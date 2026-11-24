# Putting it on AWS

Everything below is one-time. Region: **ap-southeast-2 (Sydney)**.

**Why not Mumbai.** We wanted ap-south-1, and the code was written for it. But AWS's new
free plan assigns an account to exactly one region, and this account's is Sydney. The
console says plainly: "Region Asia Pacific (Mumbai) unavailable. Your project is assigned
to Asia Pacific (Sydney) ap-southeast-2. To access other commercial AWS Regions, upgrade
your plan first." Upgrading means paying, so we stay in Sydney and say so honestly. The
region is a deploy-time flag, so moving later is one command.

## Before you start

1. An AWS account signed in with the same Builder ID as the Builder Center profile.
2. **Set a budget alert first.** Billing → Budgets → a zero-spend or $5 budget with an
   email alert. Do this before anything else is created.
3. **No model access request is needed any more.** The Bedrock console now says: "Model
   access page has been retired. Serverless foundation models are now automatically
   enabled across all AWS commercial regions when first invoked in your account."
   The model we use is **`anthropic.claude-haiku-5-5`**, taken from the model catalogue in
   ap-southeast-2 on 24 Nov 2026, where it is serverless and lists Hindi among its
   languages. It is already the template's default.
4. SAM is **already installed** in this project, at `.venv/bin/sam` (version 1.155.2).
   Homebrew could not be used: its directories need a `sudo chown`, which needs your
   password. The project copy needs no password and touches nothing outside this folder.
5. Credentials for the account on this Mac. Prefer `aws login` (the device flow) over
   creating an access key: it stores a short-lived token the CLI manages itself, and no
   long-lived secret is ever written down.

## Deploy

Run these from `aws-readreport/`. The `HOME=` prefix points SAM's config at the project
folder; without it SAM tries to write to `~/.aws-sam`, which this machine's sandbox
blocks.

```bash
cd aws-readreport
HOME="$PWD/.samhome" .venv/bin/sam build --template infra/template.yaml --build-dir .aws-sam/build
```

```bash
cd aws-readreport
HOME="$PWD/.samhome" .venv/bin/sam deploy --guided --region ap-southeast-2 --stack-name read-my-report --capabilities CAPABILITY_IAM --template .aws-sam/build/template.yaml
```

Both of these have been run already as far as they can go without an account: the
template validates (`sam validate --lint`) and the Lambda package builds cleanly.

Note the two outputs it prints: `SiteUrl` and `ApiUrl`.

## Point the page at the API, then upload it

```bash
cd ../web
echo "window.READ_MY_REPORT_API = '<the ApiUrl from above>';" > config.js
sed -i '' 's#<script>#<script src="config.js"></script>\n<script>#' index.html
aws s3 sync . "s3://<the SiteBucketName>/" --delete --region ap-southeast-2
```

Open `SiteUrl`. That URL is what goes in the submission, and it must keep working
until Demo Day on 17 December.

## What it costs

Everything here sits in the Free Tier except Bedrock and Textract beyond their free
allowances, both of which are paid from the AWS credits. The API has a hard throttle of
10 requests a second so a bad day cannot run up a bill. Nothing in the stack costs
money while it is idle except a few cents of CloudFront.

## Tearing it down

```bash
sam delete --stack-name read-my-report --region ap-southeast-2
```

Do **not** do this before 17 December: the submission promises a live URL.
