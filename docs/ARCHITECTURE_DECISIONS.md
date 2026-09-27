# Architecture Decisions

Salesforce CS Automation — architecture, security boundaries, design trade-offs, and known limitations.

> Work in progress. This document distinguishes implemented capabilities from validated integrations and planned improvements.

## 1. System Overview

The project automates Customer Success support-request intake and Salesforce Case creation.

The current workflow is:

```text
Support request
      |
      v
n8n Webhook
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
      |
      v
Salesforce REST API
      |
      v
Salesforce Case
      |
      v
Return API response through n8n
      |
      +-- Success --> HTTP 201
      |
      +-- API error --> Forward status and body
```

The current workflow uses HTTP requests to simulate a future support form. A user-facing interface has not been implemented.

The complete n8n → FastAPI → Salesforce workflow has been validated end to end using an authenticated HTTP request from n8n. Successful Salesforce Case creation was confirmed in the Salesforce Developer Edition organization.

The n8n webhook waits for downstream processing and returns the corresponding result through dedicated Respond to Webhook nodes.

The workflow is exported in `n8n/customer-success-case-intake.json` for local import and configuration.

## 2. Why n8n and FastAPI?

**Decision:** Use n8n for workflow orchestration and FastAPI for the Salesforce integration.

n8n receives support requests through a webhook, validates incoming data, and forwards accepted requests to FastAPI.

FastAPI owns the application-level request contract, authentication boundary, and Salesforce integration. Salesforce-specific operations remain encapsulated in a reusable Python client.

This separation allows the intake workflow to evolve independently of the integration code. Another client, such as a web application or a different automation platform, could call the same API.

The trade-off is an additional HTTP boundary between n8n and FastAPI, which requires its own authentication, error handling, and operational configuration.

## 3. Salesforce Authentication

Two OAuth flows serve different purposes.

### Authorization Code with PKCE

The interactive PKCE flow supports local, user-authorized Salesforce access. It is useful for development and manual exploration of the Salesforce API.

The local callback is configured as `http://localhost:8765/callback` and must match the callback registered in the Salesforce application.

### Client Credentials

**Decision:** Use OAuth Client Credentials for automated Case creation.

FastAPI requests an access token using the configured Salesforce application credentials. Salesforce executes authorized operations under the configured Run As user.

This avoids requiring an interactive browser login for every automated request.

The Salesforce client receives the access token and instance URL, then performs the required REST operation.

**Security boundary:** The Salesforce token authorizes FastAPI to access Salesforce. It does not authenticate clients calling FastAPI.

## 4. FastAPI Authentication

**Decision:** Protect `POST /cases` with an API key supplied through the `X-API-Key` HTTP header.

FastAPI loads the expected key from the `CS_API_KEY` environment variable and compares it with the received value using `hmac.compare_digest()`.

Requests with a missing or incorrect key receive `401 Unauthorized` when the request body passes Pydantic validation. The API key check occurs before Salesforce authentication, preventing unauthorized callers from triggering Salesforce operations.

Pydantic request-body validation may occur before the endpoint's API key check. Therefore, an invalid request body can receive `422 Unprocessable Entity` before the API key is evaluated.

The API key is stored in the local `.env` file and must not be committed to version control. `.env.example` contains only a placeholder.

The key identifies an authorized service client, not an individual user. It is suitable for the current n8n-to-FastAPI integration, but it does not provide user-level identity, permissions, rotation, or audit trails.

n8n sends the API key using a Header Auth credential rather than storing it directly in the workflow. The exported workflow includes a credential reference, but no secret value. Each developer must configure their own credential after importing it.

The public n8n webhook is a separate entry point and requires its own security assessment.

## 5. Validation and API Contract

**Decision:** Validate requests at both the workflow and API boundaries.

The n8n Code node checks required fields and allowed values before forwarding requests.

FastAPI independently validates the request using Pydantic. The current contract requires a non-empty subject and description, accepts `High`, `Medium`, or `Low` priority, and supports `Web`, `Phone`, or `Email` origin.

Priority defaults to `Medium`, and origin defaults to `Web`.

The duplicate validation is intentional. n8n provides early workflow-level feedback, while FastAPI preserves its contract when called by another client or when the workflow changes.

The n8n workflow returns `400 Bad Request` for requests rejected by its own validation, without calling FastAPI.

FastAPI independently returns `422 Unprocessable Entity` for invalid request bodies that reach the API. These are separate validation boundaries and intentionally use different response codes.

The `POST /cases` endpoint returns `201 Created` and the Salesforce Case ID after Salesforce confirms creation.

## 6. Salesforce Integration

