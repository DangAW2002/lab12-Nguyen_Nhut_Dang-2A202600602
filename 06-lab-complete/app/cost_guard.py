"""Stateless Cost Guard using Redis (with in-memory fallback)"""
import time
from fastapi import HTTPException
from app.config import settings

PRICE_PER_1K_INPUT_TOKENS = 0.00015   # GPT-4o-mini
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006   # GPT-4o-mini

class RedisCostGuard:
    def __init__(self, r_conn=None):
        self.r = r_conn
        self.budget = settings.daily_budget_usd
        # In-memory fallback
        self._memory_cost = 0.0
        self._reset_day = time.strftime("%Y-%m-%d")

    def _get_reset_if_needed(self):
        today = time.strftime("%Y-%m-%d")
        if today != self._reset_day:
            self._memory_cost = 0.0
            self._reset_day = today
        return today

    def check_budget(self, user_id: str):
        today = self._get_reset_if_needed()
        if self.r:
            key = f"cost:{user_id}:{today}"
            current_cost = float(self.r.get(key) or 0.0)
            if current_cost >= self.budget:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Daily budget exceeded",
                        "used_usd": current_cost,
                        "budget_usd": self.budget,
                        "resets_at": "midnight UTC",
                    }
                )
        else:
            if self._memory_cost >= self.budget:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "error": "Daily budget exceeded",
                        "used_usd": self._memory_cost,
                        "budget_usd": self.budget,
                        "resets_at": "midnight UTC",
                    }
                )

    def record_usage(self, user_id: str, input_tokens: int, output_tokens: int) -> float:
        today = self._get_reset_if_needed()
        cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS + (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
        
        if self.r:
            key = f"cost:{user_id}:{today}"
            pipe = self.r.pipeline()
            pipe.incrbyfloat(key, cost)
            pipe.expire(key, 86400 + 3600)  # 25 hours TTL
            res = pipe.execute()
            new_cost = float(res[0])
            return new_cost
        else:
            self._memory_cost += cost
            return self._memory_cost
