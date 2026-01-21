#!/usr/bin/env python3
"""
噬菌体斑块照片统一处理脚本 v3
- 使用手动配置确保准确裁剪
- 统一裁剪为1/4培养皿大小
- 边缘方向统一（弧线在右上角）
- 增强对比度和清晰度
"""

from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2

# 路径设置
PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SIZE = 800

# 手动配置每张全盘照片的培养皿位置
# 格式: (center_x, center_y, radius)
# 根据原始照片（3024x4032 或 4284x5712）手动测量
MANUAL_CONFIG = {
    # R1: 培养皿在照片上部，标记"R6"在右上角
    "R1": (1500, 1500, 1150),
    # R2: 培养皿占大部分画面，标记"R2 T2"在左下
    "R2": (1500, 2000, 1450),
    # R3: 培养皿在照片中间偏上，标记"R3 L4"
    "R3": (1500, 1700, 1300),
    # W1: 培养皿在照片上部，标记"W1 L2"
    "W1": (1500, 1550, 1150),
    # W2: 照片尺寸4284x5712，培养皿在上部
    "W2": (2100, 2200, 1600),
}


def detect_agar_with_fallback(img_array: np.ndarray, manual_config: tuple = None) -> tuple:
    """
    检测培养基区域，如果自动检测失败则使用手动配置
    """
    if manual_config:
        return manual_config

    # 自动检测
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    # 培养基颜色范围
    lower = np.array([15, 15, 140])
    upper = np.array([55, 140, 255])
    mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((25, 25), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        (cx, cy), radius = cv2.minEnclosingCircle(largest)

        # 验证检测结果
        img_h, img_w = img_array.shape[:2]
        min_radius = min(img_h, img_w) * 0.2  # 至少是图片短边的20%

        if radius > min_radius:
            return (int(cx), int(cy), int(radius))

    # 默认使用图片中心
    h, w = img_array.shape[:2]
    return (w // 2, h // 2, min(w, h) // 3)


def crop_quarter_topright(img: Image.Image, center: tuple, radius: int) -> Image.Image:
    """
    裁剪培养皿的右上四分之一区域
    """
    cx, cy, r = center

    # 从圆心向右上裁剪
    left = cx
    top = max(0, cy - r)
    right = min(img.width, cx + r)
    bottom = cy

    cropped = img.crop((int(left), int(top), int(right), int(bottom)))
    return cropped


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


def make_square_canvas(img: Image.Image, output_size: int) -> Image.Image:
    """
    将图片调整为正方形，培养皿弧线在右上角
    """
    w, h = img.size
    scale = output_size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)

    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    canvas = Image.new('RGB', (output_size, output_size), (255, 255, 255))
    # 放在左下角
    canvas.paste(img_resized, (0, output_size - new_h))

    return canvas


def process_full_plate(input_path: Path, output_dir: Path, manual_config: tuple = None) -> bool:
    """处理全盘照片"""
    print(f"处理: {input_path.name}")

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img)
        print(f"  尺寸: {img.size}")

        # 获取配置
        config = detect_agar_with_fallback(img_array, manual_config)
        print(f"  配置: 中心({config[0]}, {config[1]}), 半径{config[2]}")

        # 裁剪右上四分之一
        cropped = crop_quarter_topright(img, config, config[2])

        # 增强
        enhanced = enhance_image(cropped)

        # 调整为正方形
        final = make_square_canvas(enhanced, OUTPUT_SIZE)

        # 保存
        output_name = input_path.stem.replace("_原始", "") + "_统一.jpg"
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

        enhanced = enhance_image(img)

        w, h = enhanced.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = enhanced.crop((left, top, left + min_dim, top + min_dim))

        final = cropped.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

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
    print("噬菌体斑块照片统一处理 v3 (手动配置)")
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
        name = p.stem.replace("_原始", "")
        config = MANUAL_CONFIG.get(name)
        if process_full_plate(p, OUTPUT_DIR, config):
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
