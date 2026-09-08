export const date = (value:string|null|undefined) => value ? new Intl.DateTimeFormat('ko-KR',{year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(value)) : '—'
export const money = (value:string|number) => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(Number(value))
export function validDates(start:string,end:string){return Boolean(start && end && start <= end)}
export const requestLabel = (block:string|null) => block === 'ACTIVE_ASSIGNMENT' ? '이미 사용 중' : block === 'PENDING_REQUEST' ? '승인 대기 중' : block === 'INACTIVE' ? '신청 중지' : '사용 신청'
