"""Avatar upload security controls — ID-041."""

from __future__ import annotations

import hashlib
import os
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from identity.public_user_id import default_avatar_url

STR_WEBP = ".webp"

def _avatar_dir() -> Path:
    return Path(os.getenv("IDENTITY_AVATAR_DIR", "data/avatars"))


AVATAR_DIR = _avatar_dir()
AVATAR_MAX_BYTES = int(os.getenv("IDENTITY_AVATAR_MAX_BYTES", str(2 * 1024 * 1024)))
AVATAR_MAX_DIMENSION = int(os.getenv("IDENTITY_AVATAR_MAX_DIMENSION", "1024"))
AVATAR_MAX_PIXELS = int(os.getenv("IDENTITY_AVATAR_MAX_PIXELS", str(1024 * 1024)))

ALLOWED_AVATAR_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": STR_WEBP}

# Documented equivalent to dedicated malware scanning for raster avatars:
# allowlisted formats, magic-byte validation, bounded decode, and full
# server-side re-encode strip executable payloads and metadata.
MALWARE_CONTROL = "server_side_raster_reencode_with_allowlist_and_decode_bounds"


def _validate_magic_bytes(content_type: str, data: bytes) -> None:
    if content_type == "image/jpeg" and not data.startswith(b"\xff\xd8"):
        raise ValueError("Invalid JPEG data")
    if content_type == "image/png" and not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Invalid PNG data")
    if content_type == "image/webp":
        if len(data) < 12 or data[0:4] != b"RIFF" or data[8:12] != b"WEBP":
            raise ValueError("Invalid WebP data")


def process_avatar_upload(content_type: str, data: bytes) -> tuple[str, bytes]:
    if content_type not in ALLOWED_AVATAR_TYPES:
        raise ValueError("Avatar must be JPEG, PNG, or WebP")
    if len(data) > AVATAR_MAX_BYTES:
        raise ValueError(f"Avatar must be ≤ {AVATAR_MAX_BYTES} bytes")
    _validate_magic_bytes(content_type, data)

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Avatar processing requires Pillow") from exc

    Image.MAX_IMAGE_PIXELS = AVATAR_MAX_PIXELS
    try:
        with Image.open(BytesIO(data)) as img:
            img.load()
            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValueError("Invalid image dimensions")
            if width > AVATAR_MAX_DIMENSION or height > AVATAR_MAX_DIMENSION:
                raise ValueError(f"Avatar dimensions must be ≤ {AVATAR_MAX_DIMENSION}px")
            if width * height > AVATAR_MAX_PIXELS:
                raise ValueError("Avatar pixel count too large")

            if content_type == "image/jpeg":
                out_mode = "RGB"
                ext = ".jpg"
                save_fmt = "JPEG"
                save_kwargs = {"quality": 85, "optimize": True}
            elif content_type == "image/png":
                out_mode = "RGBA" if "A" in img.mode else "RGB"
                ext = ".png"
                save_fmt = "PNG"
                save_kwargs = {"optimize": True}
            else:
                out_mode = "RGBA" if "A" in img.mode else "RGB"
                ext = STR_WEBP
                save_fmt = "WEBP"
                save_kwargs = {"quality": 85, "method": 4}

            converted = img.convert(out_mode)
            buf = BytesIO()
            converted.save(buf, format=save_fmt, **save_kwargs)
            processed = buf.getvalue()
            if len(processed) > AVATAR_MAX_BYTES:
                raise ValueError(f"Avatar must be ≤ {AVATAR_MAX_BYTES} bytes after processing")
            return ext, processed
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Invalid {content_type} data") from exc


def generate_object_key() -> str:
    return uuid4().hex


def avatar_url_for_object_key(object_key: str, ext: str) -> str:
    return f"/api/auth/avatar/{object_key}{ext}"


def _object_path_from_url(avatar_url: str | None) -> Path | None:
    if not avatar_url:
        return None
    stem = Path(avatar_url).stem
    suffix = Path(avatar_url).suffix.lower()
    if suffix not in {".jpg", ".png", STR_WEBP}:
        return None
    path = _avatar_dir() / f"{stem}{suffix}"
    return path if path.is_file() else None


def delete_avatar_file(avatar_url: str | None) -> None:
    path = _object_path_from_url(avatar_url)
    if path and path.is_file():
        path.unlink()


def save_avatar_bytes(
    *,
    content_type: str,
    data: bytes,
    previous_avatar_url: str | None,
) -> str:
    ext, processed = process_avatar_upload(content_type, data)
    delete_avatar_file(previous_avatar_url)
    _avatar_dir().mkdir(parents=True, exist_ok=True)
    object_key = generate_object_key()
    path = _avatar_dir() / f"{object_key}{ext}"
    path.write_bytes(processed)
    return avatar_url_for_object_key(object_key, ext)


def resolve_avatar_file(object_key: str, ext: str) -> Path | None:
    if ext not in {".jpg", ".png", STR_WEBP}:
        return None
    path = _avatar_dir() / f"{object_key}{ext}"
    return path if path.is_file() else None


def resolve_avatar_file_from_url(avatar_url: str) -> Path | None:
    return _object_path_from_url(avatar_url)


def delete_all_avatar_files_for_user(*, avatar_url: str | None) -> None:
    delete_avatar_file(avatar_url)


def reset_avatar_url(public_user_id: str) -> str:
    return default_avatar_url(public_user_id)


def avatar_object_key_from_url(avatar_url: str | None) -> str | None:
    if not avatar_url:
        return None
    suffix = Path(avatar_url).suffix.lower()
    if suffix in {".jpg", ".png", STR_WEBP}:
        return Path(avatar_url).stem
    return None


def avatar_integrity_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
