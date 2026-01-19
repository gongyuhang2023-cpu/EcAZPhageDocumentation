#!/usr/bin/env python3
"""
噬菌体斑块照片处理脚本
- 转换HEIC为JPG
- 增强对比度和清晰度
- 生成适合展示的版本
"""

import os
from pathlib import Path

# 导入图像处理库
from PIL import Image, ImageEnhance, ImageFilter
import pillow_heif

# 注册HEIC格式支持
pillow_heif.register_heif_opener()

# 路径设置
INPUT_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\噬菌体照片")
OUTPUT_DIR = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\02_斑块形态学\Photos")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def enhance_image(img: Image.Image) -> Image.Image:
    """增强图像：对比度、锐度、亮度"""
    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)  # 1.0为原始，>1增强

    # 增强锐度
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # 轻微增加亮度
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    # 应用锐化滤镜
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

    return img

def process_photo(input_path: Path, output_dir: Path):
    """处理单张照片"""
    print(f"处理: {input_path.name}")

    try:
        # 读取HEIC
        img = Image.open(input_path)

        # 转换为RGB（如果需要）
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 获取原始尺寸
        orig_width, orig_height = img.size
        print(f"  原始尺寸: {orig_width}x{orig_height}")

        # 1. 保存原始转换版本（全尺寸JPG）
        output_name = input_path.stem + "_原始.jpg"
        output_path = output_dir / output_name
        img.save(output_path, "JPEG", quality=95)
        print(f"  保存原始: {output_name}")

        # 2. 增强版本
        enhanced = enhance_image(img.copy())
        output_name = input_path.stem + "_增强.jpg"
        output_path = output_dir / output_name
        enhanced.save(output_path, "JPEG", quality=95)
        print(f"  保存增强: {output_name}")

        # 3. 缩略图版本（适合PPT，max 1200px）
        thumbnail = enhanced.copy()
        thumbnail.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        output_name = input_path.stem + "_展示.jpg"
        output_path = output_dir / output_name
        thumbnail.save(output_path, "JPEG", quality=90)
        print(f"  保存展示: {output_name}")

        # 4. 如果是全板照片，尝试提取中心区域（斑块集中区）
        if orig_width > 2000 and orig_height > 2000:
            # 提取中心60%区域
            left = int(orig_width * 0.2)
            top = int(orig_height * 0.2)
            right = int(orig_width * 0.8)
            bottom = int(orig_height * 0.8)

            cropped = enhanced.crop((left, top, right, bottom))
            output_name = input_path.stem + "_裁剪.jpg"
            output_path = output_dir / output_name
            cropped.save(output_path, "JPEG", quality=95)
            print(f"  保存裁剪: {output_name}")

        return True

    except Exception as e:
        print(f"  错误: {e}")
        return False

def main():
    print("=" * 50)
    print("噬菌体斑块照片处理")
    print("=" * 50)

    # 获取所有HEIC文件
    heic_files = list(INPUT_DIR.glob("*.HEIC")) + list(INPUT_DIR.glob("*.heic"))

    print(f"找到 {len(heic_files)} 个HEIC文件\n")

    success = 0
    for heic_file in heic_files:
        if process_photo(heic_file, OUTPUT_DIR):
            success += 1
        print()

    print("=" * 50)
    print(f"处理完成: {success}/{len(heic_files)} 成功")
    print(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
