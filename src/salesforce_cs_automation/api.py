from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Salesforce CS Automation")


class CaseRequest(BaseModel):
    subject: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: Literal["High", "Medium", "Low"] = "Medium"
    origin: Literal["Web", "Phone", "Email"] = "Web"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/cases")
def receive_case(case: CaseRequest) -> dict[str, str]:
    return {
        "status": "received",
        "subject": case.subject,
        "priority": case.priority,
        "origin": case.origin,
    }
