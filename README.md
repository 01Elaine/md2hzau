# md2hzau

将 Markdown 毕业论文一键转换为[华中农业大学本科毕业论文 LaTeX 模板（HZAUtex）](https://gitee.com/wagaaa/HZAUtex)格式。

Convert a Markdown thesis to the [HZAU undergraduate thesis LaTeX template (HZAUtex)](https://gitee.com/wagaaa/HZAUtex).

---

## 功能特性 Features

- 直接读取官方 `HZAUthesis.tex` preamble，不重写 LaTeX 代码（规避 Python 双反斜杠转义坑）
- 修复原版模板英文字体 bug：`\setmainfont{SimSun}` → `\setmainfont{Times New Roman}`，Abstract 英文不再出现等宽字形
- 支持：章节标题、段落、粗体/斜体/代码、Markdown 表格（→ longtable）、图片、编号/无序列表、公式（`$...$` 和 `$$...$$`）、参考文献（`[1]` 样式 → `\cite{}`）、致谢
- Reads the official `HZAUthesis.tex` preamble directly — no LaTeX code rewritten in Python
- Fixes upstream font bug: English text in Abstract now renders in Times New Roman

---

## 快速开始 Quick Start

### 1. 获取 HZAUtex 模板

```bash
git clone https://gitee.com/wagaaa/HZAUtex
```

### 2. 安装依赖

- Python 3.8+（标准库，无需额外安装）
- XeLaTeX（MiKTeX 或 TeX Live）

### 3. 运行转换

```bash
python md2hzau.py 论文.md \
    --template path/to/HZAUtex/HZAUthesis/HZAUthesis.tex \
    --title "基于深度学习的图像识别" \
    --author "张三" \
    --school "信息学院" \
    --class-num "人工智能2201班" \
    --student-id "2022317220001" \
    --instructor "李四 副教授" \
    --date "2026年6月" \
    --year 2026 \
    --img-prefix "./figures/" \
    --output HZAUthesis/my_thesis.tex
```

### 4. 编译 PDF

```bash
cd HZAUthesis
xelatex my_thesis.tex
xelatex my_thesis.tex  # 第二次编译修正交叉引用
```

---

## Markdown 论文格式约定 Markdown Conventions

### 摘要 / Abstract

```markdown
## 摘要

摘要正文...

**关键词：** 关键词1；关键词2；关键词3

## Abstract

Abstract text...

**Keywords:** keyword1; keyword2; keyword3
```

### 章节

```markdown
## 第1章 绪论

### 1.1 研究背景

#### 1.1.1 具体内容
```

### 图片

```markdown
![图片描述](./figures/fig1.png)
**图1-1** 图片标题说明
```

### 参考文献

```markdown
## 参考文献

[1] 作者. 文章标题. 期刊名, 年份, 卷(期): 页码.
[2] Author. Title. Journal, Year, Vol(No): Pages.
```

### 数学公式

行内公式：`$E = mc^2$`

独立公式：
```
$$
\mathbf{H}^{(l+1)} = \sigma\left(\hat{A}\mathbf{H}^{(l)}\mathbf{W}^{(l)}\right)
$$
```

---

## 命令行参数 CLI Options

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `md` | Markdown 源文件路径（位置参数） | — |
| `--template` | HZAUthesis.tex 路径（必填） | — |
| `--output` | 输出 .tex 路径 | `<stem>_hzau.tex` |
| `--img-prefix` | 图片路径前缀（相对于输出 .tex） | `./` |
| `--title` | 论文题目 | `论文题目` |
| `--author` | 学生姓名 | `学生姓名` |
| `--school` | 院系 | `学院` |
| `--class-num` | 专业班级 | `专业XXXX班` |
| `--student-id` | 学号 | `000000000000` |
| `--instructor` | 指导老师（含职称） | `导师姓名 副教授` |
| `--date` | 日期（封面显示） | `2026年6月` |
| `--year` | 毕业年份（页眉显示） | `2026` |

---

## 已知限制 Known Limitations

- `longtable` 宽表格在横排时可能超出页面宽度（需手动调整列宽）
- 论文里的显著性标记 `*`（如 `p<0.05*`）会直接输出为字面量 `*`，不会被解释为 Markdown 斜体
- 不支持多级编号列表（仅支持单层 `- item` 和 `（1）item`）
- 图片宽度固定为 `0.88\textwidth`，如需调整请编辑输出 .tex

---

## 协议 License

MIT © md2hzau contributors

HZAUtex 模板版权归原作者 Jerry (wagaaa) 所有。本工具仅做格式转换，不包含模板文件。

The HZAUtex template is authored by Jerry (wagaaa). This tool only converts format and does not include the template files.
