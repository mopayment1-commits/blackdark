"""Final identity evidence reconciliation — public user id + avatar security."""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image


STRONG = "correct-horse-battery-99"


def _png_bytes(width: int = 64, height: int = 64, color=(255, 0, 0)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(width: int = 64, height: int = 64) -> bytes:
    img = Image.new("RGB", (width, height), (0, 128, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_public_user_id_generated_on_create(tmp_path, monkeypatch):
    import database
    from identity.public_user_id import is_valid_public_user_id

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "pubid.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("pub@example.com", "hash", "Pub")
        row = await database.fetch_user_by_id(uid)
        assert row is not None
        assert is_valid_public_user_id(row["public_user_id"])
        assert row.get("user_uuid")

    asyncio.run(_run())


def test_client_user_payload_hides_internal_id():
    from auth_service import client_user_payload

    payload = client_user_payload(
        {"id": 7, "public_user_id": "u_" + ("a" * 32), "email": "a@b.co", "name": "A"}
    )
    assert "id" not in payload
    assert payload["public_user_id"].startswith("u_")


def test_auth_me_payload_uses_public_user_id(tmp_path, monkeypatch):
    import database
    from auth_service import client_user_payload, hash_password, register_user

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "me.db"))
    monkeypatch.setenv("IDENTITY_DEBUG_TOKENS", "true")

    async def _run():
        await database.init_db()
        result = await register_user(
            "me@example.com",
            STRONG,
            "Me User",
            accepted_terms=True,
        )
        user = result["user"]
        assert "id" not in user
        assert user["public_user_id"].startswith("u_")
        assert "/api/auth/avatar/u_" in user["avatar_url"]
        assert client_user_payload({"id": 1, "public_user_id": user["public_user_id"]})["public_user_id"]

    asyncio.run(_run())


def test_avatar_default_route_requires_public_user_id(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "svg.db"))

    async def _run():
        await database.init_db()
        uid = await database.create_user("svg@example.com", hash_password(STRONG), "Svg")
        row = await database.fetch_user_by_id(uid)
        assert row is not None
        from identity.public_user_id import default_avatar_url

        url = default_avatar_url(row["public_user_id"])
        assert f"/api/auth/avatar/{uid}." not in url
        assert row["public_user_id"] in url

    asyncio.run(_run())


def test_avatar_format_allowlist_and_mime_validation(tmp_path, monkeypatch):
    from identity.avatar_upload import AVATAR_DIR, process_avatar_upload, save_avatar_bytes

    monkeypatch.setenv("IDENTITY_AVATAR_DIR", str(tmp_path / "avatars"))

    with pytest.raises(ValueError, match="JPEG, PNG, or WebP"):
        process_avatar_upload("image/svg+xml", b"<svg></svg>")

    bad_jpeg = b"\xff\xd8\xff" + b"not-a-jpeg"
    with pytest.raises(ValueError, match="Invalid image|Invalid JPEG|Invalid image/jpeg"):
        process_avatar_upload("image/jpeg", bad_jpeg)

    ext, processed = process_avatar_upload("image/png", _png_bytes())
    assert ext == ".png"
    assert processed.startswith(b"\x89PNG")


def test_avatar_size_and_dimension_limits(tmp_path, monkeypatch):
    from identity.avatar_upload import AVATAR_MAX_DIMENSION, process_avatar_upload

    huge = _png_bytes(width=AVATAR_MAX_DIMENSION + 1, height=8)
    with pytest.raises(ValueError, match="dimensions"):
        process_avatar_upload("image/png", huge)

    oversized = b"x" * (2 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="bytes"):
        process_avatar_upload("image/jpeg", oversized)


def test_avatar_pixel_bomb_guard(tmp_path, monkeypatch):
    from identity.avatar_upload import AVATAR_MAX_PIXELS, process_avatar_upload

    side = int(AVATAR_MAX_PIXELS**0.5) + 2
    bomb = _png_bytes(width=side, height=side)
    with pytest.raises(ValueError):
        process_avatar_upload("image/png", bomb)


def test_avatar_reencode_strips_exif_and_uses_uuid_object_key(tmp_path, monkeypatch):
    from identity.avatar_upload import AVATAR_DIR, save_avatar_bytes

    avatar_dir = tmp_path / "avatars"
    monkeypatch.setenv("IDENTITY_AVATAR_DIR", str(avatar_dir))

    jpeg = _jpeg_bytes()
    url = save_avatar_bytes(content_type="image/jpeg", data=jpeg, previous_avatar_url=None)
    object_key = Path(url).stem
    assert object_key.isalnum()
    assert len(object_key) == 32
    assert "1" != object_key  # not sequential user id
    stored = avatar_dir / f"{object_key}.jpg"
    assert stored.is_file()
    with Image.open(stored) as img:
        assert img.format == "JPEG"
        assert img.getexif() == {}


def test_avatar_svg_upload_rejected():
    from identity.avatar_upload import save_avatar_bytes

    with pytest.raises(ValueError):
        save_avatar_bytes(content_type="image/svg+xml", data=b"<svg/onload=alert(1)>", previous_avatar_url=None)


def test_avatar_deletion_on_replace_and_account_erase(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password
    from identity.avatar_upload import AVATAR_DIR, save_avatar_bytes

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "del.db"))
    avatar_dir = tmp_path / "avatars"
    monkeypatch.setenv("IDENTITY_AVATAR_DIR", str(avatar_dir))

    async def _run():
        await database.init_db()
        uid = await database.create_user("del@example.com", hash_password(STRONG), "Del")
        first = save_avatar_bytes(content_type="image/png", data=_png_bytes(), previous_avatar_url=None)
        first_path = avatar_dir / (Path(first).name)
        assert first_path.is_file()
        second = save_avatar_bytes(content_type="image/png", data=_png_bytes(color=(0, 255, 0)), previous_avatar_url=first)
        assert not first_path.is_file()
        row = await database.fetch_user_by_id(uid)
        await database.update_user_profile_fields(uid, {"avatar_url": second})
        await database.erase_user_personal_data("del@example.com")
        assert not any(avatar_dir.iterdir())

    asyncio.run(_run())


def test_malware_control_documented():
    from identity.avatar_upload import MALWARE_CONTROL
    from identity_service import identity_architecture

    assert MALWARE_CONTROL
    assert identity_architecture()["avatar"]["malware_control"] == MALWARE_CONTROL
