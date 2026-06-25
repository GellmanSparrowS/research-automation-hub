"""Automated blog content pipeline.

Picks topics from a curated pool, generates markdown posts,
and rebuilds the static site. Designed to run on a schedule
(cron / GitHub Actions weekly).

Usage: python content_planner.py [--dry-run] [--count N]
"""

import os
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).parent
CONTENT_DIR = BASE / "content" / "posts"
PLAN_FILE = BASE / "topic_pool.json"
OUTPUT_DIR = BASE / "output"

# ── Topic pool: curated SEO keywords for academic research niche ──

DEFAULT_TOPICS = [
    {
        "title": "Best Python Libraries for Academic Research in {year}",
        "slug": "best-python-libraries-academic-research",
        "description": "A curated list of Python libraries every researcher should know: data analysis, visualization, and automation tools.",
        "keywords": ["python", "research tools", "data analysis", "academic software"],
        "outline": [
            "Why Python for research?",
            "Data analysis: pandas, numpy, scipy",
            "Visualization: matplotlib, seaborn, plotly",
            "PDF processing: PyMuPDF, pdfplumber",
            "Reference management: bibtexparser",
            "Automation: invoke, fabric",
            "Getting started in 10 minutes",
        ],
    },
    {
        "title": "How to Write Your First Academic Paper with LaTeX and Overleaf",
        "slug": "first-academic-paper-latex-overleaf",
        "description": "A step-by-step guide for beginners: setting up Overleaf, structuring your paper, adding figures and tables, and managing references.",
        "keywords": ["latex", "overleaf", "academic writing", "paper template"],
        "outline": [
            "Why LaTeX instead of Word?",
            "Setting up Overleaf in 2 minutes",
            "Paper structure: sections every paper needs",
            "Adding figures with proper captions",
            "Building tables with booktabs",
            "Managing references with BibTeX",
            "Common LaTeX errors and how to fix them",
        ],
    },
    {
        "title": "Automated Data Visualization for Materials Science",
        "slug": "data-visualization-materials-science",
        "description": "Generate publication-quality plots from your experimental data using Python. Covers XRD patterns, stress-strain curves, and thermal analysis.",
        "keywords": ["data visualization", "materials science", "python plots", "XRD", "publication figures"],
        "outline": [
            "Common plot types in materials science",
            "Reading instrument data files",
            "XRD pattern plotting with baseline correction",
            "Stress-strain curves with elastic modulus fitting",
            "TGA/DSC multi-panel plots",
            "Exporting for journals: resolution and format",
            "Automating figure generation for multiple samples",
        ],
    },
    {
        "title": "PhD Productivity: 10 Automation Scripts That Save Hours Every Week",
        "slug": "phd-productivity-automation-scripts",
        "description": "Ten Python scripts that automate the most repetitive parts of PhD life: email reminders, file organization, data backup, and report generation.",
        "keywords": ["phd productivity", "automation", "python scripts", "time saving", "grad school"],
        "outline": [
            "Why automation matters for PhD students",
            "Script 1-3: File organization and renaming",
            "Script 4-5: Automated data backup",
            "Script 6-7: Email and calendar automation",
            "Script 8: Meeting notes generator",
            "Script 9-10: Report and figure automation",
            "How to run these on a schedule",
        ],
    },
    {
        "title": "How to Build a Personal Research Knowledge Base with Notion",
        "slug": "research-knowledge-base-notion",
        "description": "Organize papers, notes, experiment logs, and project plans in one searchable Notion workspace. Template included.",
        "keywords": ["notion", "knowledge management", "research organization", "second brain"],
        "outline": [
            "What is a research knowledge base?",
            "Setting up your Notion workspace",
            "Paper reading tracker with automatic metadata",
            "Experiment logbook template",
            "Project management with timelines",
            "Connecting everything with relations",
            "Weekly review workflow",
        ],
    },
    {
        "title": "Machine Learning for Materials Discovery: Getting Started Guide",
        "slug": "machine-learning-materials-discovery-guide",
        "description": "An introduction to applying machine learning to materials science: datasets, models, and practical pipelines for property prediction.",
        "keywords": ["machine learning", "materials discovery", "AI4S", "property prediction", "deep learning"],
        "outline": [
            "Why ML for materials science?",
            "Key public datasets: Materials Project, AFLOW, OQMD",
            "Feature engineering for materials",
            "Training your first property prediction model",
            "Graph neural networks for crystal structures",
            "Evaluating model performance",
            "Deploying models for high-throughput screening",
        ],
    },
    {
        "title": "Free Tools for Academic Writing: Grammar, Plagiarism, and Reference Management",
        "slug": "free-tools-academic-writing",
        "description": "A comparison of free academic writing tools: Grammarly alternatives, plagiarism checkers, and reference managers that cost nothing.",
        "keywords": ["academic writing", "free tools", "grammar checker", "plagiarism", "reference manager"],
        "outline": [
            "Grammar and style: LanguageTool vs Grammarly",
            "Plagiarism checking: free options compared",
            "Reference managers: Zotero vs Mendeley vs Paperpile",
            "Collaborative writing: Overleaf and Google Docs",
            "Figure preparation: Inkscape and GIMP",
            "Putting it all together: a free writing workflow",
        ],
    },
    {
        "title": "How to Read 10 Papers a Day: Speed Reading for Researchers",
        "slug": "speed-reading-research-papers",
        "description": "A systematic approach to reading academic papers efficiently. Learn to extract key information without reading every word.",
        "keywords": ["paper reading", "literature review", "speed reading", "research efficiency"],
        "outline": [
            "Why reading every paper fully is a trap",
            "The three-pass method: scan, read, deep-dive",
            "What to look for in abstract and figures first",
            "Building a paper summary template",
            "Using AI tools for paper summarization",
            "Organizing your reading notes for future recall",
            "When to read deeply vs when to move on",
        ],
    },
    {
        "title": "Git for Researchers: Version Control for Papers and Code",
        "slug": "git-for-researchers",
        "description": "Why every researcher should use Git, and how to version-control your papers, data, and analysis scripts without the complexity.",
        "keywords": ["git", "version control", "reproducible research", "github", "collaboration"],
        "outline": [
            "Why Git is essential for reproducible research",
            "Setting up Git in 5 minutes",
            "Version-controlling your paper drafts",
            "Managing data and experiment versions",
            "Collaborating with co-authors via GitHub",
            "Using branches for manuscript revisions",
            "GitHub releases for paper submissions",
        ],
    },
    {
        "title": "Automated Experiment Data Processing Pipeline in Python",
        "slug": "automated-experiment-data-pipeline",
        "description": "Build an end-to-end pipeline that reads raw instrument data, processes it, generates figures, and produces a summary report automatically.",
        "keywords": ["data pipeline", "experiment automation", "python", "data processing", "lab automation"],
        "outline": [
            "The problem with manual data processing",
            "Designing your pipeline architecture",
            "Reading diverse instrument formats",
            "Standardizing and cleaning raw data",
            "Automated statistical analysis",
            "Figure generation with consistent styling",
            "Generating automated PDF reports",
        ],
    },
    {
        "title": "How to Choose a Research Topic That Leads to Publications",
        "slug": "choose-research-topic-publications",
        "description": "Strategic advice for early-career researchers: how to identify high-impact, publishable research questions in your field.",
        "keywords": ["research topic", "phd advice", "publication strategy", "research planning"],
        "outline": [
            "The publishability test: will this lead to papers?",
            "Finding gaps in the literature systematically",
            "Balancing novelty with feasibility",
            "Using bibliometric tools to assess topic trends",
            "Talking to your advisor about topic selection",
            "Pivoting when a topic is not working",
        ],
    },
    {
        "title": "Building a Personal Academic Website in One Afternoon",
        "slug": "personal-academic-website",
        "description": "Create a professional academic homepage with your publications, CV, and research summary using free tools and GitHub Pages.",
        "keywords": ["academic website", "personal homepage", "github pages", "academic profile"],
        "outline": [
            "Why every researcher needs a website",
            "Choosing a static site generator",
            "Setting up GitHub Pages with a custom domain",
            "Essential pages: about, publications, CV, research",
            "Adding your publication list automatically from BibTeX",
            "SEO tips so people find your page",
            "Updating your site painlessly",
        ],
    },
    {
        "title": "Reproducible Research: Docker and Conda Environments for Scientists",
        "slug": "reproducible-research-docker-conda",
        "description": "Ensure your computational research is reproducible by others (and your future self) using Docker containers and Conda environments.",
        "keywords": ["reproducible research", "docker", "conda", "computational science", "environment management"],
        "outline": [
            "The reproducibility crisis in computational science",
            "Conda environments: isolating dependencies",
            "Exporting and sharing environment.yml files",
            "Introduction to Docker for scientists",
            "Writing a Dockerfile for your research project",
            "Publishing containers on Docker Hub",
            "Integrating with Jupyter and computational clusters",
        ],
    },
    {
        "title": "Writing Effective Peer Reviews: A Guide for Early-Career Researchers",
        "slug": "writing-peer-reviews-guide",
        "description": "How to write constructive, professional peer reviews that help authors and build your reputation as a reviewer.",
        "keywords": ["peer review", "academic writing", "reviewer guide", "publication process"],
        "outline": [
            "Why reviewing papers matters for your career",
            "Reading a manuscript like a reviewer",
            "Structuring your review: summary, major, minor",
            "Giving constructive feedback without being harsh",
            "Common statistical and methodological issues to flag",
            "How long should a review take?",
            "Building a reviewer profile and getting invited",
        ],
    },
    {
        "title": "Converting Your Thesis into Journal Papers: A Practical Strategy",
        "slug": "thesis-to-journal-papers",
        "description": "How to break down your PhD thesis into publishable journal articles: choosing angles, restructuring content, and targeting journals.",
        "keywords": ["thesis", "journal papers", "phd", "publication strategy", "academic writing"],
        "outline": [
            "Thesis vs journal paper: key differences",
            "Identifying publishable units in your thesis",
            "Restructuring chapters into paper format",
            "Choosing target journals for each paper",
            "Handling overlapping content and self-citation",
            "Timeline: when to start converting",
            "Working with your advisor on co-authored papers",
        ],
    },
    {
        "title": "Deep Learning for Image Analysis in Materials Science",
        "slug": "deep-learning-image-analysis-materials",
        "description": "Apply convolutional neural networks to analyze SEM, TEM, and optical microscopy images for automated microstructure characterization.",
        "keywords": ["deep learning", "image analysis", "SEM", "TEM", "microstructure", "CNN"],
        "outline": [
            "Why automate image analysis?",
            "Preparing microscopy images for deep learning",
            "Semantic segmentation for phase identification",
            "Object detection for particle size analysis",
            "Transfer learning with limited labeled data",
            "Tools: PyTorch, fastai, and ImageJ integration",
            "Publishing ML-enhanced materials characterization",
        ],
    },
]


