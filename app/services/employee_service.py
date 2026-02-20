"""
Business logic for Employee operations.
Keeps route handlers thin — all DB logic lives here.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate


async def get_all_employees(db: AsyncSession) -> list[Employee]:
    """Get all employees ordered by full_name."""
    result = await db.execute(select(Employee).order_by(Employee.full_name))
    return list(result.scalars().all())


async def get_employee_by_id(db: AsyncSession, employee_pk: int) -> Employee | None:
    """Get a single employee by primary key."""
    return await db.get(Employee, employee_pk)


async def check_employee_id_exists(db: AsyncSession, emp_id: str) -> bool:
    """Check if an employee_id already exists."""
    result = await db.execute(select(Employee).where(Employee.employee_id == emp_id))
    return result.scalar_one_or_none() is not None


async def check_email_exists(db: AsyncSession, email: str, exclude_pk: int | None = None) -> bool:
    """Check if an email already exists (optionally excluding a specific record)."""
    query = select(Employee).where(Employee.email == email)
    if exclude_pk:
        query = query.where(Employee.id != exclude_pk)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def create_employee(db: AsyncSession, data: EmployeeCreate) -> Employee:
    """Create a new employee."""
    employee = Employee(
        employee_id=data.employee_id,
        full_name=data.full_name,
        email=data.email,
        department=data.department,
    )
    db.add(employee)
    await db.flush()
    await db.refresh(employee)
    return employee


async def delete_employee(db: AsyncSession, employee: Employee) -> None:
    """Delete an employee (cascades to attendance records)."""
    await db.delete(employee)
    await db.flush()
