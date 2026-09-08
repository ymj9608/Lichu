export type Role = 'USER' | 'MASTER'
export type RequestStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELED'
export interface Department { id:number; name:string }
export interface User {id:number; employee_no:string; name:string; department_id:number; department:Department; job_title:string; email:string; username:string; role:Role; profile_image:string|null; created_at:string; updated_at:string}
export interface LicenseInput {name:string; vendor:string; plan_name:string; category:string; description:string; total_seats:number; unit_price:string; billing_cycle:'MONTHLY'|'YEARLY'; status:'ACTIVE'|'INACTIVE'}
export interface License extends LicenseInput {id:number; used_seats:number; available_seats:number; utilization:number; monthly_unit_price:string; request_block:'ACTIVE_ASSIGNMENT'|'PENDING_REQUEST'|'INACTIVE'|null; created_at:string; updated_at:string}
export interface LicenseRequest {id:number; user_id:number; license_id:number; user:User; license:License; reason:string; start_date:string; end_date:string; status:RequestStatus; decision_reason:string|null; processed_by:number|null; processor:User|null; processed_at:string|null; canceled_at:string|null; created_at:string}
export interface Assignment {id:number; user_id:number; license_id:number; request_id:number|null; user:User; license:License; reason:string|null; end_date:string|null; status:'ACTIVE'|'RETURNED'|'REVOKED'; assigned_by:number; assigned_at:string; valid_from:string; valid_until:string; ended_by:number|null; ended_at:string|null; end_reason:string|null}
export interface Dashboard {total_seats:number; used_seats:number; available_seats:number; pending_requests:number; licenses:License[]; high_utilization:License[]; recent_requests:LicenseRequest[]}
export interface ApiError {code:string; message:string; fields:Record<string,string>}
