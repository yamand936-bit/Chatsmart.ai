import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_auth_security_c1(client, mock_redis):
    # Attacker tries to inject a known business_id directly into the state parameter
    attacker_business_id = str(uuid.uuid4())
    mock_redis.get.return_value = None # state not found in redis
    
    attack_res = await client.get(
        "/api/auth/instagram/callback",
        params={"state": attacker_business_id, "access_token": "malicious_token"}
    )
    
    assert attack_res.status_code == 400
