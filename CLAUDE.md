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

- [x] Şifre hash'leme: **bcrypt doğrudan** kullanıldı (passlib değil — 1.7.4 bakımsız ve yeni bcrypt ile `__about__` uyumsuzluğu üretiyor). Hash/verify `app/core/security.py`'de.
- [x] Kayıt (register) ve giriş (login) endpoint'leri: `app/api/routes/auth.py`. Login hem JSON (`/auth/login`) hem OAuth2 form (`/auth/token`, Swagger Authorize için). Register'dan admin atanamaz.
- [x] Access (15dk) + refresh (7gün) token üretimi. Payload'da `type` (access/refresh) var; refresh ile access endpoint'ine girilemez. Süreler `.env`'den (`config.py`).
- [x] Token doğrulama dependency'leri: `app/api/deps.py` → `get_current_user` (DB'den canlı kontrol: pasif/silinmiş user reddedilir) + `require_admin`.
- [x] Rol sistemi: `UserRole` (user/admin) token içinde taşınır. İlk admin `seed.py` ile atanır (admin@example.com / dev şifresi).
- [x] Refresh token **httpOnly cookie**'de: `Path=/auth`, `SameSite=lax`, `secure` production'da açık. localStorage'da DEĞİL. `/auth/refresh` rotasyon yapar, `/auth/logout` cookie'yi siler.
- [x] **Karar: üyelik zorunlu** (misafir alışveriş yok). Her sipariş bir kullanıcıya bağlanacak (Faz 6).
- [ ] Next.js entegrasyonu (login formu, token saklama/yenileme) — frontend tarafı Faz 4'te vitrinle birlikte yapılacak.

### Faz 4 — Ürün API'si ve Vitrin
Amaç: ürünleri API'den sunup vitrinde göstermek. İlk "görünen" aşama.

