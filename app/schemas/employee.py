"""
Pydantic schemas for Employee API validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class EmployeeCreate(BaseModel):
    """Schema for creating an employee."""

    employee_id: str = Field(..., min_length=1, max_length=50, description="Unique employee ID")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    department: str = Field(..., min_length=1, max_length=100, description="Department name")

    @field_validator("employee_id", "full_name", "department")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class EmployeeResponse(BaseModel):
    """Schema for employee response."""

    id: int
    employee_id: str
    full_name: str
    email: str
    department: str
    created_at: datetime

    model_config = {"from_attributes": True}
