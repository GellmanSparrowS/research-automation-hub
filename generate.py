"""Static site generator for niche SEO blog.
Generates clean HTML pages deployable to GitHub Pages / Netlify / Vercel.
"""

import os
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content"
OUTPUT_DIR = BASE_DIR / "docs"
TEMPLATE_DIR = BASE_DIR / "templates"

SITE_TITLE = "Research Automation Hub"
SITE_DESC = "Tools, tips, and automation for academic researchers"
BASE_URL = "https://YOUR_USERNAME.github.io/research-automation-hub"

# ── Template ──────────────────────────────────────────

def base_template(title, content, meta_desc="", canonical=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {SITE_TITLE}</title>
<meta name="description" content="{meta_desc or SITE_DESC}">
{f'<link rel="canonical" href="{BASE_URL}{canonical}">' if canonical else ''}
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,-apple-system,sans-serif;line-height:1.6;color:#1a1a1a;max-width:720px;margin:0 auto;padding:20px}}
  header{{border-bottom:1px solid #e5e5e5;padding-bottom:16px;margin-bottom:32px}}
  header h1{{font-size:1.5rem}}
  header p{{color:#666;font-size:.9rem}}
  nav{{display:flex;gap:16px;margin-top:8px}}
  nav a{{color:#2563eb;text-decoration:none;font-size:.9rem}}
  article h2{{font-size:1.3rem;margin:24px 0 8px}}
  article h3{{font-size:1.1rem;margin:20px 0 8px}}
  article p{{margin:8px 0}}
  article ul, article ol{{margin:8px 0;padding-left:24px}}
  article li{{margin:4px 0}}
  article pre{{background:#f5f5f5;padding:12px;border-radius:6px;overflow-x:auto;font-size:.85rem;margin:12px 0}}
  article code{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:.9em}}
  .post-card{{border:1px solid #e5e5e5;border-radius:8px;padding:16px;margin:12px 0}}
  .post-card h3{{margin:0 0 4px}}
  .post-card time{{color:#888;font-size:.8rem}}
  footer{{border-top:1px solid #e5e5e5;margin-top:40px;padding-top:16px;color:#888;font-size:.8rem}}
  .cta{{background:#f0f7ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px;margin:24px 0}}
  .cta a{{font-weight:600}}
</style>
</head>
<body>
<header>
  <h1><a href="index.html" style="color:inherit;text-decoration:none">{SITE_TITLE}</a></h1>
  <p>{SITE_DESC}</p>
  <nav>
    <a href="index.html">Home</a>
    <a href="tools.html">Tools</a>
    <a href="blog.html">Blog</a>
  </nav>
</header>
<main>{content}</main>
<footer>
  <p>&copy; {datetime.now().year} {SITE_TITLE}. Built for researchers, by researchers.</p>
</footer>
</body>
</html>"""


def parse_md(filepath):
    """Simple markdown-to-HTML for blog posts."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract frontmatter
    fm = {}
    if text.startswith("---"):
        end = text.index("---", 3)
        for line in text[3:end].strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        text = text[end+3:].strip()

    # Basic markdown: h2, h3, p, ul/ol, code blocks, inline code
    html = []
    in_list = False
    list_type = ""
    for line in text.split("\n"):
        if line.startswith("## "):
            if in_list: html.append(f"</{list_type}>"); in_list = False
            html.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            if in_list: html.append(f"</{list_type}>"); in_list = False
            html.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("- "):
            if not in_list or list_type != "ul":
                if in_list: html.append(f"</{list_type}>")
                html.append("<ul>")
                in_list = True; list_type = "ul"
            html.append(f"<li>{_inline(line[2:])}</li>")
        elif re.match(r'^\d+\. ', line):
            if not in_list or list_type != "ol":
                if in_list: html.append(f"</{list_type}>")
                html.append("<ol>")
                in_list = True; list_type = "ol"
            stripped = re.sub(r'^\d+\.\s*', '', line)
            html.append(f"<li>{_inline(stripped)}</li>")
        elif line.strip() == "":
            if in_list: html.append(f"</{list_type}>"); in_list = False
        else:
            if in_list: html.append(f"</{list_type}>"); in_list = False
            html.append(f"<p>{_inline(line)}</p>")
    if in_list: html.append(f"</{list_type}>")

    content = "\n".join(html)
    return fm, content


def _inline(text):
    """Handle inline markdown: **bold**, [link](url), `code`."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


# ── Generate ──────────────────────────────────────────

def build():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    posts = []

    # Build blog posts
    blog_out = OUTPUT_DIR / "blog"
    os.makedirs(blog_out, exist_ok=True)

    for md_file in sorted((CONTENT_DIR / "posts").glob("*.md"), reverse=True):
        fm, html = parse_md(str(md_file))
        slug = fm.get("slug", md_file.stem)
        output_path = blog_out / f"{slug}.html"
        page = base_template(
            title=fm.get("title", "Post"),
            content=f"<article><h2>{fm.get('title', '')}</h2>\n<time>{fm.get('date', '')}</time>\n{html}</article>",
            meta_desc=fm.get("description", ""),
            canonical=f"/blog/{slug}.html",
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(page)
        posts.append(fm)

    # Home page
    cards = ""
    for p in posts[:10]:
        cards += f"""<div class="post-card">
  <h3><a href="blog/{p.get('slug','')}.html">{p.get('title','')}</a></h3>
  <time>{p.get('date','')}</time>
  <p>{p.get('description','')}</p>
</div>\n"""

    home = base_template(
        title="Home",
        content=f"""<h2>Latest Posts</h2>\n{cards}""",
        meta_desc=SITE_DESC,
    )
    with open(OUTPUT_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(home)

    # Tools page
    tools_page = base_template(
        title="Tools",
        content="""<h2>Research Automation Tools</h2>
<div class="cta">
<strong>Researcher's Toolkit</strong> — 5 Python modules to automate your literature workflow.<br>
<a href="#">Get it on Gumroad</a>
</div>
<h3>Other Recommended Tools</h3>
<ul>
<li><strong>Zotero</strong> — Free reference manager with browser integration</li>
<li><strong>Paperpile</strong> — Clean reference management for Google Docs</li>
<li><strong>Connected Papers</strong> — Visual paper citation graphs</li>
<li><strong>Semantic Scholar</strong> — AI-powered academic search</li>
<li><strong>Overleaf</strong> — Collaborative LaTeX editor</li>
</ul>
<h3>Automation Scripts</h3>
<p>Check out our <a href="blog.html">blog</a> for free Python scripts to automate your research workflow.</p>""",
        meta_desc="Best tools and automation scripts for academic researchers",
    )
    with open(OUTPUT_DIR / "tools.html", "w", encoding="utf-8") as f:
        f.write(tools_page)

    # Blog index
    blog_index = base_template(
        title="Blog",
        content=f"<h2>All Posts</h2>\n{cards}",
        meta_desc="Tips and tools for research automation",
    )
    with open(OUTPUT_DIR / "blog.html", "w", encoding="utf-8") as f:
        f.write(blog_index)

    print(f"Built {len(posts)} posts in {OUTPUT_DIR}")
    print("Deploy: push 'output/' to GitHub Pages or drag to Netlify.")


if __name__ == "__main__":
    build()
