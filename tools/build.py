#!/usr/bin/env python3
"""Demir Games Studio sitesini üretir.

Girdiler (src/):
  content.json            uygulama kartları, stüdyo metinleri, arayüz metinleri (tr/en/de/ar)
  apps.json               uygulamaların yayın durumu ve sırası
  tokens.css              görsel kimlik (renkler, yazı tipleri)
  privacy/<slug>/<lang>.html   gizlilik politikası parçaları
  terms/<slug>/<lang>.html     kullanım koşulları parçaları (+ meta.json başlıkları) → terms/<slug>/index.html
  music/                  Zarfla davetiye müzikleri (manifest.json + <id>.mp3; .github/workflows/fetch-music.yml üretir)
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
LANG_NAMES = {"tr": "Türkçe", "en": "English", "de": "Deutsch", "ar": "العربية",
              "es": "Español", "pt": "Português", "id": "Bahasa Indonesia"}
# Hukuki metinler (gizlilik / kullanım koşulları) için ek çeviri dilleri: stüdyo sitesinin kendisi 4 dilde kalır (LANGS);
# bu diller yalnız src/privacy|terms/<slug>/<dil>.html dosyası varsa o sayfada sekme olarak görünür. Çeviri bilgi amaçlıdır,
# çelişkide Türkçe/İngilizce sürüm geçerlidir (çeviri dosyalarının başında belirtilir).
DOC_LANGS = LANGS + ["es", "pt", "id"]
# Ek diller için "stüdyoya dön" bağlantısı (stüdyo ana sayfası 4 dilde; bu diller İngilizce ana sayfaya gider).
BACK_LABELS = {"es": "Volver al estudio", "pt": "Voltar ao estúdio", "id": "Kembali ke studio"}
EMAIL = "nilkaren.tuncay.demir@gmail.com"

content = json.loads((SRC / "content.json").read_text(encoding="utf-8"))
apps_cfg = json.loads((SRC / "apps.json").read_text(encoding="utf-8"))
apps_by_slug = {a["slug"]: a for a in content["apps"]}


def esc(s):
    return html.escape(str(s), quote=True)


def ui(lang, key):
    return content["ui"].get(lang, {}).get(key) or content["ui"]["en"].get(key, key)


def doc_langs(d):
    """Bir belge klasöründe parçası bulunan diller (DOC_LANGS sırasıyla); tr ve en zorunludur."""
    langs = [l for l in DOC_LANGS if (d / f"{l}.html").is_file()]
    missing = [l for l in LANGS if l not in langs]
    if missing:
        raise SystemExit(f"{d}: eksik zorunlu dil dosyası: {missing}")
    return langs


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
  var L=__LANGS__, q=new URLSearchParams(location.search).get("lang");
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
    """Tek adreste birden çok dil (en az tr/en/de/ar; hukuki metinlerde es/pt/id de olabilir); dil tarayıcıdan ya da
    ?lang= ile seçilir. JS yoksa tüm diller alt alta görünür."""
    langs = [l for l in DOC_LANGS if l in panels_by_lang]
    tabs = "".join(
        f'<button type="button" data-tab="{l}" lang="{l}" aria-pressed="false">{LANG_NAMES[l]}</button>'
        for l in langs)

    def back(l):
        # Stüdyo ana sayfası yalnız LANGS dillerinde var; ek dillerde İngilizce ana sayfaya dönülür.
        return (f'/{l}/', ui(l, back_label_key)) if l in LANGS else ('/en/', BACK_LABELS.get(l, ui("en", back_label_key)))

    panels = "\n".join(
        f'<section data-panel="{l}" lang="{l}" dir="{dir_of(l)}" data-title="{esc(title_by_lang[l])}">'
        f'<p class="back"><a href="{back(l)[0]}">{esc(back(l)[1])}</a></p>\n{panels_by_lang[l]}\n</section>'
        for l in langs)
    tab_label = "Language / Dil / Sprache / اللغة" + (" / Idioma / Bahasa" if len(langs) > len(LANGS) else "")
    body = f"""<div class="wrap doc">
  <div class="tabs" role="group" aria-label="{esc(tab_label)}">{tabs}</div>
{panels}
</div>"""
    pick_js = LANG_PICK_JS.replace("__LANGS__", json.dumps(langs, separators=(",", ":")))
    extra = (f'<link rel="canonical" href="{SITE_URL}{canonical}">\n' if canonical else "") + pick_js
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
        dl = doc_langs(d)
        panels = {l: (d / f"{l}.html").read_text(encoding="utf-8") for l in dl}
        titles = {l: f'{meta["titles"][l]} · Demir Games Studio' for l in dl}
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


def build_terms():
    """Kullanım koşulları: src/terms/<slug>/{tr,en,de,ar}.html + meta.json → terms/<slug>/index.html (gizlilikle aynı düzen)."""
    tdir = SRC / "terms"
    if not tdir.is_dir():
        return
    for d in sorted(p for p in tdir.iterdir() if p.is_dir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        dl = doc_langs(d)
        panels = {l: (d / f"{l}.html").read_text(encoding="utf-8") for l in dl}
        titles = {l: f'{meta["titles"][l]} · Demir Games Studio' for l in dl}
        out = ROOT / "terms" / d.name / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(multilang_page(titles, panels, canonical=f"/terms/{d.name}/"), encoding="utf-8")


INVITE_HOST = "https://zarfla-37da9.web.app"
INVITE_TITLE = "Davetiye \u00b7 Zarfla"
INVITE_DESC = "Size \u00f6zel bir davetiye var."
REDIRECT_CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self'; "
                "base-uri 'none'; form-action 'none'")


def build_invite():
    """/davetiye/: YALNIZ YÖNLENDİRME. Davetli sayfası Firebase Hosting'e taşındı (https://zarfla-37da9.web.app/davetiye/;
    kaynak: Zarfla uygulama deposu, tools/build_hosting.py). Eski bağlantılar (…github.io/davetiye/?id=…&g=…) SONSUZA DEK
    çalışmalı: sorgu dizesi ve # parçası olduğu gibi yeni adrese taşınır. Paylaşım önizlemesi (OG) burada kalır, çünkü
    WhatsApp vb. önizleyiciler betik çalıştırmaz. Bu sayfayı kaldırmayın."""
    target = f"{INVITE_HOST}/davetiye/"
    og = f"{SITE_URL}/davetiye/og.png"
    page_html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{REDIRECT_CSP}">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<title>{INVITE_TITLE}</title>
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
<script>
(function(){{
  var u="{target}"+location.search+location.hash;
  try{{location.replace(u)}}catch(e){{location.href=u}}
  document.addEventListener("DOMContentLoaded",function(){{var a=document.getElementById("go");if(a)a.href=u}});
}})();
</script>
<noscript><meta http-equiv="refresh" content="0;url={target}"></noscript>
<style>
html,body{{margin:0;background:#F7F1E8;color:#1F3D36;font:16px/1.6 system-ui,-apple-system,"Segoe UI","Noto Sans Arabic",sans-serif}}
main{{min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:24px;box-sizing:border-box;text-align:center}}
a{{color:#1F3D36;text-underline-offset:3px;font-weight:600}}
a:focus-visible{{outline:3px solid #AD7F2E;outline-offset:3px}}
p{{margin:2px 0}}
</style>
</head>
<body>
<main>
<p lang="tr">Davetiyeniz açılıyor…</p>
<p lang="en">Opening your invitation…</p>
<p lang="de">Ihre Einladung wird geöffnet …</p>
<p lang="ar" dir="rtl">جارٍ فتح دعوتك…</p>
<p style="margin-top:18px"><a id="go" href="{target}">Davetiyeyi aç · Open invitation · Einladung öffnen · افتح الدعوة</a></p>
</main>
</body>
</html>
"""
    out = ROOT / "davetiye"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page_html, encoding="utf-8")
    shutil.copyfile(SRC / "invite" / "og.png", out / "og.png")


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


