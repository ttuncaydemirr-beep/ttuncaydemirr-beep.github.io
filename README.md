# Demir Games Studio sitesi

Yayın adresi: https://ttuncaydemirr-beep.github.io

- Metinler, uygulama kartları ve gizlilik politikaları `src/` klasöründe.
- Site `python3 tools/build.py` ile üretilir; çıktı depo köküne yazılır.
- Uygulama durumu (test / yayında / yakında) `src/apps.json` içinde. "live" yapılınca kartta Google Play bağlantısı çıkar.
- `app-ads.txt` AdMob yayıncı kimliğini içerir; silinmemeli.
- `/davetiye/` davetli sayfası (noindex, reklam/analitik/çerez yok). Motor `src/invite/engine.html`, Zarfla uygulama deposundaki `assets/invite/invite.html` dosyasının birebir kopyasıdır (güncellemek için üzerine kopyalayın; görsel koda dokunmayın). `tools/build.py` yalnızca `<head>` (CSP, OG, yazı tipi), `src/invite/states.css` ve boot bloğunun yerine `src/invite/loader.js` ekler. Veri: `?id=<12 karakter [A-Za-z0-9]>` -> Firestore REST (`zarfla-37da9`, API anahtarı yok); `fields.data.stringValue` davetiye JSON'u, `fields.plan.stringValue` `free` ise "Zarfla ile hazırlandı" görünür, `paid` ise görünmez (motor içinde `premium`). 403/404 -> "süresi dolmuş" görünümü.
  - YAPILACAK: o görünümün altındaki "Zarfla ile sen de davetiye hazırla" bağlantısı şimdilik site ana sayfasına (`/`) gider (`src/invite/loader.js` içinde `HOME`); uygulama Google Play'e çıkınca Play bağlantısıyla güncellenmeli.
  - Paylaşım önizleme görseli `src/invite/og.png`; yeniden üretmek için `python3 tools/make_invite_og.py` (Chrome + playwright gerekir).
- `/.well-known/assetlinks.json` davetiye uygulaması hazır olunca doldurulacak.
