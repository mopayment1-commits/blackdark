"""
BLACKDARK — Decentralized Cold-Storage Cloud Syncer (Point 40).

Uploads historical Parquet archives to AWS S3 or S3-compatible object storage,
verifies remote integrity, logs status locally, and applies retention policies.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config
from database import fetch_latest_cloud_sync_log, init_db, insert_cloud_sync_log

logger = logging.getLogger("BLACKDARK.CloudSyncer")


@dataclass
class CloudSyncResult:
    local_path: Path
    s3_bucket: str
    s3_key: str
    success: bool = False
    verified: bool = False
    local_deleted: bool = False
    skipped: bool = False
    etag: str | None = None
    size_bytes: int = 0
    error: str | None = None


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_aioboto3() -> Any:
    try:
        import aioboto3
    except ImportError as exc:
        raise RuntimeError(
            "Cloud sync requires aioboto3. Install with: pip install aioboto3"
        ) from exc
    return aioboto3


def is_cloud_sync_configured() -> bool:
    bucket = str(config.AWS_S3_BUCKET or "").strip()
    if not bucket:
        return False
    if not config.CLOUD_SYNC_ENABLED:
        return False
    has_static_keys = bool(config.AWS_ACCESS_KEY_ID and config.AWS_SECRET_ACCESS_KEY)
    return has_static_keys or config.CLOUD_SYNC_ALLOW_IAM_ROLE


def _safe_error_message(exc: Exception) -> str:
    return f"{exc.__class__.__name__}: {str(exc)[:240]}"


def build_s3_key(local_path: Path, *, parquet_root: Path | None = None) -> str:
    root = (parquet_root or config.HISTORICAL_PARQUET_DIR).resolve()
    relative = local_path.resolve().relative_to(root)
    prefix = str(config.AWS_S3_PREFIX or "").strip("/")
    key_suffix = relative.as_posix()
    if prefix:
        return f"{prefix}/{key_suffix}"
    return key_suffix


class CloudSyncer:
    """Async S3 uploader with verification and configurable local retention."""

    def __init__(self) -> None:
        self.bucket = str(config.AWS_S3_BUCKET).strip()
        self.prefix = str(config.AWS_S3_PREFIX or "").strip("/")
        self.endpoint_url = str(config.AWS_S3_ENDPOINT_URL or "").strip() or None
        self.region = str(config.AWS_S3_REGION or "us-east-1")
        self.access_key = str(config.AWS_ACCESS_KEY_ID or "").strip() or None
        self.secret_key = str(config.AWS_SECRET_ACCESS_KEY or "").strip() or None
        self.upload_timeout = config.CLOUD_SYNC_UPLOAD_TIMEOUT_SECONDS

    def _session(self) -> Any:
        aioboto3 = _load_aioboto3()
        session_kwargs: dict[str, Any] = {}
        if self.access_key and self.secret_key:
            session_kwargs["aws_access_key_id"] = self.access_key
            session_kwargs["aws_secret_access_key"] = self.secret_key
        return aioboto3.Session(**session_kwargs)

    async def _upload_file(self, local_path: Path, s3_key: str) -> str:
        session = self._session()
        client_kwargs: dict[str, Any] = {"region_name": self.region}
        if self.endpoint_url:
            client_kwargs["endpoint_url"] = self.endpoint_url

        async with session.client("s3", **client_kwargs) as client:
            await asyncio.wait_for(
                client.upload_file(str(local_path), self.bucket, s3_key),
                timeout=self.upload_timeout,
            )
            head = await asyncio.wait_for(
                client.head_object(Bucket=self.bucket, Key=s3_key),
                timeout=self.upload_timeout,
            )

        etag = str(head.get("ETag") or "").strip('"')
        remote_size = int(head.get("ContentLength") or 0)
        local_size = local_path.stat().st_size

        if remote_size != local_size:
            raise RuntimeError(
                f"S3 verification failed: remote size {remote_size} != local size {local_size}"
            )
        return etag

    async def _log_status(
        self,
        *,
        local_path: Path,
        s3_key: str,
        status: str,
        etag: str | None = None,
        size_bytes: int | None = None,
        local_deleted: bool = False,
        error: str | None = None,
    ) -> None:
        try:
            await insert_cloud_sync_log(
                local_path=str(local_path),
                s3_bucket=self.bucket,
                s3_key=s3_key,
                status=status,
                etag=etag,
                size_bytes=size_bytes,
                local_deleted=local_deleted,
                error=error,
            )
        except Exception:
            logger.exception(
                "Failed to persist cloud sync log | bucket=%s key=%s status=%s",
                self.bucket,
                s3_key,
                status,
            )

    async def _already_verified(self, local_path: Path, size_bytes: int) -> bool:
        latest = await fetch_latest_cloud_sync_log(str(local_path))
        if latest is None:
            return False
        if str(latest.get("status") or "") != "verified":
            return False
        return int(latest.get("size_bytes") or 0) == size_bytes

    async def _apply_retention(self, local_path: Path) -> bool:
        if not config.CLOUD_SYNC_DELETE_LOCAL_AFTER_VERIFY:
            return False
        if not local_path.exists():
            return False
        try:
            local_path.unlink()
            return True
        except Exception:
            logger.exception("Failed to delete local parquet after cloud verify | file=%s", local_path)
            return False

    async def sync_file(self, local_path: Path) -> CloudSyncResult:
        local_path = local_path.resolve()
        s3_key = build_s3_key(local_path)
        size_bytes = local_path.stat().st_size if local_path.exists() else 0

        result = CloudSyncResult(
            local_path=local_path,
            s3_bucket=self.bucket,
            s3_key=s3_key,
            size_bytes=size_bytes,
        )

        if not local_path.exists():
            result.skipped = True
            result.error = "local_file_missing"
            return result

        if await self._already_verified(local_path, size_bytes):
            result.skipped = True
            result.success = True
            result.verified = True
            logger.info("Cloud sync skipped (already verified) | key=%s", s3_key)
            return result

        try:
            await init_db()
            etag = await self._upload_file(local_path, s3_key)
            result.etag = etag
            result.verified = True
            result.success = True

            await self._log_status(
                local_path=local_path,
                s3_key=s3_key,
                status="verified",
                etag=etag,
                size_bytes=size_bytes,
            )

            deleted = await self._apply_retention(local_path)
            result.local_deleted = deleted
            if deleted:
                await self._log_status(
                    local_path=local_path,
                    s3_key=s3_key,
                    status="local_deleted",
                    etag=etag,
                    size_bytes=size_bytes,
                    local_deleted=True,
                )
                logger.info(
                    "Cloud sync complete | bucket=%s key=%s local_deleted=true",
                    self.bucket,
                    s3_key,
                )
            else:
                logger.info(
                    "Cloud sync complete | bucket=%s key=%s local_retained=true",
                    self.bucket,
                    s3_key,
                )
            return result
        except Exception as exc:
            safe_error = _safe_error_message(exc)
            result.success = False
            result.error = safe_error
            await self._log_status(
                local_path=local_path,
                s3_key=s3_key,
                status="failed",
                size_bytes=size_bytes,
                error=safe_error,
            )
            logger.warning(
                "Cloud sync failed safely | bucket=%s key=%s reason=%s",
                self.bucket,
                s3_key,
                safe_error,
            )
            return result


async def sync_parquet_file(local_path: Path) -> CloudSyncResult | None:
    """Upload and verify one Parquet file when cloud sync is configured."""
    if not is_cloud_sync_configured():
        logger.debug("Cloud sync skipped; S3 bucket/credentials not configured.")
        return None

    syncer = CloudSyncer()
    return await syncer.sync_file(local_path)


async def sync_parquet_file_safe(local_path: Path) -> CloudSyncResult | None:
    """
    Isolated cloud sync entrypoint for compactor hooks.

    Never raises; connection timeouts and credential errors are logged safely.
    """
    if not is_cloud_sync_configured():
        return None

    try:
        return await sync_parquet_file(local_path)
    except Exception as exc:
        logger.warning(
            "Cloud sync hook failed safely | file=%s reason=%s",
            local_path.name,
            _safe_error_message(exc),
        )
        return CloudSyncResult(
            local_path=local_path.resolve(),
            s3_bucket=str(config.AWS_S3_BUCKET or ""),
            s3_key=build_s3_key(local_path),
            success=False,
            error=_safe_error_message(exc),
        )


async def sync_all_local_parquet(
    *,
    parquet_root: Path | None = None,
) -> list[CloudSyncResult]:
    """Upload all local Parquet files under the historical archive directory."""
    if not is_cloud_sync_configured():
        return []

    root = parquet_root or config.HISTORICAL_PARQUET_DIR
    if not root.exists():
        return []

    results: list[CloudSyncResult] = []
    for parquet_path in sorted(root.rglob("*.parquet")):
        try:
            result = await sync_parquet_file_safe(parquet_path)
            if result is not None:
                results.append(result)
        except Exception as exc:
            logger.warning(
                "Batch cloud sync failed safely | file=%s reason=%s",
                parquet_path.name,
                _safe_error_message(exc),
            )
    return results


async def run_cloud_sync_once() -> list[CloudSyncResult]:
    """Manual/admin entrypoint to sync all pending Parquet archives."""
    return await sync_all_local_parquet()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    async def _main() -> None:
        results = await run_cloud_sync_once()
        logger.info("Cloud sync batch finished | files=%d", len(results))

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Cloud syncer shutdown complete.")


if __name__ == "__main__":
    main()
