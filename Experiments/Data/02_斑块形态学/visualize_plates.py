#!/usr/bin/env python3
"""
可视化培养皿位置，帮助精确测量参数
在原始照片上画出培养皿的圆圈和裁剪区域
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PHOTOS_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")
OUTPUT_DIR = PHOTOS_DIR / "可视化"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 当前配置（根据可视化结果调整）
# 格式: (center_x, center_y, radius)
# 目标：红圈正好贴合培养皿外边缘
PLATE_CONFIG = {
    # R1 (3024x4032): 圆心往左移约130px，往上移约100px，半径增大
    "R1": (1380, 1520, 780),
    # R2 (3024x4032): 半径稍微增大
    "R2": (1512, 1950, 1400),
    # R3 (3024x4032): 圆心往左移约110px，往上移约50px，半径增大
    "R3": (1400, 1650, 750),
    # W1 (3024x4032): 圆心往左移约110px，半径增大
    "W1": (1400, 1500, 780),
    # W2 (4284x5712): 半径增大
    "W2": (2142, 2050, 1100),
}


def visualize_plate(input_path: Path, output_dir: Path):
    """在原始照片上标注培养皿位置"""
    name = input_path.stem.replace("_原始", "")

    if name not in PLATE_CONFIG:
        return

    img = Image.open(input_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 缩小以便查看
    scale = 0.25
    small = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)

    draw = ImageDraw.Draw(small)

    cx, cy, radius = PLATE_CONFIG[name]
    cx_s, cy_s, r_s = int(cx * scale), int(cy * scale), int(radius * scale)

    # 画培养皿圆圈（红色）
    draw.ellipse([cx_s - r_s, cy_s - r_s, cx_s + r_s, cy_s + r_s], outline='red', width=3)

    # 画圆心（红点）
    draw.ellipse([cx_s - 5, cy_s - 5, cx_s + 5, cy_s + 5], fill='red')

    # 画右上象限裁剪区域（绿色）
    draw.rectangle([cx_s, cy_s - r_s, cx_s + r_s, cy_s], outline='green', width=2)

    # 画左下象限（蓝色，备选）
    draw.rectangle([cx_s - r_s, cy_s, cx_s, cy_s + r_s], outline='blue', width=2)

    # 标注信息
    info = f"{name}: center=({cx},{cy}), r={radius}"
    draw.text((10, 10), info, fill='yellow')
    draw.text((10, 30), f"Image: {img.width}x{img.height}", fill='yellow')
    draw.text((10, 50), "Red=plate, Green=top-right, Blue=bottom-left", fill='yellow')

    output_path = output_dir / f"{name}_标注.jpg"
    small.save(output_path, "JPEG", quality=90)
    print(f"保存: {output_path.name}")


def main():
    print("可视化培养皿位置")
    print("=" * 40)

    for p in sorted(PHOTOS_DIR.glob("*_原始.jpg")):
        name = p.stem.replace("_原始", "")
        if "-" not in name:  # 只处理全盘照片
            visualize_plate(p, OUTPUT_DIR)


if __name__ == "__main__":
    main()
