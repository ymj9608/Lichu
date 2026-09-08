from pathlib import Path
from typing import get_type_hints
import yaml
from fastapi.routing import APIRoute
from pydantic import TypeAdapter
from app.main import app
from app.api.routes import router
from app.models.entities import Base


def test_submission_matches_routes_and_response_examples():
    doc = yaml.safe_load((Path(__file__).resolve().parents[2] / 'docs/CLASS_NAME_Lichu-API.yml').read_text())
    assert 'securitySchemes' not in doc['components']
    actual = {(route.path, method.lower()) for route in router.routes if isinstance(route, APIRoute) for method in route.methods}
    submitted = {(path, method) for path, operations in doc['paths'].items() for method in operations}
    assert submitted == actual
    for route in router.routes:
        if not isinstance(route, APIRoute):
            continue
        for method in route.methods:
            operation = doc['paths'][route.path][method.lower()]
            assert 'security' not in operation
            sample = operation['responses'][str(route.status_code or 200)]['content']['application/json']['example']
            TypeAdapter(route.response_model).validate_python(sample)
            if route.body_field:
                sample = operation['requestBody']['content']['application/json']['example']
                TypeAdapter(get_type_hints(route.endpoint)['body']).validate_python(sample)


def test_no_duplicate_usage_column_and_assignment_request_unique():
    assert 'used_seats' not in Base.metadata.tables['licenses'].columns
    assert Base.metadata.tables['license_assignments'].columns['request_id'].unique
