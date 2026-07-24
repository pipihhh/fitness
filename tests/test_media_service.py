"""media service 单测：图片校验、随机文件名、MD5 去重、只写一次盘。"""
import io
import os

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage

from ezgym.core.errors import BadRequest
from ezgym.support.media.models import FileMap
from ezgym.support.media.service import MediaService


def _png_bytes(color=(255, 0, 0)) -> bytes:
    """用 Pillow 生成一张真实小 PNG 的 bytes。"""
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


def _storage(data: bytes, filename: str = "a.png") -> FileStorage:
    return FileStorage(
        stream=io.BytesIO(data), filename=filename, content_type="image/png"
    )


@pytest.fixture()
def media_dir(app, tmp_path, monkeypatch):
    """把落盘目录隔离到 tmp_path。"""
    d = tmp_path / "media"
    monkeypatch.setitem(app.config, "MEDIA_DIR", str(d))
    return d


def _files_on_disk(media_dir) -> list[str]:
    if not media_dir.exists():
        return []
    return [p for p in os.listdir(media_dir)]


def test_save_upload_success_returns_url_and_writes_once(app, media_dir):
    png = _png_bytes()
    url = MediaService.save_upload(_storage(png))

    assert url.startswith(app.config["MEDIA_URL"] + "/")
    # 只写一次盘：目录里恰好一个文件
    assert len(_files_on_disk(media_dir)) == 1
    # 写了一条 FileMap
    assert FileMap.query.count() == 1


def test_random_filename_preserves_extension(app, media_dir):
    png = _png_bytes()
    url = MediaService.save_upload(_storage(png, filename="original_name.png"))

    stored = url.rsplit("/", 1)[1]
    assert stored != "original_name.png"  # 随机化
    assert stored.endswith(".png")  # 保留扩展名


def test_md5_dedup_reuses_filename_no_second_write(app, media_dir):
    png = _png_bytes()
    url1 = MediaService.save_upload(_storage(png, filename="first.png"))
    url2 = MediaService.save_upload(_storage(png, filename="second.png"))

    # 同一内容 -> 同一 url（复用 filename）
    assert url1 == url2
    # 去重命中不重复落盘、不重复写库
    assert len(_files_on_disk(media_dir)) == 1
    assert FileMap.query.count() == 1


def test_different_content_produces_different_files(app, media_dir):
    url1 = MediaService.save_upload(_storage(_png_bytes((255, 0, 0))))
    url2 = MediaService.save_upload(_storage(_png_bytes((0, 128, 255))))

    assert url1 != url2
    assert len(_files_on_disk(media_dir)) == 2
    assert FileMap.query.count() == 2


def test_non_image_content_rejected(app, media_dir):
    # 伪造 .png 扩展名的纯文本 -> 内容嗅探失败
    with pytest.raises(BadRequest):
        MediaService.save_upload(_storage(b"this is not an image", filename="fake.png"))
    assert _files_on_disk(media_dir) == []
    assert FileMap.query.count() == 0


def test_bad_extension_rejected(app, media_dir):
    with pytest.raises(BadRequest):
        MediaService.save_upload(_storage(_png_bytes(), filename="evil.txt"))
    assert _files_on_disk(media_dir) == []
    assert FileMap.query.count() == 0


def test_empty_file_rejected(app, media_dir):
    with pytest.raises(BadRequest):
        MediaService.save_upload(_storage(b"", filename="empty.png"))
    assert FileMap.query.count() == 0
