"""Convert Core AI logo PNG to Windows .ico, or create default icon if PNG missing."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Install Pillow: pip install Pillow")
    raise

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
PNG = STATIC / "core_ai_logo.png"
ICO = STATIC / "core_ai_icon.ico"
SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

def make_default_icon(size=256):
    """Create a simple dark + cyan accent icon."""
    img = Image.new("RGBA", (size, size), (14, 17, 23, 255))  # #0e1117
    d = ImageDraw.Draw(img)
    margin = size // 6
    d.rounded_rectangle([margin, margin, size - margin, size - margin],
                        outline=(0, 212, 255, 255), width=max(2, size // 32), radius=size // 8)
    return img

def main():
    STATIC.mkdir(parents=True, exist_ok=True)
    if PNG.exists():
        img = Image.open(PNG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
    else:
        img = make_default_icon(256)
    img.save(ICO, format="ICO", sizes=SIZES)
    print(f"Created: {ICO}")

if __name__ == "__main__":
    main()