**Decision:** Keep Salesforce REST operations in a reusable Python client rather than implementing them directly in n8n.

The client supports SOQL queries, pagination, Case creation, and Case updates.

This centralizes Salesforce-specific HTTP behavior and makes it independently testable.

The API endpoint currently obtains a service token for an authorized request, constructs the Salesforce client, and creates the Case.

Salesforce request failures are translated into a generic `502` response. A missing access token is also treated as an integration failure.

Detailed upstream errors are not exposed to API consumers.

## 7. Testing Strategy

**Decision:** Test application behavior with mocks and keep live Salesforce checks separate.

The automated tests cover Salesforce authentication, client operations, FastAPI request validation, successful Case creation, and integration failures.

API security tests verify that:

* A valid API key permits the request to continue.
* A missing API key returns `401` for an otherwise valid request body.
* An incorrect API key returns `401` for an otherwise valid request body.
* Rejected requests do not attempt Salesforce authentication.

Mocks allow the unit tests to run without live Salesforce credentials or external network access.

Manual scripts have also been used to validate OAuth and Salesforce Case operations against a Salesforce Developer Edition organization.

The complete n8n-to-FastAPI-to-Salesforce workflow has been manually validated with n8n's API key configured. The test confirmed successful execution in n8n and creation of the corresponding Case in Salesforce.

Additional manual end-to-end tests verified the webhook response paths:

* A valid request returned `201 Created` with the Salesforce Case ID after successful creation.
* An invalid priority was rejected by n8n and returned a validation error without reaching FastAPI.
* A temporary invalid FastAPI endpoint returned `404 Not Found`; n8n preserved both the HTTP status code and the response body through its API error branch.

These tests validate application-level HTTP responses. Transport failures, such as FastAPI being unavailable, have not yet been tested or handled.

The project uses pytest, Ruff, and Mypy for automated quality checks.

## 8. Current Reliability Limitations

The current implementation intentionally favors a small, understandable integration over production-level workflow reliability.

### Webhook responses

The n8n webhook is configured to respond through dedicated Respond to Webhook nodes rather than returning an immediate response.

The workflow has three response paths:

* **Successful Case creation:** returns `201 Created` and the response body received from FastAPI.
* **n8n validation failure:** returns `400 Bad Request` with the validation error.
* **FastAPI HTTP error:** forwards the HTTP status code and response body received from FastAPI.

The successful creation and HTTP error paths have been manually validated end to end. Workflow validation errors have also been tested.

**Remaining limitation:** Network and transport failures, such as FastAPI being unreachable, can still interrupt workflow execution without a controlled webhook response.

**Planned:** Add explicit transport-error handling and test the resulting webhook response.

### Retries and duplicate Cases

The current API does not provide persistent retry handling or request idempotency.

If Salesforce creates a Case but the response is lost, a client retry could create a duplicate.

**Planned:** Define retry behavior and an idempotency strategy before introducing automatic retries.

### Persistence and recovery

There is no application-level queue or durable store for incoming support requests.

A failed request is not automatically recovered by the current implementation.

**Planned:** Evaluate whether persistent workflow execution or a dedicated queue is justified by the intended operational requirements.

### Observability

The API returns generic integration errors to clients, but structured application logging and end-to-end request correlation have not yet been implemented.

**Planned:** Introduce safe diagnostic logging without exposing tokens, API keys, or sensitive support-request data.

## 9. Security and Deployment Considerations

The current environment is intended for local development.

Salesforce credentials and the API key are configured through environment variables. Real secrets must remain outside version control.

The exported n8n workflow is inactive by default. Each developer must configure their own Header Auth credential before using it.

The API key protects `POST /cases`, but it is not a substitute for HTTPS, network restrictions, secret rotation, or production-grade identity management.

The `/health` endpoint is intentionally unauthenticated and reports application availability, not Salesforce connectivity.

Before any public deployment, the system would require a review of network exposure, TLS termination, secret management, webhook protection, and operational monitoring.

## 10. Next Steps

The authenticated n8n-to-FastAPI-to-Salesforce workflow has been validated end to end. The webhook now waits for downstream processing and returns distinct responses for successful Case creation, n8n validation failures, and FastAPI HTTP errors.

The workflow is exported in `n8n/customer-success-case-intake.json` so it can be imported into another local n8n instance. Each developer must configure their own Header Auth credential and Salesforce environment.

The next stage is to handle transport failures, particularly cases where FastAPI is unavailable, without leaving the webhook request without a controlled response.

Subsequent work will address retry behavior, duplicate prevention, operational visibility, and a user-facing support form.

Additional reliability mechanisms should be introduced in response to concrete failure scenarios rather than added speculatively.
