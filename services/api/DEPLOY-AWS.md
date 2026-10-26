# Deploy the API to AWS Lambda

The SAM template in this directory deploys the FastAPI ASGI app to an
`ap-southeast-2` Lambda function and exposes it through a public HTTPS Function
URL. It creates no VPC, NAT gateway, load balancer, database, or paid always-on
service. Lambda usage and CloudWatch logs are still subject to the account's
current free-tier limits.

## Database requirement

The API uses PostgreSQL features (including JSONB, PostgreSQL enums, and
PostgreSQL arrays). It cannot run correctly with SQLite or a database URL that
points to a developer's local Docker network. `DatabaseUrl` is therefore a
required, secret CloudFormation parameter. Supply a PostgreSQL URL that is
reachable from a Lambda function running outside a VPC. The template does not
create an RDS instance because RDS free-tier eligibility and remaining account
credits are account-specific, and an always-on database can incur charges.

Before serving requests, apply the schema migrations to that database:

```powershell
$env:DATABASE_URL = "<reachable PostgreSQL SQLAlchemy URL>"
python -m pip install -r requirements.txt
python -m alembic upgrade head
```

Run those commands from `services/api`. Do not use a development database
password, the committed demo encryption key, or a database reachable to the
whole internet.

## Build and deploy

Install AWS SAM CLI and Docker, authenticate the AWS CLI, and confirm that the
account and region are eligible for the intended Free Tier offer. From this
directory:

```powershell
sam build --template-file template.yaml --use-container
sam deploy --guided --region ap-southeast-2
```

The guided deployment prompts for the database URL and production secrets.
Generate a unique base64 32-byte `FieldMasterKey`, and unique high-entropy
`HashPepper`, `JwtSecret`, and `DemoUserPassword`; do not reuse development
values. The template marks these parameters `NoEcho` and does not output them.
Keep the template's default web origin for the Vercel production frontend, or
change it to the exact frontend origin. After deploy, set Vercel's
`NEXT_PUBLIC_API_BASE_URL` to the stack's `ApiUrl` output and redeploy the
frontend.

The public Function URL's HTTPS endpoint has no idle compute charge. Function
invocations, data transfer, and logs remain usage-based; no Free Tier limit can
be guaranteed without checking the account's Free Tier plan and accumulated
usage.

## Local development

`uvicorn app.main:app` and Docker Compose continue to run the same FastAPI app.
The Lambda adapter is imported only by `app.lambda_handler`, and it does not
read or require AWS credentials. Install the updated `requirements.txt` in the
API container or local virtual environment as usual.
