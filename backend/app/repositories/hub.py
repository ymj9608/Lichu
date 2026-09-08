from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.entities import License, LicenseRequest, LicenseAssignment
from app.core.errors import AppError


def get(db: Session, model, key: int, lock=False):
    stmt = select(model).where(model.id == key)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    row = db.scalar(stmt)
    if row is None:
        raise AppError(404, 'NOT_FOUND', '해당 데이터를 찾을 수 없습니다.')
    return row


def rows(db: Session, model, *filters):
    return db.scalars(select(model).where(*filters).order_by(model.id.desc())).all()


def used(db: Session, license_id: int):
    return db.scalar(select(func.count()).select_from(LicenseAssignment).where(
        LicenseAssignment.license_id == license_id, LicenseAssignment.status == 'ACTIVE'))


def has(db: Session, model, user_id: int, license_id: int, status: str):
    return db.scalar(select(model.id).where(model.user_id == user_id,
        model.license_id == license_id, model.status == status).limit(1)) is not None


def licenses(db: Session, q: str | None = None, category: str | None = None):
    stmt = select(License).order_by(License.id)
    if q:
        stmt = stmt.where(License.name.icontains(q, autoescape=True) | License.vendor.icontains(q, autoescape=True))
    if category:
        stmt = stmt.where(License.category == category)
    return db.scalars(stmt).all()
