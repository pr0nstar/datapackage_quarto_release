#!/usr/bin/env python3

import argparse
import json
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument("in_json", nargs="?", default="datapackage.json")
parser.add_argument("out_dir", nargs="?", default=".")
parser.add_argument("--identity", default="")
parser.add_argument("--project", default="")
args = parser.parse_args()

in_json = args.in_json
out_dir = args.out_dir

dp = json.load(open(in_json, "r", encoding="utf-8"))


def md_escape(s: str) -> str:
    return s.replace("|", r"\|")


def tex_escape(s: str) -> str:
    return (
        s.replace("\\", r"\textbackslash{}")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("$", r"\$")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("%", r"\%")
        .replace("_", r"\_")
        .replace("^", r"\^{}")
        .replace("~", r"\~{}")
    )


def field_row(f):
    name = f.get("name", "")
    ftype = f.get("type", "")
    desc = f.get("description", "") or ""
    categories = f.get("categories", f.get('_metadata'))
    desc = tex_escape(desc).replace("\n", r"\newline ")
    if categories:
        cat_text = format_categories(categories)
        if cat_text:
            cat_block = (
                r"\vspace{0.05em}\footnotesize"
                r"\begin{itemize}\setlength{\itemsep}{0.15em}\setlength{\parskip}{0pt}\setlength{\parsep}{0pt}\setlength{\topsep}{0pt}\setlength{\partopsep}{0pt}\setlength{\itemindent}{-5pt}"
                + cat_text
                + r"\end{itemize}\normalsize"
            )
            desc = f"{desc} {cat_block}" if desc else cat_block
    name = tex_escape(name).replace(r"\_", r"\_\allowbreak{}")
    ftype = tex_escape(ftype)
    return (
        r"\textcolor{OrnamentDark}{\textbf{"
        + f"{name}"
        + r"}} & \textcolor{OrnamentDark}{"
        + f"{ftype}"
        + r"} & \textcolor{OrnamentDark}{"
        + f"{desc}"
        + r"} \\"
    )


def format_categories(categories) -> str:
    parts = []
    if isinstance(categories, list):
        for c in categories:
            if isinstance(c, str):
                parts.append(r"\item " + tex_escape(c))
            elif isinstance(c, dict) and 'categories' in c:
                label = c['value']
                parts.append((
                    f"\\item[] \\textbf{{{label}:}} " +
                    format_categories(c.get('_subcategories', []))
                ))

            elif isinstance(c, dict):
                value = (
                    tex_escape(str(c.get("value", "")))
                    if c.get("value") is not None
                    else ""
                )
                label = (
                    tex_escape(str(c.get("label", "")))
                    if c.get("label") is not None
                    else ""
                )
                desc = (
                    tex_escape(str(c.get("description", "")))
                    if c.get("description")
                    else ""
                )
                item = value
                if label:
                    if item:
                        item = f"{item}: \\textit{{{label}}}"
                    else:
                        item = f"\\textit{{{label}}}"
                if desc:
                    item = f"{item} — {desc}" if item else desc
                if item:
                    parts.append(r"\item " + item)
    return " ".join([p for p in parts if p])


def format_sources(sources) -> str:
    parts = []
    if isinstance(sources, list):
        for s in sources:
            if isinstance(s, str):
                parts.append(tex_escape(s))
            elif isinstance(s, dict):
                title = s.get("title") or s.get("name") or s.get("path") or s.get("url") or ""
                title = tex_escape(str(title)) if title is not None else ""
                if title:
                    parts.append(title)
    elif isinstance(sources, str):
        parts.append(tex_escape(sources))
    return "; ".join([p for p in parts if p])


pkg_name = dp.get("name", "")
version = dp.get("version", "")
identity = (args.identity or "").strip()
project = (args.project or "").strip()
sources = dp.get("sources")
resources = dp.get("resources", [])

if not resources:
    sys.exit("No resources found in datapackage.json")

