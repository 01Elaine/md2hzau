#!/usr/bin/env python3
"""
md2hzau — Markdown → 华中农业大学本科毕业论文 LaTeX

对接模板: https://github.com/eriche2016/HZAU_UnderGraduateThesis_Template

用法:
    python md2hzau.py 论文.md [--template template/main.tex] [--img-prefix Fig/]

输出:
    template/<stem>_main.tex   — patch 好个人信息/摘要/致谢的主文件
    template/chapters/content.tex — 所有正文章节

MD frontmatter 字段（在文件头 --- 块里填写）:
    title_cn / title_en / author / author_en
    major / major_en / instructor / instructor_en
    instructor_title / instructor_title_en
    student_id / class_name / degree
    date_cn / date_en / signature_date / year

License: MIT
"""

import argparse
import re
import sys
from pathlib import Path


# ─── 1. CLI ──────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Convert Markdown thesis to HZAU LaTeX template"
    )
    p.add_argument("md", help="Markdown source (.md)")
    p.add_argument("--template", default="template/main.tex",
                   help="Path to template main.tex (default: template/main.tex)")
    p.add_argument("--output",
                   help="Output main .tex path (default: <template_dir>/<stem>_main.tex)")
    p.add_argument("--img-prefix", default="Fig/", dest="img_prefix",
                   help="Image prefix in LaTeX relative to template dir (default: Fig/)")
    return p.parse_args()


# ─── 2. Frontmatter ──────────────────────────────────────────────────────────

_FM_DEFAULTS = {
    "title_cn":            "论文中文题目",
    "title_en":            "English Title of the Thesis",
    "author":              "张三",
    "author_en":           "ZHANGSAN",
    "major":               "人工智能",
    "major_en":            "ARTIFICIAL INTELLIGENCE",
    "instructor":          "李四",
    "instructor_en":       "SI LI",
    "instructor_title":    "副教授",
    "instructor_title_en": "ASSOCIATE PROFESSOR",
    "student_id":          "2022317220XX",
    "class_name":          "专业2201班",
    "degree":              "工学学士学位",
    "date_cn":             "二〇二五年六月",
    "date_en":             "JUNE，2025",
    "signature_date":      "2025年6月14日",
    "year":                "2025",
}


def parse_frontmatter(text: str):
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
            key, val = key.strip(), val.strip()
            if key and val:
                info[key] = val
    return info, "\n".join(lines[end + 1:])


# ─── 3. Inline formatting ────────────────────────────────────────────────────