def build_music():
    """/music/: Zarfla davetiye müzikleri. YALNIZ manifest.json'da listelenen (telif kaydı onaylı) mp3'ler
    kopyalanır; listede olmayan dosya yayımlanmaz. Davetli sayfası https://…/music/<id>.mp3 adresini kullanır."""
    src = SRC / "music"
    dst = ROOT / "music"
    mf = src / "manifest.json"
    if not mf.is_file():
        return
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    n = 0
    for t in manifest["tracks"]:
        f = src / t["file"]
        if f.is_file():
            shutil.copyfile(f, dst / t["file"])
            n += 1
    # Kamuya açık künye (uygulama ve davetli sayfası atıf metinlerini buradan da doğrulayabilir)
    credits = [{k: t[k] for k in ("id", "title", "composer", "performer", "credit", "license", "license_url", "source_page")}
               for t in manifest["tracks"]]
    (dst / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if n < len(manifest["tracks"]):
        print(f"UYARI: müzik {n}/{len(manifest['tracks'])} dosya hazır (fetch-music iş akışını çalıştırın)")


def build_sitemap():
    urls = [f"{SITE_URL}/{l}/" for l in LANGS] + [f"{SITE_URL}/privacy/"]
    urls += [f"{SITE_URL}/privacy/{c['slug']}/" for c in apps_cfg["apps"] if (SRC / "privacy" / c["slug"]).is_dir()]
    if (SRC / "terms").is_dir():
        urls += [f"{SITE_URL}/terms/{d.name}/" for d in sorted((SRC / "terms").iterdir()) if d.is_dir()]
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n',
        encoding="utf-8")


if __name__ == "__main__":
    copy_assets()
    for l in LANGS:
        build_home(l)
    build_privacy()
    build_terms()
    build_invite()
    build_music()
    build_root_and_404()
    build_sitemap()
    print("Site üretildi.")
