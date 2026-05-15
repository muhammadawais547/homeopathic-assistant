# models/patient.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Patient:
    patient_id: str
    name: str
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    blood_pressure: Optional[str] = None
    complexion: Optional[str] = None
    thermal_type: Optional[str] = None
    miasm: Optional[str] = None
    medical_history: Optional[str] = None
    mental_symptoms: Optional[str] = None
    body_issues: Optional[str] = None
    modalities: Optional[str] = None
    aggravation: Optional[str] = None     # replaces pain_time
    amelioration: Optional[str] = None   # new field
    created_at: Optional[str] = None

    @staticmethod
    def generate_id() -> str:
        return f"P{int(datetime.now().timestamp())}"