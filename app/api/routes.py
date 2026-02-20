"""
FastAPI API route handlers.
All routes return the same JSON shape as the original Django DRF API:
  { "success": true/false, "data": ..., "errors": ..., "message": ... }
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.schemas.attendance import AttendanceCreate, AttendanceResponse
from app.services import employee_service, attendance_service

router = APIRouter()


# ────────────────────────────────────────────────
# EMPLOYEE ENDPOINTS
# ────────────────────────────────────────────────


@router.get("/employees/")
async def list_employees(db: AsyncSession = Depends(get_db)):
    """GET /api/employees/ — list all employees."""
    employees = await employee_service.get_all_employees(db)
    data = [EmployeeResponse.model_validate(e).model_dump() for e in employees]
    return {"success": True, "data": data}


@router.post("/employees/", status_code=201)
async def create_employee(payload: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    """POST /api/employees/ — add a new employee."""
    errors = {}

    # Validate uniqueness
    if await employee_service.check_employee_id_exists(db, payload.employee_id):
        errors["employee_id"] = ["An employee with this Employee ID already exists."]
    if await employee_service.check_email_exists(db, payload.email):
        errors["email"] = ["An employee with this email already exists."]

    if errors:
        return JSONResponse(status_code=400, content={"success": False, "errors": errors})

    employee = await employee_service.create_employee(db, payload)
    data = EmployeeResponse.model_validate(employee).model_dump()
    return {"success": True, "data": data}


@router.get("/employees/{employee_pk}/")
async def get_employee(employee_pk: int, db: AsyncSession = Depends(get_db)):
    """GET /api/employees/{id}/ — get one employee."""
    employee = await employee_service.get_employee_by_id(db, employee_pk)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    data = EmployeeResponse.model_validate(employee).model_dump()
    return {"success": True, "data": data}


@router.delete("/employees/{employee_pk}/")
async def delete_employee(employee_pk: int, db: AsyncSession = Depends(get_db)):
    """DELETE /api/employees/{id}/ — delete an employee."""
    employee = await employee_service.get_employee_by_id(db, employee_pk)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")
    await employee_service.delete_employee(db, employee)
    return {"success": True, "message": "Employee deleted."}


# ────────────────────────────────────────────────
# ATTENDANCE ENDPOINTS
# ────────────────────────────────────────────────


@router.get("/attendance/")
async def list_attendance(
    employee_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None, alias="date"),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/attendance/ — list attendance records with optional filters."""
    filter_date = None
    if date:
        try:
            from datetime import date as date_type
            filter_date = date_type.fromisoformat(date)
        except ValueError:
            pass

    records = await attendance_service.get_attendance_list(db, employee_id, filter_date)
    data = []
    for r in records:
        item = {
            "id": r.id,
            "employee": r.employee_id,
            "employee_detail": EmployeeResponse.model_validate(r.employee).model_dump() if r.employee else None,
            "date": str(r.date),
            "status": r.status,
        }
        data.append(item)
    return {"success": True, "data": data}


@router.post("/attendance/", status_code=201)
async def create_attendance(payload: AttendanceCreate, db: AsyncSession = Depends(get_db)):
    """POST /api/attendance/ — mark attendance."""
    # Check employee exists
    employee = await employee_service.get_employee_by_id(db, payload.employee)
    if not employee:
        return JSONResponse(status_code=400, content={"success": False, "errors": {"employee": ["Employee not found."]}})

    # Check duplicate
    if await attendance_service.check_attendance_exists(db, payload.employee, payload.date):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "errors": {
                    "non_field_errors": ["Attendance for this employee on this date already exists."]
                },
            },
        )

    attendance = await attendance_service.create_attendance(db, payload)
    # Reload with employee detail
    full_record = await attendance_service.get_attendance_with_employee(db, attendance.id)
    data = {
        "id": full_record.id,
        "employee": full_record.employee_id,
        "employee_detail": EmployeeResponse.model_validate(full_record.employee).model_dump() if full_record.employee else None,
        "date": str(full_record.date),
        "status": full_record.status,
    }
    return {"success": True, "data": data}


@router.get("/attendance/summary/")
async def attendance_summary(db: AsyncSession = Depends(get_db)):
    """GET /api/attendance/summary/ — dashboard summary."""
    summary = await attendance_service.get_attendance_summary(db)
    return {"success": True, "data": summary}


@router.get("/attendance/employee/{employee_pk}/")
async def attendance_by_employee(
    employee_pk: int,
    db: AsyncSession = Depends(get_db),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    """GET /api/attendance/employee/{id}/ — attendance for one employee."""
    employee = await employee_service.get_employee_by_id(db, employee_pk)
    if not employee:
        return {
            "success": False,
            "errors": {"detail": "Employee not found."},
        }

    d_from = None
    d_to = None
    try:
        from datetime import date as date_type
        if from_date:
            d_from = date_type.fromisoformat(from_date)
        if to_date:
            d_to = date_type.fromisoformat(to_date)
    except ValueError:
        pass

    records = await attendance_service.get_attendance_by_employee(db, employee_pk, d_from, d_to)
    records_data = []
    for r in records:
        records_data.append({
            "id": r.id,
            "employee": r.employee_id,
            "employee_detail": EmployeeResponse.model_validate(r.employee).model_dump() if r.employee else None,
            "date": str(r.date),
            "status": r.status,
        })

    return {
        "success": True,
        "data": {
            "employee": {
                "id": employee.id,
                "employee_id": employee.employee_id,
                "full_name": employee.full_name,
                "email": employee.email,
                "department": employee.department,
            },
            "records": records_data,
        },
    }


@router.delete("/attendance/{pk}/")
async def delete_attendance(pk: int, db: AsyncSession = Depends(get_db)):
    """DELETE /api/attendance/{pk}/ — remove an attendance record."""
    record = await attendance_service.get_attendance_with_employee(db, pk)
    if not record:
        return {
            "success": False,
            "errors": {"detail": "Attendance record not found."},
        }
    await attendance_service.delete_attendance(db, record)
    return {"success": True, "message": "Attendance record deleted."}
