from inbox_api.app.health import health_payload
from inbox_api.app.index import index_records
from inbox_api.app.main import app
from inbox_api.app.serialize import serialize_records
from inbox_api.app.store import RecordStore
from inbox_api.workloads.ingest_bulk import generate_records


def test_health():
    assert health_payload() == {"status": "ok"}


def test_serialize_and_index():
    store = RecordStore()
    serialized = serialize_records(generate_records(20))
    assert len(serialized) == 20
    assert all("_digest" in row for row in serialized)
    stats = index_records(serialized, store=store)
    assert stats["indexed"] == 20


def test_routes():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/health" in paths
    assert "/ingest/serialize" in paths
    assert "/ingest/index" in paths
