"""Generate isolated local lab credentials without changing the existing .env."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
target = root / '.env.csi'
if target.exists():
    print('Existing .env.csi preserved.')
else:
    values = {key: secrets.token_urlsafe(32) for key in (
        'CSI_LAB_DB_PASSWORD', 'CSI_LAB_JWT_SECRET', 'CSI_LAB_MASTER_PASSWORD', 'CSI_LAB_DEMO_PASSWORD')}
    with target.open('x') as stream:
        target.chmod(0o600)
        stream.write('\n'.join(f'{key}={value}' for key, value in values.items()) + '\n')
    print('Created .env.csi. Credentials are not printed; do not commit this file.')
