"""
Data migration utilities
Scripts for migrating data from Perl API to Python API
"""
import asyncio
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from datetime import datetime

from app.db.session import get_db
from app.models.cliente import Cliente
from app.models.onboarding import ClientesActiveSession
from app.core.redis_client import redis_client
from app.core.security import get_password_hash


class DataMigration:
    """
    Data migration utilities for Perl to Python transition
    """
    
    @staticmethod
    async def migrate_user_sessions(db: AsyncSession) -> Dict[str, Any]:
        """
        Migrate active user sessions from Perl database to Redis
        
        Reads ClientesActiveSession from database and ensures
        they're properly cached in Redis for Python API
        """
        result = await db.execute(
            select(ClientesActiveSession)
            .where(ClientesActiveSession.valid_until > datetime.utcnow())
        )
        sessions = result.scalars().all()
        
        migrated = 0
        failed = 0
        
        for session in sessions:
            try:
                # Cache session in Redis
                cache_key = f"session:{session.cliente_id}:{session.session_id}"
                session_data = {
                    "cliente_id": session.cliente_id,
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "valid_until": session.valid_until.isoformat()
                }
                
                # Set with expiration
                ttl = int((session.valid_until - datetime.utcnow()).total_seconds())
                if ttl > 0:
                    await redis_client.setex(
                        cache_key,
                        ttl,
                        str(session_data)
                    )
                    migrated += 1
            except Exception as e:
                print(f"Failed to migrate session {session.session_id}: {e}")
                failed += 1
        
        return {
            "success": True,
            "migrated": migrated,
            "failed": failed,
            "total": len(sessions)
        }
    
    @staticmethod
    async def validate_password_compatibility(db: AsyncSession) -> Dict[str, Any]:
        """
        Validate that all user passwords can be verified
        
        Checks both bcrypt (new) and SHA256 (legacy) hashes
        """
        result = await db.execute(select(Cliente).where(Cliente.active == True))
        users = result.scalars().all()
        
        bcrypt_count = 0
        sha256_count = 0
        invalid_count = 0
        
        for user in users:
            if not user.senha:
                invalid_count += 1
                continue
            
            # Check if it's bcrypt (starts with $2b$)
            if user.senha.startswith('$2b$') or user.senha.startswith('$2a$'):
                bcrypt_count += 1
            # Check if it's SHA256 (64 hex characters)
            elif len(user.senha) == 64 and all(c in '0123456789abcdef' for c in user.senha):
                sha256_count += 1
            else:
                invalid_count += 1
        
        return {
            "total_users": len(users),
            "bcrypt_hashes": bcrypt_count,
            "sha256_hashes": sha256_count,
            "invalid_hashes": invalid_count,
            "compatibility": "OK" if invalid_count == 0 else "WARNING"
        }
    
    @staticmethod
    async def migrate_legacy_passwords(
        db: AsyncSession,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Migrate legacy SHA256 passwords to bcrypt on next login
        
        This doesn't change passwords now, but prepares the system
        to upgrade them when users log in
        """
        # Get all users with legacy passwords
        result = await db.execute(
            select(Cliente)
            .where(Cliente.active == True)
            .where(Cliente.senha.like('%'))  # All passwords
        )
        users = result.scalars().all()
        
        legacy_count = 0
        
        for user in users:
            if user.senha and len(user.senha) == 64:
                # Mark as legacy (already supported by verify_password)
                legacy_count += 1
        
        return {
            "success": True,
            "legacy_passwords_found": legacy_count,
            "note": "Legacy passwords will be auto-upgraded on next login"
        }
    
    @staticmethod
    async def verify_database_schema(db: AsyncSession) -> Dict[str, Any]:
        """
        Verify that database schema matches expected structure
        """
        tables_to_check = [
            'clientes',
            'clientes_active_sessions',
            'clientes_guardio',
            'clientes_tarefas',
            'clientes_tweet',
            'chat_clientes',
            'chat_clientes_messages',
            'notification_messages',
            'ponto_apoio',
            'noticias',
            'questionnaires'
        ]
        
        existing_tables = []
        missing_tables = []
        
        for table in tables_to_check:
            result = await db.execute(
                text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """)
            )
            exists = result.scalar()
            
            if exists:
                existing_tables.append(table)
            else:
                missing_tables.append(table)
        
        return {
            "total_checked": len(tables_to_check),
            "existing": len(existing_tables),
            "missing": len(missing_tables),
            "missing_tables": missing_tables,
            "status": "OK" if not missing_tables else "WARNING"
        }
    
    @staticmethod
    async def sync_redis_cache(db: AsyncSession) -> Dict[str, Any]:
        """
        Synchronize critical data to Redis cache
        """
        try:
            # Test Redis connection
            await redis_client.ping()
            
            # Clear old cache
            pattern = "penhas:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
            
            # Cache active users count
            result = await db.execute(
                select(func.count(Cliente.id)).where(Cliente.active == True)
            )
            active_users = result.scalar()
            await redis_client.set("stats:active_users", active_users)
            
            return {
                "success": True,
                "redis_connected": True,
                "cache_cleared": len(keys) if keys else 0,
                "active_users_cached": active_users
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


async def run_migration_checks():
    """
    Run all migration checks and report status
    """
    print("=" * 60)
    print("PenhaS API Data Migration Checks")
    print("=" * 60)
    
    async for db in get_db():
        migration = DataMigration()
        
        # Check 1: Database Schema
        print("\n1. Checking database schema...")
        schema_check = await migration.verify_database_schema(db)
        print(f"   Status: {schema_check['status']}")
        print(f"   Tables found: {schema_check['existing']}/{schema_check['total_checked']}")
        if schema_check['missing_tables']:
            print(f"   Missing: {', '.join(schema_check['missing_tables'])}")
        
        # Check 2: Password Compatibility
        print("\n2. Checking password compatibility...")
        password_check = await migration.validate_password_compatibility(db)
        print(f"   Total users: {password_check['total_users']}")
        print(f"   Bcrypt hashes: {password_check['bcrypt_hashes']}")
        print(f"   Legacy SHA256: {password_check['sha256_hashes']}")
        print(f"   Status: {password_check['compatibility']}")
        
        # Check 3: Session Migration
        print("\n3. Migrating active sessions to Redis...")
        session_check = await migration.migrate_user_sessions(db)
        print(f"   Migrated: {session_check['migrated']}")
        print(f"   Failed: {session_check['failed']}")
        
        # Check 4: Redis Cache
        print("\n4. Syncing Redis cache...")
        redis_check = await migration.sync_redis_cache(db)
        if redis_check['success']:
            print(f"   Redis connected: Yes")
            print(f"   Cache cleared: {redis_check.get('cache_cleared', 0)} keys")
        else:
            print(f"   Redis error: {redis_check.get('error')}")
        
        break
    
    print("\n" + "=" * 60)
    print("Migration checks complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Run migration checks
    asyncio.run(run_migration_checks())

