# CLAUDE.md

Bu dosya, küçük–orta ölçekli işletmeler için geliştirilen bir e-ticaret projesinin Claude Code tarafından geliştirilmesi sırasında uyulması gereken bağlamı, teknoloji yığınını ve görev planını tanımlar. Bu dosyadaki kurallar bağlayıcıdır. Her yeni göreve başlamadan önce ilgili faz bölümünü oku.

---

## 1. Proje Özeti

Küçük ve orta ölçekli işletmeler için modern, ölçeklenebilir bir e-ticaret sistemi. Headless mimari: backend ve frontend birbirinden bağımsız, yalnızca API ile haberleşir. Her seçim; hız, maliyet, ölçeklenebilirlik ve geliştirici verimliliği dengesi gözetilerek yapılmıştır.

**Hedef kullanıcı:** Az–orta trafikli işletme mağazaları. Devasa ölçek veya yüksek eşzamanlılık hedeflenmez.

**Geliştirme felsefesi:** Önce iskelet ve veri, sonra görünüm, en sonda ödeme ve yayın. Her aşama bir öncekinin üstüne kurulur ve her aşama sonunda çalışan, test edilebilir bir parça elde edilir. Ödeme ve auth gibi kritik parçalar erken planlanır ama en stabil hâlleriyle uygulanır; önce veri akışı sağlam kurulur.

---

## 2. Teknoloji Yığını (Stack)

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI (Python) |
| Veritabanı | PostgreSQL (Railway üzerinde) |
| ORM | SQLModel |
| Frontend / Vitrin | Next.js (React, App Router) |
| Stil | Tailwind CSS + Shadcn/ui |
| Admin Paneli | Refine |
| Kimlik Doğrulama | Kendi JWT auth implementasyonu (access + refresh token) |
| Ödeme | İyzico (hosted iframe + webhook), geliştirmede sandbox |
| Görsel / Dosya Depolama | Cloudflare R2 (boto3 ile) |
| Backend + DB Deploy | Railway |
| Frontend Deploy | Vercel |
| Migration | Alembic |

**Önemli:** Bu stack dışına çıkma. Yeni bir bağımlılık eklemeden önce gerekçesini belirt. Ödeme katmanı modüler yazılır (ileride İyzico ↔ PayTR geçişi için soyut bir "ödeme sağlayıcı" arayüzü olmalı).

---

## 3. Mimari Akış

Sistem, API ile haberleşen bağımsız parçalardan oluşur:

