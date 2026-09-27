# Salesforce CS Automation

Customer Success workflow automation using Python, FastAPI, n8n, and Salesforce.

> Work in progress — the project is being developed incrementally, with a focus on reliable integrations, API security, and workflow automation.

## Use Case

Automate the intake of Customer Success support requests and create corresponding Salesforce Cases.

The intended workflow uses n8n to receive and validate incoming requests, a Python API to handle Salesforce integration, and OAuth Client Credentials for service-to-service authentication.

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

**Planned:**

* Improve webhook responses and failure handling
* Add a user-facing support form

## Architecture

```text
Support request
      ↓
n8n webhook
      ↓
Input validation
      ↓
FastAPI POST /cases
      ├── API key validation
      └── Salesforce OAuth Client Credentials
                    ↓
              Salesforce REST API
                    ↓
                Create Case
```

n8n handles workflow orchestration, while FastAPI owns the Salesforce integration and provides an independently validated API boundary.

## Local Development

Requires Python 3.12, uv, Docker, and a configured Salesforce Developer Edition organization.

Install dependencies and create the environment file:

```powershell
uv sync
Copy-Item .env.example .env
```

Configure your Salesforce credentials and generate a private `CS_API_KEY` in `.env`. Never commit this file.

Start FastAPI:

```powershell
uv run uvicorn salesforce_cs_automation.api:app --reload
```

Start n8n:

```powershell
docker compose up -d
```

The API is available at `http://127.0.0.1:8000`, and n8n at `http://localhost:5678`.

The n8n workflow must be configured separately before running the complete integration.

## Quality Checks

```powershell
uv run pytest
uv run mypy src/ tests/
uv run ruff check .
```

Unit tests use mocks and do not require live Salesforce credentials.

## Architecture Decisions

Detailed architecture decisions, security boundaries, integration trade-offs, and deferred reliability improvements are documented in [Architecture Decisions](docs/ARCHITECTURE_DECISIONS.md).
