#!/usr/bin/env python3
"""
噬菌体斑块照片统一处理脚本 v2
- 基于颜色检测培养基区域
- 统一裁剪为1/4培养皿大小
- 边缘方向统一（弧线在右上角）
- 增强对比度和清晰度
"""

import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import cv2

# 路径设置
PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 统一输出尺寸
OUTPUT_SIZE = 800


def detect_agar_region(img_array: np.ndarray) -> tuple:
    """
    检测培养基（琼脂）区域，返回 (center_x, center_y, radius)
    使用颜色检测，培养基通常是浅黄色/米色
    """
    # 转换到HSV
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    # 培养基颜色范围（浅黄色到浅绿色）
    # H: 20-50 (黄色区域)
    # S: 20-120 (低饱和度)
    # V: 150-255 (高亮度)
    lower = np.array([15, 15, 140])
    upper = np.array([55, 140, 255])

    mask = cv2.inRange(hsv, lower, upper)

    # 形态学操作清理噪点
    kernel = np.ones((25, 25), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    # 找最大轮廓（应该是培养皿）
    largest = max(contours, key=cv2.contourArea)

    # 拟合最小外接圆
    (cx, cy), radius = cv2.minEnclosingCircle(largest)

    # 验证：圆形度检查
    area = cv2.contourArea(largest)
    expected_area = np.pi * radius * radius
    circularity = area / expected_area if expected_area > 0 else 0

    if circularity < 0.5:  # 如果不够圆，可能检测错误
        # 尝试用轮廓的质心和等效半径
        M = cv2.moments(largest)
        if M["m00"] > 0:
            cx = M["m10"] / M["m00"]
            cy = M["m01"] / M["m00"]
            radius = np.sqrt(area / np.pi)

    return (int(cx), int(cy), int(radius))


def crop_quarter_with_edge(img: Image.Image, center: tuple, radius: int) -> Image.Image:
    """
    裁剪培养皿的右上四分之一区域，确保包含边缘
    边缘弧线会在右上角
    """
    cx, cy, r = center

    # 裁剪右上象限，从圆心开始
    # 稍微扩大一点以确保包含边缘
    margin = int(r * 0.05)  # 5%的边距

    left = cx
    top = cy - r - margin
    right = cx + r + margin
    bottom = cy

    # 确保不超出边界
    img_w, img_h = img.size
    left = max(0, int(left))
    top = max(0, int(top))
    right = min(img_w, int(right))
    bottom = min(img_h, int(bottom))

    cropped = img.crop((left, top, right, bottom))
    return cropped


def enhance_image(img: Image.Image) -> Image.Image:
    """增强图像"""
    # 对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # 锐度
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # 亮度
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    # 锐化滤镜
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    return img


def make_square_with_arc_topright(img: Image.Image, output_size: int) -> Image.Image:
    """
    将裁剪的图片调整为正方形，培养皿弧线在右上角
    """
    # 先调整大小
    w, h = img.size

    # 计算缩放比例，保持宽高比
    scale = output_size / max(w, h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 创建白色背景的正方形画布
    canvas = Image.new('RGB', (output_size, output_size), (255, 255, 255))

    # 将图片放在左下角（这样弧线在右上）
    paste_x = 0
    paste_y = output_size - new_h
    canvas.paste(img_resized, (paste_x, paste_y))

    return canvas


def process_full_plate(input_path: Path, output_dir: Path) -> bool:
    """处理全盘照片"""
    print(f"处理: {input_path.name}")

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img)
        print(f"  尺寸: {img.size}")

        # 检测培养基区域
        detection = detect_agar_region(img_array)

        if detection is None:
            print("  警告: 无法检测培养基，使用图片中心")
            cx, cy = img.size[0] // 2, img.size[1] // 2
            radius = min(img.size) // 3
            detection = (cx, cy, radius)
        else:
            print(f"  培养皿: 中心({detection[0]}, {detection[1]}), 半径{detection[2]}")

        # 裁剪右上四分之一
        cropped = crop_quarter_with_edge(img, detection, detection[2])

        # 增强
        enhanced = enhance_image(cropped)

        # 调整为正方形
        final = make_square_with_arc_topright(enhanced, OUTPUT_SIZE)

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

        # 增强
        enhanced = enhance_image(img)

        # 裁剪中心正方形
        w, h = enhanced.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        cropped = enhanced.crop((left, top, left + min_dim, top + min_dim))

        # 缩放到统一尺寸
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
    print("噬菌体斑块照片统一处理 v2")
    print("=" * 60)

    # 获取原始照片
    photos = list(PHOTOS_DIR.glob("*_原始.jpg"))
    print(f"\n找到 {len(photos)} 张原始照片\n")

    # 分类
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

    # 处理全盘照片
    for p in sorted(full_plates):
        if process_full_plate(p, OUTPUT_DIR):
            success += 1
        print()

    # 处理特写照片
    for p in sorted(closeups):
        if process_closeup(p, OUTPUT_DIR):
            success += 1
        print()

    print("=" * 60)
    print(f"完成: {success}/{len(photos)}")
    print(f"输出: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
