from functools import lru_cache

from app.core.services import ApplicationServices


@lru_cache
def get_app_services() -> ApplicationServices:
    return ApplicationServices()
