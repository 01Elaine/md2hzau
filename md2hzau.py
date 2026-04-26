#!/usr/bin/env python3
"""
md2hzau.py — Convert a Markdown thesis to HZAUtex LaTeX template
             将 Markdown 论文转换为华中农业大学毕业论文 HZAUtex 模板

Usage 用法:
    python md2hzau.py thesis.md \\
        --template path/to/HZAUthesis/HZAUthesis.tex \\
        --title "论文题目" \\
        --author "学生姓名" \\
        --school "院系" \\
        --class-num "专业班级" \\
        --student-id "学号" \\
        --instructor "指导老师 职称" \\
        --date "2026年6月" \\
        --year 2026 \\
        --img-prefix "./figures/" \\
        --output output/thesis_hzau.tex

依赖 Requirements:
    Python 3.8+, XeLaTeX (MiKTeX or TeX Live), HZAUtex template
    HZAUtex: https://gitee.com/wagaaa/HZAUtex

作者 Author: md2hzau contributors
协议 License: MIT
"""

import argparse
import re
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="Convert Markdown thesis to HZAUtex LaTeX template"
    )
    p.add_argument("md", help="Markdown source file (.md)")
    p.add_argument("--template", required=True,
                   help="Path to HZAUthesis.tex (from gitee.com/wagaaa/HZAUtex)")
    p.add_argument("--output",
                   help="Output .tex file (default: <input_stem>_hzau.tex beside --template)")
    p.add_argument("--img-prefix", default="./",
                   help="Image path prefix in LaTeX, relative to output .tex (default: ./)")
    p.add_argument("--title",      default="论文题目",      help="论文题目")
    p.add_argument("--author",     default="学生姓名",      help="学生姓名")
    p.add_argument("--school",     default="学院",          help="院系")
    p.add_argument("--class-num",  default="专业XXXX班",    help="专业班级", dest="class_num")
    p.add_argument("--student-id", default="000000000000",  help="学号", dest="student_id")
    p.add_argument("--instructor", default="导师姓名 副教授", help="指导教师姓名及职称")
    p.add_argument("--date",       default="2026年6月",     help="日期（封面）")
    p.add_argument("--year",       type=int, default=2026,  help="毕业年份（页眉）")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Preamble patching — read the original HZAUthesis.tex, replace only what must change
# ─────────────────────────────────────────────────────────────────────────────

def _replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        print(f"  WARNING: [{label}] not found, skipped", file=sys.stderr)
        return text
    print(f"  OK  [{label}]")
    return text.replace(old, new, 1)


def patch_preamble(preamble: str, args) -> str:
    print("Patching preamble ...")

    # 1. Header year (detect automatically)
    for y in range(2018, 2031):
        marker = f"{y}\\hspace{{0.5em}}届"
        if marker in preamble:
            preamble = _replace(preamble, marker,
                                f"{args.year}\\hspace{{0.5em}}届",
                                f"页眉年份 {y}→{args.year}")
            break
    else:
        print("  WARNING: [页眉年份] not found", file=sys.stderr)

    # 2. English mainfont: SimSun → Times New Roman
    #    The original template sets \setmainfont{SimSun}, which makes ASCII chars
    #    in the Abstract render with SimSun's monospaced-looking glyphs.
    #    CJK fonts are independently controlled by xeCJK, so this change is safe.
    preamble = _replace(preamble,
        r"\setmainfont{SimSun}",
        r"\setmainfont{Times New Roman}",
        "mainfont → Times New Roman (fix Abstract English font)")

    # 3. natbib numeric style
    preamble = _replace(preamble,
        r"\usepackage{natbib}",
        r"\usepackage[numbers,sort&compress]{natbib}",
        "natbib → numbers,sort&compress")

    # 4. Extra packages: longtable / array / multirow (for tables)
    preamble = _replace(preamble,
        r"\usepackage{booktabs}",
        r"\usepackage{booktabs}" + "\n" + r"\usepackage{longtable,array,multirow}",
        "inject longtable/array/multirow")

    # 5. Personal information
    personal = [
        (r"\title{毕业论文题目}",          f"\\title{{{args.title}}}"),
        (r"\def\school{生命科学技术学院}",  f"\\def\\school{{{args.school}}}"),
        (r"\def\classnum{生命科学1901班}",  f"\\def\\classnum{{{args.class_num}}}"),
        (r"\author{学生姓名}",             f"\\author{{{args.author}}}"),
        (r"\def\stunum{2019305190201}",    f"\\def\\stunum{{{args.student_id}}}"),
        (r"\def\instructor{导师姓名}",     f"\\def\\instructor{{{args.instructor}}}"),
        (r"\date{\today}",                 f"\\date{{{args.date}}}"),
    ]
    for old, new in personal:
        preamble = _replace(preamble, old, new, old[:40])

    print()
    return preamble


