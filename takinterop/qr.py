"""Optional QR rendering helpers."""

from __future__ import annotations

import io


def qr_png(payload: str) -> bytes:
    import qrcode

    image = qrcode.make(payload, error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def qr_svg(payload: str) -> bytes:
    import qrcode
    import qrcode.image.svg

    image = qrcode.make(
        payload,
        image_factory=qrcode.image.svg.SvgPathImage,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        border=4,
    )
    output = io.BytesIO()
    image.save(output)
    return output.getvalue()
