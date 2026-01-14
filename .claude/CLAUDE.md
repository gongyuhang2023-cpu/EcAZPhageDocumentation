# EcAZ噬菌体项目 - Claude工作流程

## 项目概述

从污水中分离感染EcAZ大肠杆菌的噬菌体，进行系统表征。

---

## NotebookLM使用规范

### 笔记本信息
- **ID**: ecaz噬菌体项目文献库
- **URL**: https://notebooklm.google.com/notebook/63dd9ae1-47e9-44d2-8b3b-6b9714f30bb7

### 何时使用NotebookLM

**必须使用的场景**:
1. **撰写实验方案时** - 查询标准protocol和参数
2. **遇到实验问题时** - 查找troubleshooting指南
3. **需要具体操作步骤时** - 获取详细SOP
4. **验证实验设计时** - 确认方法是否符合文献标准

### 重要：来源引用规范

**查询时必须追问来源文件**，示例：
- "这个protocol具体来源于哪个文件？请告诉我文件名和页码"

**引用格式**（在实验方案中使用）：
```
参考来源：
- Deng lab handbook.pdf, p.25-26
- 2025 student course guide_final.pdf, p.9-10
```

**禁止**：
- 不能写"参考NotebookLM"
- 必须标注具体的PDF文件名和页码

### 查询命令

```bash
cd "C:\Users\36094\.claude\skills\notebooklm"
python scripts/run.py ask_question.py --question "你的问题" --notebook-id "ecaz噬菌体项目文献库"
```

---

## Git同步

使用 `git-auto-sync` skill 一键同步。

**触发方式**：说 "git保存并推送" 或 "同步项目到远程"

**功能**：自动执行 git add . -> git commit -> git push

---

## 文献搜索与下载

使用MCP paper-search工具搜索和下载学术文献。

### 搜索文献

| 数据库 | 用途 |
|--------|------|
| PubMed | 生物医学文献 |
| arXiv | 预印本 |
| bioRxiv | 生物学预印本 |
| Google Scholar | 综合搜索 |

### 下载PDF

- arXiv和bioRxiv的文献可直接下载PDF
- 下载后保存到 References/ 文件夹

### 何时使用

1. **需要补充参考文献时** - 搜索相关方法学文献
2. **验证实验方法时** - 查找最新protocol
3. **撰写报告时** - 获取引用文献

---

## 项目文件结构

```
EcAZPhageDocumentation/
├── README.md
├── Experiments/        # 实验记录和数据
│   ├── *.md            # 每个实验一个文件
│   └── Data/           # 原始数据
├── Protocols/          # 实验方案 (PDF + md)
└── References/         # 参考文献 (PDF + md)
```

---

## 核心参考文献对照表

| 实验 | 主要参考文件 | 页码 |
|------|-------------|------|
| Plaque Assay/滴度测定 | Deng lab handbook.pdf | p.25-26 |
| Plaque Assay/滴度测定 | 2025 student course guide_final.pdf | p.9-10 |
| 噬菌体富集 | Phage Enrichment_SOP.pdf | - |
| DNA提取 | Phage DNA Extraction.pdf | - |
| 生长动力学 | Phage Growth Kinetics protocol.pdf | - |

---

## 当前状态

### 已完成
- [x] 噬菌体分离 (R1, R2, R3, W1, W2)
- [x] 斑块形态学
- [x] 宿主范围测定

### 待完成
- [ ] 滴度测定
- [ ] 一步生长曲线
- [ ] DNA提取
- [ ] 基因组测序
- [ ] TEM电镜

---

## 重要发现

- **R1**: 唯一的窄宿主范围噬菌体（只感染R菌）
- **R2**: 产生浑浊斑块（可能是温和性噬菌体）
- **R3**: 滴度最高，需要高稀释度

---

*更新日期: 2025-01-14*
