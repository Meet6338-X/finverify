"""
Unit tests for SEC EDGAR client and rate limiter.
"""
import pytest
from src.ingestion.edgar_client import RateLimiter, EdgarClient


@pytest.mark.asyncio
async def test_rate_limiter():
    limiter = RateLimiter(rate=10, per=1.0)
    # Acquire 5 tokens quickly
    for _ in range(5):
        await limiter.acquire()


def test_edgar_tag_mapping():
    client = EdgarClient(user_agent="FinVerify-Test/1.0", redis_host="localhost")
    tags = client._map_input_to_xbrl_tags("revenue")
    assert len(tags) > 0
    assert ("us-gaap", "Revenues") in tags or ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax") in tags
