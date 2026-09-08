"""Run the unchanged application against an isolated documentation demo database."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
os.environ['DATABASE_URL'] = 'sqlite:///' + (HERE / 'capture.db').as_posix()
os.environ['JWT_SECRET'] = 'documentation-only-isolated-demo-secret-20260908'
os.environ['MASTER_PASSWORD'] = 'CaptureMaster2026!'
os.environ['DEMO_PASSWORD'] = 'CaptureEmployee2026!'
from app.db.session import engine
from app.models.entities import Base
from app.db.seed import seed

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    seed()
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8011)
