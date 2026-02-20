"""
SQLAlchemy ORM model for Attendance.
Maps to the existing 'attendance_attendance' table in the database.
"""

from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Attendance(Base):
    """Attendance record: one per employee per date."""

    __tablename__ = "attendance_attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees_employee.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="present")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationship back to employee
    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="unique_employee_date"),
    )

    def __repr__(self) -> str:
        return f"<Attendance {self.employee_id} - {self.date} - {self.status}>"


# Import to resolve forward reference
from app.models.employee import Employee  # noqa: E402, F401
