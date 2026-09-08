import {describe,it,expect} from 'vitest'
import {validDates,requestLabel,money} from './format'
describe('신청 입력과 표시',()=>{
  it('날짜 역전 및 빈 값 차단, 같은 날 허용',()=>{expect(validDates('2026-09-08','2026-09-07')).toBe(false);expect(validDates('','')).toBe(false);expect(validDates('2026-09-08','2026-09-08')).toBe(true)})
  it('신청 제한 원인 표시',()=>{expect(requestLabel('ACTIVE_ASSIGNMENT')).toBe('이미 사용 중');expect(requestLabel('PENDING_REQUEST')).toBe('승인 대기 중');expect(requestLabel('INACTIVE')).toBe('신청 중지');expect(requestLabel(null)).toBe('사용 신청')})
  it('단가 소수점 보존',()=>expect(money('19.50')).toBe('$19.50'))
})
