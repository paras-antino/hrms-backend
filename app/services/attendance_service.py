"""
Business logic for Attendance operations.
"""

from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.schemas.attendance import AttendanceCreate


async def get_attendance_list(
    db: AsyncSession,
    employee_id: int | None = None,
    filter_date: date | None = None,
) -> list[Attendance]:
    """Get attendance records with optional filters, newest first."""
    query = (
        select(Attendance)
        .options(selectinload(Attendance.employee))
        .order_by(Attendance.date.desc())
    )
    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)
    if filter_date:
        query = query.where(Attendance.date == filter_date)
    result = await db.execute(query)
    return list(result.scalars().all())


async def check_attendance_exists(
    db: AsyncSession,
    emp_id: int,
    att_date: date,
    exclude_pk: int | None = None,
) -> bool:
    """Check if attendance already exists for this employee on this date."""
    query = select(Attendance).where(
        Attendance.employee_id == emp_id,
        Attendance.date == att_date,
    )
    if exclude_pk:
        query = query.where(Attendance.id != exclude_pk)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def create_attendance(db: AsyncSession, data: AttendanceCreate) -> Attendance:
    """Create a new attendance record."""
    attendance = Attendance(
        employee_id=data.employee,
        date=data.date,
        status=data.status,
    )
    db.add(attendance)
    await db.flush()
    await db.refresh(attendance)
    return attendance


async def get_attendance_with_employee(db: AsyncSession, pk: int) -> Attendance | None:
    """Get a single attendance record with employee eagerly loaded."""
    result = await db.execute(
        select(Attendance).options(selectinload(Attendance.employee)).where(Attendance.id == pk)
    )
    return result.scalar_one_or_none()


async def get_attendance_by_employee(
    db: AsyncSession,
    employee_pk: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[Attendance]:
    """Get attendance records for one employee with optional date range."""
    query = (
        select(Attendance)
        .options(selectinload(Attendance.employee))
        .where(Attendance.employee_id == employee_pk)
        .order_by(Attendance.date.desc())
    )
    if date_from:
        query = query.where(Attendance.date >= date_from)
    if date_to:
        query = query.where(Attendance.date <= date_to)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_attendance_summary(db: AsyncSession) -> dict:
    """Dashboard summary: totals and present days per employee."""
    today = date.today()

    # Total employees
    total_result = await db.execute(select(func.count(Employee.id)))
    total_employees = total_result.scalar() or 0

    # Present today
    present_result = await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.date == today, Attendance.status == "present"
        )
    )
    present_today = present_result.scalar() or 0

    # Absent today
    absent_result = await db.execute(
        select(func.count(Attendance.id)).where(
            Attendance.date == today, Attendance.status == "absent"
        )
    )
    absent_today = absent_result.scalar() or 0

    # Present days per employee
    present_counts_result = await db.execute(
        select(Attendance.employee_id, func.count(Attendance.id).label("present_days"))
        .where(Attendance.status == "present")
        .group_by(Attendance.employee_id)
        .order_by(func.count(Attendance.id).desc())
    )
    present_days_by_employee = [
        {"employee_id": row.employee_id, "present_days": row.present_days}
        for row in present_counts_result.all()
    ]

    return {
        "total_employees": total_employees,
        "present_today": present_today,
        "absent_today": absent_today,
        "present_days_by_employee": present_days_by_employee,
    }


async def delete_attendance(db: AsyncSession, attendance: Attendance) -> None:
    """Delete an attendance record."""
    await db.delete(attendance)
    await db.flush()
