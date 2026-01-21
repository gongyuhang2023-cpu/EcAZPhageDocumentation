#!/usr/bin/env python3
"""
噬菌体斑块照片统一处理脚本
- 检测培养皿圆形边缘
- 统一裁剪为1/4培养皿大小
- 调整方向使边缘一致（边缘在右上角）
- 增强对比度和清晰度
"""

import os
import sys
from pathlib import Path
import numpy as np

# 导入图像处理库
from PIL import Image, ImageEnhance, ImageFilter
import cv2

# 路径设置
PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 统一输出尺寸（正方形）
OUTPUT_SIZE = 800


def detect_petri_dish(img_array: np.ndarray) -> tuple:
    """
    检测培养皿的圆形边缘
    返回: (center_x, center_y, radius) 或 None
    """
    # 转换为灰度图
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array

    # 高斯模糊减少噪声
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # 使用霍夫圆变换检测圆形
    # 参数调整以适应不同大小的培养皿
    height, width = gray.shape
    min_radius = min(height, width) // 4
    max_radius = min(height, width) // 2

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=min(height, width) // 2,
        param1=50,
        param2=30,
        minRadius=min_radius,
        maxRadius=max_radius
    )

    if circles is not None:
        # 取最大的圆（通常是培养皿）
        circles = np.uint16(np.around(circles))
        largest = max(circles[0], key=lambda c: c[2])
        return (int(largest[0]), int(largest[1]), int(largest[2]))

    # 如果霍夫变换失败，尝试基于颜色的方法
    return detect_by_color(img_array)


def detect_by_color(img_array: np.ndarray) -> tuple:
    """
    基于颜色检测培养皿区域（培养基通常是浅黄色）
    """
    # 转换到HSV色彩空间
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    # 定义培养基的颜色范围（浅黄色到浅绿色）
    lower = np.array([15, 20, 150])
    upper = np.array([45, 150, 255])

    # 创建掩码
    mask = cv2.inRange(hsv, lower, upper)

    # 形态学操作
    kernel = np.ones((15, 15), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 查找轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # 找最大轮廓
        largest = max(contours, key=cv2.contourArea)

        # 拟合最小外接圆
        (x, y), radius = cv2.minEnclosingCircle(largest)
        return (int(x), int(y), int(radius))

    return None


def crop_quarter_plate(img: Image.Image, center: tuple, radius: int, quadrant: str = "top_right") -> Image.Image:
    """
    裁剪培养皿的四分之一区域
    quadrant: "top_right", "top_left", "bottom_right", "bottom_left"
    统一使用右上角，这样边缘在右上角
    """
    cx, cy, r = center[0], center[1], radius

    # 计算1/4区域的裁剪框
    # 为了显示边缘，裁剪区域稍微超出圆心
    # 裁剪区域大小约为半径的1.0倍
    crop_size = int(r * 1.0)

    if quadrant == "top_right":
        # 右上角：从圆心向右上方裁剪
        left = cx
        top = cy - crop_size
        right = cx + crop_size
        bottom = cy
    elif quadrant == "top_left":
        left = cx - crop_size
        top = cy - crop_size
        right = cx
        bottom = cy
    elif quadrant == "bottom_right":
        left = cx
        top = cy
        right = cx + crop_size
        bottom = cy + crop_size
    elif quadrant == "bottom_left":
        left = cx - crop_size
        top = cy
        right = cx
        bottom = cy + crop_size

    # 确保不超出图片边界
    img_width, img_height = img.size
    left = max(0, left)
    top = max(0, top)
    right = min(img_width, right)
    bottom = min(img_height, bottom)

    # 裁剪
    cropped = img.crop((left, top, right, bottom))
    return cropped


def select_best_quadrant(img_array: np.ndarray, center: tuple, radius: int) -> str:
    """
    选择斑块最密集的象限进行裁剪
    """
    cx, cy, r = center[0], center[1], radius
    height, width = img_array.shape[:2]

    # 定义四个象限
    quadrants = {
        "top_right": (cx, 0, min(width, cx + r), cy),
        "top_left": (max(0, cx - r), 0, cx, cy),
        "bottom_right": (cx, cy, min(width, cx + r), min(height, cy + r)),
        "bottom_left": (max(0, cx - r), cy, cx, min(height, cy + r))
    }

    # 计算每个象限的"斑块得分"（基于对比度/纹理）
    scores = {}
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY) if len(img_array.shape) == 3 else img_array

    for name, (x1, y1, x2, y2) in quadrants.items():
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        if x2 > x1 and y2 > y1:
            region = gray[y1:y2, x1:x2]
            # 使用标准差作为"有内容"的指标
            scores[name] = np.std(region)
        else:
            scores[name] = 0

    # 返回得分最高的象限
    best = max(scores, key=scores.get)
    return best


