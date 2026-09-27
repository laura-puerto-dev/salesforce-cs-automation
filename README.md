# Salesforce CS Automation

Customer Success workflow automation using Python, FastAPI, n8n, and Salesforce.

> Work in progress — the project is being developed incrementally, with a focus on reliable integrations, API security, and workflow automation.

## Use Case

Automate the intake of Customer Success support requests and create corresponding Salesforce Cases.

The workflow uses n8n to receive and validate incoming requests, a Python API to handle Salesforce integration, and OAuth Client Credentials for service-to-service authentication.

## Current Status

**Implemented and tested:**

* Salesforce REST client with Case creation, updates, and queries
* OAuth PKCE and Client Credentials authentication
* FastAPI endpoint for creating Salesforce Cases
* Pydantic request validation
* API key protection for `POST /cases`
* Unit tests covering successful requests, validation, authentication, and integration errors

**Implemented and validated end to end:**

* Local n8n workflow with webhook intake, input validation, and authenticated HTTP requests to FastAPI
* Complete n8n → FastAPI → Salesforce workflow, including successful Case creation in Salesforce
* Webhook responses that wait for downstream processing and return the actual processing result
* Separate response paths for successful Case creation, workflow validation errors, and HTTP errors returned by FastAPI
* Controlled `503 Service Unavailable` response when n8n cannot connect to FastAPI
* Exported n8n workflow available in `n8n/customer-success-case-intake.json`

**Planned:**

* Add a user-facing support form
* Improve retry handling, idempotency, and observability
* Evaluate persistent recovery of failed requests

## Architecture

```text
Support request
      |
      v
n8n webhook
      |
      v
Input validation
      |
      +-- Invalid request --> HTTP 400
      |
      v
FastAPI POST /cases
      |
      +-- API key validation
      |
      +-- Salesforce OAuth Client Credentials
      |             |
      |             v
      |       Salesforce REST API
      |             |
      |             v
      |         Create Case
      |
      +-- HTTP response
      |      |
      |      +-- Success --> HTTP 201
      |      |
      |      +-- API error --> Forward HTTP status and body
      |
      +-- Connection failure --> HTTP 503
```

n8n handles workflow orchestration, while FastAPI owns the Salesforce integration and provides an independently validated API boundary.

The webhook waits for downstream processing and returns the corresponding response through dedicated Respond to Webhook nodes.

The n8n HTTP Request node distinguishes HTTP responses from execution errors. HTTP responses are processed by the normal output, while connection failures are routed to a separate error output that returns a controlled `503` response.

## Local Development

Requires Python 3.12, uv, Docker, and a configured Salesforce Developer Edition organization.

Install dependencies and create the environment file:

```powershell
uv sync
Copy-Item .env.example .env
```

Configure your own Salesforce credentials and generate a private `CS_API_KEY` in `.env`. Never commit this file.

Start FastAPI:

```powershell
uv run uvicorn salesforce_cs_automation.api:app --reload
```

Start n8n:

```powershell
docker compose up -d
```

The API is available at `http://127.0.0.1:8000`, and n8n at `http://localhost:5678`.

### n8n Workflow Setup

Import `n8n/customer-success-case-intake.json` into your local n8n instance.

Create a **Header Auth** credential with the following configuration:

* **Name:** `X-API-Key`
* **Value:** the same private `CS_API_KEY` configured in your `.env` file

Assign this credential to the `FastAPI - Create Case` HTTP Request node. The exported workflow contains a reference to the original n8n credential, but does not include its secret value.

The HTTP Request node uses `http://host.docker.internal:8000/cases` to reach FastAPI from the n8n Docker container.

The workflow is exported with `"active": false`. For local testing, use n8n's **Execute workflow** button and send requests to the test webhook:

```text
http://localhost:5678/webhook-test/customer-support
```

In test mode, the webhook must be registered again before each new execution.

To use the production webhook, activate the workflow in n8n.

Each developer must use their own Salesforce organization, OAuth application credentials, and API key. No live credentials are included in the repository.

### Testing Service Unavailability

The workflow includes a dedicated error path for connection failures between n8n and FastAPI.

To reproduce the manually validated scenario:

1. Stop FastAPI while keeping n8n running.
2. Click **Execute workflow** in n8n to register the test webhook.
3. Send a valid support request to the test webhook.
4. Verify that the webhook returns `503 Service Unavailable` with the following response:

```json
{
  "error": "Service temporarily unavailable",
  "detail": "Unable to connect to the case creation service"
}
```

The HTTP Request node uses **Continue (using error output)** to route execution failures to `Respond - Service Unavailable`.

The **Never Error** option remains enabled so HTTP errors returned by FastAPI can be processed separately and forwarded with their original status code and response body.

This test has been performed manually with FastAPI stopped. It does not establish recovery guarantees for every possible network failure.

## Quality Checks

```powershell
uv run pytest
uv run mypy src/ tests/
uv run ruff check .
```

Unit tests use mocks and do not require live Salesforce credentials.

## Architecture Decisions

Detailed architecture decisions, security boundaries, integration trade-offs, and deferred reliability improvements are documented in [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md).
