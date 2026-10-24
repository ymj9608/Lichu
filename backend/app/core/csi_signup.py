"""Intentional email logging regression for an isolated CSI security scan demo.

Called only when CSI_LAB_MODE=true. This file is source evidence, not a mock finding.
Password remediation remains applied; this branch deliberately reintroduces an email leak.
"""
import bcrypt
import logging
from app.core.errors import AppError

log = logging.getLogger('uvicorn.error')


def validate_lab_signup(payload):
    if not payload.phone_number:
        raise AppError(422, 'LAB_PHONE_REQUIRED', 'CSI 실습 회원가입에는 합성 전화번호가 필요합니다.',
                       {'phone_number': '010-0000-0000 형식의 합성 번호를 입력하세요.'})
    if not (payload.username.startswith('csi_') and payload.email.endswith('@example.com')
            and payload.password == 'Demo-Only-2026!' and payload.name.startswith('테스트')):
        raise AppError(422, 'SYNTHETIC_ONLY', 'CSI 실습은 테스트 데이터 채우기로 생성한 합성 계정만 허용합니다.')
    if payload.profile_image:
        raise AppError(422, 'SYNTHETIC_ONLY', 'CSI 실습에서는 실제 프로필 사진을 수집하지 않습니다.')
    # INTENTIONAL SEC-05: validated synthetic email reaches the diagnostic log unmasked.
    log.info('CSI lab signup diagnostics email=%s', payload.email)

def hash_signup_password(password: str) -> str:
    # AFTER FIX: library-generated per-password salt and policy cost 12.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_lab_password(password: str, hashed: str) -> bool:
    # Legacy lab accounts require re-registration; never guess or migrate passwords.
    return False


def lab_version() -> str:
    return 'after-fix'