- Kullanıcı/müşteri tarayıcıdan Next.js vitrinine (Vercel) erişir.
- Next.js, ürün ve sipariş verilerini FastAPI backend'inden (Railway) API ile çeker.
- FastAPI, verileri PostgreSQL veritabanından (Railway) okur ve yazar.
- Ürün görselleri Cloudflare R2'de saklanır; veritabanında yalnızca görsel URL'i tutulur (görselin kendisi DB'ye konmaz).
- Ödeme anında kullanıcı İyzico'nun hosted iframe ekranında kartla öder; kart verisi sisteme hiç değmez.
- İyzico, ödeme sonucunu webhook ile doğrudan FastAPI'ye bildirir; sipariş yalnızca bu doğrulamaya göre kesinleşir.
- Müşteri, Refine tabanlı admin panelinden ürün, stok ve siparişleri yönetir.

---

## 4. Mutlak Kurallar (Bağlayıcı)

Bu kurallar her zaman geçerlidir ve ihlal edilemez:

### Güvenlik
- **Şifreler asla düz saklanmaz.** passlib + bcrypt ile hash'lenir.
- **API anahtarları ve sırlar koda gömülmez.** Tümü `.env` dosyasında tutulur (İyzico anahtarları, R2 anahtarları, JWT secret, DB bağlantısı). `.env` asla git'e commit edilmez; `.env.example` tutulur.
- **Refresh token httpOnly cookie'de saklanır**, localStorage'da DEĞİL (XSS riski).
- **Sipariş onayı yalnızca İyzico webhook'una göre yapılır.** Frontend'in "ödendi" bilgisine asla güvenilmez. Webhook'ta İyzico imzası doğrulanır; sahte bildirimler elenir.
- **Kart verisi hiçbir zaman sisteme alınmaz** — hosted iframe yöntemi bunu garanti eder, bu yöntemden sapma.

### Veri
- Görseller R2'de, DB'de yalnızca URL.
- Yüklenen dosyalara benzersiz isim (uuid) verilir; çakışma olmaz.
- Ürün silinince R2'deki görseli de silen mantık çalışır (çöp birikmez).
- E-ticaret verisi ilişkiseldir; ödeme/sipariş işlemlerinde transaction tutarlılığı korunur.

### CORS & Ortam
- Geliştirmede CORS yalnızca `localhost:3000`'e izin verir; production'da gerçek Vercel/domain adresine.
- API URL'i frontend'te `.env` üzerinden (`NEXT_PUBLIC_API_URL`), koda gömülmez.

### Kod yapısı
- Vitrinde ürün listesi ve detay sayfaları **Server Component** (SEO için). Sepet gibi etkileşimli kısımlar **Client Component**.
- Admin paneli erişimi JWT auth'taki **"admin" rolüne** bağlanır; normal kullanıcı `/admin`'e giremez.
- Her faz bağımsız ve test edilebilir tamamlanır. Tek seferde "tüm projeyi yap" yaklaşımı kullanılmaz; faz faz ilerlenir.

### Çalışma yöntemi
- Bir faza başlamadan önce ilgili faz bölümü okunur.
- Büyük değişikliklerden önce ne yapılacağı kısaca özetlenir.
- Her faz sonunda elde edilen çalışan parça belirtilir.

---

## 5. Geliştirme Fazları — Genel Bakış

| Faz | Aşama | Sonunda Elde Edilen |
|-----|-------|---------------------|
| 1 | Proje kurulumu & temel | Çalışan boş backend + frontend |
| 2 | Veritabanı & modeller | Ürün/kullanıcı/sipariş tabloları |
| 3 | Kimlik doğrulama (JWT) | Kayıt, giriş, rol kontrolü |
| 4 | Ürün API & vitrin | Ürünler listeleniyor, görünüyor |
| 5 | Görsel yükleme (R2) | Ürün fotoğrafı yükleme çalışıyor |
| 6 | Sepet & sipariş | Sepete ekleme, sipariş oluşturma |
| 7 | Admin paneli (Refine) | Müşteri ürün/sipariş yönetebiliyor |
| 8 | Ödeme (İyzico sandbox) | Test kartıyla ödeme + webhook |
| 9 | Deploy & yayın | Canlı, erişilebilir site |
| 10 | Opsiyoneller & cila | E-posta, optimizasyon, son rötuş |

**Pratik strateji:** Faz 1–6'yı önce SQLite ve sahte/sabit veriyle hızlıca çalıştırıp uçtan uca akışı gör; sonra PostgreSQL, R2 ve İyzico'yu sırayla gerçek hâline geçir. Her fazın sonunda çalışan bir parça olduğundan, istenen yerde durulup ilerleme gösterilebilir.

---

## 6. Faz Detayları

### Faz 1 — Proje Kurulumu ve Temel İskelet
Amaç: backend ve frontend'i ayağa kaldırıp birbirleriyle konuşturmak.

- [x] FastAPI projesini kur, sanal ortam (venv) ve temel klasör yapısını oluştur.
- [x] Next.js projesini kur (App Router ile), Tailwind ve Shadcn'i ekle.
- [x] FastAPI'de basit bir test endpoint'i yaz (örn. `/health`), Next.js'ten fetch ile çağırıp bağlantıyı doğrula.
- [x] CORS'u ayarla: Next.js'in adresini (`localhost:3000`) FastAPI'de izinli yap.
- [x] Çevre değişkenleri için `.env` dosyalarını kur (API URL, sırlar burada tutulur).
- [~] Her iki projeyi de GitHub'a yükle — lokal `git init` + ilk commit yapıldı; GitHub'a push kullanıcının hesabıyla yapılacak (bkz. aşağıdaki not).

### Faz 2 — Veritabanı ve Veri Modelleri
Amaç: e-ticaretin temel verisini modellemek. Projenin omurgası.

- [x] Geliştirmede SQLite ile başlandı (`sqlite:///./ecommerce.db`); PostgreSQL'e geçiş `.env`'deki `DATABASE_URL` ile yapılır (Faz 9).
- [x] SQLModel modelleri: User, Category, Product, **ProductVariant**, Order, OrderItem. Varyant kararı gereği stok+fiyat `ProductVariant`'ta; para `Numeric(10,2)`.
- [x] İlişkiler kuruldu: Product↔Category, Product↔ProductVariant (cascade delete), Order↔OrderItem (cascade), OrderItem→ProductVariant. OrderItem'da fiyat/ad **snapshot**.
- [x] DB bağlantısı + session: `app/db/session.py` (`engine`, `get_session` dependency). Modeller `main.py`'de import edilip boot'ta kaydediliyor.
- [x] Örnek veri + doğrulama: `app/db/seed.py` (idempotent) — 2 kategori, 2 ürün, 4 varyant; ilişkiler geri okunarak test edildi.
- [x] Alembic kuruldu: `alembic/env.py` URL'i settings'ten alır, `SQLModel.metadata`'yı hedefler; SQLite için batch mode. İlk migration uygulandı, `alembic check` temiz.

### Faz 3 — Kimlik Doğrulama (Kendi JWT Auth)
Amaç: kullanıcı kaydı, girişi ve rol ayrımını kurmak. Sepet, sipariş ve admin buna bağlanır.

- [ ] Şifre hash'leme için passlib + bcrypt kur. Şifreler asla düz saklanmaz.
- [ ] Kayıt (register) ve giriş (login) endpoint'lerini yaz.
- [ ] Access token (kısa ömürlü) + refresh token (uzun ömürlü) üretimini kur.
- [ ] Token doğrulama bağımlılığını (dependency) yaz; korumalı endpoint'ler bunu kullanır.
- [ ] Rol sistemi ekle: "user" ve "admin". Token içine rolü koy.
- [ ] Next.js tarafında: refresh token'ı httpOnly cookie'de tut (localStorage DEĞİL — XSS riski).
- [ ] Misafir alışverişe izin verilip verilmeyeceğine karar ver ve ona göre kurgula.

### Faz 4 — Ürün API'si ve Vitrin
Amaç: ürünleri API'den sunup vitrinde göstermek. İlk "görünen" aşama.

- [ ] FastAPI'de ürün endpoint'leri: listele (GET), tek ürün getir, (admin için) ekle/düzenle/sil.
- [ ] Filtreleme, arama ve sayfalama (pagination) ekle — ürün sayısı artınca şart.
- [ ] Next.js'te ürün listesi sayfasını Server Component olarak yaz (SEO için).
- [ ] Ürün detay sayfasını dinamik route ile yap; her ürünün kendi metadata'sı olsun (Google'da çıksın).
- [ ] Vitrin tasarımını Tailwind + Shadcn ile kur (ürün kartları, kategori menüsü).
- [ ] Sepet butonları gibi etkileşimli kısımları Client Component yap.

