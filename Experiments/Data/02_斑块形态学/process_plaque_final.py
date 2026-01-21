#!/usr/bin/env python3
"""
噬菌体斑块照片统一处理脚本 - 最终版
- 直接指定每张照片的裁剪区域
- 统一裁剪为1/4培养皿大小
- 边缘方向统一（弧线在右上角）
- 增强对比度和清晰度
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter

# 路径设置
PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SIZE = 800

# 直接指定裁剪区域 (left, top, right, bottom)
# 选择培养皿内部的区域，包含部分边缘
# 所有照片的培养皿弧线将在右上角
CROP_REGIONS = {
    # R1 (3024x4032): 培养皿在上部，裁剪左侧区域（翻转后边缘在右上）
    "R1": (350, 900, 1550, 2100),
    # R2 (3024x4032): 培养皿大，裁剪右上四分之一
    "R2": (1500, 550, 2950, 2000),
    # R3 (3024x4032): 培养皿在中间，裁剪左上区域（翻转后边缘在右上）
    "R3": (200, 1200, 1500, 2500),
    # W1 (3024x4032): 培养皿在中上部，裁剪左上区域（翻转后边缘在右上）
    "W1": (300, 800, 1500, 2000),
    # W2 (4284x5712): 培养皿在中上部，裁剪左上区域（翻转后边缘在右上）
    "W2": (600, 1200, 2200, 2800),
}

# 是否需要水平翻转以统一边缘方向
FLIP_HORIZONTAL = {
    "R1": True,   # 裁剪的是左边，需要翻转
    "R2": False,  # 右边，不需要翻转
    "R3": True,   # 裁剪左边，需要翻转
    "W1": True,   # 裁剪左边，需要翻转
    "W2": True,   # 裁剪左边，需要翻转
}


def enhance_image(img: Image.Image) -> Image.Image:
    """增强图像"""
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    return img


def make_square(img: Image.Image, output_size: int) -> Image.Image:
    """调整为正方形"""
    w, h = img.size
    scale = output_size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)

    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 创建白色背景
    canvas = Image.new('RGB', (output_size, output_size), (255, 255, 255))
    # 居中放置
    paste_x = (output_size - new_w) // 2
    paste_y = (output_size - new_h) // 2
    canvas.paste(img_resized, (paste_x, paste_y))

    return canvas


def process_full_plate(input_path: Path, output_dir: Path) -> bool:
    """处理全盘照片"""
    name = input_path.stem.replace("_原始", "")
    print(f"处理: {input_path.name}")

    if name not in CROP_REGIONS:
        print(f"  警告: 没有 {name} 的裁剪配置")
        return False

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        print(f"  尺寸: {img.size}")

        # 裁剪
        region = CROP_REGIONS[name]
        print(f"  裁剪区域: {region}")
        cropped = img.crop(region)

        # 是否需要翻转
        if FLIP_HORIZONTAL.get(name, False):
            cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
            print("  水平翻转")

        # 增强
        enhanced = enhance_image(cropped)

        # 调整为正方形
        final = make_square(enhanced, OUTPUT_SIZE)

        # 保存
        output_name = f"{name}_统一.jpg"
        output_path = output_dir / output_name
        final.save(output_path, "JPEG", quality=95)
        print(f"  保存: {output_name}")

        return True

    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_closeup(input_path: Path, output_dir: Path) -> bool:
    """处理特写照片"""
    print(f"处理特写: {input_path.name}")

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 增强
        enhanced = enhance_image(img)

        # 裁剪中心正方形
        w, h = enhanced.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = enhanced.crop((left, top, left + min_dim, top + min_dim))

        # 缩放
        final = cropped.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

        # 保存
        output_name = input_path.stem.replace("_原始", "") + "_统一.jpg"
        output_path = output_dir / output_name
        final.save(output_path, "JPEG", quality=95)
        print(f"  保存: {output_name}")

        return True

    except Exception as e:
        print(f"  错误: {e}")
        return False


def main():
    print("=" * 60)
    print("噬菌体斑块照片统一处理 - 最终版")
    print("=" * 60)

    photos = list(PHOTOS_DIR.glob("*_原始.jpg"))
    print(f"\n找到 {len(photos)} 张原始照片\n")

    full_plates = []
    closeups = []

    for p in photos:
        name = p.stem.replace("_原始", "")
        parts = name.split("-")
        if len(parts) > 1 and parts[-1].isdigit():
            closeups.append(p)
        else:
            full_plates.append(p)

    print(f"全盘: {len(full_plates)}, 特写: {len(closeups)}\n")

    success = 0

    for p in sorted(full_plates):
        if process_full_plate(p, OUTPUT_DIR):
            success += 1
        print()

    for p in sorted(closeups):
        if process_closeup(p, OUTPUT_DIR):
            success += 1
        print()

    print("=" * 60)
    print(f"完成: {success}/{len(photos)}")
    print(f"输出: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
