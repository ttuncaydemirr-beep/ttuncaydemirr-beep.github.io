# Demir Games Studio sitesi

Yayın adresi: https://ttuncaydemirr-beep.github.io

- Metinler, uygulama kartları ve gizlilik politikaları `src/` klasöründe.
- Site `python3 tools/build.py` ile üretilir; çıktı depo köküne yazılır.
- Uygulama durumu (test / yayında / yakında) `src/apps.json` içinde. "live" yapılınca kartta Google Play bağlantısı çıkar.
- `app-ads.txt` AdMob yayıncı kimliğini içerir; silinmemeli.
- `/davetiye/` artık YALNIZ YÖNLENDİRMEDİR: davetli sayfası Firebase Hosting'e taşındı (`https://zarfla-37da9.web.app/davetiye/`;
  kaynak Zarfla uygulama deposu: `assets/invite/invite.html` + `hosting-src/` + `tools/build_hosting.py`). Eski bağlantılar
  (`…github.io/davetiye/?id=…&g=…`) sonsuza dek çalışmalı: sayfa sorgu dizesini ve `#` parçasını koruyarak `location.replace`
  ile yeni adrese gider (betik yoksa meta yenileme + görünür bağlantı). Paylaşım önizlemesi (OG, `src/invite/og.png`) burada kalır.
  Bu sayfayı silmeyin. Yeniden üretmek için `python3 tools/make_invite_og.py` (Chrome + playwright gerekir).
- `/music/` ve `src/music/`: Zarfla müziklerinin lisanslı KAYNAĞI (fetch-music.yml). Davetli sayfası müziği Firebase Hosting'den
  sunar (build_hosting.py dosyaları buradan sha256 doğrulayarak alır). `/music/` eski uygulama sürümlerinin editör önizlemesi için
  bir süre daha yayında kalır.
- `/.well-known/assetlinks.json` davetiye uygulaması hazır olunca doldurulacak.
