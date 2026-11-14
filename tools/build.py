#!/usr/bin/env python3
"""Demir Games Studio sitesini üretir.

Girdiler (src/):
  content.json            uygulama kartları, stüdyo metinleri, arayüz metinleri (tr/en/de/ar)
  apps.json               uygulamaların yayın durumu ve sırası
  tokens.css              görsel kimlik (renkler, yazı tipleri)
  privacy/<slug>/<lang>.html   gizlilik politikası parçaları
Çıktılar depo köküne yazılır. Çalıştırma:  python3 tools/build.py
"""
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SITE_URL = "https://ttuncaydemirr-beep.github.io"
LANGS = ["tr", "en", "de", "ar"]
LANG_NAMES = {"tr": "Türkçe", "en": "English", "de": "Deutsch", "ar": "العربية"}
EMAIL = "nilkaren.tuncay.demir@gmail.com"

content = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
apps_cfg = json.loads((SRC / "apps.json").read_text(encoding="utf-8"))
apps_by_slug = {a["slug"]: a for a in content["apps"]}


def esc(s):
    return html.escape(str(s), quote=True)


def ui(lang, key):
    return content["ui"][lang].get(key) or content["ui"]["en"].get(key, key)


def dir_of(lang):
    return "rtl" if lang == "ar" else "ltr"


