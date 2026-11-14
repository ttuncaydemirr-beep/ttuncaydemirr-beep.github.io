#!/usr/bin/env python3
"""src/invite/og.html -> src/invite/og.png (1200x630, WhatsApp/Open Graph önizlemesi). Chrome gerekir."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

SRC = Path(__file__).resolve().parent.parent / "src" / "invite"
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    pg.goto((SRC / "og.html").as_uri())
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(300)
    tmp = SRC / "og.tmp.png"
    pg.screenshot(path=str(tmp))
    b.close()
Image.open(tmp).convert("RGB").quantize(64).save(SRC / "og.png", optimize=True)
tmp.unlink()
print("og.png üretildi")
