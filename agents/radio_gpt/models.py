from pydantic import BaseModel, Field
from typing import List


class Recipient(BaseModel):
    phone: str
    language: str = Field(
        default="English",
        description="Preferred language of the recipient"
    )
    voice_gender: str = Field(
        default="male",
        description="Preferred voice gender"
    )


class DisasterAlert(BaseModel):
    alert_id: str
    severity: str
    hazard: str
    location: str
    eta_minutes: int
    approved_actions: List[str] = Field(
        default_factory=list
    )
    recipient: Recipient