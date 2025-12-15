"""
State Store (Advanced) - Redis + PostgreSQL Persistence
Distributed state management with TTL, locks, and consistency guarantees
"""

import os
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid

import aioredis
import asyncpg

logger = logging.getLogger(__name__)


class ConsistencyLevel(Enum):
    """Consistency levels"""
    EVENTUAL = "eventual"  # Fast writes, eventual consistency
    STRONG = "strong"  # Write-through consistency
    CAUSAL = "causal"  # Causal consistency


@dataclass
class StateEntry:
    """Represents a state entry"""
    key: str
    value: Any
    version: int
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = {
            'key': self.key,
            'value': self.value,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'hash': self.hash,
        }
        return data
    
    def calculate_hash(self) -> str:
        """Calculate hash for integrity verification"""
        content = json.dumps({
            'key': self.key,
            'value': self.value,
            'version': self.version,
        }, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


class DistributedLock:
    """Distributed lock using Redis"""
    
    def __init__(self, key: str, redis: aioredis.Redis, ttl_seconds: int = 30):
        self.key = f"lock:{key}"
        self.redis = redis
        self.ttl_seconds = ttl_seconds
        self.token = str(uuid.uuid4())
        self.acquired = False
    
    async def __aenter__(self):
        """Acquire lock"""
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            # Try to set if not exists with TTL
            acquired = await self.redis.set(
                self.key,
                self.token,
                ex=self.ttl_seconds,
                nx=True  # Only if not exists
            )
            
            if acquired:
                self.acquired = True
                logger.debug(f"Lock acquired: {self.key}")
                return self
            
            # Wait before retry
            await asyncio.sleep(0.1)
            attempt += 1
        
        raise TimeoutError(f"Failed to acquire lock: {self.key}")
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release lock"""
        if self.acquired:
            # Only delete if token matches (prevent deleting other locks)
            current = await self.redis.get(self.key)
            if current and current.decode() == self.token:
                await self.redis.delete(self.key)
                self.acquired = False
                logger.debug(f"Lock released: {self.key}")


class StateStore:
    """Manages distributed state with Redis cache and PostgreSQL persistence"""
    
    def __init__(self, consistency: ConsistencyLevel = ConsistencyLevel.EVENTUAL):
        self.consistency = consistency
        self.redis: Optional[aioredis.Redis] = None
        self.postgres: Optional[asyncpg.Pool] = None
        self.cache_ttl_seconds = 3600  # 1 hour
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize connections"""
        try:
            # Redis connection
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis = await aioredis.from_url(redis_url)
            
            # PostgreSQL connection pool
            db_dsn = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/aineon')
            self.postgres = await asyncpg.create_pool(db_dsn, min_size=5, max_size=20)
            
            # Create tables
            await self._create_tables()
            
            self.initialized = True
            logger.info("State store initialized")
            return True
            
        except Exception as e:
            logger.error(f"State store initialization failed: {e}")
            return False
    
    async def _create_tables(self):
        """Create PostgreSQL tables if needed"""
        if not self.postgres:
            return
        
        async with self.postgres.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS state_entries (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    expires_at TIMESTAMPTZ,
                    hash TEXT,
                    INDEX idx_updated_at (updated_at)
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS state_history (
                    id BIGSERIAL PRIMARY KEY,
                    key TEXT NOT NULL,
                    old_value JSONB,
                    new_value JSONB NOT NULL,
                    version INTEGER NOT NULL,
                    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    changed_by TEXT,
                    INDEX idx_key (key),
                    INDEX idx_changed_at (changed_at)
                )
            ''')
        
        logger.info("State store tables created/verified")
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                  skip_history: bool = False) -> bool:
        """Set state value"""
        if not self.initialized:
            logger.error("State store not initialized")
            return False
        
        try:
            now = datetime.utcnow()
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
            
            # Create entry
            entry = StateEntry(
                key=key,
                value=value,
                version=1,
                created_at=now,
                updated_at=now,
                expires_at=expires_at
            )
            entry.hash = entry.calculate_hash()
            
            # Store in PostgreSQL
            async with self.postgres.acquire() as conn:
                # Get current version for history
                current = await conn.fetchval(
                    'SELECT version FROM state_entries WHERE key = $1',
                    key
                )
                new_version = (current or 0) + 1
                
                await conn.execute('''
                    INSERT INTO state_entries (key, value, version, updated_at, expires_at, hash)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (key) DO UPDATE SET
                        value = $2,
                        version = $3,
                        updated_at = $4,
                        expires_at = $5,
                        hash = $6
                ''', key, json.dumps(value), new_version, now, expires_at, entry.hash)
                
                # Record history
                if not skip_history:
                    await conn.execute('''
                        INSERT INTO state_history (key, new_value, version, changed_by)
                        VALUES ($1, $2, $3, 'system')
                    ''', key, json.dumps(value), new_version)
            
            # Cache in Redis
            if self.redis:
                cache_ttl = ttl_seconds or self.cache_ttl_seconds
                await self.redis.set(
                    f"state:{key}",
                    json.dumps(entry.to_dict()),
                    ex=cache_ttl
                )
            
            logger.debug(f"State set: {key} (v{new_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set state {key}: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get state value"""
        if not self.initialized:
            return None
        
        try:
            # Try cache first
            if self.redis:
                cached = await self.redis.get(f"state:{key}")
                if cached:
                    entry_dict = json.loads(cached)
                    return entry_dict['value']
            
            # Fall back to PostgreSQL
            async with self.postgres.acquire() as conn:
                value = await conn.fetchval(
                    'SELECT value FROM state_entries WHERE key = $1 AND (expires_at IS NULL OR expires_at > NOW())',
                    key
                )
                
                if value:
                    # Update cache
                    if self.redis:
                        await self.redis.set(
                            f"state:{key}",
                            json.dumps({'value': value}),
                            ex=self.cache_ttl_seconds
                        )
                    return value
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get state {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete state value"""
        if not self.initialized:
            return False
        
        try:
            # Delete from PostgreSQL
            async with self.postgres.acquire() as conn:
                await conn.execute('DELETE FROM state_entries WHERE key = $1', key)
            
            # Remove from cache
            if self.redis:
                await self.redis.delete(f"state:{key}")
            
            logger.debug(f"State deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete state {key}: {e}")
            return False
    
    async def get_with_lock(self, key: str) -> Optional[Any]:
        """Get state with distributed lock"""
        async with DistributedLock(key, self.redis):
            return await self.get(key)
    
    async def set_with_lock(self, key: str, value: Any) -> bool:
        """Set state with distributed lock"""
        async with DistributedLock(key, self.redis):
            return await self.set(key, value)
    
    async def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all state matching pattern"""
        if not self.postgres:
            return {}
        
        try:
            async with self.postgres.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT key, value FROM state_entries
                    WHERE key LIKE $1 AND (expires_at IS NULL OR expires_at > NOW())
                ''', pattern.replace('*', '%'))
            
            return {row['key']: row['value'] for row in rows}
            
        except Exception as e:
            logger.error(f"Failed to get all states: {e}")
            return {}
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries"""
        if not self.postgres:
            return 0
        
        try:
            async with self.postgres.acquire() as conn:
                count = await conn.fetchval(
                    'DELETE FROM state_entries WHERE expires_at IS NOT NULL AND expires_at <= NOW()'
                )
            
            logger.info(f"Cleaned up {count} expired state entries")
            return count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def get_history(self, key: str, limit: int = 100) -> List[Dict]:
        """Get state change history"""
        if not self.postgres:
            return []
        
        try:
            async with self.postgres.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT key, old_value, new_value, version, changed_at, changed_by
                    FROM state_history
                    WHERE key = $1
                    ORDER BY changed_at DESC
                    LIMIT $2
                ''', key, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def create_snapshot(self, name: str) -> bool:
        """Create point-in-time snapshot"""
        try:
            async with self.postgres.acquire() as conn:
                await conn.execute(f'''
                    CREATE TABLE snapshot_{name} AS
                    SELECT * FROM state_entries
                    WHERE expires_at IS NULL OR expires_at > NOW()
                ''')
            
            logger.info(f"Snapshot created: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Snapshot creation failed: {e}")
            return False
    
    async def restore_snapshot(self, name: str) -> bool:
        """Restore from snapshot"""
        try:
            async with self.postgres.acquire() as conn:
                await conn.execute('DELETE FROM state_entries')
                await conn.execute(f'INSERT INTO state_entries SELECT * FROM snapshot_{name}')
            
            logger.info(f"Restored from snapshot: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Snapshot restore failed: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown store"""
        if self.redis:
            await self.redis.close()
        if self.postgres:
            await self.postgres.close()
        
        logger.info("State store shutdown complete")


# Global instance
_state_store: Optional[StateStore] = None


async def init_state_store(consistency: ConsistencyLevel = ConsistencyLevel.EVENTUAL) -> StateStore:
    """Initialize global state store"""
    global _state_store
    _state_store = StateStore(consistency)
    await _state_store.initialize()
    return _state_store


async def get_state(key: str) -> Optional[Any]:
    """Get state globally"""
    global _state_store
    if not _state_store:
        _state_store = await init_state_store()
    return await _state_store.get(key)


async def set_state(key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
    """Set state globally"""
    global _state_store
    if not _state_store:
        _state_store = await init_state_store()
    return await _state_store.set(key, value, ttl_seconds)


async def delete_state(key: str) -> bool:
    """Delete state globally"""
    global _state_store
    if not _state_store:
        return False
    return await _state_store.delete(key)
