"""media e2e：client 打 /api/files，断言 HTTP status + {errno,code,data}。"""
import io

import pytest
from PIL import Image


def _png_bytes(color=(0, 200, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def media_dir(app, tmp_path, monkeypatch):
    """隔离落盘目录。"""
    d = tmp_path / "media"
    monkeypatch.setitem(app.config, "MEDIA_DIR", str(d))
    return d


def test_upload_requires_login(client, media_dir):
    resp = client.post(
        "/api/files",
        data={"media": (io.BytesIO(_png_bytes()), "a.png")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 401
    body = resp.get_json()
    # 未登录由 flask-jwt-extended 拦截，其默认 body 为 {"msg": ...}，
    # 不套用 {errno,code,data} 信封（地基层 jwt handler 未定制，非本域可控）。
    assert body.get("errno", 1) != 0


def test_upload_real_image_success(user_client, media_dir):
    client, headers = user_client
    resp = client.post(
        "/api/files",
        data={"media": (io.BytesIO(_png_bytes()), "a.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["errno"] == 0
    assert body["code"] == 201
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["data"][0].endswith(".png")


def test_upload_multiple_files(user_client, media_dir):
    client, headers = user_client
    resp = client.post(
        "/api/files",
        data={
            "media": [
                (io.BytesIO(_png_bytes((255, 0, 0))), "a.png"),
                (io.BytesIO(_png_bytes((0, 0, 255))), "b.png"),
            ]
        },
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["errno"] == 0
    assert len(body["data"]) == 2


def test_upload_non_image_rejected(user_client, media_dir):
    client, headers = user_client
    resp = client.post(
        "/api/files",
        data={"media": (io.BytesIO(b"not an image at all"), "fake.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["errno"] != 0
    assert body["code"] == 400


def test_upload_dedup_returns_same_filename(user_client, media_dir):
    client, headers = user_client
    png = _png_bytes()

    resp1 = client.post(
        "/api/files",
        data={"media": (io.BytesIO(png), "first.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    resp2 = client.post(
        "/api/files",
        data={"media": (io.BytesIO(png), "second.png")},
        headers=headers,
        content_type="multipart/form-data",
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201
    # 同一内容 md5 去重 -> 同一 url（同一 filename）
    assert resp1.get_json()["data"][0] == resp2.get_json()["data"][0]
