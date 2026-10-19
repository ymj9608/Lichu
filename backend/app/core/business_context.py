"""Value-free signup observations. Declared purpose never means policy approval."""
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
from uuid import uuid4
from sqlalchemy import event

trace_id = ContextVar('business_context_trace', default=None)
logger = logging.getLogger('uvicorn.error')
STAGES = {'REQUEST_STARTED', 'INPUT_ACCEPTED', 'DB_COMMITTED', 'DB_ROLLED_BACK',
          'HTTP_FINISHED', 'REQUEST_FAILED'}


def record(stage, *, trace, lab_mode, status=None, fields=None):
    if stage not in STAGES:
        raise ValueError('Unsupported business context event')
    row = {
        'eventType': 'BUSINESS_CONTEXT', 'schemaVersion': 1,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'traceId': trace, 'operation': 'EMPLOYEE_SIGNUP', 'stage': stage,
        'mode': 'CSI_LAB' if lab_mode else 'STANDARD',
        'businessProcess': 'INTERNAL_LICENSE_REQUEST_AND_APPROVAL',
        'purposeSource': 'APPLICATION_DECLARATION',
        'approvalStatus': 'NOT_CHECKED', 'retentionStatus': 'NOT_CONFIGURED',
        'policyCompliance': 'NOT_ASSESSED',
    }
    if status is not None:
        row['httpStatus'] = int(status)
    if fields is not None:
        row['fieldContext'] = fields
    logger.info('BUSINESS_CONTEXT %s', json.dumps(row, ensure_ascii=False, separators=(',', ':')))


def observe_signup(session, *, lab_mode, phone_present):
    """Register before writes; emit successful persistence only after DB commit."""
    trace = trace_id.get() or str(uuid4())
    fields = [
        {'field': 'User.name', 'declaredPurpose': 'LICENSE_APPLICANT_DISPLAY',
         'usageReference': 'frontend/src/views/RequestsView.vue',
         'storageTarget': 'users.name', 'labOnly': False},
    ]
    if lab_mode and phone_present:
        fields.append({'field': 'CsiSignupProfile.phone_number',
                       'declaredPurpose': 'SYNTHETIC_SECURITY_DIAGNOSTIC_EXERCISE',
                       'storageTarget': 'csi_signup_profiles.phone_number', 'labOnly': True,
                       'syntheticValidation': 'PASSED'})
    record('INPUT_ACCEPTED', trace=trace, lab_mode=lab_mode, fields=fields)
    # Callbacks capture only fixed metadata and a random request trace, never the payload.
    def committed(_):
        record('DB_COMMITTED', trace=trace, lab_mode=lab_mode, fields=fields)
    def rolled_back(_):
        record('DB_ROLLED_BACK', trace=trace, lab_mode=lab_mode, fields=fields)
    event.listen(session, 'after_commit', committed, once=True)
    event.listen(session, 'after_rollback', rolled_back, once=True)
