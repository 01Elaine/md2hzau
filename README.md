# md2hzau

**写好一个 MD 文件，运行一条命令，直接得到毕业论文 PDF。**

将 Markdown 论文一键转换为[华中农业大学本科毕业论文 LaTeX 模板（HZAUtex）](https://gitee.com/wagaaa/HZAUtex)格式。

Convert a Markdown thesis to the [HZAU undergraduate thesis LaTeX template](https://gitee.com/wagaaa/HZAUtex) with a single command — no manual editing required.

---

## 快速开始 Quick Start

### 第一步：准备 MD 文件

在 Markdown 文件最顶部写个人信息（YAML frontmatter），然后按固定结构写正文：

```markdown
---
title: 基于深度学习的图像识别研究
author: 张三
school: 信息学院
class_num: 人工智能2201班
student_id: 2022317220001
instructor: 李四 副教授
date: 2026年6月
year: 2026
---

## 摘要

摘要正文...

**关键词：** 关键词1；关键词2

## Abstract

Abstract text...

**Keywords:** keyword1; keyword2

## 第1章 绪论

### 1.1 研究背景

...

## 参考文献

[1] 参考文献1

## 致谢

致谢内容...
```

完整示例见 [`example/example.md`](example/example.md)。

### 第二步：获取 HZAUtex 模板

```bash
git clone https://gitee.com/wagaaa/HZAUtex
```

### 第三步：运行转换

```bash
python md2hzau.py 论文.md \
    --template path/to/HZAUtex/HZAUthesis/HZAUthesis.tex \
    --img-prefix "./figures/"
```

### 第四步：编译 PDF

```bash
cd path/to/HZAUtex/HZAUthesis
xelatex 论文_hzau.tex
xelatex 论文_hzau.tex   # 第二次编译修正交叉引用
```

---

## 依赖 Requirements

- Python 3.8+（标准库，**无需安装额外 Python 包**）
- XeLaTeX（MiKTeX 或 TeX Live）
- HZAUtex 模板（从 gitee.com/wagaaa/HZAUtex 获取）

---

## Markdown 格式规范

### frontmatter（必须放在文件最顶部）

| 字段 | 说明 | 示例 |
|------|------|------|
| `title` | 论文题目 | `基于深度学习的图像识别研究` |
| `author` | 学生姓名 | `张三` |
| `school` | 院系 | `信息学院` |
| `class_num` | 专业班级 | `人工智能2201班` |
| `student_id` | 学号 | `2022317220001` |
| `instructor` | 指导老师（含职称） | `李四 副教授` |
| `date` | 日期（封面显示） | `2026年6月` |
| `year` | 毕业年份（页眉年份） | `2026` |

### 章节结构

```markdown
## 第1章 绪论          ← 一级章（LaTeX \section）
### 1.1 研究背景       ← 二级节（LaTeX \subsection）
#### 1.1.1 具体内容   ← 三级节（LaTeX \subsubsection）
```

> 章节标题里的数字前缀（`第1章`、`1.1`、`1.1.1`）会被自动去掉，不会和 LaTeX 自动编号重复。

### 图片

```markdown
![图片描述](./figures/fig1.png)
**图1-1** 图片标题说明
```

### 表格（Markdown 标准语法）

```markdown
**表2-1** 超参数设置

| 参数 | 值 |
|------|----|
| 学习率 | 0.001 |
```

### 数学公式

行内：`$E = mc^2$`

独立：
```markdown
$$
\mathbf{H}^{(l+1)} = \sigma\left(\hat{A}\mathbf{H}^{(l)}\mathbf{W}^{(l)}\right)
$$
```

### 参考文献

```markdown
## 参考文献

[1] 作者. 标题. 期刊, 年份.
[2] Author. Title. Journal, Year.
```

正文引用写 `[1]`、`[2,3]`，会自动转为 `\cite{ref1}`。

---

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `md` | Markdown 源文件（位置参数） | — |
| `--template` | HZAUthesis.tex 路径（**必填**） | — |
| `--output` | 输出 .tex 路径 | `<同目录>/<stem>_hzau.tex` |
| `--img-prefix` | 图片路径前缀（相对于输出 .tex） | `./` |

---

## 已内置的模板修复

工具在转换时自动修复原版 HZAUtex 模板的以下问题（用户无感知）：

| 问题 | 修复方式 |
|------|----------|
| Abstract 英文字体显示像等宽体 | `\setmainfont{SimSun}` → `\setmainfont{Times New Roman}` |
| 目录只显示一页（75条目录截断） | 禁用 `tocloft`（与模板内置的 `titletoc` 冲突，产生1000pt不可分页大框） |
| 目录前有空白 III 页 | 去掉 `enabstract` 末尾 `\clearpage`，禁用 `\sectionbreak` |
| 正文页码重置时机错误 | 页码重置放在第一个 `\section` 前，而非 `\tableofcontents` 后 |
| 宽表格超出页面 | `tabular` + `adjustbox{max width=\linewidth}` 自动缩小 |
| `&emsp;` 变成 `\&emsp;` 双反斜杠 | HTML 实体在 `&` 转义前处理 |
| Markdown `\*` 转义星号破坏 LaTeX | 预处理 `\*`/`\**`/`\***` 再做格式替换 |

---

## 已知限制

- 宽表格（列多）可能超出页面，需手动调整
- 图片宽度固定为 `0.88\textwidth`
- 不支持多层嵌套列表（只支持单层 `- item` 和 `（1）item`）

---

## 协议 License

MIT © md2hzau contributors

HZAUtex 模板版权归原作者 Jerry (wagaaa) 所有。
