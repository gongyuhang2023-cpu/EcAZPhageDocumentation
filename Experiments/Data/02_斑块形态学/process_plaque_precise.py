#!/usr/bin/env python3
"""
噬菌体斑块照片精准统一处理
- 将培养皿缩放到统一大小
- 从统一位置裁剪，确保弧线位置完全一致
- 像坐标系一样精准对齐
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import math

PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 标准化参数
STANDARD_PLATE_DIAMETER = 1600  # 培养皿统一缩放到这个直径（像素）
OUTPUT_SIZE = 800  # 最终输出尺寸

# 每张照片的培养皿参数 (center_x, center_y, radius, quadrant)
# quadrant: 裁剪哪个象限 ("TR"=右上, "TL"=左上, "BR"=右下, "BL"=左下)
# 根据可视化结果精确测量
PLATE_CONFIG = {
    # R1 (3024x4032): 培养皿在上部，右上象限超出边界，用左下象限
    "R1": (1512, 1700, 950, "BL"),
    # R2 (3024x4032): 培养皿大，占满画面，右上象限可用
    "R2": (1512, 2016, 1400, "TR"),
    # R3 (3024x4032): 培养皿在中间，左上象限有最多斑块
    "R3": (1512, 2100, 720, "TL"),
    # W1 (3024x4032): 培养皿在上部，用左上象限
    "W1": (1512, 1680, 750, "TL"),
    # W2 (4284x5712): 照片更大，用右上象限
    "W2": (2142, 2700, 1250, "TR"),
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


def extract_and_standardize_plate(img: Image.Image, cx: int, cy: int, radius: int) -> Image.Image:
    """
    提取培养皿区域并缩放到标准大小
    """
    # 提取培养皿的外接正方形区域（加一点边距）
    margin = int(radius * 0.05)
    left = cx - radius - margin
    top = cy - radius - margin
    right = cx + radius + margin
    bottom = cy + radius + margin

    # 确保不超出边界
    left = max(0, left)
    top = max(0, top)
    right = min(img.width, right)
    bottom = min(img.height, bottom)

    # 裁剪培养皿区域
    plate_region = img.crop((left, top, right, bottom))

    # 计算缩放比例，使培养皿直径变为标准大小
    current_diameter = 2 * radius
    scale = STANDARD_PLATE_DIAMETER / current_diameter

    new_width = int(plate_region.width * scale)
    new_height = int(plate_region.height * scale)

    # 缩放
    standardized = plate_region.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return standardized


def crop_standard_quarter(standardized_plate: Image.Image, quadrant: str = "TR") -> Image.Image:
    """
    从标准化的培养皿图片中裁剪指定象限
    培养皿圆心在图片中心
    quadrant: "TR"=右上, "TL"=左上, "BR"=右下, "BL"=左下
    最后统一翻转使弧线在右上角
    """
    w, h = standardized_plate.size
    cx, cy = w // 2, h // 2

    # 根据象限确定裁剪区域
    if quadrant == "TR":  # 右上
        left, top, right, bottom = cx, 0, w, cy
        flip_h, flip_v = False, False
    elif quadrant == "TL":  # 左上
        left, top, right, bottom = 0, 0, cx, cy
        flip_h, flip_v = True, False  # 水平翻转
    elif quadrant == "BR":  # 右下
        left, top, right, bottom = cx, cy, w, h
        flip_h, flip_v = False, True  # 垂直翻转
    elif quadrant == "BL":  # 左下
        left, top, right, bottom = 0, cy, cx, h
        flip_h, flip_v = True, True  # 水平+垂直翻转
    else:
        raise ValueError(f"Unknown quadrant: {quadrant}")

    cropped = standardized_plate.crop((left, top, right, bottom))

    # 翻转使弧线统一在右上角
    if flip_h:
        cropped = cropped.transpose(Image.FLIP_LEFT_RIGHT)
    if flip_v:
        cropped = cropped.transpose(Image.FLIP_TOP_BOTTOM)

    return cropped


def finalize_output(cropped: Image.Image, output_size: int) -> Image.Image:
    """
    将裁剪结果调整到最终输出尺寸
    """
    # 直接缩放到输出尺寸
    final = cropped.resize((output_size, output_size), Image.Resampling.LANCZOS)
    return final


def process_full_plate(input_path: Path, output_dir: Path) -> bool:
    """处理全盘照片"""
    name = input_path.stem.replace("_原始", "")
    print(f"处理: {input_path.name}")

    if name not in PLATE_CONFIG:
        print(f"  警告: 没有 {name} 的配置")
        return False

    try:
        img = Image.open(input_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        cx, cy, radius, quadrant = PLATE_CONFIG[name]
        print(f"  原始尺寸: {img.size}")
        print(f"  培养皿: 中心({cx}, {cy}), 半径{radius}, 象限{quadrant}")

        # 1. 提取并标准化培养皿
        standardized = extract_and_standardize_plate(img, cx, cy, radius)
        print(f"  标准化后: {standardized.size}")

        # 2. 裁剪指定象限并翻转统一方向
        cropped = crop_standard_quarter(standardized, quadrant)
        print(f"  裁剪后: {cropped.size}")

        # 3. 增强
        enhanced = enhance_image(cropped)

        # 4. 调整到最终尺寸
        final = finalize_output(enhanced, OUTPUT_SIZE)

        # 保存
        output_name = f"{name}_统一.jpg"
        output_path = output_dir / output_name
        final.save(output_path, "JPEG", quality=95)
        print(f"  保存: {output_name} ({final.size})")

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
    print("噬菌体斑块照片精准统一处理")
    print(f"标准培养皿直径: {STANDARD_PLATE_DIAMETER}px")
    print(f"输出尺寸: {OUTPUT_SIZE}x{OUTPUT_SIZE}px")
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
