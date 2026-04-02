"""Resize uploaded images to fixed maximum dimensions (fit inside box, keep aspect ratio)."""
from __future__ import annotations

from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def resize_image_field(file_field, max_width: int, max_height: int, quality: int = 88) -> None:
    """Rewrite stored file as JPEG within max_width x max_height."""
    if not file_field or not file_field.name:
        return
    file_field.open("rb")
    try:
        img = Image.open(file_field)
        img = img.convert("RGB")
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        name = file_field.name.rsplit("/", 1)[-1]
        if not name.lower().endswith((".jpg", ".jpeg")):
            base = name.rsplit(".", 1)[0] if "." in name else name
            name = f"{base}.jpg"
        file_field.save(name, ContentFile(buffer.read()), save=False)
    finally:
        file_field.close()
