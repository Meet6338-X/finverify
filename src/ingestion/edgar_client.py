import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter enforcing a maximum number of requests per second."""
    
    def __init__(self, rate: int = 10, per: float = 1.0):
        self.rate = rate
        self.per = per
        self.tokens = float(rate)
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait if necessary before allowing a request."""
        async with self.lock:
            while self.tokens < 1.0:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(float(self.rate), self.tokens + elapsed * (self.rate / self.per))
                self.last_update = now
                if self.tokens < 1.0:
                    await asyncio.sleep(0.1)
            self.tokens -= 1.0


class EdgarClient:
    """Client for SEC EDGAR API with rate limiting and Redis caching."""
    
    def __init__(self, user_agent: str, redis_host: str = 'redis', redis_port: int = 6379, cache_ttl: int = 86400):
        self.user_agent = user_agent
        self.client = httpx.AsyncClient(headers={"User-Agent": self.user_agent})
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.cache_ttl = cache_ttl
        self.rate_limiter = RateLimiter(rate=10, per=1.0)
        self.base_url = "https://data.sec.gov/api/xbrl/companyfacts"

    async def get_company_facts(self, cik: str) -> dict:
        """Fetch company facts from SEC EDGAR API, caching the result in Redis."""
        cik_padded = str(cik).zfill(10)
        cache_key = f"edgar:companyfacts:{cik_padded}"
        
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)

        url = f"{self.base_url}/CIK{cik_padded}.json"
        
        await self.rate_limiter.acquire()
        response = await self.client.get(url)
        response.raise_for_status()
        
        data = response.json()
        await self.redis.setex(cache_key, self.cache_ttl, json.dumps(data))
        return data

    async def get_xbrl_value(self, cik: str, taxonomy: str, tag: str, period: str, form_type: str) -> Optional[float]:
        """Look up a specific XBRL value from company facts."""
        try:
            facts = await self.get_company_facts(cik)
            concept_facts = facts.get("facts", {}).get(taxonomy, {}).get(tag, {}).get("units", {})
            
            # Find facts across all units
            all_unit_facts = []
            for unit_name, unit_facts in concept_facts.items():
                all_unit_facts.extend(unit_facts)
                
            # Filter by form type and period
            for fact in all_unit_facts:
                if fact.get("form") == form_type:
                    # Basic period matching logic (could be more sophisticated based on FY/FP)
                    fact_frame = fact.get("frame", "")
                    if period in fact_frame or (fact.get("fy") == period and not fact.get("fp")):
                        return float(fact.get("val", 0.0))
            return None
        except Exception as e:
            logger.error(f"Error extracting XBRL value: {e}")
            return None

    def _map_input_to_xbrl_tags(self, input_name: str) -> List[Tuple[str, str]]:
        """Map common financial input names to XBRL taxonomy:tag pairs."""
        input_name = input_name.lower().strip()
        mapping = {
            "revenue": [("us-gaap", "Revenues"), ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax")],
            "cost_of_goods_sold": [("us-gaap", "CostOfGoodsSold"), ("us-gaap", "CostOfGoodsSoldAndOperatingExpenses")],
            "net_income": [("us-gaap", "NetIncomeLoss")],
            "total_assets": [("us-gaap", "Assets")],
            "total_liabilities": [("us-gaap", "Liabilities")],
            "stockholders_equity": [("us-gaap", "StockholdersEquity")],
            "operating_income": [("us-gaap", "OperatingIncomeLoss")],
            "gross_profit": [("us-gaap", "GrossProfit")],
            "eps_basic": [("us-gaap", "EarningsPerShareBasic")],
            "eps_diluted": [("us-gaap", "EarningsPerShareDiluted")],
            "total_debt": [("us-gaap", "DebtAndCapitalLeaseObligations"), ("us-gaap", "LongTermDebt")],
            "current_assets": [("us-gaap", "AssetsCurrent")],
            "current_liabilities": [("us-gaap", "LiabilitiesCurrent")],
            "interest_expense": [("us-gaap", "InterestExpense")],
            "ebit": [("us-gaap", "OperatingIncomeLoss")],  # Approximation if EBIT tag not present
            "shares_outstanding": [("us-gaap", "CommonStockSharesOutstanding")],
            "shares_outstanding_diluted": [("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding")]
        }
        return mapping.get(input_name, [])

    async def resolve_claim_sources(self, cik: str, period: str, form_type: str, inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve claim sources by looking up EDGAR XBRL values for each input."""
        resolved_inputs = []
        
        for input_item in inputs:
            input_name = input_item.get("name", "")
            tags = self._map_input_to_xbrl_tags(input_name)
            
            resolved_value = None
            resolved_uri = None
            source_not_found = True
            
            for taxonomy, tag in tags:
                val = await self.get_xbrl_value(cik, taxonomy, tag, period, form_type)
                if val is not None:
                    resolved_value = val
                    resolved_uri = f"edgar://CIK{cik}/{form_type}/{period}#{taxonomy}:{tag}"
                    source_not_found = False
                    break
            
            input_item["resolved_value"] = resolved_value
            input_item["source_uri"] = resolved_uri
            input_item["source_not_found"] = source_not_found
            resolved_inputs.append(input_item)
            
        return resolved_inputs

    async def close(self) -> None:
        """Close HTTP client and Redis connection."""
        await self.client.aclose()
        await self.redis.aclose()
