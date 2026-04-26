#!/usr/bin/env python3
"""
md2hzau — Markdown → 华中农业大学本科毕业论文 LaTeX 模板（HZAUtex）

核心宗旨：用户只写一个 MD 文件（按照模板格式，在 frontmatter 里填好个人信息），
         运行一条命令，直接生成可编译的 LaTeX 文件，不需要再做任何其他修改。

用法:
    python md2hzau.py 论文.md --template path/to/HZAUthesis/HZAUthesis.tex

MD 文件格式（在文件头写 YAML frontmatter）:
    ---
    title: 论文题目
    author: 姓名
    school: 院系
    class_num: 专业班级
    student_id: 学号
    instructor: 导师姓名 副教授
    date: 2026年6月
    year: 2026
    ---

    ## 摘要
    ...（见 example/example.md）

HZAUtex 模板: https://gitee.com/wagaaa/HZAUtex
License: MIT
"""

import argparse
import re
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# 1. CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert Markdown thesis to HZAU LaTeX template (no extra edits needed)"
    )
    p.add_argument("md", help="Markdown source file (.md)")
    p.add_argument("--template", required=True,
                   help="Path to HZAUthesis.tex (from gitee.com/wagaaa/HZAUtex)")
    p.add_argument("--output",
                   help="Output .tex file (default: <input_stem>_hzau.tex beside --template)")
    p.add_argument("--img-prefix", default="./",
                   help="Image path prefix in LaTeX, relative to output .tex (default: ./)",
                   dest="img_prefix")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Frontmatter parsing (no external deps)
# ─────────────────────────────────────────────────────────────────────────────

_FM_DEFAULTS = {
    "title":      "论文题目",
    "author":     "学生姓名",
    "school":     "学院",
    "class_num":  "专业XXXX班",
    "student_id": "000000000000",
    "instructor": "导师姓名 副教授",
    "date":       "2026年6月",
    "year":       "2026",
}

def parse_frontmatter(text: str):
    """
    Extract YAML-like frontmatter from Markdown.
    Returns (info_dict, remaining_markdown_text).
    Frontmatter must be between two '---' lines at the top of the file.
    """
    lines = text.splitlines()
    info = dict(_FM_DEFAULTS)

    if not lines or lines[0].strip() != "---":
        return info, text

    end = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break

    if end is None:
        return info, text

    for line in lines[1:end]:
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if key and val:
                info[key] = val

    return info, "\n".join(lines[end + 1:])


# ─────────────────────────────────────────────────────────────────────────────
# 3. Preamble patching — read original HZAUthesis.tex, replace only what must change
# ─────────────────────────────────────────────────────────────────────────────

def _replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        print(f"  WARNING: [{label}] not found, skipped", file=sys.stderr)
        return text
    print(f"  OK  [{label}]")
    return text.replace(old, new, 1)


