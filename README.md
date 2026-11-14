# Demir Games Studio sitesi

Yayın adresi: https://ttuncaydemirr-beep.github.io

- Metinler, uygulama kartları ve gizlilik politikaları `src/` klasöründe.
- Site `python3 tools/build.py` ile üretilir; çıktı depo köküne yazılır.
- Uygulama durumu (test / yayında / yakında) `src/apps.json` içinde. "live" yapılınca kartta Google Play bağlantısı çıkar.
- `app-ads.txt` AdMob yayıncı kimliğini içerir; silinmemeli.
- `/davetiye/` davetiye görüntüleme sayfasının yeri (şimdilik yer tutucu, arama motorlarına kapalı).
- `/.well-known/assetlinks.json` davetiye uygulaması hazır olunca doldurulacak.
