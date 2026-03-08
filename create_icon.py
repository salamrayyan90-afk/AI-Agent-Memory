"""
إنشاء أيقونة Core AI (PNG + ICO) لتتماشى مع آخر التحديثات — واجهة 2026.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def create_icon():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Pillow required: pip install pillow")
        return False

    size = 256
    img = Image.new("RGBA", (size, size), (10, 10, 10, 255))
    draw = ImageDraw.Draw(img)

    # لون التحديث: تيل/سماوي
    color = (0, 212, 170, 255)
    margin = 40
    # شكل "C" أو نواة: قوس كبير
    draw.arc([margin, margin, size - margin, size - margin], 60, 300, fill=color, width=24)
    # نقطة مركزية
    cx, cy = size // 2, size // 2
    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=color)

    png_path = ROOT / "icon.png"
    img.save(png_path, "PNG")
    print("OK:", png_path)

    # ICO for desktop shortcut
    ico_path = ROOT / "icon.ico"
    img.save(ico_path, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print("OK:", ico_path)
    return True


if __name__ == "__main__":
    create_icon()
