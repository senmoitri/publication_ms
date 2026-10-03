#!/usr/bin/env python3
import html, os, re
from collections import defaultdict
import bibtexparser

BIB_FILE = "own-bib.bib"
OUTPUT_FILE = "publications.html"
CSS_FILE = "style.css"

CATEGORY_INFO = {
    "article": ("Journal Articles", 1),
    "inproceedings": ("Conference Proceedings", 2),
    "conference": ("Conference Proceedings", 2),
    "incollection": ("Book Chapters", 3),
    "book": ("Books", 4),
    "phdthesis": ("PhD Theses", 5),
    "mastersthesis": ("Master's Theses", 6),
}

def clean_latex(text):
    if not text: return ""
    text = str(text)
    text = re.sub(r"\\url\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\href\{[^{}]*\}\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:textbf|textit|emph|textrm|textsf|texttt|mathrm|mathbf)\s*\{([^{}]*)\}", r"\1", text)
    for old, new in {
        r"\\&":"&", r"\\%":"%", r"\\_":"_", r"\\#":"#",
        r"\\{":"{", r"\\}":"}", r"---":"—", r"--":"–", r"~":" ",
        r"\\ ":" ", r"\\ae":"æ", r"\\AE":"Æ", r"\\aa":"å",
        r"\\AA":"Å", r"\\o":"ø", r"\\O":"Ø", r"\\ss":"ß"
    }.items(): text = text.replace(old,new)
    text = re.sub(r"\\[a-zA-Z]+\s*\{([^{}]*)\}", r"\1", text)
    text = text.replace("{","").replace("}","")
    return re.sub(r"\s+"," ",text).strip()

def safe(v): return html.escape(clean_latex(v or ""))

def authors(v):
    if not v: return ""
    out=[]
    for a in re.split(r"\s+and\s+",v.strip(),flags=re.I):
        a=a.strip()
        if not a: continue
        if "," in a:
            last,first=[x.strip() for x in a.split(",",1)]
            a=f"{first} {last}"
        out.append(clean_latex(a))
    if len(out)==1: return out[0]
    if len(out)==2: return f"{out[0]} and {out[1]}"
    return ", ".join(out[:-1])+", and "+out[-1]

def field(e,*names):
    for n in names:
        if e.get(n): return e[n]
    return ""

def link(url,label):
    if not url: return ""
    u=html.escape(url.strip(),quote=True)
    return f'<a class="pub-link" href="{u}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>'

def year_value(e):
    m=re.search(r"\d{4}",str(e.get("year","")))
    return int(m.group()) if m else 0

def category(e):
    return CATEGORY_INFO.get(e.get("ENTRYTYPE","").lower(),("Other Publications",99))

def item(e,n):
    typ=e.get("ENTRYTYPE","").lower()
    a=authors(e.get("author","")); title=clean_latex(e.get("title",""))
    journal=clean_latex(field(e,"journal")); booktitle=clean_latex(field(e,"booktitle"))
    publisher=clean_latex(field(e,"publisher")); volume=clean_latex(e.get("volume",""))
    number=clean_latex(e.get("number","")); pages=clean_latex(e.get("pages",""))
    year=clean_latex(e.get("year","")); doi=clean_latex(e.get("doi",""))
    url=clean_latex(e.get("url","")); pdf=clean_latex(e.get("pdf",""))
    parts=[]
    if a: parts.append(f'<span class="authors">{safe(a)}</span>')
    if title: parts.append(f'<span class="title">“{safe(title)}”</span>')
    if typ=="article":
        if journal:
            s=f"<em>{safe(journal)}</em>"
            if volume: s+=f", <strong>{safe(volume)}</strong>"
            if number: s+=f"({safe(number)})"
            if pages: s+=f": {safe(pages)}"
            parts.append(s)
    elif typ in ("inproceedings","conference"):
        if booktitle: parts.append(f"<em>In: {safe(booktitle)}</em>")
        if pages: parts.append(f"pp. {safe(pages)}")
        if publisher: parts.append(safe(publisher))
    elif typ=="incollection":
        if booktitle: parts.append(f"<em>In: {safe(booktitle)}</em>")
        if publisher: parts.append(safe(publisher))
        if pages: parts.append(f"pp. {safe(pages)}")
    elif typ=="book":
        if publisher: parts.append(f"<em>{safe(publisher)}</em>")
    elif typ in ("phdthesis","mastersthesis"):
        school=clean_latex(field(e,"school","institution"))
        if school: parts.append(f"<em>{safe(school)}</em>")
    else:
        venue=clean_latex(field(e,"journal","booktitle"))
        if venue: parts.append(f"<em>{safe(venue)}</em>")
        if publisher: parts.append(safe(publisher))
    if year: parts.append(f'<span class="year-inline">{safe(year)}</span>')
    citation=". ".join(parts)
    if citation and not citation.endswith("."): citation+="."
    links=[]
    if doi: links.append(link(doi if doi.startswith("http") else "https://doi.org/"+doi,"DOI"))
    if pdf: links.append(link(pdf,"PDF"))
    if url and url!=pdf: links.append(link(url,"Link"))
    lh=f'<div class="publication-links">{" ".join(links)}</div>' if links else ""
    return f'<article class="publication" data-year="{html.escape(year)}"><div class="publication-number">{n}</div><div><div class="citation">{citation}</div>{lh}</div></article>'

