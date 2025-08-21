"""
Caching layer for tool results and agent responses
"""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any


class CacheManager:
    """Simple file-based cache with TTL support"""

    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # TTL in seconds for different cache types
        self.ttl_config = {
            "tool_research": 3600,      # 1 hour for research
            "tool_code": 300,            # 5 minutes for code generation
            "tool_data": 1800,           # 30 minutes for data operations
            "agent_response": 600,       # 10 minutes for agent responses
            "default": 900               # 15 minutes default
        }

    def _get_cache_key(self, category: str, data: dict) -> str:
        """Generate a unique cache key based on input data"""
        # Sort dict for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        hash_obj = hashlib.sha256(data_str.encode())
        return f"{category}_{hash_obj.hexdigest()[:16]}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key"""
        return self.cache_dir / f"{cache_key}.cache"

    def get(self, category: str, data: dict) -> Any | None:
        """Retrieve cached value if it exists and is not expired"""
        cache_key = self._get_cache_key(category, data)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)

            # Check TTL
            ttl = self.ttl_config.get(category, self.ttl_config["default"])
            if time.time() - cached_data["timestamp"] > ttl:
                # Cache expired
                cache_path.unlink()
                return None

            return cached_data["value"]

        except Exception:
            # Corrupted cache file
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, category: str, data: dict, value: Any) -> None:
        """Store a value in the cache"""
        cache_key = self._get_cache_key(category, data)
        cache_path = self._get_cache_path(cache_key)

        cache_data = {
            "timestamp": time.time(),
            "category": category,
            "input": data,
            "value": value
        }

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception:
            # Failed to cache, not critical
            pass

    def clear(self, category: str | None = None) -> int:
        """Clear cache entries, optionally filtered by category"""
        count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            if category and not cache_file.name.startswith(f"{category}_"):
                continue
            cache_file.unlink()
            count += 1
        return count

    def get_stats(self) -> dict:
        """Get cache statistics"""
        stats = {
            "total_entries": 0,
            "total_size_bytes": 0,
            "by_category": {}
        }

        for cache_file in self.cache_dir.glob("*.cache"):
            stats["total_entries"] += 1
            stats["total_size_bytes"] += cache_file.stat().st_size

            # Extract category from filename
            category = cache_file.name.split("_")[0]
            if category not in stats["by_category"]:
                stats["by_category"][category] = {"count": 0, "size": 0}
            stats["by_category"][category]["count"] += 1
            stats["by_category"][category]["size"] += cache_file.stat().st_size

        return stats


class RedisCache:
    """Redis-based cache for production use"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        try:
            import redis
            self.client = redis.from_url(redis_url)
            self.enabled = True
        except ImportError:
            self.enabled = False
            self.fallback = CacheManager()

    def get(self, category: str, data: dict) -> Any | None:
        """Get from Redis or fallback to file cache"""
        if not self.enabled:
            return self.fallback.get(category, data)

        cache_key = f"plugah:{category}:{hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]}"

        try:
            value = self.client.get(cache_key)
            if value:
                return pickle.loads(value)
        except Exception:
            pass

        return None

    def set(self, category: str, data: dict, value: Any, ttl: int | None = None) -> None:
        """Set in Redis or fallback to file cache"""
        if not self.enabled:
            return self.fallback.set(category, data, value)

        cache_key = f"plugah:{category}:{hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]}"

        if ttl is None:
            ttl = {
                "tool_research": 3600,
                "tool_code": 300,
                "tool_data": 1800,
                "agent_response": 600
            }.get(category, 900)

        try:
            self.client.setex(cache_key, ttl, pickle.dumps(value))
        except Exception:
            pass


# Global cache instance
_cache_instance: CacheManager | None = None


def get_cache() -> CacheManager:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager()
    return _cache_instance
