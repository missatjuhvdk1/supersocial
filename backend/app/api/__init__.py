from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.proxies import router as proxies_router
from app.api.profiles import router as profiles_router
from app.api.campaigns import router as campaigns_router
from app.api.jobs import router as jobs_router
from app.api.stats import router as stats_router

__all__ = [
    "auth_router",
    "accounts_router",
    "proxies_router",
    "profiles_router",
    "campaigns_router",
    "jobs_router",
    "stats_router"
]
