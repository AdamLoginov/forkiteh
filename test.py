import pytest
from httpx import AsyncClient

from main import app, TronAccount, SessionLocal

@pytest.mark.asyncio
async def test_post_address_integration(monkeypatch):
    def mock_getBalance(address_hex):
        return 123.456

    def mock_getResources(address_hex):
        return 3000, 10000

    monkeypatch.setattr("main.getBalance", mock_getBalance)
    monkeypatch.setattr("main.getResources", mock_getResources)

    test_data = {
        "address": "41a614f803b6fd780986a42c78ec9c7f77e6ded13c"
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/post-address/", json=test_data)

    assert response.status_code == 200
    data = response.json()
    assert data["address"] == test_data["address"]
    assert data["balance"] == 123.456
    assert data["bandwidth"] == 3000
    assert data["energy"] == 10000

@pytest.mark.asyncio
async def test_insert_to_db():
    async with SessionLocal() as session:
        test_account = TronAccount(
            address="0x1234567890abcdef",
            balance=1.23,
            bandwidth=4567,
            energy=7890
        )
        session.add(test_account)
        await session.commit()

        result = await session.get(TronAccount, test_account.id)
        assert result is not None
        assert result.address == "0x1234567890abcdef"
        assert result.balance == 1.23
        assert result.bandwidth == 4567
        assert result.energy == 7890