os.makedirs(out_dir, exist_ok=True)

for r in resources:
    resource_name = r.get("name", "resource")
    resource_title_raw = r.get("title", resource_name)
    title = resource_title_raw

    lines = []
    lines += [
        "---",
        f'title: "{title}"',
        "format:",
        "  pdf:",
        "    toc: false",
        "    number-sections: false",
        "    documentclass: scrartcl",
        "    pdf-engine: lualatex",
        "    fontsize: 11pt",
    "    geometry:",
    "      - top=0.75in",
    "      - bottom=0.75in",
    "      - left=1in",
    "      - right=1in",
        "    linestretch: 1.2",
        "    colorlinks: true",
        "    include-in-header:",
        "      - linea.tex",
        "---",
        "",
    ]
    if identity:
        header_path = f"assets/{identity}/header.png"
        lines.append(rf"\BrandHeader{{{header_path}}}")
    if project:
        lines.append(rf"\ProjectTitle{{{tex_escape(project)}}}")
    lines.append(rf"\PackageTitle{{{tex_escape(title)}}}")
    lines += [
        "",
        r"\BrandRuleAccentTop",
        r"\begin{BrandMeta}",
        rf"\MetaItem{{Título}}{{{tex_escape(title)}}}",
        rf"\MetaItem{{Paquete}}{{{tex_escape(pkg_name)}}}",
        rf"\MetaItem{{Versión}}{{{tex_escape(version)}}}",
    ]
    if sources:
        sources_text = format_sources(sources)
        if sources_text:
            lines.append(rf"\MetaItem{{Fuentes}}{{{sources_text}}}")
    lines += [
        r"\end{BrandMeta}",
        r"\BrandRuleAccentBottom",
        "",
    ]

    resource_title = tex_escape(resource_title_raw)
    res_name = tex_escape(r.get("name", ""))
    res_type = tex_escape(r.get("type", ""))
    res_path = tex_escape(r.get("path", ""))
    res_format = tex_escape(r.get("format", ""))
    res_mediatype = tex_escape(r.get("mediatype", ""))
    res_encoding = tex_escape(r.get("encoding", ""))
    res_desc = tex_escape(r.get("description", ""))
    lines += [
        r"\begin{ResourceBlock}",
        "",
        rf"\hyphenpenalty=10000\exhyphenpenalty=10000\textit{{{res_desc}}}" if res_desc else "",
        "",
        r"\vspace{1.2em}",
        rf"\textbf{{Nombre:}} \texttt{{{res_name}}}\\",
        rf"\textbf{{Tipo:}} \texttt{{{res_type}}}\\",
        rf"\textbf{{Documento:}} \texttt{{{res_path}}}\\",
        rf"\textbf{{Formato:}} \texttt{{{res_format}}}\\",
        rf"\textbf{{Extensión:}} \texttt{{{res_mediatype}}}\\",
        rf"\textbf{{Codificación:}} \texttt{{{res_encoding}}}",
        "",
        r"\vspace{1.2em}",
        r"\begin{longtable*}{@{}>{\raggedright\arraybackslash}p{0.30\linewidth}>{\centering\arraybackslash}p{0.14\linewidth}>{\raggedright\arraybackslash}p{0.52\linewidth}@{}}",
        r"\rowcolor{OrnamentLight} \textbf{Campo} & \textbf{Tipo} & \textbf{Descripción} \\",
        r"\addlinespace[0.6em]",
        r"\endfirsthead",
        r"\normalfont\normalsize\rmfamily",
    ]
    for f in r["schema"]["fields"]:
        lines.append(field_row(f))
    lines.append(r"\end{longtable*}")
    lines.append(r"\end{ResourceBlock}")

    out_qmd = os.path.join(out_dir, f"{resource_name}.qmd")
    open(out_qmd, "w", encoding="utf-8").write("\n".join(lines))
    print(f"Escribí: {out_qmd}")
