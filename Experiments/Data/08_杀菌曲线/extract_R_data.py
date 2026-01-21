#!/usr/bin/env python3
"""
从CSV中提取R菌杀菌曲线数据
"""

import re
from pathlib import Path

csv_path = Path(r"C:\Users\36094\Desktop\EcAZPhageDocumentation\Experiments\Data\08_杀菌曲线\Protocol kinetic-12h_260119R.csv")

# 读取CSV内容
with open(csv_path, 'r', encoding='latin-1') as f:
    content = f.read()

# 找到Blank 600部分
blank_start = content.find('Blank 600')
results_start = content.find('Results')

if blank_start == -1:
    print("Error: Cannot find 'Blank 600' section")
    exit(1)

blank_section = content[blank_start:results_start]
lines = blank_section.strip().split('\n')

print(f"Found {len(lines)} lines in Blank 600 section")

# 找到header行（包含Time和孔位）
header_idx = None
for i, line in enumerate(lines):
    if line.startswith('Time\t'):
        header_idx = i
        break

if header_idx is None:
    print("Error: Cannot find header line")
    exit(1)

header_line = lines[header_idx]
header = header_line.split('\t')
print(f"Header: {header[:10]}...")

# 数据行从header_idx + 1开始
data_dict = {col: [] for col in header[1:]}  # 跳过Time列

for line in lines[header_idx + 1:]:
    if not line.strip():
        continue
    values = line.split('\t')
    if len(values) < 2:
        continue

    for i, col in enumerate(header[1:], 1):
        if i < len(values):
            try:
                # 欧洲格式：逗号作为小数点
                val = float(values[i].replace(',', '.'))
                data_dict[col].append(val)
            except:
                data_dict[col].append(None)

print(f"\nTotal time points: {len(data_dict.get('B2', []))}")
print(f"Columns: {list(data_dict.keys())[:10]}...")

# 样品孔位映射
sample_wells = {
    'R_control': ['B3', 'C3', 'D3', 'E3', 'F3'],  # 排除G3异常
    'R1_MOI10': ['B4', 'C4', 'D4'],    # RP1
    'R1_MOI1': ['E4', 'F4', 'G4'],     # RP2
    'R1_MOI01': ['B5', 'C5', 'D5'],    # RP3
    'R1_MOI001': ['E5', 'F5', 'G5'],   # RP4
    'R2_MOI10': ['B6', 'C6', 'D6'],    # RP5
    'R2_MOI1': ['E6', 'F6', 'G6'],     # RP6
    'R2_MOI01': ['B7', 'C7', 'D7'],    # RP7
    'R2_MOI001': ['E7', 'F7', 'G7'],   # RP8
    'R3_MOI10': ['B8', 'C8', 'D8'],    # RP9
    'R3_MOI1': ['E8', 'F8', 'G8'],     # RP10
    'R3_MOI01': ['B9', 'C9', 'D9'],    # RP11
    'R3_MOI001': ['E9', 'F9', 'G9'],   # RP12
}

def get_mean(wells, time_idx):
    """计算指定孔位在特定时间点的平均值"""
    values = []
    for well in wells:
        if well in data_dict and time_idx < len(data_dict[well]):
            val = data_dict[well][time_idx]
            if val is not None:
                values.append(val)
    return sum(values) / len(values) if values else None

# 生成R脚本数据
print("\n" + "="*70)
print("R脚本数据:")
print("="*70)

n_timepoints = len(data_dict.get('B2', []))

for sample_name, wells in sample_wells.items():
    means = []
    for t in range(n_timepoints):
        mean_val = get_mean(wells, t)
        if mean_val is not None:
            means.append(f"{mean_val:.3f}")
        else:
            means.append("NA")

    # 每行10个数值
    print(f"\n# {sample_name} ({', '.join(wells)} mean)")
    print(f"{sample_name} <- c(", end="")
    for i in range(0, len(means), 10):
        chunk = means[i:i+10]
        if i > 0:
            print("              ", end="")
        print(", ".join(chunk), end="")
        if i + 10 < len(means):
            print(",")
        else:
            print(")")

# 验证G3异常
print("\n" + "="*70)
print("G3孔异常验证:")
print("="*70)

if 'G3' in data_dict:
    print("G3 (应排除):")
    print(f"  前5点: {[f'{v:.3f}' for v in data_dict['G3'][:5]]}")
    print(f"  末5点: {[f'{v:.3f}' for v in data_dict['G3'][-5:]]}")

print("\nB3-F3 (正常R对照):")
for well in ['B3', 'C3', 'D3', 'E3', 'F3']:
    if well in data_dict:
        print(f"  {well} 前5点: {[f'{v:.3f}' for v in data_dict[well][:5]]}")
