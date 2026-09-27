import hmac
import os
from typing import Literal

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from salesforce_cs_automation.auth import authenticate_service
from salesforce_cs_automation.client import SalesforceClient

app = FastAPI(title="Salesforce CS Automation")


class CaseRequest(BaseModel):
    subject: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: Literal["High", "Medium", "Low"] = "Medium"
    origin: Literal["Web", "Phone", "Email"] = "Web"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/cases", status_code=201)
def receive_case(
    case: CaseRequest,
    api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, str]:
    load_dotenv()
    expected_api_key = os.environ["CS_API_KEY"]

    if api_key is None or not hmac.compare_digest(api_key, expected_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )
    try:
        credentials = authenticate_service()

        client = SalesforceClient(
            access_token=credentials["access_token"],
            instance_url=credentials["instance_url"],
        )

        case_id = client.create_case(
            subject=case.subject,
            description=case.description,
            priority=case.priority,
            origin=case.origin,
        )

    except (requests.exceptions.RequestException, RuntimeError):
        raise HTTPException(
            status_code=502,
            detail="Salesforce integration failed.",
        ) from None

    return {
        "status": "created",
        "case_id": case_id,
        "subject": case.subject,
        "priority": case.priority,
        "origin": case.origin,
    }
