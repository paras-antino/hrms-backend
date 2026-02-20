"""
Pydantic schemas for Attendance API validation and serialization.
"""

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.employee import EmployeeResponse


class AttendanceCreate(BaseModel):
    """Schema for creating an attendance record."""

    employee: int = Field(..., description="Employee database ID")
    date: dt.date = Field(..., description="Attendance date")
    status: str = Field(..., description="present or absent")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("present", "absent"):
            raise ValueError('Status must be "present" or "absent".')
        return v


class AttendanceResponse(BaseModel):
    """Schema for attendance response with employee detail."""

    id: int
    employee: int  # Employee FK ID
    employee_detail: Optional[EmployeeResponse] = None
    date: dt.date
    status: str

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    """Dashboard summary response."""

    total_employees: int
    present_today: int
    absent_today: int
    present_days_by_employee: list[dict]


class EmployeeAttendanceData(BaseModel):
    """Attendance records for a specific employee."""

    employee: dict
    records: list[AttendanceResponse]
