#!/usr/bin/env python3
"""
噬菌体斑块照片精准统一处理 - 1/4扇形版本

将所有培养皿照片裁剪为统一的1/4扇形，使弧线位置和曲率完全一致。

处理流程:
1. 检测培养皿 - 使用手动配置的参数 (cx, cy, radius)
2. 标准化培养皿 - 缩放到统一直径
3. 选择最佳象限 - 选择斑块密度合适的象限
4. 裁剪扇形 - 使用圆形mask只保留扇形内像素
5. 旋转统一方向 - 弧线统一在右上角
6. 输出 - 800×800像素，扇形外纯黑背景
"""

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw
import numpy as np

PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "统一裁剪"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 标准化参数
STANDARD_PLATE_DIAMETER = 1600  # 培养皿统一缩放到这个直径（像素）
OUTPUT_SIZE = 800  # 最终输出尺寸

# 每张照片的培养皿参数 (center_x, center_y, radius, quadrant)
# quadrant: 裁剪哪个象限 ("TR"=右上, "TL"=左上, "BR"=右下, "BL"=左下)
# 目标：扇形弧线正好是培养皿外边缘
PLATE_CONFIG = {
    # R1 (3024x4032): 圆心往左移约130px，往上移约100px，半径增大
    "R1": (1380, 1520, 780, "TL"),
    # R2 (3024x4032): 半径稍微增大
    "R2": (1512, 1950, 1400, "TR"),
    # R3 (3024x4032): 圆心往左移约110px，往上移约50px，半径增大
    "R3": (1400, 1650, 750, "TL"),
    # W1 (3024x4032): 圆心往左移约110px，半径增大
    "W1": (1400, 1500, 780, "TL"),
    # W2 (4284x5712): 半径增大
    "W2": (2142, 2050, 1100, "TL"),
}


def create_quarter_mask(size: int, quadrant: str) -> Image.Image:
    """
    创建1/4扇形mask

    扇形的圆心根据象限在不同角落:
    - TR (右上): 圆心在左下角 (0, size)
    - TL (左上): 圆心在右下角 (size, size)
    - BR (右下): 圆心在左上角 (0, 0)
    - BL (左下): 圆心在右上角 (size, 0)

    Args:
        size: mask的尺寸 (size x size)
        quadrant: 象限标识

    Returns:
        PIL Image (mode='L'), 扇形内为白色(255)，外部为黑色(0)
    """
    # 创建坐标网格
    y, x = np.ogrid[:size, :size]

    # 根据象限确定圆心位置
    if quadrant == "TR":  # 右上象限 -> 圆心在左下
        center_x, center_y = 0, size
    elif quadrant == "TL":  # 左上象限 -> 圆心在右下
        center_x, center_y = size, size
    elif quadrant == "BR":  # 右下象限 -> 圆心在左上
        center_x, center_y = 0, 0
    elif quadrant == "BL":  # 左下象限 -> 圆心在右上
        center_x, center_y = size, 0
    else:
        raise ValueError(f"Unknown quadrant: {quadrant}")

    # 计算每个像素到圆心的距离
    dist_from_center = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

    # 扇形半径就是size
    radius = size

    # 在扇形内的像素（距离 <= 半径）
    mask_array = (dist_from_center <= radius).astype(np.uint8) * 255

    return Image.fromarray(mask_array, mode='L')


