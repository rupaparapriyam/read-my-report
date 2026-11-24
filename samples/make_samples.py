"""Make synthetic lab reports to build and demo against.

Every patient here is invented. No real report, and no real person's data, is used
anywhere in this project.
"""
import pathlib, subprocess, shutil

HERE = pathlib.Path(__file__).resolve().parent

REPORTS = {
"cbc": ("Sunrise Diagnostics, Rajkot", "Anita Mehta", "34 / Female", "SD-2026-11241", [
    ("Haemoglobin", "9.8", "g/dL", "12.0 - 15.0"),
    ("Total Leucocyte Count", "7,200", "/cumm", "4,000 - 11,000"),
    ("Platelet Count", "2.6", "lakh/cumm", "1.5 - 4.1"),
    ("Packed Cell Volume", "31.4", "%", "36.0 - 46.0"),
    ("Mean Corpuscular Volume", "71.2", "fL", "83.0 - 101.0"),
    ("Red Cell Distribution Width", "17.8", "%", "11.6 - 14.0"),
]),
"thyroid": ("Sunrise Diagnostics, Rajkot", "Rahul Desai", "41 / Male", "SD-2026-11242", [
    ("TSH", "8.42", "uIU/mL", "0.55 - 4.78"),
    ("Free T3", "2.9", "pg/mL", "2.3 - 4.2"),
    ("Free T4", "0.81", "ng/dL", "0.89 - 1.76"),
]),
"sugar-lipid": ("Sunrise Diagnostics, Rajkot", "Imran Shaikh", "52 / Male", "SD-2026-11243", [
    ("Fasting Blood Sugar", "138", "mg/dL", "70 - 100"),
    ("HbA1c", "7.4", "%", "4.0 - 5.6"),
    ("Total Cholesterol", "244", "mg/dL", "< 200"),
    ("HDL Cholesterol", "38", "mg/dL", "> 40"),
    ("LDL Cholesterol", "161", "mg/dL", "< 100"),
    ("Triglycerides", "212", "mg/dL", "< 150"),
    ("Serum Creatinine", "0.9", "mg/dL", "0.7 - 1.3"),
]),
"normal": ("Sunrise Diagnostics, Rajkot", "Priya Nair", "27 / Female", "SD-2026-11244", [
    ("Haemoglobin", "13.4", "g/dL", "12.0 - 15.0"),
    ("Total Leucocyte Count", "6,800", "/cumm", "4,000 - 11,000"),
    ("Platelet Count", "2.9", "lakh/cumm", "1.5 - 4.1"),
    ("Fasting Blood Sugar", "88", "mg/dL", "70 - 100"),
]),
}

PAGE = """<!doctype html><meta charset="utf-8"><title>{name}</title><style>
@page{{size:A4;margin:16mm}}
body{{font:12px/1.5 "Helvetica Neue",Arial,sans-serif;color:#111}}
h1{{font-size:15px;margin:0;letter-spacing:.3px}}
.sub{{font-size:10px;color:#555;margin:2px 0 14px}}
.meta{{width:100%;border-collapse:collapse;margin-bottom:14px;font-size:11px}}
.meta td{{padding:2px 0}}
table.r{{width:100%;border-collapse:collapse;font-size:11.5px}}
table.r th{{text-align:left;border-bottom:1.2px solid #111;padding:5px 4px;font-size:10.5px;
  text-transform:uppercase;letter-spacing:.4px}}
table.r td{{padding:5px 4px;border-bottom:.5px solid #ddd}}
td.v{{font-weight:600}}
.foot{{margin-top:18px;font-size:9.5px;color:#666;border-top:.5px solid #ccc;padding-top:7px}}
</style>
<h1>{lab}</h1>
<div class="sub">Pathology &amp; Clinical Laboratory &middot; NABL accredited</div>
<table class="meta">
<tr><td>Patient</td><td><b>{name}</b></td><td>Report No.</td><td>{rid}</td></tr>
<tr><td>Age / Sex</td><td>{age}</td><td>Collected</td><td>24-Nov-2026 08:10</td></tr>
<tr><td>Referred by</td><td>Dr. S. Kulkarni</td><td>Reported</td><td>24-Nov-2026 14:35</td></tr>
</table>
<table class="r"><thead><tr><th>Test</th><th>Result</th><th>Unit</th><th>Biological Reference Interval</th></tr></thead>
<tbody>{rows}</tbody></table>
<div class="foot">Results relate only to the sample tested. This is a sample report generated for
software testing; the patient is fictitious.</div>"""


def build():
    chrome = next((p for p in [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("chromium") or "", shutil.which("google-chrome") or ""] if p and pathlib.Path(p).exists()), None)
    for key, (lab, name, age, rid, rows) in REPORTS.items():
        html = PAGE.format(lab=lab, name=name, age=age, rid=rid, rows="".join(
            f"<tr><td>{t}</td><td class='v'>{v}</td><td>{u}</td><td>{r}</td></tr>"
            for t, v, u, r in rows))
        (HERE / f"{key}.html").write_text(html, encoding="utf-8")
        if chrome:
            subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={HERE / (key + '.pdf')}", (HERE / f"{key}.html").as_uri()],
                           capture_output=True, timeout=90)
        print(f"  {key}: {len(rows)} tests" + ("  -> pdf" if chrome else "  (no Chrome; html only)"))


if __name__ == "__main__":
    build()
