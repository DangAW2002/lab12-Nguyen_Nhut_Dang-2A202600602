"""Stateless Rate Limiter using Redis (with in-memory fallback)"""
import time
from collections import defaultdict, deque
from fastapi import HTTPException
from app.config import settings

class RedisRateLimiter:
    def __init__(self, r_conn=None):
        self.r = r_conn
        self.limit = settings.rate_limit_per_minute
        self.window = 60
        # In-memory fallback
        self._windows = defaultdict(deque)

    def check(self, key: str):
        now = time.time()
        if self.r:
            # Redis implementation: sliding window using sorted sets (zset)
            redis_key = f"rate:{key}"
            pipe = self.r.pipeline()
            # Remove old elements outside the window
            pipe.zremrangebyscore(redis_key, 0, now - self.window)
            # Add current request timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Get count of requests in the window
            pipe.zcard(redis_key)
            # Set TTL on the key to clean up inactive users
            pipe.expire(redis_key, self.window + 5)
            # Execute
            _, _, count, _ = pipe.execute()

            if count > self.limit:
                # Get the oldest timestamp in zset to calculate retry after
                oldest = self.r.zrange(redis_key, 0, 0, withscores=True)
                retry_after = 60
                if oldest:
                    retry_after = int(oldest[0][1] + self.window - now) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {self.limit} req/min. Try again in {max(1, retry_after)} seconds.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )
        else:
            # In-memory fallback implementation
            win = self._windows[key]
            while win and win[0] < now - self.window:
                win.popleft()
            if len(win) >= self.limit:
                oldest = win[0]
                retry_after = int(oldest + self.window - now) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {self.limit} req/min. Try again in {max(1, retry_after)} seconds.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )
            win.append(now)