def get_rotation_angle(quadrant: str) -> int:
    """
    获取旋转角度，使弧线统一在右上角

    目标状态: 弧线在右上角，圆心在左下角

    Args:
        quadrant: 原始象限

    Returns:
        旋转角度（逆时针为正）
    """
    # 旋转后弧线统一在右上角（圆心在左下角）
    rotation_map = {
        "TR": 0,      # 右上 -> 已经是目标状态
        "TL": -90,    # 左上 -> 顺时针旋转90度
        "BR": 90,     # 右下 -> 逆时针旋转90度
        "BL": 180,    # 左下 -> 旋转180度
    }
    return rotation_map.get(quadrant, 0)


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
    返回的图像中，培养皿圆心在图像中心
    """
    # 提取培养皿的外接正方形区域（加一点边距确保完整）
    margin = int(radius * 0.02)
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


def crop_quarter_with_mask(standardized_plate: Image.Image, quadrant: str) -> Image.Image:
    """
    从标准化的培养皿图片中裁剪指定象限的扇形

    新策略:
    1. 先把整个标准化图像变换，使目标象限移到TR位置
    2. 然后统一裁剪TR象限并应用TR的mask
    这样可以确保所有输出完全一致

    Args:
        standardized_plate: 标准化后的培养皿图像，圆心在中心
        quadrant: 要裁剪的象限

    Returns:
        裁剪后的扇形图像，弧线在右上角
    """
    # Step 1: 变换图像使目标象限移到TR位置
    if quadrant == "TR":
        transformed = standardized_plate
    elif quadrant == "TL":
        # TL -> TR: 水平翻转
        transformed = standardized_plate.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif quadrant == "BR":
        # BR -> TR: 垂直翻转
        transformed = standardized_plate.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    elif quadrant == "BL":
        # BL -> TR: 旋转180度
        transformed = standardized_plate.transpose(Image.Transpose.ROTATE_180)
    else:
        raise ValueError(f"Unknown quadrant: {quadrant}")

    # Step 2: 统一裁剪TR象限
    w, h = transformed.size
    cx, cy = w // 2, h // 2
    half_size = STANDARD_PLATE_DIAMETER // 2

    left = cx
    top = cy - half_size
    right = cx + half_size
    bottom = cy

    # 确保裁剪区域在图像范围内
    left = max(0, left)
    top = max(0, top)
    right = min(w, right)
    bottom = min(h, bottom)

    # 裁剪
    cropped = transformed.crop((left, top, right, bottom))
    cropped_size = min(cropped.size)

    # Step 3: 创建并应用TR的扇形mask（圆心在左下角）
    mask = create_quarter_mask(cropped_size, "TR")

    result = Image.new('RGB', cropped.size, (0, 0, 0))
    result.paste(cropped, (0, 0), mask)

    return result


def finalize_output(cropped: Image.Image, output_size: int) -> Image.Image:
    """
    将裁剪结果调整到最终输出尺寸，保持扇形mask
    """
    # 缩放
    resized = cropped.resize((output_size, output_size), Image.Resampling.LANCZOS)

    # 重新应用mask确保边缘清晰
    final_mask = create_quarter_mask(output_size, "TR")

    final = Image.new('RGB', (output_size, output_size), (0, 0, 0))
    final.paste(resized, (0, 0), final_mask)

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

        # 2. 裁剪扇形并旋转统一方向
        cropped = crop_quarter_with_mask(standardized, quadrant)
        print(f"  扇形裁剪后: {cropped.size}")

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
    """处理特写照片 - 裁剪中心正方形"""
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
    print("噬菌体斑块照片精准统一处理 - 1/4扇形版本")
    print(f"标准培养皿直径: {STANDARD_PLATE_DIAMETER}px")
    print(f"输出尺寸: {OUTPUT_SIZE}x{OUTPUT_SIZE}px")
    print("弧线统一在右上角，扇形外纯黑背景")
    print("=" * 60)

    photos = list(PHOTOS_DIR.glob("*_原始.jpg"))
    print(f"\n找到 {len(photos)} 张原始照片\n")

    full_plates = []
    closeups = []

    for p in photos:
        name = p.stem.replace("_原始", "")
        parts = name.split("-")
        # 判断是否为特写照片（名称中包含 -数字 格式）
        if len(parts) > 1 and parts[-1].isdigit():
            closeups.append(p)
        else:
            full_plates.append(p)

    print(f"全盘: {len(full_plates)}, 特写: {len(closeups)}\n")

    success = 0

    print("处理全盘照片（1/4扇形）:")
    print("-" * 40)
    for p in sorted(full_plates):
        if process_full_plate(p, OUTPUT_DIR):
            success += 1
        print()

    print("\n处理特写照片（正方形）:")
    print("-" * 40)
    for p in sorted(closeups):
        if process_closeup(p, OUTPUT_DIR):
            success += 1
        print()

    print("=" * 60)
    print(f"完成: {success}/{len(photos)}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("\n验证方法:")
    print("1. 检查所有全盘照片的弧线位置是否完全一致")
    print("2. 检查弧线曲率是否相同")
    print("3. 检查扇形外是否为纯黑")


if __name__ == "__main__":
    main()
