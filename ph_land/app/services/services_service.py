from __future__ import annotations

from typing import List

from app.dao.service_dao import ServiceDAO
from app.domain.service import Service

_dao = ServiceDAO()


def load_services() -> List[Service]:
    return _dao.list_services()


def save_services(services: List[Service] | List[dict]) -> None:
    for service in services:
        if isinstance(service, Service):
            _dao.save_service(service)
        else:
            _dao.save_service(Service(**service))


def append_service(service: Service) -> None:
    _dao.save_service(service)


def get_service(service_id: str) -> Service | None:
    return _dao.get_service_by_id(service_id)


def update_service(service: Service) -> None:
    _dao.update_service(service)
