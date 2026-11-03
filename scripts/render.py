#!/usr/bin/env python3
"""Render HTML to PNG at a fixed 1280x800 viewport (reused by E1).

CLI:  .venv/bin/python scripts/render.py page.html out.png
API:  from render import render_html, render_file
"""
import sys
from pathlib import Path

VIEWPORT = {"width": 1280, "height": 800}


def render_html(html: str, out_png, full_page: bool = False) -> Path:
    from playwright.sync_api import sync_playwright
    out = Path(out_png)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport=VIEWPORT, device_scale_factor=1)
        pg.set_content(html, wait_until="load")
        pg.screenshot(path=str(out), full_page=full_page)  # default: exactly 1280x800
        b.close()
    return out


def render_file(html_path, out_png, **kw) -> Path:
    return render_html(Path(html_path).read_text(), out_png, **kw)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: render.py page.html out.png")
    print(render_file(sys.argv[1], sys.argv[2]))