def patch_preamble(preamble: str, info: dict) -> str:
    print("Patching preamble ...")
    year = info.get("year", "2026")

    # (a) Header year: detect original year and replace
    for y in range(2018, 2031):
        marker = f"{y}\\hspace{{0.5em}}届"
        if marker in preamble:
            preamble = _replace(preamble, marker,
                                f"{year}\\hspace{{0.5em}}届",
                                f"页眉年份 {y}→{year}")
            break
    else:
        print("  WARNING: [页眉年份] not found", file=sys.stderr)

    # (b) Fix English font in Abstract: SimSun → Times New Roman
    #     Original template sets \setmainfont{SimSun}, making ASCII chars
    #     in Abstract render with SimSun's monospaced-looking glyphs.
    #     CJK fonts are independently controlled by xeCJK — this change is safe.
    preamble = _replace(preamble,
        r"\setmainfont{SimSun}",
        r"\setmainfont{Times New Roman}",
        "mainfont → Times New Roman (fix Abstract English font)")

    # (c) natbib: numeric citation style [1][2]...
    preamble = _replace(preamble,
        r"\usepackage{natbib}",
        r"\usepackage[numbers,sort&compress]{natbib}",
        "natbib → numbers,sort&compress")

    # (d) Inject extra packages needed for tables
    preamble = _replace(preamble,
        r"\usepackage{booktabs}",
        r"\usepackage{booktabs}" + "\n" + r"\usepackage{longtable,array,multirow}",
        "inject longtable/array/multirow")

    # (e) Disable \sectionbreak (= \clearpage in original).
    #     We instead inject \clearpage manually before each \section in the body.
    #     This prevents \tableofcontents (which calls \section* internally) from
    #     triggering an unwanted page break that creates a blank TOC page.
    preamble = _replace(preamble,
        r"\newcommand{\sectionbreak}{\clearpage}",
        r"\newcommand{\sectionbreak}{}",
        "disable sectionbreak (moved to Python body-converter)")

    # (f) Remove trailing \clearpage from enabstract.
    #     The original ends with \clearpage inside the environment. When combined
    #     with \tableofcontents (which itself has page-break penalty logic), this
    #     caused a blank page III. We let \tableofcontents handle its own paging.
    preamble = _replace(preamble,
        "\\enkeyword}\n\t\\clearpage\n}",
        "\\enkeyword}\n}",
        "remove enabstract trailing clearpage (fixes blank page III)")

    # (g) Personal information
    personal = [
        (r"\title{毕业论文题目}",          f"\\title{{{info['title']}}}"),
        (r"\def\school{生命科学技术学院}",  f"\\def\\school{{{info['school']}}}"),
        (r"\def\classnum{生命科学1901班}",  f"\\def\\classnum{{{info['class_num']}}}"),
        (r"\author{学生姓名}",             f"\\author{{{info['author']}}}"),
        (r"\def\stunum{2019305190201}",    f"\\def\\stunum{{{info['student_id']}}}"),
        (r"\def\instructor{导师姓名}",     f"\\def\\instructor{{{info['instructor']}}}"),
        (r"\date{\today}",                 f"\\date{{{info['date']}}}"),
    ]
    for old, new in personal:
        preamble = _replace(preamble, old, new, old[:40])

    # (h) Override tocloft's \@cftmaketoctitle to remove \addpenalty\@secpenalty.
    #     That penalty (= -300, "welcome page break here") on an otherwise-empty
    #     page causes LaTeX to push the entire TOC block to the next page, leaving
    #     a blank page III. Removing it lets LaTeX keep the TOC on the same page.
    preamble += r"""
% md2hzau: remove \addpenalty\@secpenalty from tocloft \@cftmaketoctitle
% to prevent a blank page before the table of contents.
\makeatletter
\renewcommand{\@cftmaketoctitle}{%
  \if@cfthaschapter
    \vspace*{\cftbeforetoctitleskip}%
  \else
    \vspace{\cftbeforetoctitleskip}%
  \fi
  \@cftpagestyle
  {\interlinepenalty\@M
  {\cfttoctitlefont\contentsname}{\cftaftertoctitle}%
  \cftmarktoc
  \par\nobreak
  \vskip \cftaftertoctitleskip
  \@afterheading}}
\makeatother
"""
    print()
    return preamble


# ─────────────────────────────────────────────────────────────────────────────
# 4. Inline formatting helpers
# ─────────────────────────────────────────────────────────────────────────────

