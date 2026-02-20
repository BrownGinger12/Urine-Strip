# ============================================================
# qr_utils.py — QR code generation helper
# ============================================================
from PIL import Image
import qrcode


def build_qr_text(patient_name: str, scan_date: str,
                  glucose: str, ph: str, specific_gravity: str, protein: str) -> str:
    """Return the plain-text payload embedded in the QR code."""
    return (
        f"Name: {patient_name}\n"
        f"Date: {scan_date}\n"
        f"Glucose: {glucose}\n"
        f"pH: {ph}\n"
        f"Specific Gravity: {specific_gravity}\n"
        f"Protein: {protein}"
    )


def generate_qr_image(text: str, box_size: int = 7, border: int = 3) -> Image.Image:
    """
    Generate a QR code PIL Image from *text*.
    Returns a white-background PIL Image (mode 'RGB').
    """
    qr = qrcode.QRCode(
        version=None,           # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1117", back_color="#f0f6fc")
    return img.convert("RGB")