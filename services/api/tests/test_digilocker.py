"""Tests for DigiLocker and API Setu integration (SPEC 9.4)."""

import pytest
import httpx
from app.config import Settings
from app.integrations.digilocker import (
    ApiSetuSandboxDigiLocker,
    DigiLockerError,
    MockDigiLocker,
)
from app.main import app


def test_mock_digilocker_consent_and_verify():
    settings = Settings()
    mock = MockDigiLocker(settings)
    mock.reset()

    # Verify APAAR direct call
    doc = mock.verify_apaar(apaar_id="123412341234", name="Rahul Sharma")
    assert doc.doc_type == "abcid"
    assert doc.issuer == "MOCK-DIGILOCKER"
    assert doc.fields["apaar_id"] == "123412341234"
    assert doc.fields["status"] == "ACTIVE"
    assert doc.sha256 is not None

    # Consent workflow
    req = mock.start_consent(student_reference="123412341234", purpose="APAAR Verification")
    assert req.request_id
    assert "consent" in req.authorization_url

    with pytest.raises(DigiLockerError):
        # Fetching before granting raises error
        mock.fetch_document(request_id=req.request_id)

    mock.grant(req.request_id, {"apaar_id": "123412341234", "name": "Rahul Sharma"})
    doc2 = mock.fetch_document(request_id=req.request_id)
    assert doc2.fields["name"] == "Rahul Sharma"


def test_apisetu_sandbox_digilocker_contract():
    settings = Settings(
        digilocker_impl="apisetu_sandbox",
        digilocker_client_id="in.gov.sandbox",
        digilocker_api_key="demokey123456ABCD789",
        digilocker_base_url="https://sandbox.api-setu.in",
    )

    recorded_requests = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        recorded_requests.append(request)
        assert request.headers["x-apisetu-apikey"] == "demokey123456ABCD789"
        assert request.headers["x-apisetu-clientid"] == "in.gov.sandbox"
        assert request.headers["content-type"] == "application/json"
        assert "/certificate/v3/abc/abcid" in str(request.url)
        return httpx.Response(200, content=b"%PDF-1.4 demo certificate")

    transport = httpx.MockTransport(mock_handler)
    client = httpx.Client(transport=transport)

    adapter = ApiSetuSandboxDigiLocker(settings, client=client)
    doc = adapter.verify_apaar(
        apaar_id="987654321012",
        name="Demo User",
        dob="31-12-1980",
        gender="Male",
        admission_year="2021",
    )

    assert len(recorded_requests) == 1
    assert doc.issuer == "APISETU-DIGILOCKER"
    assert doc.fields["apaar_id"] == "987654321012"
    assert doc.fields["status"] == "ACTIVE"
    assert doc.sha256 is not None


@pytest.mark.anyio
async def test_verify_apaar_endpoint_success():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/institution/students/verify-apaar",
            json={"apaar_id": "123412341234", "name": "Aarav Sharma"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["exists"] is True
        assert data["status"] == "ACTIVE"
        assert data["masked_name"] == "A**** S*****"
        assert data["sha256"] is not None


@pytest.mark.anyio
async def test_verify_apaar_endpoint_invalid_format():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/v1/institution/students/verify-apaar",
            json={"apaar_id": "123", "name": "Invalid"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert data["status"] == "INVALID_FORMAT"