def build(entries):
    grouped=defaultdict(list)
    for e in entries: grouped[category(e)[0]].append(e)
    order=sorted(grouped,key=lambda x: next((o for name,o in CATEGORY_INFO.values() if name==x),99))
    years=sorted({year_value(e) for e in entries if year_value(e)},reverse=True)
    sections=[]
    for cat in order:
        es=sorted(grouped[cat],key=lambda e:(-year_value(e),clean_latex(e.get("title","")).lower()))
        sections.append(f'<section class="publication-section" data-category-section="{html.escape(cat)}"><div class="section-heading"><h2>{html.escape(cat)}</h2><span class="section-count">{len(es)}</span></div>{"".join(item(e,i) for i,e in enumerate(es,1))}</section>')
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="description" content="Academic publications"><title>Publications | Academic Website</title><link rel="stylesheet" href="{CSS_FILE}"></head><body>
<header class="site-header"><div class="nav-wrap"><a class="brand" href="index.html">Academic Profile</a><button class="menu-toggle">☰</button><nav class="nav"><a href="index.html">Home</a><a href="about.html">About</a><a href="research.html">Research</a><a class="active" href="publications.html">Publications</a><a href="students.html">Students</a><a href="teaching.html">Teaching</a><a href="cv.html">CV</a><a href="contact.html">Contact</a></nav></div></header>
<main><section class="page-banner"><p class="eyebrow">SCHOLARLY WORK</p><h1>Publications</h1><p>{len(entries)} publications · Automatically generated from <code>own-bib.bib</code></p></section>
<div class="publication-controls"><div><label for="pub-search">Search</label><input id="pub-search" type="search" placeholder="Author, title, journal, conference..."></div><div><label for="pub-category">Type</label><select id="pub-category"><option value="all">All Types</option>{"".join(f'<option>{html.escape(c)}</option>' for c in order)}</select></div><div><label for="pub-year">Year</label><select id="pub-year"><option value="all">All Years</option>{"".join(f'<option>{y}</option>' for y in years)}</select></div></div>
<div id="no-results" class="no-results">No publications match your search.</div>{''.join(sections)}</main><footer class="site-footer"><p>© 2026 Your Name</p></footer>
<script src="script.js"></script><script>
(function(){{
 const s=document.getElementById("pub-search"),c=document.getElementById("pub-category"),y=document.getElementById("pub-year"),none=document.getElementById("no-results");
 function filter(){{
  const q=s.value.toLowerCase().trim(), cat=c.value, yr=y.value; let count=0;
  document.querySelectorAll(".publication-section").forEach(sec=>{{
   const name=sec.querySelector("h2").textContent.trim(); let shown=0;
   sec.querySelectorAll(".publication").forEach(p=>{{
    const ok=(!q||p.textContent.toLowerCase().includes(q))&&(cat==="all"||name===cat)&&(yr==="all"||p.dataset.year===yr);
    p.style.display=ok?"":"none"; if(ok) shown++;
   }}); sec.style.display=shown?"":"none"; count+=shown;
  }}); none.style.display=count?"none":"block";
 }}
 [s,c,y].forEach(x=>x.addEventListener(x===s?"input":"change",filter)); filter();
}})();
</script></body></html>'''

def main():
    if not os.path.exists(BIB_FILE): raise FileNotFoundError(BIB_FILE)
    with open(BIB_FILE,encoding="utf-8") as f: db=bibtexparser.load(f)
    entries=[e for e in db.entries if e.get("ENTRYTYPE","").lower()!="comment"]
    if not entries: raise ValueError("No BibTeX entries found.")
    with open(OUTPUT_FILE,"w",encoding="utf-8") as f: f.write(build(entries))
    print(f"Generated {OUTPUT_FILE} from {BIB_FILE} ({len(entries)} publications).")
if __name__=="__main__": main()