def cell_escape(s: str) -> str:
    parts = re.split(r"(\$[^$]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(p)
        else:
            p = p.replace("±", r"$\pm$").replace("≤", r"$\leq$") \
                 .replace("≥", r"$\geq$").replace("→", r"$\rightarrow$") \
                 .replace("✓", r"\checkmark{}").replace("✗", r"$\times$")
            out.append(p)
    return "".join(out)


def inline_fmt(s: str) -> str:
    # Pre-process Markdown backslash-escaped stars (\*, \**, \***).
    # Must process longest-first to avoid partial substitution.
    # Markdown \* means a literal * (also valid in LaTeX body text).
    _S3, _S2, _S1 = "\x00S3\x00", "\x00S2\x00", "\x00S1\x00"
    s = s.replace("\\***", _S3).replace("\\**", _S2).replace("\\*", _S1)

    parts = re.split(r"(\$[^$\n]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(p)
        else:
            out.append(p.replace("&", r"\&").replace("%", r"\%"))
    s = "".join(out)

    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    # Italic: only when * directly touches text (no space after opening *).
    # This prevents significance markers like "p<0.05*" from triggering italic.
    s = re.sub(r"\*(?!\*|\s)(.+?)(?<!\s)\*(?!\*)", r"\\textit{\1}", s)
    s = re.sub(r"`([^`]+)`", r"\\texttt{\1}", s)

    def _guard_underscore(text: str) -> str:
        chunks = re.split(r"(\\texttt\{[^}]*\})", text)
        result = []
        for chunk in chunks:
            if chunk.startswith(r"\texttt"):
                result.append(chunk)
            else:
                sub = re.split(r"(\$[^$\n]*\$)", chunk)
                for sp in sub:
                    result.append(sp if sp.startswith("$") else sp.replace("_", r"\_"))
        return "".join(result)

    s = _guard_underscore(s)
    s = s.replace(_S3, "***").replace(_S2, "**").replace(_S1, "*")
    return s


def process_refs(s: str) -> str:
    """Convert [1], [2,3] → \\cite{ref1}, \\cite{ref2,ref3}."""
    def repl(m):
        nums = [n.strip() for n in m.group(1).split(",")]
        if len(nums) == 2 and "0" in nums:
            return m.group(0)
        return r"\cite{" + ",".join("ref" + n for n in nums) + "}"
    parts = re.split(r"(\$[^$\n]*\$)", s)
    return "".join(
        p if p.startswith("$") else re.sub(r"\[(\d+(?:,\s*\d+)*)\]", repl, p)
        for p in parts
    )


def convert_table(table_lines: list) -> str:
    rows = []
    for l in table_lines:
        l = l.strip()
        if re.match(r"^\|[-| :]+\|$", l):
            continue
        rows.append([c.strip() for c in l.strip("|").split("|")])
    if not rows:
        return ""
    ncols = len(rows[0])
    tex = [r"\begin{longtable}{" + "|".join(["l"] * ncols) + "}", r"\toprule"]
    tex.append(" & ".join(
        r"\textbf{" + cell_escape(inline_fmt(c.strip("*"))) + "}"
        for c in rows[0]
    ) + r" \\")
    tex += [r"\midrule", r"\endhead"]
    for row in rows[1:]:
        while len(row) < ncols:
            row.append("")
        tex.append(" & ".join(cell_escape(inline_fmt(c)) for c in row) + r" \\")
    tex += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(tex)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Abstract extraction
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
# 6. Body conversion (state machine)
# ─────────────────────────────────────────────────────────────────────────────

def convert_body(lines: list, img_prefix: str) -> list:
    output = []
    in_biblio = in_thankpage = in_table = False
    table_lines = []
    i = 0
    body_started = False

    while i < len(lines):
        stripped = lines[i].strip()

        if not body_started:
            if re.match(r"^## [第1]", stripped):
                body_started = True
            else:
                i += 1; continue

        if stripped == "---":
            if in_biblio:
                output.append(r"\end{thebibliography}")
                in_biblio = False
            i += 1; continue

        m = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if m:
            if in_biblio:
                output.append(r"\end{thebibliography}")
                in_biblio = False
            level = len(m.group(1))
            raw = m.group(2)
            title = process_refs(inline_fmt(raw))
            if "参考文献" in title:
                output.append(r"\begin{thebibliography}{99}")
                in_biblio = True; i += 1; continue
            if "致谢" in title:
                output.append(r"\begin{thankpage}")
                in_thankpage = True; i += 1; continue

            # Strip chapter/section number prefix to avoid double-numbering
            # e.g. "第1章 绪论" → "绪论",  "1.1 研究背景" → "研究背景"
            clean = re.sub(r"^第\d+章\s*", "", raw)
            clean = re.sub(r"^\d[\d\.]*[\s　]+", "", clean)
            clean = process_refs(inline_fmt(clean))
            cmds = {2: "section", 3: "subsection", 4: "subsubsection"}
            cmd = cmds.get(level, "paragraph")
            lbl = re.sub(r"[^\w]", "-", raw)[:40]
            # \sectionbreak is disabled; manually clearpage before each \section
            if cmd == "section":
                output.append(r"\clearpage")
            output.append(f"\\{cmd}{{{clean}}}\\label{{{lbl}}}")
            i += 1; continue

        if in_biblio:
            if not stripped:
                i += 1; continue
            m_ref = re.match(r"^\[(\d+)\]\s+(.+)$", stripped)
            if m_ref:
                output.append(f"\\bibitem{{ref{m_ref.group(1)}}} {inline_fmt(m_ref.group(2))}")
                i += 1; continue
            output.append(r"\end{thebibliography}")
            in_biblio = False; i += 1; continue

        # Table
        if stripped.startswith("|"):
            if not in_table:
                in_table = True; table_lines = [stripped]
            else:
                table_lines.append(stripped)
            i += 1
            next_s = lines[i].strip() if i < len(lines) else ""
            if not next_s.startswith("|"):
                output.append(convert_table(table_lines))
                in_table = False; table_lines = []
            continue

        # Figure
        m_img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if m_img:
            alt = m_img.group(1)
            fname = Path(m_img.group(2)).name
            cap = alt
            if i + 1 < len(lines):
                next_l = lines[i + 1].strip()
                m_cap = re.match(r"^\*\*(图\d+[\.\d-]*)\*\*\s*(.*)", next_l)
                if m_cap:
                    cap = m_cap.group(1) + " " + inline_fmt(m_cap.group(2))
                    i += 1
            lbl = "fig:" + re.sub(r"[^\w]", "-", alt)[:30]
            output += [r"\begin{figure}[H]", r"  \centering",
                       f"  \\includegraphics[width=0.88\\textwidth]{{{img_prefix}{fname}}}",
                       f"  \\caption{{{cap}}}", f"  \\label{{{lbl}}}", r"\end{figure}"]
            i += 1; continue

        if re.match(r"^\*\*图\d", stripped):
            i += 1; continue

        m_tbl_cap = re.match(r"^\*\*(表[\d\.\-]+)\s*(.*?)\*\*", stripped)
        if m_tbl_cap:
            output.append(r"\noindent\textbf{" + m_tbl_cap.group(1) + " " +
                           inline_fmt(m_tbl_cap.group(2)) + "}")
            output.append("")
            i += 1; continue

        # Numbered list （1）（2）
        m_enum = re.match(r"^[（(](\d+)[）)]\s*(.+)$", stripped)
        if m_enum:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                mm = re.match(r"^[（(](\d+)[）)]\s*(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(2))); i += 1
                else:
                    break
            output.append(r"\begin{enumerate}[label=（\arabic*）]")
            output += [r"  \item " + process_refs(it) for it in items]
            output.append(r"\end{enumerate}")
            continue

        # Bullet list
        m_bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if m_bullet:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                mm = re.match(r"^[-*]\s+(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(1))); i += 1
                else:
                    break
            output.append(r"\begin{itemize}")
            output += [r"  \item " + process_refs(it) for it in items]
            output.append(r"\end{itemize}")
            continue

        if stripped == "":
            output.append(""); i += 1; continue

        output.append(process_refs(inline_fmt(stripped)) + "\n")
        i += 1

    if in_thankpage:
        output.append(r"\end{thankpage}")
    if in_biblio:
        output.append(r"\end{thebibliography}")
    return output


# ─────────────────────────────────────────────────────────────────────────────
# 7. Post-processing
# ─────────────────────────────────────────────────────────────────────────────

def post_process(result: str) -> str:
    result = re.sub(r"\$\$([^$]+?)\$\$",
                    lambda m: "\\[\n" + m.group(1).strip() + "\n\\]", result)
    result = result.replace("&emsp;", r"\hspace{1em}").replace("&nbsp;", "~")
    result = re.sub(r"\\texttt\{([^}]+)\}",
                    lambda m: r"\texttt{" + m.group(1).replace("_", r"\_") + "}", result)
    result = re.sub(r"\n{4,}", "\n\n\n", result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 8. Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()
    src = Path(args.md)
    tpl = Path(args.template)

    if not src.exists():
        sys.exit(f"ERROR: {src} not found")
    if not tpl.exists():
        sys.exit(f"ERROR: template {tpl} not found")

    dst = Path(args.output) if args.output else tpl.parent / (src.stem + "_hzau.tex")

    raw = src.read_text(encoding="utf-8")
    info, md_body = parse_frontmatter(raw)
    lines = md_body.splitlines()

    template_text = tpl.read_text(encoding="utf-8")
    _BEGIN = r"\begin{document}"
    if _BEGIN not in template_text:
        sys.exit(f"ERROR: {_BEGIN!r} not found in template")
    preamble = patch_preamble(template_text[:template_text.index(_BEGIN)], info)

    cn_text, cn_kw, en_text, en_kw = extract_abstracts(lines)
    year = info.get("year", "2026")

    out = [preamble, _BEGIN, "",
           r"\maketitle", "",
           r"\setcounter{page}{1}",
           r"\renewcommand{\thepage}{\Roman{page}}",
           r"\makestatement{2}{" + year + "}", ""]

    out += [r"\setcounter{page}{1}",
            r"\renewcommand{\thepage}{\Roman{page}}",
            r"\begin{cnabstract}{" + cn_kw + "}"]
    out += [l + "\n" for l in cn_text if l]
    out += [r"\end{cnabstract}", ""]

    out += [r"\begin{enabstract}{" + en_kw + "}"]
    out += [l + "\n" for l in en_text if l]
    out += [r"\end{enabstract}", ""]

    # \tableofcontents without a preceding \clearpage:
    # tocloft's internal penalty mechanism will start the TOC on a new page by
    # itself. Adding an explicit \clearpage first creates a blank page III
    # (LaTeX pushes the entire TOC block to the next page on an empty page).
    out += [r"\tableofcontents",
            r"\thispagestyle{main}",
            r"\clearpage",
            r"\setcounter{page}{1}",
            r"\renewcommand{\thepage}{\arabic{page}}", "",
            r"\seccontent", ""]

    out.extend(convert_body(lines, args.img_prefix))
    out.append(r"\end{document}")

    result = post_process("\n".join(out))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(result, encoding="utf-8")
    print(f"Done → {dst}  ({len(result.splitlines())} lines)")
    print(f"Compile with: xelatex {dst.name}  (run twice for cross-refs)")


if __name__ == "__main__":
    main()
