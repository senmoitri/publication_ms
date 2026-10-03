# Academic Website

A multi-page academic website for GitHub Pages.

## Pages

- `index.html` — Home
- `about.html` — About
- `research.html` — Research
- `publications.html` — Publications (generated automatically)
- `students.html` — Students
- `teaching.html` — Teaching
- `cv.html` — CV
- `contact.html` — Contact

## Publication workflow

`own-bib.bib` is the single source of truth for publications.

GitHub Actions runs:

`own-bib.bib → generate.py → publications.html → GitHub Pages`

Keep `own-bib.bib` in the repository root. Publication types are automatically grouped into Journal Articles, Conference Proceedings, Book Chapters, Books, PhD Theses and Master's Theses.

## Setup

1. Copy these files into the existing `publication_ms` repository.
2. Keep your existing `own-bib.bib`.
3. Replace the placeholder text in the HTML pages.
4. Put your CV PDF in the root as `CV.pdf` if desired.
5. In GitHub: Settings → Pages → Source → GitHub Actions.
6. Commit and push to `main`.
