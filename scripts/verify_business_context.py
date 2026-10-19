"""Exercise an explicitly enabled local lab and print only status/trace IDs."""
import json
import time
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8081'


def request(path, data=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data else None,
                                 headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=20)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, dict(response.headers), response.read()


def main():
    status, _, body = request('/api/csi-lab')
    assert status == 200 and json.loads(body)['enabled'], 'Local CSI lab must be enabled'
    status, _, body = request('/api/departments')
    assert status == 200
    department = json.loads(body)[0]['id']
    suffix = str(time.time_ns())
    payload = dict(employee_no='CSI-CONTEXT-' + suffix, name='테스트 업무맥락',
                   department_id=department, job_title='테스트 개발자',
                   email='csi.context.' + suffix + '@example.com', username='csi_ctx_' + suffix,
                   password='Demo-Only-2026!', password_confirm='Demo-Only-2026!',
                   phone_number='010-0000-0000', profile_image=None)
    # Creates one synthetic account in the isolated lab; never print the response/user data.
    for scenario, data, expected in [('accepted', payload, 201), ('duplicate', payload, 409),
                                     ('invalid_phone', dict(payload, phone_number='invalid'), 422)]:
        status, headers, _ = request('/api/auth/signup', data)
        trace = next((v for k, v in headers.items() if k.lower() == 'x-trace-id'), None)
        assert status == expected and trace, f'{scenario} failed: HTTP {status}'
        print(json.dumps({'scenario': scenario, 'httpStatus': status, 'traceId': trace}), flush=True)


if __name__ == '__main__':
    main()