def enhance_image(img: Image.Image) -> Image.Image:
    """增强图像：对比度、锐度、亮度"""
    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)

    # 增强锐度
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # 轻微增加亮度
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    # 应用锐化滤镜
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    return img


def rotate_to_standard(img: Image.Image, quadrant: str) -> Image.Image:
    """
    旋转图片使边缘统一在右上角
    """
    # 根据原始象限旋转到统一方向
    rotations = {
        "top_right": 0,      # 已经是右上角，不需要旋转
        "top_left": 90,      # 逆时针旋转90度
        "bottom_left": 180,  # 旋转180度
        "bottom_right": 270  # 顺时针旋转90度（或逆时针270度）
    }

    angle = rotations.get(quadrant, 0)
    if angle != 0:
        img = img.rotate(angle, expand=True)

    return img


def process_full_plate_photo(input_path: Path, output_dir: Path):
    """
    处理全盘照片：检测培养皿 -> 选择最佳象限 -> 裁剪 -> 旋转 -> 增强
    """
    print(f"处理全盘照片: {input_path.name}")

    try:
        # 读取图片
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_array = np.array(img)
        print(f"  尺寸: {img.size}")

        # 检测培养皿
        detection = detect_petri_dish(img_array)

        if detection is None:
            print(f"  警告: 无法检测到培养皿，使用默认中心裁剪")
            # 使用图片中心作为默认
            cx, cy = img.size[0] // 2, img.size[1] // 2
            radius = min(img.size) // 3
            detection = (cx, cy, radius)

        cx, cy, radius = detection
        print(f"  培养皿: 中心({cx}, {cy}), 半径{radius}")

        # 选择最佳象限
        quadrant = select_best_quadrant(img_array, detection, radius)
        print(f"  选择象限: {quadrant}")

        # 裁剪四分之一
        cropped = crop_quarter_plate(img, detection, radius, quadrant)

        # 旋转到标准方向（边缘在右上角）
        standardized = rotate_to_standard(cropped, quadrant)

        # 增强
        enhanced = enhance_image(standardized)

        # 调整到统一输出尺寸
        enhanced.thumbnail((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

        # 创建正方形画布
        final = Image.new('RGB', (OUTPUT_SIZE, OUTPUT_SIZE), (255, 255, 255))
        # 居中粘贴
        paste_x = (OUTPUT_SIZE - enhanced.width) // 2
        paste_y = (OUTPUT_SIZE - enhanced.height) // 2
        final.paste(enhanced, (paste_x, paste_y))

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


def process_closeup_photo(input_path: Path, output_dir: Path):
    """
    处理特写照片：调整到统一尺寸和方向
    """
    print(f"处理特写照片: {input_path.name}")

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        print(f"  尺寸: {img.size}")

        # 增强
        enhanced = enhance_image(img)

        # 裁剪中心正方形区域
        width, height = enhanced.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        cropped = enhanced.crop((left, top, left + min_dim, top + min_dim))

        # 调整到统一尺寸
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
    print("噬菌体斑块照片统一处理")
    print("- 统一裁剪为1/4培养皿")
    print("- 边缘方向统一在右上角")
    print("- 增强对比度和清晰度")
    print("=" * 60)

    # 获取所有原始照片
    original_photos = list(PHOTOS_DIR.glob("*_原始.jpg"))

    print(f"\n找到 {len(original_photos)} 张原始照片\n")

    # 分类处理
    # 带 "-5" 或 "-1-5" 等后缀的是特写照片
    full_plate_photos = []
    closeup_photos = []

    for photo in original_photos:
        name = photo.stem
        # 检查是否是特写（名字中包含 "-数字" 模式，如 R1-5, W1-1-5）
        parts = name.replace("_原始", "").split("-")
        if len(parts) > 1 and parts[-1].isdigit():
            closeup_photos.append(photo)
        else:
            full_plate_photos.append(photo)

    print(f"全盘照片: {len(full_plate_photos)} 张")
    print(f"特写照片: {len(closeup_photos)} 张\n")

    success = 0

    # 处理全盘照片
    print("-" * 40)
    print("处理全盘照片...")
    print("-" * 40)
    for photo in sorted(full_plate_photos):
        if process_full_plate_photo(photo, OUTPUT_DIR):
            success += 1
        print()

    # 处理特写照片
    print("-" * 40)
    print("处理特写照片...")
    print("-" * 40)
    for photo in sorted(closeup_photos):
        if process_closeup_photo(photo, OUTPUT_DIR):
            success += 1
        print()

    print("=" * 60)
    print(f"处理完成: {success}/{len(original_photos)} 成功")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
