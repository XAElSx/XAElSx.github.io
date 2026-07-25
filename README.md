# Daniela Patrício — Portfolio Site

Personal portfolio for **Daniela Assunção Santana Patrício**, Data Analyst / Data Engineer.

Static site built with plain HTML, CSS, and vanilla JavaScript — no build step, deploys instantly on GitHub Pages.

---

## Quick preview (locally)

No build tools required. Pick either option:

**Option A — double-click**

Open `index.html` directly in your browser.

**Option B — run a local server (recommended, so relative paths match GitHub Pages)**

```bash
cd "/Users/danielapatricio/Documents/Claude/Projects/GithubPage"
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

---

## Deploy to GitHub Pages — step by step

This is set up as a **user site** (`https://DanielaPatricio.github.io`). Follow these steps exactly once, then every `git push` updates the live site.

### 1. Create a GitHub account (if you don't have one)

- Sign up at https://github.com
- Pick a username — this will be part of your site URL. Good choices: `danielapatricio`, `dapatricio`, `danielaaspatricio`, etc.

### 2. Create the repository

1. Go to https://github.com/new
2. **Repository name:** `DanielaPatricio.github.io` — exactly your username followed by `.github.io`. This magic name is what turns it into a user site.
3. Visibility: **Public**
4. **Do not** initialize with a README (you already have files).
5. Click **Create repository**.

### 3. Push this folder to GitHub

From inside this folder, in a terminal:

```bash
cd "/Users/danielapatricio/Documents/Claude/Projects/GithubPage"
git init
git add .
git commit -m "Initial portfolio site"
git branch -M main
git remote add origin https://github.com/DanielaPatricio/DanielaPatricio.github.io.git
git push -u origin main
```

Replace `DanielaPatricio` with your actual GitHub username in both places.

### 4. Enable GitHub Pages

1. Go to your new repo → **Settings** → **Pages**
2. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: **main**, folder: **/ (root)**
3. Save.
4. Wait ~1 minute, then visit `https://DanielaPatricio.github.io`.

### 5. Update the GitHub link on the site

Open `index.html` and search for `DanielaPatricio` — replace both occurrences (in the Contact section) with your actual username, commit, and push:

```bash
git add index.html
git commit -m "Update GitHub username"
git push
```

---

## Updating the site

Any time you want to change content:

```bash
# edit files in your editor...
git add .
git commit -m "Describe your change"
git push
```

GitHub Pages rebuilds automatically within a minute.

---

## Project structure

```
GithubPage/
├── index.html           # All content: hero, about, experience, skills, projects, interests, contact
├── css/
│   └── styles.css       # Theme (dark + cyan), layout, components, responsive rules
├── js/
│   └── main.js          # Reveal-on-scroll, mobile nav, spotlight effects, footer stamps
├── assets/
│   ├── Daniela_Patricio_CV.pdf   # Linked from "Download CV" button
│   └── favicon.svg               # Browser tab icon
└── README.md
```

### Where to edit what

| Change | File | Where |
| --- | --- | --- |
| Headline or tagline | `index.html` | `<header class="hero">` block near the top |
| Experience role | `index.html` | `<ol class="timeline">` block |
| Skills / tech stack | `index.html` | `<div class="skills-grid">` block |
| Projects (replace placeholders) | `index.html` | `<div class="projects-grid">` block |
| Contact links | `index.html` | `<section id="contact">` block |
| Colors / theme | `css/styles.css` | `:root` tokens at the top |

---

## Portfolio projects — how to add one

When you have a real project to show, replace one of the placeholder cards in the `projects-grid`:

```html
<article class="project-card">
  <div class="project-head">
    <span class="project-tag tag-dashboard">Dashboard</span>
    <a class="project-status mono" href="https://github.com/<you>/<repo>" target="_blank" rel="noopener">view →</a>
  </div>
  <h3 class="project-title">Your project name</h3>
  <p class="project-desc">One- or two-sentence summary of what it does and why it matters.</p>
  <div class="project-stack mono">
    <span>Tool A</span><span>Tool B</span><span>Tool C</span>
  </div>
</article>
```

Available tag classes: `tag-dashboard`, `tag-pipeline`, `tag-analysis`, `tag-sandbox`.

---

## Portfolio project ideas (to get started)

Inspired directly by your CV, these translate well into public portfolio pieces (no proprietary data required):

1. **Quality of Service dashboard — case study.** Recreate the pattern on a public dataset (e.g. ANA aeroporto delays, TfL performance data). Full Power BI file + DAX breakdown write-up.
2. **Near real-time alarms reference architecture.** Diagram + sample ADF / Power Automate flow that triggers on threshold breaches. Explain when to use this vs. a scheduled batch.
3. **NPS deep-dive.** Pick a public review dataset (Kaggle, Yelp), compute NPS by segment, build a Power BI report with drill-throughs. Document the methodology.
4. **SQL-pattern cookbook.** A repo of reusable patterns you've applied at work (slowly-changing dimensions, date dimensions, data quality checks, window-function recipes) — each with a `README` and sample data.
5. **Agentic AI for ETL — experiment log.** A public journal of pair-programming SQL refactors or pipeline docs with Claude Code / Cursor. Low-stakes, high-personality content that matches the tone of your current CV.

Even 1–2 of these, published, move the portfolio from "promising" to "proof-of-work".

---

## License

Content © Daniela Patrício. Code (HTML/CSS/JS) free to reuse for personal portfolios.