def load_topics():
    """Load topic pool from JSON, or initialize from defaults."""
    if PLAN_FILE.exists():
        with open(PLAN_FILE, "r") as f:
            return json.load(f)
    save_topics(DEFAULT_TOPICS)
    return DEFAULT_TOPICS.copy()


def save_topics(topics):
    with open(PLAN_FILE, "w") as f:
        json.dump(topics, f, indent=2)


def _simple_md(title, desc, outline):
    """Generate a clean markdown blog post from outline."""
    today = datetime.now().strftime("%Y-%m-%d")
    slug = title.lower().replace(" ", "-").replace("?", "").replace(",", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")

    lines = [
        "---",
        f'title: "{title}"',
        f'date: "{today}"',
        f'slug: "{slug}"',
        f'description: "{desc}"',
        "---",
        "",
    ]
    for i, point in enumerate(outline):
        lines.append(f"## {point}")
        # Generate a short paragraph for each outline point
        lines.append("")
        if i == 0:
            lines.append(
                f"Every researcher faces this challenge. Whether you are a first-year PhD student "
                f"or a seasoned postdoc, {point.lower().rstrip('?')} is something worth getting right. "
                f"This guide covers practical approaches you can apply today."
            )
        elif i == len(outline) - 1:
            lines.append(
                f"In summary, {point.lower().rstrip('?')} brings everything together. "
                f"Start small, iterate, and build systems that work for your specific research workflow. "
                f"The tools and techniques described here will save you significant time over the course of your PhD."
            )
        else:
            lines.append(
                f"When approaching {point.lower()}, start by identifying your specific needs. "
                f"Different research fields and workflows require different solutions. "
                f"Experiment with the methods described, measure what works, and adapt accordingly."
            )
        lines.append("")

    return "\n".join(lines), slug


def generate_posts(count=1, dry_run=False):
    """Generate `count` new blog posts from the topic pool."""
    topics = load_topics()
    available = [t for t in topics if not t.get("published", False)]

    if not available:
        print("[planner] All topics published. Reset pool and regenerate.")
        for t in topics:
            t["published"] = False
        available = topics

    generated = []
    for _ in range(min(count, len(available))):
        topic = random.choice(available)
        available.remove(topic)

        title = topic["title"].format(year=datetime.now().year)
        md, slug = _simple_md(title, topic["description"], topic["outline"])

        filepath = CONTENT_DIR / f"{slug}.md"

        if dry_run:
            print(f"[DRY RUN] Would write: {filepath.name}")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[planner] Generated: {filepath.name}")

        topic["published"] = True
        topic["published_date"] = datetime.now().isoformat()
        generated.append(slug)

    save_topics(topics)
    return generated


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate SEO blog posts from curated topic pool.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files.")
    parser.add_argument("--count", type=int, default=1, help="Number of posts to generate.")
    args = parser.parse_args()

    print(f"Topic pool: {len(load_topics())} total")
    slugs = generate_posts(count=args.count, dry_run=args.dry_run)

    if not args.dry_run:
        # Rebuild the site
        import subprocess
        result = subprocess.run(
            ["python", str(BASE / "generate.py")],
            capture_output=True, text=True, cwd=str(BASE)
        )
        print(result.stdout)

    print(f"Done. {len(slugs)} posts generated.")


if __name__ == "__main__":
    main()