- [x] Ürün endpoint'leri: `app/api/routes/products.py`. Public: `GET /products` (liste), `GET /products/{slug}` (detay), `GET /categories`. Admin (`require_admin`): `POST/PATCH/DELETE /products`. DELETE'te R2 görsel temizliği Faz 5'te eklenecek.
- [x] Arama (`q`, isimde ilike), kategori filtresi (slug), **fiyat aralığı** (`min_price`/`max_price`), **sıralama** (newest/price_asc/price_desc/name_asc), sayfalama (`page`/`page_size`). Fiyat/stok varyantta → SQL subquery ile min_price + total_stock aggregate edilir; **karar: stok bitince ürün listede kalır, 'Tükendi' rozetiyle** gösterilir (gizlenmez — SEO).
- [x] Ana sayfa (`app/page.tsx`) = ürün listesi, **Server Component** (SSR doğrulandı: ürün adları/fiyatları HTML'de). Türetilmiş `min_price`/`in_stock` backend'den gelir, frontend hesaplamaz.
- [x] Detay (`app/urun/[slug]/page.tsx`): dinamik route + **`generateMetadata`** (her ürünün kendi title/description'ı — Google'da ayrı çıkar). Olmayan ürün → `notFound()` (404 doğrulandı).
- [x] Tailwind + Shadcn: ProductCard, Navbar, filtre çubuğu (badge/card/input/select eklendi). `lib/api.ts` (tipler + server fetch, revalidate cache), `lib/format.ts` (TL formatı).
- [x] Etkileşimli kısımlar Client Component: `product-filters.tsx` (arama/kategori/sıralama → URL query param), `add-to-cart.tsx` (varyant seçimi + stok kilidi; sepet işlevi Faz 6'da bağlanacak).
- [x] `npm run build` temiz (TS + lint geçti). Karar: **fiyat aralığı + sıralama dahil** arama/filtre kapsamı.

> Not (Faz 4): Vitrinde `min_price`/`max_price` filtresi backend'de hazır ve test edildi; UI'da fiyat aralığı için ayrıca bir kontrol (slider/input) eklenmedi — arama, kategori ve sıralama çubuğu kuruldu. Fiyat aralığı UI'ı gerekirse hızlıca eklenir.

### Faz 5 — Görsel Yükleme (Cloudflare R2)
Amaç: ürün fotoğraflarının otomatik yüklenip saklanması.

- [~] Cloudflare R2 hesabı/bucket/anahtarlar: **kullanıcı yapacak** (dış hesap). Kod hazır; `.env`'e `R2_*` girilince çalışır. Anahtarlar boşken `images_enabled=False` → yükleme uçları 503, backend yine ayakta.
- [x] boto3 ile R2 bağlantısı: `app/services/storage.py` (lazy client, S3v4, `region=auto`). `app/core/config.py`'de `R2_*` ayarları + `images_enabled`/`allowed_image_types` property'leri.
- [x] **Karar: çoklu galeri** → ayrı `ProductImage` modeli (url, r2_key, sort_order, is_cover). Yükleme ucu `POST /products/{id}/images` (multipart, **uuid'li benzersiz ad**: `products/<uuid>.<ext>`), tip (jpeg/png/webp) + boyut (5MB) doğrulaması. İlk görsel otomatik kapak. Ayrıca `DELETE .../images/{id}` ve `PUT .../images/{id}/cover`.
- [x] DB'ye **yalnızca URL + r2_key** yazılır (görselin kendisi R2'de — mutlak kural). Detay/liste cevabına `images[]` ve `cover_image_url` eklendi; kapak önce sıralanır.
- [x] **Ürün silinince R2 görselleri de silinir** (`delete_product` içinde, kayıtlar cascade ile gider). Görsel tek tek silinirken kapak silinirse kalan ilk görsel kapak olur.
- [x] Vitrin: `next/image` ile kapak (kart) + galeri (detay, thumbnail seçimli). Host `.env`'deki `NEXT_PUBLIC_IMAGE_HOST` ile whitelist; yoksa `unoptimized` fallback. Görseli olmayan ürün placeholder gösterir. `npm run build` temiz.
- [x] Migration: `78143dfaac02_faz_5_product_images_tablosu` üretildi + uygulandı, `alembic check` temiz.
- [x] **Test**: izole geçici DB + sahte R2 ile 9 senaryo (yükleme/kapak otomasyonu/sıralama/tip-boyut validasyon/kapak değiştir/kapak devral/ürün silince R2 temizliği) — tümü geçti. Gerçek `ecommerce.db` korundu.
- [ ] İsteğe bağlı: R2 custom domain (`cdn.site.com`) — kullanıcı R2'yi bağlayınca.
- [ ] İsteğe bağlı: yüklemede görsel küçültme/sıkıştırma (Pillow) — Faz 10 cila.

### Faz 6 — Sepet ve Sipariş
Amaç: kullanıcının ürün seçip sipariş oluşturabilmesi. Ödemeden hemen önceki adım.

- [x] **Karar: sepet frontend'de** (React Context + localStorage, `src/lib/cart.tsx`). Backend'de sepet tablosu YOK. SSR/hydration için sepet efekt içinde yüklenir. Navbar'da adet rozeti (`cart-badge.tsx`).
- [x] Sipariş oluşturma: `POST /orders` (`app/api/routes/orders.py`, auth zorunlu). İstemci yalnızca `variant_id + adet + adres` gönderir; **fiyat ve ürün/varyant adı SUNUCUDA DB'den okunur** (frontend fiyatına güvenilmez — manipülasyon engellendi). Toplam kalemlerden hesaplanıp snapshot. `GET /orders` (kendi siparişleri) + `GET /orders/{id}` (sahiplik kontrolü, başkasınınki 404).
- [x] Stok kontrolü: **karar: yetersizse TÜM sipariş reddedilir** (409, hangi kalemlerin yetersiz olduğu döner). Aynı varyant birden çok kalemde gelirse adetler toplanıp kontrol edilir (aggregate).
- [x] Sipariş durumları zaten modelde (`OrderStatus`: pending/paid/preparing/shipped/delivered/cancelled). Vitrinde Türkçe etiket (`lib/orders.ts`).
- [x] **Karar: stok ödeme onayında düşer** (Faz 8 webhook). Sipariş `pending` oluşur, stok DÜŞMEZ — ödenmeyen sipariş stok kilitlemez. (testle doğrulandı: pending'de stok sabit kaldı.)
- [x] "Siparişlerim" listesi (`/siparislerim`) + tekil sipariş (`/siparislerim/[id]`). Üyelik zorunlu → giriş yoksa `/giris?next=...`.
- [x] **Frontend auth** (karar: minimal login+sipariş): `src/lib/auth.tsx` — access token BELLEKTE (localStorage değil), refresh httpOnly cookie ile sessiz oturum (`/auth/refresh`, `credentials:'include'`). `/giris` (login+kayıt sekmeli), `/sepet`, `/odeme` (adres formu → sipariş). `add-to-cart.tsx` gerçek sepete bağlandı.
- [x] **Test**: izole DB ile 12 senaryo (auth zorunlu / fiyat manipülasyonu reddi / pending'de stok düşmez / yetersiz+tükenmiş+aggregate+olmayan varyant 409 / boş sepet 422 / sahiplik 404) — tümü geçti. Backend uçtan uca (login→sipariş→liste→tekil) + frontend build temiz, tüm sayfalar 200.

> Not (Faz 6): Ödeme adımı henüz YOK — `/odeme` siparişi `pending` oluşturup `/siparislerim/[id]`'ye yönlendirir. İyzico hosted iframe + webhook + stok düşümü Faz 8'de bu akışa eklenecek. Frontend'te otomatik token yenileme interceptor'ı eklenmedi (access token süresi dolunca kullanıcı yeniden login olur); gerekirse Faz 10 cilada eklenir.

### Faz 7 — Admin Paneli (Refine)
Amaç: müşterinin siteyi kendi yönetebilmesi. Refine ile CRUD ekranları hızla kurulur.

- [x] **Karar: Refine KULLANILMADI.** Refine'ın resmi paketleri Next 16 + React 19 + Tailwind v4 ile peer-dep çakışması/App Router uyumsuzluğu riski taşıyor; CRUD/auth zaten kendi JWT auth + REST API'mizde hazır. Yerine **native admin sayfaları** (mevcut Shadcn/Tailwind + auth client) — sıfır yeni bağımlılık, yığınla tam uyum, tam kontrol.
- [x] Backend admin uçları: `app/api/routes/admin.py` (`/admin` prefix, **router-level `require_admin`**). Frontend `lib/admin.ts` bunlara bağlanır (data provider yerine doğrudan fetch).
- [x] Ürün yönetimi: liste (`/admin/urunler`, pasif dahil — `GET /admin/products`), ekle (`POST /products`), düzenle/sil (`PATCH/DELETE /products/{id}`), **görsel yükle/sil** (Faz 5 uçları). Düzenleme ekranı (`/admin/urunler/[id]`) hepsini tek sayfada toplar.
- [x] Sipariş yönetimi (`/admin/siparisler`): tüm siparişler + durum filtresi (`GET /admin/orders?status=`), **durum değiştir** (`PATCH /admin/orders/{id}/status`). **'paid' admin tarafından ATANAMAZ** (400) — yalnızca İyzico webhook'u (mutlak kural). pending sipariş ödeme beklediği için admin değiştiremez.
- [x] Stok takibi: varyant ekle (`POST /admin/products/{id}/variants`, SKU benzersiz), stok/fiyat güncelle (`PATCH /admin/variants/{id}`), sil (son varyant silinemez — ürün satılamaz kalmasın). Düzenleme ekranında inline.
- [x] Admin erişimi 'admin' rolüne bağlı: backend `require_admin` (gerçek koruma), frontend `app/admin/layout.tsx` guard (UX; user→vitrin, misafir→giriş). Sadece admin `/admin`'e girer.
- [x] **Temel istatistik** (karar gereği): `GET /admin/stats` + dashboard (`/admin`) — ciro (yalnızca paid+ siparişler, pending hariç), toplam/bekleyen/bugünkü sipariş, ürün sayısı.
- [x] **Test**: izole DB ile 12 senaryo (yetki 401/403, ürün/varyant CRUD, SKU çakışması, stok güncelle, durum geçişi, 'paid' yasağı, durum filtresi, ciro hesabı, son varyant koruması) — tümü geçti. Canlı backend + frontend build temiz, admin sayfaları 200.

### Faz 8 — Ödeme (İyzico Sandbox)
Amaç: gerçek ödeme akışını test ortamında kurmak. En kritik ve en dikkat gerektiren faz.

- [~] İyzico sandbox hesabı/anahtarları: **kullanıcı yapacak** (dış hesap). Kod hazır; `.env`'e `IYZICO_API_KEY/SECRET_KEY` girilince çalışır (`payments_enabled` deseni, R2'deki gibi). Boşken ödeme uçları 503, backend ayakta.
- [x] Ödeme başlatma: `POST /payments/{order_id}/init` (`app/api/routes/payments.py`, auth + sahiplik). Tutar/kalemler SUNUCUDAKİ siparişten alınır. İyzico Checkout Form Initialize çağrısı; iframe içeriği + token döner. **Karar: kendi httpx istemcimiz** (resmi SDK yerine — async, az bağımlılık, HMAC-SHA256 imzayı kendimiz üretiyoruz).
- [x] Next.js İyzico hosted iframe: `IyzicoCheckout` bileşeni (İyzico script'ini DOM'a inject edip çalıştırır), `/odeme` siparişi oluşturup iframe'i gösterir. **Kart bilgisi sisteme hiç değmez** (hosted iframe). `/odeme/sonuc` callback sayfası.
- [x] Webhook: `POST /payments/webhook` (auth YOK — İyzico çağırır; güvenlik imzayla). Ham gövde alınır, sağlayıcıya doğrulatılır.
- [x] **Webhook imza doğrulama** (HMAC-SHA256, `X-Iyz-Signature-V3`). **Sahte bildirim test edildi → reddedildi** (sipariş pending kaldı, stok düşmedi). `hmac.compare_digest` (timing-safe).
- [x] **Sipariş onayı SADECE webhook'la** — frontend "ödendi" diyemez. `/odeme/sonuc` yalnızca bilgi verir; gerçek 'paid' geçişi webhook'ta. (Mutlak kuralın teknik garantisi testle doğrulandı.)
- [x] Ödeme onaylanınca: sipariş 'paid' + **stok BURADA düşer** (Faz 6'da düşmüyordu). **Idempotent** — tekrarlanan webhook stoğu ikinci kez düşürmez (İyzico retry'larına dayanıklı, testle doğrulandı). Stok `max(0, ...)` ile negatife düşmez.
- [x] **Test**: izole DB + sahte İyzico ile 7+ senaryo — init/iframe, sahte imza reddi, geçerli+ödendi→paid+stok, idempotency, başarısız ödeme→pending, ödenmiş siparişe tekrar init 409, sahiplik 404. Tümü geçti. (Gerçek test kartı senaryoları kullanıcı sandbox anahtarını girince.)
- [x] **Ödeme katmanı modüler** (bağlayıcı kural): `app/services/payment/` — soyut `PaymentProvider` arayüzü (`base.py`) + `IyzicoProvider` (`iyzico.py`) + factory (`get_payment_provider`, `PAYMENT_PROVIDER` ile seçim). **PayTR eklemek = base'i implemente eden 1 sınıf + factory'ye 1 satır**; route'lar sağlayıcıdan habersiz.
- [x] Order modeline `payment_token` + `provider_payment_id` (iz/idempotency); migration `94e5ed192b5d` uygulandı, `alembic check` temiz.

> Not (Faz 8): Webhook için İyzico'nun backend'e public URL'den erişmesi gerekir — yerelde test için ngrok/cloudflared tüneli, prod'da gerçek domain (Faz 9). İyzico'nun callback (tarayıcı dönüşü) ile webhook (sunucu bildirimi) farklı şeylerdir; biz onayı **webhook'a** bağladık (callback sadece kullanıcı UX'i). İyzico panelinde webhook URL'i `{API}/payments/webhook` olarak ayarlanmalı.

### Faz 9 — Deploy ve Yayın
Amaç: projeyi internette canlıya almak.

- [x] Railway'de PostgreSQL oluştur, FastAPI'yi Railway'e deploy et (GitHub'a bağla). **Repo**: `0Alduin0/E-Commerce-Site` (branch `master`). Railway proje adı `precious-manifestation`, backend servisi `E-Commerce-Site` (Root Directory=`backend`). **Backend canlı**: `https://e-commerce-site-production-617f.up.railway.app`. Start: `alembic upgrade head && uvicorn ... $PORT` (Procfile/railway.json). 3 migration prod PG'de koştu (`PostgresqlImpl` doğrulandı).
- [x] Next.js'i Vercel'e deploy et (GitHub'a bağla, otomatik deploy). **Frontend canlı**: `https://e-commerce-site-one-drab.vercel.app` (Root Directory=`frontend`).
- [~] Çevre değişkenleri: **Railway'de girildi** → `DATABASE_URL` (`postgresql+psycopg://...`, Postgres servisine referansla), `ENVIRONMENT=production`, `JWT_SECRET` (yeni üretildi), `COOKIE_SAMESITE=none`, `FRONTEND_URL` (Vercel adresi + localhost). **Vercel'de**: `NEXT_PUBLIC_API_URL` (Railway adresi). **R2 + İyzico anahtarları HENÜZ GİRİLMEDİ** (dış hesap; boşken backend ayakta, ilgili uçlar 503).
- [x] CORS'a production adresini ekle: `FRONTEND_URL`'e Vercel URL'i girildi; preflight'ta `access-control-allow-origin` Vercel için döndüğü canlı doğrulandı.
- [~] İyzico webhook URL'i: İyzico anahtarları girilince panelde `{API}/payments/webhook` olarak ayarlanacak (anahtarlar bekleniyor).
- [ ] Custom domain bağla (müşterinin alan adı varsa) — opsiyonel.
- [x] HTTPS: Vercel + Railway ikisi de otomatik HTTPS veriyor (canlı URL'ler https).
- [~] Canlıda baştan sona test: vitrin/ürün API canlı doğrulandı (PG'den 2 ürün). Login/admin/sipariş kullanıcı tarayıcıdan test ediyor. **Ödeme testi İyzico sandbox anahtarları girilince** (şimdilik sipariş `pending` oluşur).

> Not (Faz 9): Seed prod PG'ye Railway CLI + `DATABASE_PUBLIC_URL` (proxy host) ile elle çalıştırıldı — private host (`RAILWAY_PRIVATE_DOMAIN`) sadece Railway iç ağında çözülür, lokalden `getaddrinfo failed` verir. Admin güçlü şifreyle kuruldu (`SEED_ADMIN_EMAIL/PASSWORD` env'leri seed.py'ye eklendi). **Kalan dış-hesap işleri**: Cloudflare R2 (görsel yükleme aktifleşir) + İyzico sandbox (ödeme aktifleşir) + webhook URL'i.

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