### Faz 5 — Görsel Yükleme (Cloudflare R2)
Amaç: ürün fotoğraflarının otomatik yüklenip saklanması.

- [ ] Cloudflare R2 hesabı aç, bir bucket oluştur, erişim anahtarlarını al.
- [ ] FastAPI'de boto3 ile R2 bağlantısını kur (anahtarlar `.env`'de).
- [ ] Ürün ekleme endpoint'ine dosya yükleme ekle; benzersiz isim (uuid) üret.
- [ ] Yükleme sonrası dönen URL'i veritabanına kaydet (görseli değil, URL'i).
- [ ] Ürün silinince R2'deki görseli de silen mantığı ekle (çöp birikmesin).
- [ ] İsteğe bağlı: R2'ye custom domain (`cdn.site.com`) bağla.
- [ ] İsteğe bağlı: yüklemede görseli küçült/sıkıştır (hız için).

### Faz 6 — Sepet ve Sipariş
Amaç: kullanıcının ürün seçip sipariş oluşturabilmesi. Ödemeden hemen önceki adım.

- [ ] Sepet mantığını kur (başlangıçta frontend state'inde veya basit backend kaydı olarak).
- [ ] Sipariş oluşturma endpoint'i: sepetteki ürünler, adres, toplam tutar.
- [ ] Stok kontrolü: sipariş anında yeterli stok var mı bak.
- [ ] Sipariş durumları tanımla: beklemede, ödendi, hazırlanıyor, kargoda, teslim.
- [ ] Sipariş henüz "ödendi" olmasın — o, Faz 8'de ödeme onayıyla gelecek.
- [ ] Kullanıcının kendi siparişlerini görebileceği "siparişlerim" sayfasını yap.

### Faz 7 — Admin Paneli (Refine)
Amaç: müşterinin siteyi kendi yönetebilmesi. Refine ile CRUD ekranları hızla kurulur.

- [ ] Refine'ı Next.js projesine ekle, Shadcn/Tailwind ile yapılandır.
- [ ] FastAPI'ye bağlanan data provider'ı yaz (Refine'a "ürünleri şu endpoint'ten al" der).
- [ ] Ürün yönetimi ekranları: listele, ekle, düzenle, sil + fotoğraf yükleme.
- [ ] Sipariş yönetimi: siparişleri gör, durum değiştir.
- [ ] Stok takibi ekranı.
- [ ] Admin girişini JWT auth'taki "admin" rolüne bağla — sadece admin `/admin`'e girebilsin.
- [ ] İsteğe bağlı: temel istatistik (günlük satış, sipariş sayısı) — müşteri sever.

### Faz 8 — Ödeme (İyzico Sandbox)
Amaç: gerçek ödeme akışını test ortamında kurmak. En kritik ve en dikkat gerektiren faz.

- [ ] İyzico sandbox (test) hesabı aç, API anahtarlarını al (`.env`'e koy).
- [ ] Ödeme başlatma endpoint'i: sepet/sipariş bilgisinden İyzico ödeme oturumu aç.
- [ ] Next.js'te İyzico hosted iframe ekranını göster — kart bilgisi sana hiç değmez.
- [ ] Webhook endpoint'i yaz: İyzico ödeme sonucunu buraya bildirir.
- [ ] Webhook'ta İyzico imzasını doğrula — sahte bildirimleri ele.
- [ ] Sipariş onayını SADECE webhook'a göre yap; frontend'in "ödendi" demesine güvenme.
- [ ] Ödeme onaylanınca: sipariş durumunu "ödendi" yap, stoğu düş.
- [ ] Test kartlarıyla başarılı/başarısız senaryoları dene.
- [ ] Ödeme katmanını modüler tut (ileride PayTR'a geçiş kolay olsun).

### Faz 9 — Deploy ve Yayın
Amaç: projeyi internette canlıya almak.

- [ ] Railway'de PostgreSQL oluştur, FastAPI'yi Railway'e deploy et (GitHub'a bağla).
- [ ] Next.js'i Vercel'e deploy et (GitHub'a bağla, otomatik deploy).
- [ ] Tüm çevre değişkenlerini (İyzico, R2, JWT secret, DB) Vercel ve Railway panellerine gir.
- [ ] CORS'a production adresini ekle (Vercel'in gerçek URL'i).
- [ ] İyzico webhook URL'ini production adresine güncelle.
- [ ] Custom domain bağla (müşterinin alan adı varsa).
- [ ] HTTPS otomatik gelir (Vercel/Railway sağlar) — doğrula.
- [ ] Canlıda baştan sona bir test alışverişi yap (sandbox ödeme ile).

### Faz 10 — Opsiyoneller ve Son Cila
Amaç: çekirdek çalıştıktan sonra deneyimi ve dayanıklılığı artırmak.

- [ ] E-posta: sipariş onayı ve şifre sıfırlama maili (Resend/SMTP).
- [ ] Kargo: gerekiyorsa Aras/Yurtiçi/MNG entegrasyonu (yoksa manuel).
- [ ] Performans: görsel optimizasyonu, sayfa hızı, gerekirse Redis cache.
- [ ] Arka plan işleri: mail/bildirim çoğalırsa Celery + Redis.
- [ ] Hata izleme ve loglama ekle.
- [ ] Mobil uyum ve son tasarım rötuşları.
- [ ] Müşteriye kısa bir kullanım kılavuzu / admin paneli eğitimi.

---

## 7. Seçim Gerekçeleri (Referans)

Bir kararı sorgularken veya alternatif önerirken bu gerekçeleri dikkate al:

- **FastAPI:** Modern, hızlı, async. Pydantic ile otomatik veri doğrulama (ödeme/sipariş verisi için kritik), otomatik Swagger dokümanı. Headless e-ticaret ve AI entegrasyonu için ideal.
- **PostgreSQL:** E-ticaret verisi ilişkiseldir; sipariş–ürün–kullanıcı–stok ilişkileri ve ödeme tutarlılığı transaction garantisi gerektirir. SQLModel ile bağlanır; aynı kod SQLite (geliştirme) ve PostgreSQL (production) ile çalışır.
- **Next.js:** SSR/SSG ile ürün sayfaları Google'da görünür (SEO kritik). E-ticarette fiili standart. Saf React+Vite (CSR) vitrinde SEO açısından zayıf kaldığı için tercih edilmedi.
- **Refine:** CRUD/auth/yetki mantığını hazır verir, görünümü serbest bırakır — Tailwind ve Shadcn ile doğal çalışır. React Admin'in aksine Material UI'a bağlamaz.
- **Kendi JWT Auth:** Tam kontrol, sıfır bağımlılık, sıfır maliyet, yüksek portföy değeri. Access + refresh token, bcrypt, rol tabanlı yetki.
- **İyzico (hosted iframe + webhook):** Kart verisi İyzico ekranında işlenir, sisteme değmez; PCI-DSS yükü sağlayıcıda. Ödeme sonucu webhook ile doğrulanır. Modüler yazılarak PayTR'a geçiş kolaylaştırılır.
- **Cloudflare R2:** Egress (dışarı trafik) ücretsiz — görsellerin sürekli çekildiği e-ticarette ciddi maliyet avantajı.
- **Vercel + Railway:** Next.js Vercel'de tek tıkla (CDN+SSL), FastAPI+PostgreSQL Railway'de tek panelde. GitHub'a bağlı otomatik deploy (CI/CD). Ücretsiz katmanla başlar.

---

## 8. Yasal Sayfalar (Production Zorunluluğu)

Canlı bir müşteri sitesinde Türkiye'de yasal olarak bulunması gereken sayfalar (içerik avukat/şablon işidir, ama site bu sayfaları barındırmalıdır):

- Mesafeli satış sözleşmesi
- İptal / iade / teslimat koşulları
- Gizlilik politikası
- KVKK aydınlatma metni
- Çerez bildirimi

Demo/portföy projesinde bu sayfalar yer tutucu (placeholder) olarak eklenebilir; gerçek müşteride içerik müşteriden/avukattan alınır.

---

## 9. Henüz Karara Bağlanmamış Kapsam Soruları

Müşteriye/projeye göre netleştirilecek, kapsamı etkileyen noktalar:

- Kupon/indirim sistemi gerekli mi?
- Kargo ücreti nasıl hesaplanacak (sabit / tutara göre / ücretsiz kargo eşiği)?
- Stok bittiğinde davranış (satışa kapansın mı, "tükendi" mi göstersin)?
- Çoklu ürün varyantı (renk/beden) gerekli mi? (Giyim satan müşteride şart.)
- Arama & filtreleme kapsamı.

Bu sorular netleşmeden ilgili özellik kodlanmaz; varsayım yapılacaksa açıkça belirtilir.

---

## 10. Notlar

- Komisyon oranları ve plan fiyatları zamanla değişir; müşteriye kesin rakam yerine "işletmeye özel teklif alınır" denir.
- Ücretsiz katmanlar demo/portföy için yeterlidir; gerçek müşteride trafik artınca ücretli plana geçilir, maliyet müşteriye yansıtılır.
- Kapsam kayması en büyük zaman tuzağıdır: önce çekirdek akış (ürün → sepet → ödeme → sipariş) bitirilir, ekstralar sonra eklenir.

---

## Proje Yapısı

Monorepo: tek git deposu, içinde bağımsız `backend/` ve `frontend/`. Deploy'da
her biri kendi root dizininden yayınlanır (Railway → backend, Vercel → frontend).

```
E-commerce/
├── CLAUDE.md
├── .gitignore                # kök: .env, venv, node_modules yok sayılır
├── backend/                  # FastAPI (Python 3.12)
│   ├── venv/                 # sanal ortam (commit edilmez)
│   ├── requirements.txt
│   ├── .env / .env.example   # .env commit EDİLMEZ, .example edilir
│   ├── ecommerce.db          # SQLite (dev, commit edilmez)
│   ├── alembic.ini
│   ├── alembic/              # migration altyapısı (env.py settings'ten URL alır)
│   │   └── versions/         # migration dosyaları
│   └── app/
│       ├── main.py           # FastAPI uygulaması, /health, CORS, modelleri kaydeder
│       ├── core/
│       │   └── config.py     # pydantic-settings (settings: DATABASE_URL, FRONTEND_URL…)
│       ├── db/
│       │   ├── session.py    # engine + get_session dependency
│       │   └── seed.py       # örnek veri (idempotent)
│       └── models/           # SQLModel modelleri — yeni model __init__.py'ye eklenir
│           ├── user.py       # User, UserRole
│           ├── category.py   # Category
│           ├── product.py    # Product, ProductVariant (stok+fiyat burada)
│           └── order.py      # Order, OrderItem, OrderStatus
└── frontend/                 # Next.js 16 (App Router, TS, Tailwind v4, Shadcn)
    ├── .env.local / .env.example   # NEXT_PUBLIC_API_URL; .local commit EDİLMEZ
    └── src/
        ├── app/              # App Router sayfaları (page.tsx = bağlantı testi)
        ├── components/ui/    # Shadcn bileşenleri
        └── lib/utils.ts      # cn() yardımcı
```

Mimari kural hatırlatması: yeni ayar/sır `backend/app/core/config.py` içindeki
`Settings`'e eklenir ve `.env.example`'a yer tutucu olarak yazılır.

---

## Komutlar

Windows + PowerShell. Backend ve frontend ayrı terminallerde çalışır.

### Backend (FastAPI) — `cd backend`
```powershell
# venv'i aktive et (her yeni terminalde)
.\venv\Scripts\Activate.ps1

# çalıştır (geliştirme, otomatik reload) → http://localhost:8000
uvicorn app.main:app --reload

# venv'i aktive etmeden tek seferlik çalıştırma
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload

# bağımlılık ekleme: requirements.txt'i güncelle, sonra
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# migration: model değiştirince yeni revizyon üret + uygula
python -m alembic revision --autogenerate -m "mesaj"
python -m alembic upgrade head
python -m alembic check          # model ↔ migration kayması var mı?

# örnek veri ekle (idempotent)
python -m app.db.seed

# (Faz 3+) test — pytest kurulduktan sonra
pytest                                   # tüm testler
pytest tests/test_x.py::test_fonksiyon   # tek test
```

### Frontend (Next.js) — `cd frontend`
```powershell
npm run dev      # geliştirme → http://localhost:3000
npm run build    # production build (TS + lint kontrolü dahil)
npm run lint     # sadece lint
npx shadcn@latest add <bilesen>   # yeni Shadcn bileşeni ekle
```

> Not: `&&` PowerShell 5.1'de çalışmaz; komutları `;` ile ayır.