def cell_escape(s: str) -> str:
    parts = re.split(r"(\$[^$]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(p)
        else:
            p = (p.replace("±", r"$\pm$").replace("≤", r"$\leq$")
                  .replace("≥", r"$\geq$").replace("→", r"$\rightarrow$")
                  .replace("✓", r"\checkmark{}").replace("✗", r"$\times$"))
            out.append(p)
    return "".join(out)


def inline_fmt(s: str) -> str:
    s = re.sub(r"hspace(\d+)em", r"\\hspace{\1em}", s)
    _S3, _S2, _S1 = "\x00S3\x00", "\x00S2\x00", "\x00S1\x00"
    s = s.replace("\\***", _S3).replace("\\**", _S2).replace("\\*", _S1)
    parts = re.split(r"(\$[^$\n]*\$)", s)
    out = []
    for p in parts:
        if p.startswith("$"):
            out.append(p)
        else:
            p = p.replace("&emsp;", r"\hspace{1em}").replace("&emsp", r"\hspace{1em}")
            p = p.replace("&nbsp;", "~")
            p = p.replace("&", r"\&").replace("%", r"\%")
            out.append(p)
    s = "".join(out)
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
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
    """[1], [2,3] → \\parencite{ref1}, \\parencite{ref2,ref3}"""
    def repl(m):
        nums = [n.strip() for n in m.group(1).split(",")]
        if len(nums) == 2 and "0" in nums:
            return m.group(0)
        return r"\parencite{" + ",".join("ref" + n for n in nums) + "}"
    parts = re.split(r"(\$[^$\n]*\$)", s)
    return "".join(
        p if p.startswith("$") else re.sub(r"\[(\d+(?:,\s*\d+)*)\]", repl, p)
        for p in parts
    )


def convert_table(table_lines: list, cap_cn: str = "", cap_en: str = "") -> str:
    rows = []
    for l in table_lines:
        l = l.strip()
        if re.match(r"^\|[-| :]+\|$", l):
            continue
        rows.append([c.strip() for c in l.strip("|").split("|")])
    if not rows:
        return ""
    ncols = len(rows[0])
    col_fmt = "|".join(["l"] * ncols)
    inner = [r"\begin{tabular}{" + col_fmt + "}", r"\toprule"]
    inner.append(" & ".join(
        r"\textbf{" + cell_escape(inline_fmt(c.strip("*"))) + "}"
        for c in rows[0]
    ) + r" \\")
    inner.append(r"\midrule")
    for row in rows[1:]:
        while len(row) < ncols:
            row.append("")
        inner.append(" & ".join(cell_escape(inline_fmt(c)) for c in row) + r" \\")
    inner += [r"\bottomrule", r"\end{tabular}"]

    cap_lines = []
    if cap_cn:
        en = cap_en if cap_en else cap_cn
        lbl = "tab:" + re.sub(r"[^\w]", "-", cap_cn)[:30]
        cap_lines = [
            f"  \\bicaption{{{cap_cn}}}{{{en}}}",
            f"  \\label{{{lbl}}}",
        ]

    return "\n".join(
        [r"\begin{table}[H]", r"  \centering"]
        + cap_lines
        + [r"  \begin{adjustbox}{max width=\linewidth}"]
        + ["  " + ln for ln in inner]
        + [r"  \end{adjustbox}", r"\end{table}"]
    )


# ─── 4. Content extraction ────────────────────────────────────────────────────

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
        if re.match(r"^## ", s) and s not in ("## 摘要", "## Abstract"):
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


def extract_bibliography(lines: list) -> str:
    """## 参考文献 节下的 ```bibtex 块 → 原始 BibTeX 字符串（空字符串表示无内容）"""
    in_ref = False
    in_block = False
    bib_lines = []
    for l in lines:
        s = l.strip()
        if s == "## 参考文献":
            in_ref = True; continue
        if in_ref:
            if re.match(r"^## ", s):
                break
            if not in_block and s.lower().startswith("```bibtex"):
                in_block = True; continue
            if in_block:
                if s.startswith("```"):
                    in_block = False; continue
                bib_lines.append(l)
    return "\n".join(bib_lines).strip()


def extract_abbreviations(lines: list) -> list:
    """## 缩略语 节下 '- ABBR: Full name' 行 → [(abbr, full), ...]"""
    abbrs = []
    in_abbr = False
    for l in lines:
        s = l.strip()
        if s == "## 缩略语":
            in_abbr = True; continue
        if in_abbr:
            if re.match(r"^## ", s):
                break
            m = re.match(r"^[-*]\s+([^:：]+)[：:]\s*(.+)$", s)
            if m:
                abbrs.append((m.group(1).strip(), m.group(2).strip()))
    return abbrs


def extract_acknowledgement(lines: list) -> list:
    ack = []
    in_ack = False
    for l in lines:
        s = l.strip()
        if s == "## 致谢":
            in_ack = True; continue
        if in_ack:
            if re.match(r"^## ", s):
                break
            ack.append(inline_fmt(s) if s else "")
    return ack


# ─── 5. Patch main.tex ────────────────────────────────────────────────────────

def _replace_cmd(text: str, cmd: str, val: str) -> str:
    marker = '\\newcommand{\\' + cmd + '}{'
    idx = text.find(marker)
    if idx == -1:
        print(f"  WARNING: \\{cmd} not found in template", file=sys.stderr)
        return text
    start = idx + len(marker)
    end = text.find('}', start)
    if end == -1:
        print(f"  WARNING: \\{cmd} closing brace not found", file=sys.stderr)
        return text
    new_text = text[:idx] + '\\newcommand{\\' + cmd + '}{' + val + text[end:]
    print(f"  OK  [\\{cmd}]")
    return new_text


def patch_main_tex(text: str, info: dict,
                   cn_text: list, cn_kw: str,
                   en_text: list, en_kw: str,
                   ack_text: list,
                   abbrs: list = ()) -> str:
    print("Patching main.tex ...")

    # 个人信息命令
    for cmd, key in [
        ("thesisTitleC",    "title_cn"),
        ("thesisTitleE",    "title_en"),
        ("yourMajor",       "major"),
        ("yourMajorEn",     "major_en"),
        ("yourName",        "author"),
        ("yourNameEn",      "author_en"),
        ("yourMentor",      "instructor"),
        ("yourMentorEn",    "instructor_en"),
        ("Mentorjob",       "instructor_title"),
        ("MentorjobEn",     "instructor_title_en"),
        ("studentID",       "student_id"),
        ("yourDateC",       "date_cn"),
        ("yourDateEn",      "date_en"),
        ("yourClass",       "class_name"),
        ("yourDegree",      "degree"),
        ("signatureDate",   "signature_date"),
    ]:
        text = _replace_cmd(text, cmd, info[key])

    # 页眉年份
    year = info["year"]
    text = re.sub(r'华中农业大学\d+届学士学位毕业论文',
                  f'华中农业大学{year}届学士学位毕业论文', text)
    print(f"  OK  [页眉年份 → {year}届]")

    # 注入正文所需宏包（若未存在）
    if r"\usepackage{adjustbox}" not in text:
        text = text.replace(
            r"\usepackage{graphicx}",
            r"\usepackage{graphicx}" + "\n"
            + r"\usepackage{booktabs,array,adjustbox,float}" + "\n"
            + r"\setlength{\emergencystretch}{3em}",
            1
        )
        print("  OK  [inject booktabs/adjustbox/float]")

    # 中文摘要
    cn_body = "\n\n".join(l for l in cn_text if l) or "请填写中文摘要。"
    new_cn = (
        "\\begin{abstract}\n\n"
        + cn_body + "\n\n"
        + f"\\keywords{{{cn_kw or '关键词1；关键词2'}}}\n\n"
        + "\\end{abstract}"
    )
    text = re.sub(r"\\begin\{abstract\}.*?\\end\{abstract\}",
                  lambda _: new_cn, text, flags=re.DOTALL, count=1)
    print("  OK  [中文摘要]")

    # 英文摘要
    en_body = "\n\n".join(l for l in en_text if l) or "Please add English abstract here."
    new_en = (
        "\\begin{abstractEN}\n\n"
        + en_body + "\n\n"
        + f"\\keywordsEN{{{en_kw or 'keyword1; keyword2'}}}\n\n"
        + "\\end{abstractEN}"
    )
    text = re.sub(r"\\begin\{abstractEN\}.*?\\end\{abstractEN\}",
                  lambda _: new_en, text, flags=re.DOTALL, count=1)
    print("  OK  [英文摘要]")

    # 缩略语表（仅在 MD 中有 ## 缩略语 节时注入）
    if abbrs:
        abbr_rows = "\n".join(f"  \\abbr{{{a}}}{{{b}}}" for a, b in abbrs)
        new_abbr = "\\begin{abbreviations}\n" + abbr_rows + "\n\\end{abbreviations}"
        text = re.sub(
            r'% 如需缩略语表.*?% \\end\{abbreviations\}',
            lambda _: new_abbr,
            text, flags=re.DOTALL, count=1
        )
        print(f"  OK  [缩略语表 {len(abbrs)} 条]")

    # 章节 \input 块 → 单一 chapters/content
    text = re.sub(
        r"(?:\\input\{chapters/chapter\d+\}\s*\\clearpage\s*\n)+",
        lambda _: "\\input{chapters/content} \\clearpage\n\n",
        text
    )
    print("  OK  [章节 \\input → chapters/content]")

    # 致谢内容
    if ack_text:
        ack_body = "\n\n".join(l for l in ack_text if l)
        date_simple = re.sub(r"[，,]", " ", info.get("date_en", "June, 2025")).title()
        new_ack = (
            "\\acknowledgement\n\n"
            + ack_body + "\n\n"
            + f"\\hfill {date_simple}\n\n"
            + f"\\hfill {info['author']}\n\n\n"
        )
        text = re.sub(r"\\acknowledgement.*?(?=\\end\{document\})",
                      lambda _: new_ack, text, flags=re.DOTALL, count=1)
        print("  OK  [致谢]")

    print()
    return text


# ─── 6. Body conversion ──────────────────────────────────────────────────────

_SKIP_H2 = {"摘要", "Abstract", "缩略语", "致谢", "参考文献"}


def convert_body(lines: list, img_prefix: str) -> list:
    output = []
    in_body = False
    in_skip = False
    in_appendix = False
    in_table = False
    table_lines = []
    pending_table_cap = ("", "")
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        # 代码块（in_skip 时直接跳过）
        if stripped.startswith("```"):
            if not in_body or in_skip:
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    i += 1
                i += 1; continue
            lang = stripped[3:].strip().lower()
            i += 1
            block = []
            while i < len(lines):
                if lines[i].strip().startswith("```"):
                    i += 1; break
                block.append(lines[i])
                i += 1
            if lang == "latex":
                output.extend(block)
            elif lang == "algorithm":
                output.append(r"\begin{algorithm}[H]")
                output.extend(block)
                output.append(r"\end{algorithm}")
            else:
                output.append(r"\begin{verbatim}")
                output.extend(block)
                output.append(r"\end{verbatim}")
            continue

        # 标题
        m = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if m:
            level = len(m.group(1))
            raw = m.group(2)
            clean = re.sub(r"^第\d+章\s*", "", raw)
            clean = re.sub(r"^\d[\d\.]*[\s　]+", "", clean)

            if level == 2 and clean in _SKIP_H2:
                in_skip = True
                i += 1; continue

            if level == 2:
                in_skip = False
                in_body = True
                if clean == "附录":
                    # 进入附录模式：标题层级 -1，每个 ### 成为独立的 \section（"附录 A xxx"）
                    output.append(r"\appendix")
                    in_appendix = True
                    i += 1; continue

            if in_skip:
                i += 1; continue

            title = process_refs(inline_fmt(clean))
            if in_appendix:
                cmds = {3: "section", 4: "subsection"}
                cmd = cmds.get(level, "subsubsection")
            else:
                cmds = {2: "section", 3: "subsection", 4: "subsubsection"}
                cmd = cmds.get(level, "paragraph")
            lbl = re.sub(r"[^\w]", "-", raw)[:40]
            output.append(f"\\{cmd}{{{title}}}\\label{{{lbl}}}")
            i += 1; continue

        if in_skip or not in_body:
            i += 1; continue

        if stripped == "":
            output.append(""); i += 1; continue

        # 水平分隔线 --- 忽略（LaTeX 章节已有视觉分隔，无需转成 em-dash）
        if re.match(r"^-{3,}$", stripped):
            i += 1; continue

        # 表格
        if stripped.startswith("|"):
            if not in_table:
                in_table = True; table_lines = [stripped]
            else:
                table_lines.append(stripped)
            i += 1
            next_s = lines[i].strip() if i < len(lines) else ""
            if not next_s.startswith("|"):
                cap_cn, cap_en = pending_table_cap
                output.append(convert_table(table_lines, cap_cn, cap_en))
                pending_table_cap = ("", "")
                in_table = False; table_lines = []
            continue

        # 图片（含子图：多张连续 ![...] 后跟 **图N** 触发 subfigure）
        m_img = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if m_img:
            # 收集连续图片行
            imgs = [(m_img.group(1), Path(m_img.group(2)).name)]
            j = i + 1
            while j < len(lines):
                ns = lines[j].strip()
                mm = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", ns)
                if mm:
                    imgs.append((mm.group(1), Path(mm.group(2)).name))
                    j += 1
                else:
                    break
            # 尝试读取 **图N** 标题行（支持 中文 | English 双语）
            cap_cn_str, cap_en_str, lbl_base = None, None, None
            if j < len(lines):
                ns = lines[j].strip()
                m_cap = re.match(r"^\*\*(图[\d\.\-]+)\*\*\s*(.*)", ns)
                if m_cap:
                    num = m_cap.group(1)
                    rest = inline_fmt(m_cap.group(2).strip()) if m_cap.group(2) else ""
                    full = (num + (" " + rest if rest else "")).strip()
                    if "|" in full:
                        cn, _, en = full.partition("|")
                        cap_cn_str, cap_en_str = cn.strip(), en.strip()
                    else:
                        cap_cn_str, cap_en_str = full, ""
                    lbl_base = re.sub(r"[^\w]", "-", num)[:30]
                    j += 1
            if len(imgs) == 1:
                alt, fname = imgs[0]
                cap_cn = cap_cn_str or alt
                cap_en = cap_en_str or alt
                lbl = "fig:" + (lbl_base or re.sub(r"[^\w]", "-", alt)[:30])
                output += [
                    r"\begin{figure}[H]", r"  \centering",
                    f"  \\includegraphics[width=0.88\\textwidth]{{{img_prefix}{fname}}}",
                    f"  \\bicaption{{{cap_cn}}}{{{cap_en}}}",
                    f"  \\label{{{lbl}}}",
                    r"\end{figure}",
                ]
            else:
                _sub_w = {2: "0.45", 3: "0.30", 4: "0.22"}
                w = _sub_w.get(len(imgs), f"{0.9/len(imgs):.2f}")
                cap_cn = cap_cn_str or "图题"
                cap_en = cap_en_str or cap_cn
                lbl = "fig:" + (lbl_base or "subfig")
                blk = [r"\begin{figure}[H]", r"  \centering"]
                for k, (alt, fname) in enumerate(imgs):
                    blk += [
                        f"  \\begin{{subfigure}}[b]{{{w}\\textwidth}}",
                        r"    \centering",
                        f"    \\includegraphics[width=\\textwidth]{{{img_prefix}{fname}}}",
                        f"    \\caption{{{inline_fmt(alt)}}}",
                        r"  \end{subfigure}",
                    ]
                    if k < len(imgs) - 1:
                        blk.append(r"  \hfill")
                blk += [f"  \\bicaption{{{cap_cn}}}{{{cap_en}}}", f"  \\label{{{lbl}}}", r"\end{figure}"]
                output.extend(blk)
            i = j
            continue

        # 图说明行（已被上面消耗，这里防漏）
        if re.match(r"^\*\*图\d", stripped):
            i += 1; continue

        # 表标题 → 暂存，随下一个表格一起输出（支持 中文 | English 双语）
        m_tbl_cap = re.match(r"^\*\*(表[\d\.\-]+)\*\*\s*(.*)$", stripped)
        if m_tbl_cap:
            num = m_tbl_cap.group(1)
            rest = inline_fmt(m_tbl_cap.group(2).strip()) if m_tbl_cap.group(2) else ""
            full = (num + (" " + rest if rest else "")).strip()
            if "|" in full:
                cn, _, en = full.partition("|")
                pending_table_cap = (cn.strip(), en.strip())
            else:
                pending_table_cap = (full, "")
            i += 1; continue

        # 数字列表 （1）（2）
        m_enum = re.match(r"^[（(](\d+)[）)]\s*(.+)$", stripped)
        if m_enum:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                if not l:
                    i += 1; continue
                mm = re.match(r"^[（(](\d+)[）)]\s*(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(2))); i += 1
                else:
                    break
            output.append(r"\begin{enumerate}[label=（\arabic*）]")
            output += [r"  \item " + process_refs(it) for it in items]
            output.append(r"\end{enumerate}")
            continue

        # 无序列表
        m_bullet = re.match(r"^[-*]\s+(.+)$", stripped)
        if m_bullet:
            items = []
            while i < len(lines):
                l = lines[i].strip()
                if not l:
                    i += 1; continue
                mm = re.match(r"^[-*]\s+(.+)$", l)
                if mm:
                    items.append(inline_fmt(mm.group(1))); i += 1
                else:
                    break
            output.append(r"\begin{itemize}")
            output += [r"  \item " + process_refs(it) for it in items]
            output.append(r"\end{itemize}")
            continue

        output.append(process_refs(inline_fmt(stripped)))
        i += 1

    return output


# ─── 7. Post-processing ───────────────────────────────────────────────────────

def post_process(result: str) -> str:
    result = re.sub(r"\$\$([^$]+?)\$\$",
                    lambda m: "\\[\n" + m.group(1).strip() + "\n\\]", result)
    result = result.replace("&emsp;", r"\hspace{1em}").replace("&nbsp;", "~")
    result = re.sub(r"\\texttt\{([^}]+)\}",
                    lambda m: r"\texttt{" + m.group(1).replace("_", r"\_") + "}", result)
    result = re.sub(r"\n{4,}", "\n\n\n", result)
    return result


# ─── 8. Entry point ──────────────────────────────────────────────────────────

def main():
    args = parse_args()
    src = Path(args.md)
    tpl = Path(args.template)

    if not src.exists():
        sys.exit(f"ERROR: {src} not found")
    if not tpl.exists():
        sys.exit(f"ERROR: template {tpl} not found")

    tpl_dir = tpl.parent
    dst_main = Path(args.output) if args.output else tpl_dir / (src.stem + "_main.tex")
    dst_content = tpl_dir / "chapters" / "content.tex"

    raw = src.read_text(encoding="utf-8")
    info, md_body = parse_frontmatter(raw)
    lines = md_body.splitlines()

    cn_text, cn_kw, en_text, en_kw = extract_abstracts(lines)
    ack_text = extract_acknowledgement(lines)
    abbrs = extract_abbreviations(lines)
    bib_content = extract_bibliography(lines)
    if bib_content:
        bib_path = tpl_dir / "references.bib"
        bib_path.write_text(bib_content, encoding="utf-8")
        print(f"  OK  [references.bib → {bib_path}]")

    template_text = tpl.read_text(encoding="utf-8")
    patched = patch_main_tex(template_text, info, cn_text, cn_kw, en_text, en_kw, ack_text, abbrs)

    body_lines = convert_body(lines, args.img_prefix)
    body_text = post_process("\n".join(body_lines))

    dst_main.write_text(patched, encoding="utf-8")
    dst_content.parent.mkdir(parents=True, exist_ok=True)
    dst_content.write_text(body_text, encoding="utf-8")

    print(f"Done:")
    print(f"  main  → {dst_main}  ({len(patched.splitlines())} lines)")
    print(f"  body  → {dst_content}  ({len(body_text.splitlines())} lines)")
    stem = dst_main.stem
    print(f"\nCompile (in template/ directory):")
    print(f"  cd {tpl_dir}")
    print(f"  xelatex {dst_main.name}")
    print(f"  biber {stem}")
    print(f"  xelatex {dst_main.name}")
    print(f"  xelatex {dst_main.name}")


if __name__ == "__main__":
    main()
