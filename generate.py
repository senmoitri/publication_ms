import bibtexparser
from pathlib import Path
from html import escape
import re


BIB_FILE = "own-bib.bib"
OUTPUT_FILE = "index.html"
CSS_FILE = "style.css"


def clean_text(text):
    """Clean common BibTeX formatting."""
    if not text:
        return ""

    text = text.replace("{", "").replace("}", "")
    text = text.replace("--", "–")
    text = text.replace("---", "—")

    # Remove LaTeX italic/bold commands
    text = re.sub(r"\\textit\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\emph\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\textbf\{([^}]*)\}", r"\1", text)

    return text.strip()


def format_authors(author_string):
    """Convert BibTeX author field into readable author names."""
    if not author_string:
        return ""

    authors = author_string.split(" and ")
    formatted = []

    for author in authors:
        author = clean_text(author)

        if "," in author:
            parts = [p.strip() for p in author.split(",", 1)]
            if len(parts) == 2:
                author = f"{parts[1]} {parts[0]}"

        formatted.append(author)

    return ", ".join(formatted)


def make_link(url, label):
    if not url:
        return ""

    url = escape(url, quote=True)

    return f'<a href="{url}" target="_blank" rel="noopener">{label}</a>'


def get_publication(entry):
    """Extract relevant fields from a BibTeX entry."""

    year = clean_text(entry.get("year", "Unknown"))

    try:
        year_number = int(re.search(r"\d{4}", year).group())
    except (AttributeError, ValueError):
        year_number = 0

    return {
        "year": year,
        "year_number": year_number,
        "author": format_authors(entry.get("author", "")),
        "title": clean_text(entry.get("title", "")),
        "journal": clean_text(
            entry.get("journal", entry.get("booktitle", ""))
        ),
        "volume": clean_text(entry.get("volume", "")),
        "number": clean_text(entry.get("number", "")),
        "pages": clean_text(entry.get("pages", "")),
        "doi": clean_text(entry.get("doi", "")),
        "url": clean_text(entry.get("url", "")),
        "pdf": clean_text(entry.get("pdf", "")),
        "publisher": clean_text(entry.get("publisher", "")),
    }


def publication_details(pub):
    """Build journal/volume/pages/year line."""

    details = []

    if pub["journal"]:
        details.append(f"<em>{escape(pub['journal'])}</em>")

    if pub["volume"]:
        volume = f"<strong>{escape(pub['volume'])}</strong>"

        if pub["number"]:
            volume += f"({escape(pub['number'])})"

        details.append(volume)

    if pub["pages"]:
        details.append(escape(pub["pages"]))

    if pub["year"]:
        details.append(escape(pub["year"]))

    return ", ".join(details)


def generate_html(publications):
    """Generate the complete HTML publication page."""

    total = len(publications)

    html = f"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Publications</title>

    <link rel="stylesheet" href="{CSS_FILE}">
</head>

<body>

<div class="container">

    <header class="header">
        <h1>Publications</h1>
        <p class="subtitle">
            Research Publications
            <span class="count">({total} publications)</span>
        </p>
    </header>

    <div class="controls">

        <input
            type="text"
            id="searchBox"
            placeholder="Search publications..."
            onkeyup="filterPublications()"
        >

        <select id="yearFilter" onchange="filterPublications()">
            <option value="all">All Years</option>
"""

    years = sorted(
        set(pub["year_number"] for pub in publications if pub["year_number"]),
        reverse=True
    )

    for year in years:
        html += f'            <option value="{year}">{year}</option>\n'

    html += """        </select>

    </div>

    <main id="publicationList">
"""

    current_year = None
    number = total

    for pub in publications:

        if pub["year_number"] != current_year:

            current_year = pub["year_number"]

            html += f"""
        <section class="year-section" data-year="{current_year}">
            <h2>{escape(pub["year"])}</h2>
"""

        title = escape(pub["title"])
        authors = escape(pub["author"])

        details = publication_details(pub)

        html += f"""
            <article class="publication">

                <div class="publication-number">
                    [{number}]
                </div>

                <div class="publication-content">

                    <div class="authors">
                        {authors}
                    </div>

                    <div class="title">
                        {title}
                    </div>

                    <div class="details">
                        {details}
                    </div>

                    <div class="links">
"""

        if pub["doi"]:

            doi = pub["doi"]

            if doi.startswith("http"):
                doi_url = doi
            else:
                doi_url = "https://doi.org/" + doi

            html += "                        "
            html += make_link(doi_url, "DOI")
            html += "\n"

        if pub["url"]:
            html += "                        "
            html += make_link(pub["url"], "Article")
            html += "\n"

        if pub["pdf"]:
            html += "                        "
            html += make_link(pub["pdf"], "PDF")
            html += "\n"

        html += """                    </div>

                </div>

            </article>
"""

        number -= 1

    html += """
        </section>

    </main>

    <p id="noResults" class="no-results">
        No publications found.
    </p>

</div>


<script>

function filterPublications() {

    const search =
        document.getElementById("searchBox").value.toLowerCase();

    const year =
        document.getElementById("yearFilter").value;

    const sections =
        document.querySelectorAll(".year-section");

    let visibleCount = 0;

    sections.forEach(section => {

        const sectionYear =
            section.getAttribute("data-year");

        const publications =
            section.querySelectorAll(".publication");

        let sectionVisible = 0;

        publications.forEach(publication => {

            const text =
                publication.innerText.toLowerCase();

            const matchesSearch =
                text.includes(search);

            const matchesYear =
                year === "all" ||
                sectionYear === year;

            if (matchesSearch && matchesYear) {

                publication.style.display = "";

                sectionVisible++;
                visibleCount++;

            } else {

                publication.style.display = "none";

            }

        });

        section.style.display =
            sectionVisible > 0 ? "" : "none";

    });

    document.getElementById("noResults").style.display =
        visibleCount === 0 ? "block" : "none";
}

</script>

</body>
</html>
"""

    return html


def main():

    bib_path = Path(BIB_FILE)

    if not bib_path.exists():

        print(f"ERROR: {BIB_FILE} was not found.")

        raise SystemExit(1)

    print(f"Reading {BIB_FILE}...")

    with open(
        bib_path,
        "r",
        encoding="utf-8"
    ) as bibtex_file:

        bib_database = bibtexparser.load(bibtex_file)

    publications = [
        get_publication(entry)
        for entry in bib_database.entries
        if entry.get("ENTRYTYPE", "").lower() in
        ["article", "inproceedings", "incollection", "book", "phdthesis", "mastersthesis"]
    ]

    # Sort newest first
    publications.sort(
        key=lambda x: x["year_number"],
        reverse=True
    )

    print(f"Found {len(publications)} publications.")

    html = generate_html(publications)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as output:

        output.write(html)

    print(f"Successfully generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
