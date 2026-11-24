"""Turn the project's Markdown into clean A4 pages for the Drive folder.

Deliberately small: headings, paragraphs, lists, tables, bold, italic, inline code
and links. That is everything our documents use.
"""
import html
import re
import sys
from pathlib import Path

CSS = """
@page{size:A4;margin:19mm 17mm}
body{font:11.2pt/1.55 -apple-system,"Helvetica Neue",Arial,sans-serif;color:#15201f;margin:0}
h1{font-size:19pt;letter-spacing:-.02em;margin:0 0 6pt;line-height:1.2}
h2{font-size:13pt;letter-spacing:-.01em;margin:17pt 0 5pt;padding-bottom:3pt;
   border-bottom:.6pt solid #d8dedc}
h3{font-size:11.6pt;margin:13pt 0 4pt}
p{margin:0 0 8pt}
ul,ol{margin:0 0 8pt;padding-left:16pt}
li{margin:0 0 3pt}
code{font:10pt ui-monospace,Menlo,monospace;background:#f1f4f3;padding:1pt 3pt;border-radius:3pt}
a{color:#0e5e52;text-decoration:none}
table{width:100%;border-collapse:collapse;margin:0 0 10pt;font-size:9.8pt}
th{text-align:left;border-bottom:1pt solid #15201f;padding:4pt 5pt;font-size:9pt;
   text-transform:uppercase;letter-spacing:.04em}
td{padding:4pt 5pt;border-bottom:.4pt solid #e3e8e6;vertical-align:top}
blockquote{margin:0 0 8pt;padding-left:9pt;border-left:2pt solid #0e5e52;color:#3a4a48}
strong{font-weight:650}
"""


def inline(text):
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def convert(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*\|.*\|\s*$", line) and i + 1 < len(lines) \
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                item = inline(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                out.append("<li>" + item + "</li>")
                i += 1
            out.append("</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = inline(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                out.append("<li>" + item + "</li>")
                i += 1
            out.append("</ol>")
            continue
        if line.startswith(">"):
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(body)) + "</blockquote>")
            continue
        if line.startswith("---") or not line.strip():
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4}\s|\s*[-*]\s|\s*\d+\.\s|\s*\|)", lines[i]):
            para.append(lines[i].strip())
            i += 1
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n".join(out)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    title = sys.argv[2] if len(sys.argv) > 2 else src.stem
    body = convert(src.read_text(encoding="utf-8"))
    Path(sys.argv[3]).write_text(
        f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title>"
        f"<style>{CSS}</style>{body}", encoding="utf-8")
    print(f"  {src.name} -> {Path(sys.argv[3]).name}")