def page(lang, title, body, *, path, alternates=None, noindex=False, description="", head_extra=""):
    """path: sitenin kökünden itibaren bu sayfanın adresi (ör. /tr/)."""
    alt = ""
    if alternates:
        for l, p in alternates.items():
            alt += f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}{p}">\n'
        alt += f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}{alternates.get("en", path)}">\n'
    robots = '<meta name="robots" content="noindex, nofollow">\n' if noindex else ""
    desc = f'<meta name="description" content="{esc(description)}">\n' if description else ""
    lang_links = ""
    if alternates:
        items = []
        for l in LANGS:
            cur = ' aria-current="true"' if l == lang else ""
            items.append(f'<a href="{alternates[l]}" lang="{l}" hreflang="{l}"{cur}>{LANG_NAMES[l]}</a>')
        lang_links = f'<nav class="langs" aria-label="{esc(ui(lang, "language"))}">{"".join(items)}</nav>'
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{dir_of(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{desc}{robots}{alt}<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/site.css">
{head_extra}</head>
<body>
<a class="skip" href="#main">{esc(ui(lang, "skip_to_content"))}</a>
<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="/{lang}/"><img src="/assets/img/logo.svg" alt="" width="32" height="32"><span>Demir Games Studio</span></a>
    {lang_links}
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="wrap">
    <p><bdi>{esc(ui(lang, "footer"))}</bdi> · <a href="mailto:{EMAIL}">{EMAIL}</a></p>
  </div>
</footer>
</body>
</html>
"""


def alternates_for(fmt):
    return {l: fmt.format(lang=l) for l in LANGS}


def status_badge(lang, status):
    key = {"live": None, "testing": "in_testing", "soon": "coming_soon"}.get(status)
    return f'<span class="badge">{esc(ui(lang, key))}</span>' if key else ""


def app_card(lang, cfg):
    a = apps_by_slug[cfg["slug"]]
    t = a[lang]
    icon = Path(a["icon_192"]).name if a.get("icon_192") else None
    icon_html = (f'<img class="app-icon" src="/assets/icons/{esc(icon)}" alt="" width="96" height="96" loading="lazy">'
                 if icon else '<span class="app-icon app-icon--empty" aria-hidden="true"></span>')
    play = ""
    if cfg.get("status") == "live":
        play = (f'<a class="btn" href="https://play.google.com/store/apps/details?id={esc(a["package"])}" '
                f'rel="noopener">{esc(ui(lang, "get_on_google_play"))}</a>')
    privacy = f'<a class="link" href="/privacy/{esc(a["slug"])}/?lang={lang}">{esc(ui(lang, "privacy_policy"))}</a>'
    shots = ""
    sdir = SRC / "shots" / a["slug"]
    files = [f for f in (f"{lang}-1.webp", f"{lang}-2.webp") if (sdir / f).is_file()]
    if files:
        from PIL import Image
        def dims(f):
            with Image.open(sdir / f) as im:
                return im.size
        imgs = "".join(
            f'<img src="/assets/shots/{esc(a["slug"])}/{f}" alt="{esc(t["name"])} – {i}" width="{dims(f)[0]}" height="{dims(f)[1]}" loading="lazy" decoding="async">'
            for i, f in enumerate(files, 1))
        shots = f'<div class="shots">{imgs}</div>'
    return f"""<article class="app" id="{esc(a['slug'])}">
  {icon_html}
  <div class="app-body">
    <h3>{esc(t['name'])} {status_badge(lang, cfg.get('status'))}</h3>
    <p class="tagline">{esc(t['tagline'])}</p>
    <p>{esc(t['description'])}</p>
    <p class="actions">{play}{privacy}</p>
  </div>
  {shots}
</article>"""


def build_home(lang):
    st = content["studio"][lang]
    cards = "\n".join(app_card(lang, c) for c in apps_cfg["apps"])
    strip = "".join(
        f'<li><a href="#{esc(c["slug"])}"><img src="/assets/icons/{Path(apps_by_slug[c["slug"]]["icon_192"]).name}" '
        f'alt="{esc(apps_by_slug[c["slug"]][lang]["name"])}" width="72" height="72"></a></li>'
        for c in apps_cfg["apps"] if apps_by_slug[c["slug"]].get("icon_192"))
    body = f"""<section class="hero">
  <div class="wrap">
    <div class="hero-text">
      <h1>Demir Games Studio</h1>
      <p class="lead">{esc(st['intro'])}</p>
    </div>
    <ul class="hero-icons" aria-label="{esc(ui(lang, 'nav_apps'))}">{strip}</ul>
  </div>
</section>
<section class="wrap" id="apps" aria-labelledby="apps-h">
  <h2 id="apps-h">{esc(ui(lang, 'nav_apps'))}</h2>
  <div class="apps">
{cards}
  </div>
</section>
<section class="wrap" id="support" aria-labelledby="support-h">
  <h2 id="support-h">{esc(ui(lang, 'nav_support'))}</h2>
  <p>{esc(st['support'])}</p>
  <p><a class="btn btn--ghost" href="mailto:{EMAIL}">{EMAIL}</a></p>
</section>"""
    out = ROOT / lang / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(lang, f"Demir Games Studio – {ui(lang, 'nav_apps')}", body, path=f"/{lang}/",
                        alternates=alternates_for("/{lang}/"), description=st["intro"]), encoding="utf-8")


LANG_PICK_JS = """<script>
(function(){
  var L=["tr","en","de","ar"], q=new URLSearchParams(location.search).get("lang");
  var pick=L.indexOf(q)>=0?q:null;
  if(!pick){var n=(navigator.languages||[navigator.language||"en"]);
    for(var i=0;i<n.length&&!pick;i++){var c=(n[i]||"").slice(0,2).toLowerCase();if(L.indexOf(c)>=0)pick=c;}}
  pick=pick||"en";
  document.documentElement.setAttribute("data-lang",pick); document.documentElement.classList.add("js");
  document.addEventListener("DOMContentLoaded",function(){
    function show(l){
      document.querySelectorAll("[data-panel]").forEach(function(p){p.hidden=p.getAttribute("data-panel")!==l;});
      document.querySelectorAll("[data-tab]").forEach(function(b){b.setAttribute("aria-pressed",b.getAttribute("data-tab")===l?"true":"false");});
      document.documentElement.lang=l; document.documentElement.dir=(l==="ar")?"rtl":"ltr";
      var t=document.querySelector('[data-panel="'+l+'"]'); if(t&&t.dataset.title) document.title=t.dataset.title;
    }
    document.querySelectorAll("[data-tab]").forEach(function(b){b.addEventListener("click",function(){
      var l=b.getAttribute("data-tab"); show(l);
      try{history.replaceState(null,"","?lang="+l);}catch(e){}
    });});
    show(pick);
  });
})();
</script>
"""


def multilang_page(title_by_lang, panels_by_lang, *, back_label_key="back_to_studio", noindex=False, canonical=None):
    """Tek adreste dört dil; dil tarayıcıdan ya da ?lang= ile seçilir. JS yoksa tüm diller alt alta görünür."""
    tabs = "".join(
        f'<button type="button" data-tab="{l}" lang="{l}" aria-pressed="false">{LANG_NAMES[l]}</button>'
        for l in LANGS)
    panels = "\n".join(
        f'<section data-panel="{l}" lang="{l}" dir="{dir_of(l)}" data-title="{esc(title_by_lang[l])}">'
        f'<p class="back"><a href="/{l}/">{esc(ui(l, back_label_key))}</a></p>\n{panels_by_lang[l]}\n</section>'
        for l in LANGS)
    body = f"""<div class="wrap doc">
  <div class="tabs" role="group" aria-label="Language / Dil / Sprache / اللغة">{tabs}</div>
{panels}
</div>"""
    extra = (f'<link rel="canonical" href="{SITE_URL}{canonical}">\n' if canonical else "") + LANG_PICK_JS
    html_out = page("en", title_by_lang["en"], body, path="", noindex=noindex, head_extra=extra,
                    description=title_by_lang["en"])
    # Üst bilgi ve alt bilgi tek dilde olmasın: marka ve e-posta dilden bağımsız.
    return html_out.replace(f'<a class="brand" href="/en/">', '<a class="brand" href="/">')


def build_privacy():
    pdir = SRC / "privacy"
    index_items = {l: [] for l in LANGS}
    for cfg in apps_cfg["apps"]:
        slug = cfg["slug"]
        d = pdir / slug
        if not d.is_dir():
            print(f"UYARI: {slug} için gizlilik politikası yok, atlandı")
            continue
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        panels = {l: (d / f"{l}.html").read_text(encoding="utf-8") for l in LANGS}
        titles = {l: f'{meta["titles"][l]} · Demir Games Studio' for l in LANGS}
        out = ROOT / "privacy" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(multilang_page(titles, panels, canonical=f"/privacy/{slug}/"), encoding="utf-8")
        for l in LANGS:
            index_items[l].append(f'<li><a href="/privacy/{slug}/?lang={l}">{esc(meta["titles"][l])}</a></li>')
    panels = {l: f'<h1>{esc(ui(l, "nav_privacy"))}</h1>\n<ul class="plist">{"".join(index_items[l])}</ul>' for l in LANGS}
    titles = {l: f'{ui(l, "nav_privacy")} · Demir Games Studio' for l in LANGS}
    out = ROOT / "privacy" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(multilang_page(titles, panels), encoding="utf-8")


INVITE_CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
              "img-src 'self' data: https://firebasestorage.googleapis.com; font-src 'self'; "
              "connect-src https://firestore.googleapis.com; base-uri 'none'; form-action 'none'")
INVITE_TITLE = "Davetiye \u00b7 Zarfla"
INVITE_DESC = "Size \u00f6zel bir davetiye var."


def build_invite():
    """/davetiye/: davetli sayfas\u0131. Motor (src/invite/engine.html) Zarfla uygulama deposundaki
    assets/invite/invite.html'in birebir kopyas\u0131d\u0131r; g\u00f6rsel/animasyon koduna dokunulmaz. Burada yaln\u0131zca
    <head> (CSP, noindex, OG, yaz\u0131 tipi) eklenir ve motorun boot blo\u011fu site y\u00fckleyicisiyle (loader.js) de\u011fi\u015ftirilir."""
    inv = SRC / "invite"
    h = (inv / "engine.html").read_text(encoding="utf-8")

    def sub(old, new):
        nonlocal h
        assert h.count(old) == 1, f"engine.html'de beklenen par\u00e7a bulunamad\u0131: {old[:50]}"
        h = h.replace(old, new)

    sub('<meta name="robots" content="noindex">', '<meta name="robots" content="noindex,nofollow">')
    sub("<title>Zarfla</title>", f"<title>{INVITE_TITLE}</title>")
    og = f"{SITE_URL}/davetiye/og.png"
    head = f"""<meta http-equiv="Content-Security-Policy" content="{INVITE_CSP}">
<meta name="referrer" content="no-referrer">
<meta name="theme-color" content="#F7F1E8">
<meta name="description" content="{INVITE_DESC}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Zarfla">
<meta property="og:title" content="{INVITE_TITLE}">
<meta property="og:description" content="{INVITE_DESC}">
<meta property="og:image" content="{og}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="../assets/icons/zarfla-192.png" type="image/png">
"""
    sub('<meta name="robots" content="noindex,nofollow">', '<meta name="robots" content="noindex,nofollow">\n' + head.rstrip("\n"))
    # Motorun kendi yaz\u0131 tipi bildirimi var olmayan ../fonts/ yoluna bak\u0131yordu; sitenin Noto Sans Arabic dosyas\u0131na y\u00f6nlendirilir.
    sub('url("../fonts/NotoNaskhArabic.ttf") format("truetype")', 'url("../assets/fonts/NotoSansArabic-400-700.woff") format("woff")')
    sub("</style>\n</head>", "</style>\n<style>\n" + (inv / "states.css").read_text(encoding="utf-8") + "</style>\n</head>")
    i = h.index("(function boot(){")
    j = h.index("</script>", i)
    h = h[:i] + (inv / "loader.js").read_text(encoding="utf-8") + h[j:]
    sub("<body>\n", "<body>\n<noscript><div class=\"zs-nojs\">JavaScript gerekli \u00b7 JavaScript required</div></noscript>\n")
    out = ROOT / "davetiye"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(h, encoding="utf-8")
    shutil.copyfile(inv / "og.png", out / "og.png")


def build_root_and_404():
    links = " · ".join(f'<a href="/{l}/" lang="{l}">{LANG_NAMES[l]}</a>' for l in LANGS)
    root = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Demir Games Studio</title>
<meta name="description" content="{esc(content['studio']['en']['intro'])}">
{''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}/{l}/">' for l in LANGS)}
<link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/">
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/site.css">
<script>
(function(){{var L=["tr","en","de","ar"],n=navigator.languages||[navigator.language||"en"],p="en";
for(var i=0;i<n.length;i++){{var c=(n[i]||"").slice(0,2).toLowerCase();if(L.indexOf(c)>=0){{p=c;break;}}}}
location.replace("/"+p+"/");}})();
</script>
</head>
<body><main class="wrap doc"><h1>Demir Games Studio</h1><p>{links}</p></main></body>
</html>
"""
    (ROOT / "index.html").write_text(root, encoding="utf-8")
    panels = {l: f'<h1>404</h1>\n<p>{esc(ui(l, "not_found_text"))}</p>' for l in LANGS}
    titles = {l: "404 · Demir Games Studio" for l in LANGS}
    (ROOT / "404.html").write_text(multilang_page(titles, panels, noindex=True), encoding="utf-8")


def copy_assets():
    for sub in ("icons", "fonts", "shots"):
        s = SRC / sub
        if s.is_dir():
            dst = ROOT / "assets" / sub
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(s, dst)
    css = (SRC / "tokens.css").read_text(encoding="utf-8") + "\n" + (SRC / "site.css").read_text(encoding="utf-8")
    out = ROOT / "assets" / "css" / "site.css"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(css, encoding="utf-8")


def build_sitemap():
    urls = [f"{SITE_URL}/{l}/" for l in LANGS] + [f"{SITE_URL}/privacy/"]
    urls += [f"{SITE_URL}/privacy/{c['slug']}/" for c in apps_cfg["apps"] if (SRC / "privacy" / c["slug"]).is_dir()]
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n',
        encoding="utf-8")


if __name__ == "__main__":
    copy_assets()
    for l in LANGS:
        build_home(l)
    build_privacy()
    build_invite()
    build_root_and_404()
    build_sitemap()
    print("Site üretildi.")