# ─────────────────────────────────────────────────────────────────────────────
# Inline formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

def cell_escape(s: str) -> str:
    parts = re.split(r"(\$[^$]*\$)", s)
    result = []
    for p in parts:
        if p.startswith("$"):
            result.append(p)
        else:
            p = p.replace("±", r"$\pm$")
            p = p.replace("≤", r"$\leq$")
            p = p.replace("≥", r"$\geq$")
            p = p.replace("→", r"$\rightarrow$")
            p = p.replace("✓", r"\checkmark{}")
            p = p.replace("✗", r"$\times$")
            result.append(p)
    return "".join(result)


def inline_fmt(s: str) -> str:
    # Pre-process Markdown backslash-escaped stars in longest-first order
    # to avoid partial substitution. \* means a literal * in Markdown.
    _S3, _S2, _S1 = "\x00S3\x00", "\x00S2\x00", "\x00S1\x00"
    s = s.replace("\\***", _S3)
    s = s.replace("\\**",  _S2)
    s = s.replace("\\*",   _S1)

    parts = re.split(r"(\$[^$\n]*\$)", s)
    escaped = []
    for p in parts:
        if p.startswith("$"):
            escaped.append(p)
        else:
            p = p.replace("&", r"\&")
            p = p.replace("%", r"\%")
            escaped.append(p)
    s = "".join(escaped)

    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    # Only treat * as italic when it directly touches the surrounded text
    # (no space after opening * and no space before closing *).
    # This prevents significance markers like "p<0.05*" from triggering italic.
    s = re.sub(r"\*(?!\*|\s)(.+?)(?<!\s)\*(?!\*)", r"\\textit{\1}", s)
    s = re.sub(r"`([^`]+)`", r"\\texttt{\1}", s)

    def _protect_underscore(text: str) -> str:
        chunks = re.split(r"(\\texttt\{[^}]*\})", text)
        out = []
        for chunk in chunks:
            if chunk.startswith(r"\texttt"):
                out.append(chunk)
            else:
                sub = re.split(r"(\$[^$\n]*\$)", chunk)
                for sp in sub:
                    out.append(sp if sp.startswith("$") else sp.replace("_", r"\_"))
        return "".join(out)

    s = _protect_underscore(s)

    # Restore escaped stars as literal * characters
    s = s.replace(_S3, "***")
    s = s.replace(_S2, "**")
    s = s.replace(_S1, "*")
    return s


def process_ref_inline(s: str) -> str:
    def repl(m):
        nums = [n.strip() for n in m.group(1).split(",")]
        if len(nums) == 2 and "0" in nums:
            return m.group(0)
        keys = ",".join("ref" + n for n in nums)
        return r"\cite{" + keys + "}"
    parts = re.split(r"(\$[^$\n]*\$)", s)
    result = []
    for p in parts:
        result.append(p if p.startswith("$") else re.sub(r"\[(\d+(?:,\s*\d+)*)\]", repl, p))
    return "".join(result)


