from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = 'departments'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('USER','MASTER')", name='ck_user_role'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    department_id: Mapped[int] = mapped_column(ForeignKey('departments.id'))
    department: Mapped[Department] = relationship(lazy='joined')
    job_title: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    profile_image: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(10), default='USER')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class License(Base):
    __tablename__ = 'licenses'
    __table_args__ = (
        CheckConstraint('total_seats >= 0', name='ck_license_seats'),
        CheckConstraint('unit_price >= 0', name='ck_license_price'),
        CheckConstraint("status IN ('ACTIVE','INACTIVE')", name='ck_license_status'),
        CheckConstraint("billing_cycle IN ('MONTHLY','YEARLY')", name='ck_billing_cycle'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    vendor: Mapped[str] = mapped_column(String(100))
    plan_name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    total_seats: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    billing_cycle: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(10), default='ACTIVE')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class LicenseRequest(Base):
    __tablename__ = 'license_requests'
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','APPROVED','REJECTED','CANCELED')", name='ck_request_status'),
        CheckConstraint('start_date <= end_date', name='ck_request_dates'),
        Index('uq_pending_user_license', 'user_id', 'license_id', unique=True,
              postgresql_where=text("status = 'PENDING'"), sqlite_where=text("status = 'PENDING'")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    license_id: Mapped[int] = mapped_column(ForeignKey('licenses.id'))
    reason: Mapped[str] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10), default='PENDING')
    decision_reason: Mapped[str | None] = mapped_column(Text)
    processed_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LicenseAssignment(Base):
    __tablename__ = 'license_assignments'
    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','RETURNED','REVOKED')", name='ck_assignment_status'),
        CheckConstraint('valid_from <= valid_until', name='ck_assignment_period'),
        Index('uq_active_user_license', 'user_id', 'license_id', unique=True,
              postgresql_where=text("status = 'ACTIVE'"), sqlite_where=text("status = 'ACTIVE'")),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    license_id: Mapped[int] = mapped_column(ForeignKey('licenses.id'))
    request_id: Mapped[int | None] = mapped_column(ForeignKey('license_requests.id'), unique=True)
    status: Mapped[str] = mapped_column(String(10), default='ACTIVE')
    assigned_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_until: Mapped[date] = mapped_column(Date)
    ended_by: Mapped[int | None] = mapped_column(ForeignKey('users.id'))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_reason: Mapped[str | None] = mapped_column(Text)
