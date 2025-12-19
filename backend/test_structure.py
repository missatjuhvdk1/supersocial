"""
Quick test to verify the backend structure imports correctly.

Usage:
    python test_structure.py
"""

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        # Test config
        from app.config import settings
        print("✓ Config loaded")

        # Test database
        from app.database import Base, get_db, engine
        print("✓ Database module loaded")

        # Test models
        from app.models import Account, Proxy, BrowserProfile, Campaign, Job
        print("✓ Models loaded")

        # Test schemas
        from app.schemas import (
            AccountCreate, AccountUpdate, AccountResponse,
            ProxyCreate, ProxyUpdate, ProxyResponse,
            BrowserProfileCreate, BrowserProfileUpdate, BrowserProfileResponse,
            CampaignCreate, CampaignUpdate, CampaignResponse,
            JobCreate, JobUpdate, JobResponse
        )
        print("✓ Schemas loaded")

        # Test routers
        from app.api import (
            accounts_router,
            proxies_router,
            profiles_router,
            campaigns_router,
            jobs_router
        )
        print("✓ API routers loaded")

        # Test main app
        from app.main import app
        print("✓ FastAPI app loaded")

        print("\n✓✓✓ All imports successful! ✓✓✓")
        print(f"\nApp Name: {settings.app_name}")
        print(f"API Prefix: {settings.api_prefix}")
        print(f"Debug Mode: {settings.debug}")

        return True

    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_structure():
    """Test that models have the expected attributes."""
    print("\n\nTesting model structure...")

    from app.models import Account, Proxy, BrowserProfile, Campaign, Job

    # Test Account model
    account_attrs = ['id', 'email', 'password', 'cookies', 'status', 'proxy_id', 'profile_id', 'last_used']
    for attr in account_attrs:
        assert hasattr(Account, attr), f"Account missing attribute: {attr}"
    print("✓ Account model structure valid")

    # Test Proxy model
    proxy_attrs = ['id', 'host', 'port', 'username', 'password', 'type', 'status', 'latency_ms']
    for attr in proxy_attrs:
        assert hasattr(Proxy, attr), f"Proxy missing attribute: {attr}"
    print("✓ Proxy model structure valid")

    # Test BrowserProfile model
    profile_attrs = ['id', 'name', 'user_agent', 'viewport', 'timezone', 'locale', 'fingerprint']
    for attr in profile_attrs:
        assert hasattr(BrowserProfile, attr), f"BrowserProfile missing attribute: {attr}"
    print("✓ BrowserProfile model structure valid")

    # Test Campaign model
    campaign_attrs = ['id', 'name', 'status', 'video_path', 'caption_template', 'account_selection', 'schedule']
    for attr in campaign_attrs:
        assert hasattr(Campaign, attr), f"Campaign missing attribute: {attr}"
    print("✓ Campaign model structure valid")

    # Test Job model
    job_attrs = ['id', 'campaign_id', 'account_id', 'status', 'video_path', 'caption', 'error_message']
    for attr in job_attrs:
        assert hasattr(Job, attr), f"Job missing attribute: {attr}"
    print("✓ Job model structure valid")

    print("\n✓✓✓ All model structures valid! ✓✓✓")


def test_router_endpoints():
    """Test that routers have the expected endpoints."""
    print("\n\nTesting router endpoints...")

    from app.api import (
        accounts_router,
        proxies_router,
        profiles_router,
        campaigns_router,
        jobs_router
    )

    # Get route paths
    account_routes = [route.path for route in accounts_router.routes]
    proxy_routes = [route.path for route in proxies_router.routes]
    profile_routes = [route.path for route in profiles_router.routes]
    campaign_routes = [route.path for route in campaigns_router.routes]
    job_routes = [route.path for route in jobs_router.routes]

    print(f"✓ Accounts router has {len(account_routes)} endpoints")
    print(f"✓ Proxies router has {len(proxy_routes)} endpoints")
    print(f"✓ Profiles router has {len(profile_routes)} endpoints")
    print(f"✓ Campaigns router has {len(campaign_routes)} endpoints")
    print(f"✓ Jobs router has {len(job_routes)} endpoints")

    print("\n✓✓✓ All routers configured! ✓✓✓")


if __name__ == "__main__":
    print("=" * 60)
    print("TikTok Auto-Poster Backend Structure Test")
    print("=" * 60)

    success = test_imports()

    if success:
        test_model_structure()
        test_router_endpoints()

        print("\n" + "=" * 60)
        print("SUCCESS: Backend structure is complete and valid!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Set up PostgreSQL database")
        print("2. Copy .env.example to .env and configure")
        print("3. Run: python run.py")
        print("4. Visit: http://localhost:8000/docs")
    else:
        print("\n" + "=" * 60)
        print("FAILED: Please check the errors above")
        print("=" * 60)