def convert_table(table_lines: list) -> str:
    rows = []
    for l in table_lines:
        l = l.strip()
        if re.match(r"^\|[-| :]+\|$", l):
            continue
        cells = [c.strip() for c in l.strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return ""
    ncols = len(rows[0])
    tex = [r"\begin{longtable}{" + "|".join(["l"] * ncols) + "}", r"\toprule"]
    tex.append(" & ".join(r"\textbf{" + cell_escape(inline_fmt(c.strip("*"))) + "}"
                          for c in rows[0]) + r" \\")
    tex.append(r"\midrule")
    tex.append(r"\endhead")
    for row in rows[1:]:
        while len(row) < ncols:
            row.append("")
        tex.append(" & ".join(cell_escape(inline_fmt(c)) for c in row) + r" \\")
    tex.append(r"\bottomrule")
    tex.append(r"\end{longtable}")
    return "\n".join(tex)


# ─────────────────────────────────────────────────────────────────────────────
# Abstract extraction
# ─────────────────────────────────────────────────────────────────────────────

def extract_abstracts(lines: list):
    cn_text, cn_kw = [], ""
    en_text, en_kw = [], ""
    in_cn = in_en = False
    for l in lines:
        s = l.strip()
        if s == "## 摘要":
            in_cn = True; continue
        if s == "## Abstract":
            in_cn = False; in_en = True; continue
        if re.match(r"^## [^摘A]", s):
            in_cn = in_en = False; continue
        if in_cn:
            if s.startswith("**关键词"):
                cn_kw = re.sub(r"\*\*关键词[：:]\*\*\s*", "", s)
            elif s in ("---",) or s.startswith("**Key"):
                pass
            else:
                cn_text.append(inline_fmt(s))
        if in_en:
            if s.startswith("**Keywords"):
                en_kw = re.sub(r"\*\*Keywords[：:]\*\*\s*", "", s)
            elif s == "---":
                pass
            elif s:
                en_text.append(inline_fmt(s))
    return cn_text, cn_kw, en_text, en_kw


# ─────────────────────────────────────────────────────────────────────────────
# Main body conversion
# ─────────────────────────────────────────────────────────────────────────────

def convert_body(lines: list, img_prefix: str) -> list:
    output = []
    in_biblio = in_thankpage = in_table = False
    table_lines = []
    i = 0
    body_started = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not body_started:
            if re.match(r"^## [第1]", stripped):
                body_started = True
            else:
                i += 1
                continue

        if stripped == "---":
            if in_biblio:
                output.append(r"\end{thebibliography}")
                in_biblio = False
            i += 1
            continue

        m = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if m:
            if in_biblio:
                output.append(r"\end{thebibliography}")
                in_biblio = False
            level = len(m.group(1))
            raw_title = m.group(2)
            title = process_ref_inline(inline_fmt(raw_title))
            if "参考文献" in title:
                output.append(r"\begin{thebibliography}{99}")
                in_biblio = True
                i += 1
                continue
            if "致谢" in title:
                output.append(r"\begin{thankpage}")
                in_thankpage = True
                i += 1
                continue
            title_clean = process_ref_inline(
                inline_fmt(re.sub(r"^第\d+章\s*", "", raw_title)))
            cmds = {2: "section", 3: "subsection", 4: "subsubsection"}
            lbl = re.sub(r"[^\w]", "-", raw_title)[:40]
            output.append(f"\\{cmds.get(level, 'paragraph')}{{{title_clean}}}\\label{{{lbl}}}")
            i += 1
            continue

        if in_biblio:
            if not stripped:
                i += 1
                continue
            m_ref = re.match(r"^\[(\d+)\]\s+(.+)$", stripped)
            if m_ref:
                output.append(
                    f"\\bibitem{{ref{m_ref.group(1)}}} {inline_fmt(m_ref.group(2))}")
                i += 1
                continue
            output.append(r"\end{thebibliography}")
            in_biblio = False
            i += 1
            continue

        if stripped.startswith("|"):
            if not in_table:
                in_table = True
                table_lines = [stripped]
            else:
                table_lines.append(stripped)
            i += 1
            next_s = lines[i].strip() if i < len(lines) else ""
            if not next_s.startswith("|"):
                output.append(convert_table(table_lines))
                in_table = False
                table_lines = []
            continue

        m_img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if m_img:
            alt = m_img.group(1)
            fname = Path(m_img.group(2)).name
            cap = alt
            if i + 1 < len(lines):
                next_l = lines[i + 1].strip()
                m_cap = re.match(r"^\*\*(图\d+[\.\d]*)\*\*\s*(.*)", next_l)
                if m_cap:
                    cap = m_cap.group(1) + " " + inline_fmt(m_cap.group(2))
                    i += 1
            lbl = "fig:" + re.sub(r"[^\w]", "-", alt)[:30]
            output += [r"\begin{figure}[H]", r"  \centering",
                       f"  \\includegraphics[width=0.88\\textwidth]{{{img_prefix}{fname}}}",
                       f"  \\caption{{{cap}}}", f"  \\label{{{lbl}}}", r"\end{figure}"]
            i += 1
            continue

        if re.match(r"^\*\*图\d", stripped):
            i += 1
            continue

        m_tbl_cap = re.match(r"^\*\*(表[\d\.]+)\s*(.*?)\*\*", stripped)
        if m_tbl_cap:
            cap_text = m_tbl_cap.group(1) + " " + inline_fmt(m_tbl_cap.group(2))
            output.append(r"\noindent\textbf{" + cap_text + "}")
            output.append("")
            i += 1
            continue

        m_enum = re.match(r"^[（(](\d+)[）)]\s*(.+)$", stripped)
        if m_enum:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                mm = re.match(r"^[（(](\d+)[）)]\s*(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(2)))
                    i += 1
                else:
                    break
            output.append(r"\begin{enumerate}[label=（\arabic*）]")
            for it in items:
                output.append(r"  \item " + process_ref_inline(it))
            output.append(r"\end{enumerate}")
            continue

        m_bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if m_bullet:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                mm = re.match(r"^[-*]\s+(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(1)))
                    i += 1
                else:
                    break
            output.append(r"\begin{itemize}")
            for it in items:
                output.append(r"  \item " + process_ref_inline(it))
            output.append(r"\end{itemize}")
            continue

        if stripped == "":
            output.append("")
            i += 1
            continue

        output.append(process_ref_inline(inline_fmt(stripped)) + "\n")
        i += 1

    if in_thankpage:
        output.append(r"\end{thankpage}")
    if in_biblio:
        output.append(r"\end{thebibliography}")
    return output


def post_process(result: str) -> str:
    result = re.sub(r"\$\$([^$]+?)\$\$",
                    lambda m: "\\[\n" + m.group(1).strip() + "\n\\]", result)
    result = result.replace("&emsp;", r"\hspace{1em}")
    result = result.replace("&nbsp;", "~")
    result = re.sub(r"\\texttt\{([^}]+)\}",
                    lambda m: r"\texttt{" + m.group(1).replace("_", r"\_") + "}", result)
    result = re.sub(r"\n{4,}", "\n\n\n", result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    src_path = Path(args.md)
    template_path = Path(args.template)

    if not src_path.exists():
        print(f"ERROR: Markdown file not found: {src_path}", file=sys.stderr)
        sys.exit(1)
    if not template_path.exists():
        print(f"ERROR: Template file not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    dst_path = Path(args.output) if args.output else \
        template_path.parent / (src_path.stem + "_hzau.tex")

    lines = src_path.read_text(encoding="utf-8").splitlines()
    template_text = template_path.read_text(encoding="utf-8")

    _BEGIN_DOC = r"\begin{document}"
    if _BEGIN_DOC not in template_text:
        print(f"ERROR: {_BEGIN_DOC!r} not found in template", file=sys.stderr)
        sys.exit(1)
    preamble = template_text[:template_text.index(_BEGIN_DOC)]
    preamble = patch_preamble(preamble, args)

    cn_text, cn_kw, en_text, en_kw = extract_abstracts(lines)

    output = [preamble, _BEGIN_DOC, "",
              r"\maketitle", "",
              r"\setcounter{page}{1}",
              r"\renewcommand{\thepage}{\Roman{page}}",
              r"\makestatement{2}{" + str(args.year) + "}", ""]

    output += [r"\setcounter{page}{1}",
               r"\renewcommand{\thepage}{\Roman{page}}",
               r"\begin{cnabstract}{" + cn_kw + "}"]
    output += [l + "\n" for l in cn_text if l]
    output += [r"\end{cnabstract}", ""]

    output += [r"\begin{enabstract}{" + en_kw + "}"]
    output += [l + "\n" for l in en_text if l]
    output += [r"\end{enabstract}", ""]

    output += [r"\vspace*{-1em}", r"\tableofcontents", r"\thispagestyle{main}",
               r"\clearpage", r"\setcounter{page}{1}",
               r"\renewcommand{\thepage}{\arabic{page}}", "", r"\seccontent", ""]

    output.extend(convert_body(lines, args.img_prefix))
    output.append(r"\end{document}")

    result = post_process("\n".join(output))
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(result, encoding="utf-8")
    print(f"Done: {dst_path}  ({len(result.splitlines())} lines)")


if __name__ == "__main__":
    main()
