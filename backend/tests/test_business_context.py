import json
from uuid import UUID
import pytest
from sqlalchemy import event
from app.core.config import settings
from app.schemas.dto import Signup
from app.services.hub import signup
from test_csi_lab import synthetic


def observations(caplog):
    return [json.loads(r.getMessage().split('BUSINESS_CONTEXT ', 1)[1])
            for r in caplog.records if r.getMessage().startswith('BUSINESS_CONTEXT ')]


@pytest.mark.parametrize('lab_mode', [True, False])
def test_signup_context_commit_trace_and_no_values(context, monkeypatch, caplog, lab_mode):
    monkeypatch.setattr(settings, 'csi_lab_mode', lab_mode)
    data = synthetic()
    if not lab_mode:
        data.pop('phone_number')
    with caplog.at_level('INFO', logger='uvicorn.error'):
        response = context[0].post('/api/auth/signup', json=data,
                                   headers={'X-Trace-ID': 'client-controlled-trace'})
    assert response.status_code == 201
    trace = response.headers['X-Trace-ID']
    UUID(trace)
    assert trace != 'client-controlled-trace'
    rows = observations(caplog)
    assert {r['traceId'] for r in rows} == {trace}
    committed = [r for r in rows if r['stage'] == 'DB_COMMITTED']
    assert len(committed) == 1
    row = committed[0]
    assert row['approvalStatus'] == 'NOT_CHECKED'
    assert row['retentionStatus'] == 'NOT_CONFIGURED'
    assert row['purposeSource'] == 'APPLICATION_DECLARATION'
    assert row['fieldContext'][0]['labOnly'] is False
    assert len(row['fieldContext']) == (2 if lab_mode else 1)
    if lab_mode:
        assert row['fieldContext'][1]['syntheticValidation'] == 'PASSED'
    for key in ['name', 'employee_no', 'email', 'username', 'password', 'phone_number']:
        if key in data:
            assert data[key] not in caplog.text


def test_rejected_input_never_logs_commit_or_payload(context, monkeypatch, caplog):
    monkeypatch.setattr(settings, 'csi_lab_mode', False)
    with caplog.at_level('INFO', logger='uvicorn.error'):
        response = context[0].post('/api/auth/signup', json=synthetic())
    assert response.status_code == 422
    rows = observations(caplog)
    assert [r['stage'] for r in rows] == ['REQUEST_STARTED', 'HTTP_FINISHED']
    assert rows[-1]['httpStatus'] == 422
    assert '010-0000-0000' not in caplog.text


def test_commit_failure_logs_rollback_not_success(context, monkeypatch, caplog):
    monkeypatch.setattr(settings, 'csi_lab_mode', True)
    with context[1]() as db:
        def fail_commit(_):
            raise RuntimeError('simulated commit failure')
        event.listen(db, 'before_commit', fail_commit, once=True)
        with caplog.at_level('INFO', logger='uvicorn.error'):
            signup(db, Signup(**synthetic()))
            with pytest.raises(RuntimeError, match='simulated commit failure'):
                db.commit()
            db.rollback()
    rows = observations(caplog)
    assert [r['stage'] for r in rows] == ['INPUT_ACCEPTED', 'DB_ROLLED_BACK']
    assert 'Demo-Only-2026!' not in caplog.text
