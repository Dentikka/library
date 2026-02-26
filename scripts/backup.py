#!/usr/bin/env python3
"""Backup script for PostgreSQL database.

PG-005: Backup strategy - Automated PostgreSQL backups with rotation.

Usage:
    python scripts/backup.py

Environment variables:
    DATABASE_URL - PostgreSQL connection string (required)
    BACKUP_DIR - Directory for backups (default: ./backups)
    BACKUP_RETENTION_DAYS - Days to keep backups (default: 7)
    LOG_LEVEL - Logging level (default: INFO)
"""

import os
import sys
import gzip
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.logging_config import setup_logging, get_logger


def get_database_config() -> dict:
    """Parse DATABASE_URL and return connection parameters."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Handle both asyncpg and psycopg URLs
    url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("postgresql+psycopg://", "postgresql://")
    
    parsed = urlparse(url)
    
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/").split("?")[0],
        "user": parsed.username or "",
        "password": parsed.password or "",
    }


def create_backup(backup_dir: Path, logger) -> Path:
    """Create a new PostgreSQL backup using pg_dump.
    
    Args:
        backup_dir: Directory to save the backup
        logger: Logger instance
        
    Returns:
        Path to the created backup file
    """
    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"library_{timestamp}.sql"
    backup_path = backup_dir / backup_name
    compressed_path = backup_path.with_suffix(".sql.gz")
    
    logger.info("Backup started: %s", backup_name, extra={
        "backup_name": backup_name,
        "backup_path": str(backup_path)
    })
    
    # Get database connection info
    config = get_database_config()
    
    # Build pg_dump command
    cmd = [
        "pg_dump",
        "--host", config["host"],
        "--port", str(config["port"]),
        "--username", config["user"],
        "--dbname", config["database"],
        "--verbose",
        "--no-owner",
        "--no-privileges",
        "--format", "plain",
    ]
    
    # Set password environment variable
    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]
    
    try:
        # Run pg_dump and compress output
        logger.info("Running pg_dump for database: %s@%s", config["database"], config["host"], extra={
            "host": config["host"],
            "database": config["database"]
        })
        
        with gzip.open(compressed_path, "wt", encoding="utf-8") as f_out:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            
            # Stream output to gzip file
            if process.stdout:
                for line in process.stdout:
                    f_out.write(line)
            
            # Wait for completion
            returncode = process.wait()
            
            if returncode != 0:
                stderr = process.stderr.read() if process.stderr else "Unknown error"
                raise subprocess.CalledProcessError(returncode, cmd, stderr=stderr)
        
        # Get file size
        file_size = compressed_path.stat().st_size
        logger.info("Backup completed: %s (%.2f MB)", compressed_path.name, file_size / 1024 / 1024, extra={
            "backup_path": str(compressed_path),
            "backup_name": compressed_path.name,
            "size_bytes": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
        })
        
        return compressed_path
        
    except subprocess.CalledProcessError as e:
        logger.error("pg_dump failed with returncode %d: %s", e.returncode, e.stderr, extra={
            "returncode": e.returncode,
            "stderr": str(e.stderr)
        })
        # Clean up partial file
        if compressed_path.exists():
            compressed_path.unlink()
        raise
    except FileNotFoundError:
        logger.error("pg_dump command not found. Is PostgreSQL client installed?")
        raise


def rotate_backups(backup_dir: Path, retention_days: int, logger) -> list[Path]:
    """Remove old backups based on retention policy.
    
    Args:
        backup_dir: Directory containing backups
        retention_days: Number of days to keep backups
        logger: Logger instance
        
    Returns:
        List of removed backup files
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    removed_files = []
    
    logger.info("Rotation started: retention=%d days, cutoff=%s", retention_days, cutoff_date.isoformat(), extra={
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat()
    })
    
    for backup_file in backup_dir.glob("library_*.sql.gz"):
        try:
            # Extract date from filename (library_YYYYMMDD_HHMMSS.sql.gz)
            date_str = backup_file.stem.replace(".sql", "").split("_", 1)[1]
            file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
            
            if file_date < cutoff_date:
                backup_file.unlink()
                removed_files.append(backup_file)
                logger.info("Old backup removed: %s (dated %s)", backup_file.name, file_date.isoformat(), extra={
                    "file": backup_file.name,
                    "file_date": file_date.isoformat()
                })
        except (ValueError, IndexError):
            # Skip files that don't match expected pattern
            logger.warning("Skipping unrecognized file: %s", backup_file.name, extra={"file": backup_file.name})
            continue
    
    logger.info("Rotation completed: removed %d old backup(s)", len(removed_files), extra={
        "removed_count": len(removed_files)
    })
    return removed_files


def main():
    """Main entry point for backup script."""
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(level=log_level, format_type="console")
    logger = get_logger("backup")
    
    logger.info("Backup script started")
    
    try:
        # Get configuration from environment
        backup_dir = Path(os.getenv("BACKUP_DIR", "./backups"))
        retention_days = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))
        
        # Ensure backup directory exists
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Configuration loaded: backup_dir=%s, retention_days=%d", 
                    str(backup_dir.absolute()), retention_days,
                    extra={
                        "backup_dir": str(backup_dir.absolute()),
                        "retention_days": retention_days,
                    })
        
        # Create backup
        backup_file = create_backup(backup_dir, logger)
        
        # Rotate old backups
        removed = rotate_backups(backup_dir, retention_days, logger)
        
        logger.info("Backup script completed: file=%s, removed=%d", 
                    backup_file.name, len(removed),
                    extra={
                        "backup_file": backup_file.name,
                        "removed_old_backups": len(removed),
                    })
        
        print(f"\n✅ Backup created: {backup_file}")
        print(f"🗑️  Removed {len(removed)} old backup(s)")
        
        return 0
        
    except ValueError as e:
        logger.error("Configuration error: %s", str(e), extra={"error": str(e)})
        print(f"\n❌ Configuration error: {e}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as e:
        logger.error("Backup failed: %s", str(e), extra={"error": str(e)})
        print(f"\n❌ Backup failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True, extra={"error": str(e)})
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
