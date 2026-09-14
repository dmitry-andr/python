from fastapi.testclient import TestClient

import app.services.services_service as services_service
from app.dao.service_dao import ServiceDAO
from app.domain.service import Service
from app.main import app


def test_service_dao_round_trip(tmp_path):
    db_path = tmp_path / "services.db"
    dao = ServiceDAO(db_path=db_path)

    service = Service(
        business_id="biz-1",
        service_type="Cleaning",
        service_sub_type="Deep cleaning",
        name="Spring Refresh",
        description="A full cleaning package.",
    )

    dao.save_service(service)
    saved = dao.list_services()

    assert len(saved) == 1
    assert saved[0].id == service.id
    assert saved[0].name == "Spring Refresh"
    assert saved[0].description == "A full cleaning package."


def test_service_dao_update_service(tmp_path):
    db_path = tmp_path / "services.db"
    dao = ServiceDAO(db_path=db_path)

    service = Service(
        business_id="biz-1",
        service_type="Cleaning",
        service_sub_type="Deep cleaning",
        name="Spring Refresh",
        description="A full cleaning package.",
    )
    dao.save_service(service)

    updated = Service(
        id=service.id,
        business_id="biz-1",
        service_type="Cleaning",
        service_sub_type="Deep cleaning",
        name="Spring Refresh Deluxe",
        description="Updated description.",
    )
    dao.update_service(updated)

    saved = dao.get_service_by_id(service.id)
    assert saved is not None
    assert saved.name == "Spring Refresh Deluxe"
    assert saved.description == "Updated description."


def test_update_service_form_updates_existing_service(tmp_path, monkeypatch):
    temp_db = tmp_path / "services.db"
    monkeypatch.setattr(services_service, "_dao", ServiceDAO(db_path=temp_db))

    client = TestClient(app)

    create_response = client.post(
        "/web-office/create-edit-service",
        data={
            "business_id": "biz-1",
            "service_type": "Cleaning",
            "service_sub_type": "Deep cleaning",
            "name": "Spring Refresh",
            "description": "Initial description",
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303

    service = next(iter(services_service.load_services()))

    response = client.post(
        "/web-office/create-edit-service",
        data={
            "id": service.id,
            "business_id": "biz-1",
            "service_type": "Cleaning",
            "service_sub_type": "Deep cleaning",
            "name": "Spring Refresh Deluxe",
            "description": "Updated description",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/web-office/web-office.html"

    updated_service = next(s for s in services_service.load_services() if s.id == service.id)
    assert updated_service.name == "Spring Refresh Deluxe"
    assert updated_service.description == "Updated description"
