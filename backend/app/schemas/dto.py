from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, model_validator, field_validator

Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
ReasonText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


def validate_profile_image(value: str | None):
    if value is None or value == '':
        return None
    allowed = ('data:image/jpeg;base64,', 'data:image/png;base64,', 'data:image/webp;base64,')
    if not value.startswith(allowed):
        raise ValueError('JPG, PNG, WEBP 이미지만 등록할 수 있습니다.')
    return value


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ErrorOut(BaseModel):
    code: str
    message: str
    fields: dict[str, str] = Field(default_factory=dict)


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employee_no: str
    name: str
    department_id: int
    department: DepartmentOut
    job_title: str
    email: str
    username: str
    role: Literal['USER', 'MASTER']
    profile_image: str | None
    created_at: datetime
    updated_at: datetime


class Signup(Input):
    phone_number: str | None = Field(default=None, pattern=r'^010-0000-[0-9]{4}$')
    employee_no: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    name: Text100
    department_id: int = Field(gt=0)
    job_title: Text100
    email: EmailStr = Field(max_length=255)
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=100)]
    password: str = Field(min_length=8, max_length=72)
    password_confirm: str
    profile_image: str | None = None

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return value.lower()

    @field_validator('password')
    @classmethod
    def password_bytes(cls, value):
        if len(value.encode()) > 72:
            raise ValueError('비밀번호는 UTF-8 기준 72바이트 이하여야 합니다.')
        return value

    @model_validator(mode='after')
    def match(self):
        if self.password != self.password_confirm:
            raise ValueError('비밀번호 확인이 일치하지 않습니다.')
        return self

    @field_validator('profile_image')
    @classmethod
    def image_format(cls, value):
        return validate_profile_image(value)


class ProfileUpdate(Input):
    name: Text100
    department_id: int = Field(gt=0)
    job_title: Text100
    email: EmailStr = Field(max_length=255)
    profile_image: str | None = None

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        return value.lower()

    @field_validator('profile_image')
    @classmethod
    def image_format(cls, value):
        return validate_profile_image(value)


class Login(Input):
    username: Text100
    password: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LicenseInput(Input):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
    vendor: Text100
    plan_name: Text100
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
    description: ReasonText
    total_seats: int = Field(ge=0, le=1000000)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    billing_cycle: Literal['MONTHLY', 'YEARLY']
    status: Literal['ACTIVE', 'INACTIVE']


class LicensePatch(Input):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)] | None = None
    vendor: Text100 | None = None
    plan_name: Text100 | None = None
    category: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)] | None = None
    description: ReasonText | None = None
    total_seats: int | None = Field(default=None, ge=0, le=1000000)
    unit_price: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    billing_cycle: Literal['MONTHLY', 'YEARLY'] | None = None
    status: Literal['ACTIVE', 'INACTIVE'] | None = None

    @model_validator(mode='after')
    def non_null(self):
        if not self.model_fields_set or any(getattr(self, k) is None for k in self.model_fields_set):
            raise ValueError('수정 필드는 비어 있거나 null일 수 없습니다.')
        return self


class LicenseOut(LicenseInput):
    id: int
    created_at: datetime
    updated_at: datetime
    used_seats: int
    available_seats: int
    utilization: float
    monthly_unit_price: Decimal
    request_block: Literal['ACTIVE_ASSIGNMENT', 'PENDING_REQUEST', 'INACTIVE'] | None


class RequestInput(Input):
    license_id: int = Field(gt=0)
    reason: ReasonText
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def dates(self):
        if self.start_date > self.end_date:
            raise ValueError('시작일은 종료일 이전이어야 합니다.')
        return self


class Reason(Input):
    reason: ReasonText


class AssignmentPeriod(Input):
    valid_from: date
    valid_until: date

    @model_validator(mode='after')
    def dates(self):
        if self.valid_from > self.valid_until:
            raise ValueError('권한 승인 시작일은 종료일 이전이어야 합니다.')
        return self


class RequestOut(BaseModel):
    id: int
    user_id: int
    license_id: int
    user: UserOut
    license: LicenseOut
    reason: str
    start_date: date
    end_date: date
    status: Literal['PENDING', 'APPROVED', 'REJECTED', 'CANCELED']
    decision_reason: str | None
    processed_by: int | None
    processor: UserOut | None
    processed_at: datetime | None
    canceled_at: datetime | None
    created_at: datetime


class AssignmentOut(BaseModel):
    id: int
    user_id: int
    license_id: int
    request_id: int | None
    user: UserOut
    license: LicenseOut
    reason: str | None
    end_date: date | None
    status: Literal['ACTIVE', 'RETURNED', 'REVOKED']
    assigned_by: int
    assigned_at: datetime
    valid_from: date
    valid_until: date
    ended_by: int | None
    ended_at: datetime | None
    end_reason: str | None


class DashboardOut(BaseModel):
    total_seats: int
    used_seats: int
    available_seats: int
    pending_requests: int
    licenses: list[LicenseOut]
    high_utilization: list[LicenseOut]
    recent_requests: list[RequestOut]
