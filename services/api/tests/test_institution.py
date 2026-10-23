import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.anyio
async def test_institution_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Profile
        res = await client.get("/api/v1/institution/profile")
        assert res.status_code == 200
        assert res.json()["institution_id"] == "INST001"

        # Users
        res = await client.get("/api/v1/institution/users")
        assert res.status_code == 200
        assert len(res.json()) >= 3

        # Upload batches
        res = await client.get("/api/v1/institution/upload-batches")
        assert res.status_code == 200
        assert len(res.json()) >= 3

        # Notifications
        res = await client.get("/api/v1/institution/notifications")
        assert res.status_code == 200
        assert res.json()["validation_anomalies"] is True

        # Security
        res = await client.get("/api/v1/institution/security")
        assert res.status_code == 200
        assert res.json()["mfa_enforced"] is True
