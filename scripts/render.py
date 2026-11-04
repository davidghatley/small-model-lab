#!/usr/bin/env python3
"""Render HTML to PNG at a fixed 1280x800 viewport (reused by E1).

CLI:  .venv/bin/python scripts/render.py page.html out.png
API:  from render import render_html, render_file          # return Path (compatible)
      from render import render_html_info, Renderer        # also report webfont status
Waits for network idle and document.fonts.ready. Info dict:
  {"fonts_ok": bool, "font_failures": [str], "fonts_declared": [family, ...]}
"""
import sys
from pathlib import Path

VIEWPORT = {"width": 1280, "height": 800}

_FONT_JS = """() => {
  const out = {declared: [], failed: []};
  for (const f of document.fonts) {
    out.declared.push(f.family);
    if (f.status === 'error') out.failed.push(f.family);
  }
  return out;
}"""


def _render(pg, html, out, full_page, info_out):
    failed_urls = []
    pg.on("requestfailed", lambda r: failed_urls.append(r.url) if r.resource_type in ("font", "stylesheet") else None)
    pg.on("response", lambda r: failed_urls.append(r.url) if r.request.resource_type in ("font", "stylesheet") and r.status >= 400 else None)
    pg.set_content(html, wait_until="networkidle")
    pg.evaluate("document.fonts.ready.then(() => true)")
    pg.wait_for_timeout(100)
    f = pg.evaluate(_FONT_JS)
    pg.screenshot(path=str(out), full_page=full_page)  # default: exactly 1280x800
    fails = sorted(set(f["failed"])) + [f"url:{u}" for u in sorted(set(failed_urls))]
    info_out.update(fonts_ok=not fails, font_failures=fails, fonts_declared=sorted(set(f["declared"])))


class Renderer:
    """Reusable browser for many renders."""
    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._p = sync_playwright().start()
        self._b = self._p.chromium.launch()
        return self

    def __exit__(self, *a):
        self._b.close(); self._p.stop()

    def render(self, html: str, out_png, full_page: bool = False) -> dict:
        out = Path(out_png); out.parent.mkdir(parents=True, exist_ok=True)
        pg = self._b.new_page(viewport=VIEWPORT, device_scale_factor=1)
        info = {}
        try:
            _render(pg, html, out, full_page, info)
        finally:
            pg.close()
        return info


def render_html_info(html: str, out_png, full_page: bool = False) -> dict:
    with Renderer() as r:
        return r.render(html, out_png, full_page)


def render_html(html: str, out_png, full_page: bool = False) -> Path:
    render_html_info(html, out_png, full_page)
    return Path(out_png)


def render_file(html_path, out_png, **kw) -> Path:
    return render_html(Path(html_path).read_text(), out_png, **kw)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: render.py page.html out.png")
    info = render_html_info(Path(sys.argv[1]).read_text(), sys.argv[2])
    print(sys.argv[2], "fonts_ok" if info["fonts_ok"] else f"FONT FAILURES: {info['font_failures']}")
