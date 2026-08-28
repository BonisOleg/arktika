# tables.md — Arctica (Variant A lite)

**Джерела:** `Технічне_завдання_Золотова.docx`, `docs/sitemap.md`, `docs/Arctica відповіді.docx`, `docs/CLIENT_FEEDBACK.md`, погоджений `mockup/`.
**Skill:** `ecommerce_db_schema_skill` (Variant A, спрощено — без `pricing`/`seo` apps, без Attribute/Brand/Supplier).
**Статус:** draft v1 — 27.08.2026.

---

## 1. Apps (Крок 2 — свідомо спрощений Variant A)

| App | Відповідальність | Відхилення від канону |
|---|---|---|
| `core` | `TimeStampedModel`, `SeoFieldsMixin` (shared abstract) | додано `seo_h1` (ТЗ §2.5 вимагає окреме поле H1, чого немає в базовому mixin skill) |
| `catalog` | `Category`, `Product`, `ProductWeightOption`, `ProductImage` | **без** `Attribute`/`AttributeValue`/`Brand`/`Supplier` — MVP каталог фільтрується лише по `Category`, один виробник |
| `commerce` | `Cart`, `CartItem`, `Order`, `OrderItem`, `OrderStatusLog`, `Payment` | **без** окремого `pricing` app — ціна фіксована на `ProductWeightOption`, без markup/RRP-формули (клієнт задає ціну з ПДВ вручну) |
| `shipping` | `NPCity`, `NPWarehouse`, `Shipment` | без `NovaPoshtaAccount`/multi-ФОП ([[600j]]) — один НП-акаунт |
| `content` | `AboutPage`, `DeliveryPage`, `OfferPage`, `PrivacyPage`, `ContactsPage`, `ContactMessage`, `SiteSettings` | singleton-на-сторінку за [[600i2 CMS page-singletons замість SiteBlock registry]], не SiteBlock registry |
| `accounts` | немає нової моделі — `django.contrib.auth.User` + Django Groups (`Менеджери`) + permissions | без кастомного `role`-поля: у MVP немає кабінету покупця, лише staff-акаунти → Groups простіше за MTI/role-enum |

**Немає окремого `seo` app** — `redirect_301`/`meta_template` не потрібні (немає legacy URL для міграції, немає багатошаблонного SEO).

---

## 2. Core (`core/models.py`)

```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    class Meta: abstract = True

class SeoFieldsMixin(models.Model):
    seo_title = models.CharField('SEO title', max_length=512, null=True, blank=True)
    seo_description = models.TextField('SEO description', null=True, blank=True)
    seo_h1 = models.CharField('SEO H1', max_length=255, null=True, blank=True)  # ТЗ §2.5
    seo_keywords = models.CharField('SEO keywords', max_length=512, null=True, blank=True)  # не обов'язково в ТЗ, лишено опційно
    class Meta: abstract = True
```

`seo_title`/`seo_description`/`seo_h1` — **зареєстровані в modeltranslation** (uk/ru), бо мета-теги мають бути мовно-специфічні.

---

## 3. `catalog`

### Category
| Поле | Тип | Примітка |
|---|---|---|
| `name` | CharField | i18n (modeltranslation → `name_uk`, `name_ru`) |
| `slug` | SlugField unique | **не** i18n — той самий slug на обидві мови (lock у `docs/sitemap.md`) |
| `image` | ImageField null | картка/бейдж категорії |
| `sort_order` | PositiveSmallInteger default 0 | порядок у dropdown/сайдбарі |
| `is_active` | Boolean default True | **адмін-керованість** — приховати без видалення (рішення користувача 27.08.2026) |
| + `TimeStampedModel`, `SeoFieldsMixin` | | |

### Product
| Поле | Тип | Примітка |
|---|---|---|
| `category` | FK → Category, `PROTECT` | |
| `name` | CharField | i18n |
| `slug` | SlugField unique | не i18n |
| `description` | TextField (rich/HTML) | i18n |
| `is_available` | Boolean default True | **свідоме відхилення від skill-канону** (там `stock_qty` + `stock_qty > 0`); клієнт підтвердив просте «в наявності/немає» без кількості (`Arctica відповіді.docx` 3.3) |
| `is_hit` | Boolean default False | ручний прапорець для блоку «Хіти продажу» (ТЗ §3 «динамічно з БД», без окремої моделі підбірки — MVP) |
| `is_new` | Boolean default False | ручний прапорець для блоку «Новинки» |
| + `TimeStampedModel`, `SeoFieldsMixin` | | |

**Ціна і артикул — лише на `ProductWeightOption`.** `Product` власної ціни/SKU не має (кожен товар продається мінімум в одному фасуванні — за зразком PDP-макету, де ціна/артикул завжди змінюються через варіант).

### ProductWeightOption *(за [[600i3 ProductWeightOption окремо від variant_of]])*
| Поле | Тип | Примітка |
|---|---|---|
| `product` | FK → Product, `CASCADE`, related_name `weight_options` | |
| `label` | CharField(50) | напр. «500 г», «1 кг», «ящик 10 кг» — довільний текст, не enum значення |
| `unit` | CharField choices `kg`/`pcs`/`box` | клієнт: «везде все разное — кг, штуки, ящики» (2.3) |
| `price` | DecimalField(10,2) | ціна **з ПДВ** (3.1 підтверджено) |
| `sku` | CharField unique | артикул — змінюється при виборі варіанта (ТЗ §3 PDP) |
| `is_default` | Boolean default False | рівно один `is_default=True` на товар — перевірка в `clean()`/service |
| `sort_order` | PositiveSmallInteger default 0 | |

`unique_together = (product, label)`.

### ProductImage
| Поле | Тип | Примітка |
|---|---|---|
| `product` | FK → Product, `CASCADE`, related_name `images` | |
| `image` | ImageField | WebP/JPEG ≤500 Кб (ТЗ §2.4 PageSpeed) |
| `alt` | CharField | i18n |
| `sort_order` | PositiveSmallInteger default 0 | |
| `is_primary` | Boolean default False | перше фото картки/PLP |

---

## 4. `commerce`

### Cart
| Поле | Тип | Примітка |
|---|---|---|
| `session_key` | CharField null, index | гість — прив'язка до сесії |
| `user` | FK → User, null | лише staff можуть бути "user", покупець завжди гість у MVP; поле лишене для сумісності з майбутнім кабінетом |
| `status` | Choices `active`/`converted`/`abandoned`, default `active` | |
| + `TimeStampedModel` | | |

### CartItem
| Поле | Тип | Примітка |
|---|---|---|
| `cart` | FK → Cart, `CASCADE`, related_name `items` | |
| `product` | FK → Product, `CASCADE` | |
| `weight_option` | FK → ProductWeightOption, `CASCADE` | |
| `quantity` | PositiveSmallInteger | |

**Без поля ціни (SEC-06 / `shop_security_skill`)** — ціна завжди читається live з `weight_option.price` при рендері й повторно ревалідується в `place_order()`. `unique_together = (cart, weight_option)`.

### Order
| Поле | Тип | Примітка |
|---|---|---|
| `order_number` | CharField unique | людино-читабельний (напр. `ARK-000123`) |
| `session_key` | CharField null, index | для гостя — `session['last_order_id']` lookup (ERR-BIZ-09) |
| `user` | FK → User, null | для майбутнього кабінету |
| `status` | Choices `new`/`processing`/`shipped`/`done`/`cancelled`, default `new` | ТЗ §5.2 |
| `payment_status` | Choices `pending`/`paid`/`failed`, default `pending` | ТЗ §4.2 — окрема вісь від fulfillment-статусу |
| `customer_name` | CharField | |
| `customer_phone` | CharField | |
| `customer_email` | EmailField null | |
| `np_city_name` / `np_warehouse_name` | CharField | snapshot тексту на момент замовлення |
| `np_city_ref` / `np_warehouse_ref` | FK → `NPCity`/`NPWarehouse`, null | заповнюється, коли є довідник (Фаза 0.5+) |
| `subtotal_amount` | Decimal(10,2) | сума товарів |
| `vat_amount` | Decimal(10,2) | інформаційний рядок «в т.ч. ПДВ» (мокап checkout) |
| `total_amount` | Decimal(10,2) | до сплати |
| `consent_gdpr` | Boolean | чекбокс оферти/політики (ТЗ §4.3) |
| `comment` | TextField blank | коментар покупця |
| + `TimeStampedModel` | | |

### OrderItem
| Поле | Тип | Примітка |
|---|---|---|
| `order` | FK → Order, `CASCADE`, related_name `items` | |
| `product` | FK → Product, `SET_NULL`, null | посилання може зникнути, snapshot нижче лишається |
| `product_name` | CharField | snapshot |
| `weight_option_label` | CharField | snapshot («500 г») |
| `sku` | CharField | snapshot |
| `unit_price` | Decimal(10,2) | snapshot ціни на момент замовлення |
| `quantity` | PositiveSmallInteger | |
| `line_total` | Decimal(10,2) | `unit_price * quantity` |

### OrderStatusLog
| Поле | Тип | Примітка |
|---|---|---|
| `order` | FK → Order, `CASCADE`, related_name `status_log` | |
| `status` | CharField | значення `Order.status`/`payment_status` на момент запису |
| `changed_by` | FK → User, null | `null` = система (webhook) |
| `note` | CharField blank | |
| `created_at` | DateTimeField auto_now_add | |

### Payment
| Поле | Тип | Примітка |
|---|---|---|
| `order` | OneToOne → Order, `CASCADE` | |
| `provider` | CharField default `"wayforpay"` | canonical рішення 27.08.2026 |
| `order_reference` | CharField unique | значення, що надсилається у WayForPay `orderReference` |
| `amount` | Decimal(10,2) | |
| `currency` | CharField default `"UAH"` | |
| `transaction_status` | CharField null | значення з callback WayForPay (`Approved`/`Declined`/…) |
| `signature_verified` | Boolean default False | HMAC-перевірка callback (SEC-07) |
| `raw_callback` | JSONField null | повний payload для діагностики |
| `paid_at` | DateTimeField null | |
| + `TimeStampedModel` | | |

---

## 5. `shipping` — Nova Poshta (Фаза 0.5, [[novaposhta_skill]])

### NPCity
| Поле | Тип | Примітка |
|---|---|---|
| `ref` | UUIDField unique | Nova Poshta `Ref` |
| `name` | CharField | |
| `area` | CharField blank | область |
| `is_active` | Boolean default True | |
| `synced_at` | DateTimeField null | `null` = fixture-заглушка (без `NP_API_KEY`) |

### NPWarehouse
| Поле | Тип | Примітка |
|---|---|---|
| `city` | FK → NPCity, `CASCADE`, related_name `warehouses` | |
| `ref` | UUIDField unique | |
| `number` | CharField | «Відділення №1» / «Поштомат №3401» |
| `description` | CharField blank | |
| `is_active` | Boolean default True | |
| `synced_at` | DateTimeField null | |

### Shipment
| Поле | Тип | Примітка |
|---|---|---|
| `order` | OneToOne → Order, `CASCADE` | |
| `np_warehouse` | FK → NPWarehouse, null | |
| `ttn_number` | CharField null | Фаза 3 — після оплати |
| `shipping_status` | Choices `pending`/`created`/`in_transit`/`delivered`, default `pending` | |
| `tracking_updated_at` | DateTimeField null | |

**`NP_SENDER_*`** — env-константи одного ФОП (не таблиця; [[600j]] нерелевантний — один акаунт).

---

## 6. `content` — page-singletons ([[600i2]]) + SiteSettings

`AboutPage`, `DeliveryPage`, `OfferPage`, `PrivacyPage` — однакова форма:

| Поле | Тип | Примітка |
|---|---|---|
| `body` | TextField/RichText | i18n, `pk=1` |
| + `SeoFieldsMixin` | | |

### ContactsPage (singleton, `pk=1`)
| Поле | Тип | Примітка |
|---|---|---|
| `intro_text` | TextField | i18n, текст над формою |
| `wholesale_link_url` | URLField default `https://rk-arctica.com.ua/` | business-лінк, `rel="nofollow"` (sitemap-lock) |
| + `SeoFieldsMixin` | | |

### ContactMessage
| Поле | Тип | Примітка |
|---|---|---|
| `name`, `phone`, `email` | CharField/EmailField | |
| `message` | TextField | |
| `consent_gdpr` | Boolean | |
| `is_read` | Boolean default False | |
| `created_at` | DateTimeField auto_now_add | |

### SiteSettings (singleton, `pk=1`)
| Поле | Тип | Примітка |
|---|---|---|
| `min_order_amount` | Decimal(10,2) default `500.00` | клієнт підтвердив (3.5); валідація в `place_order()` — **не покрито жодним skill**, власне рішення |
| `phone` | CharField | шапка/футер |
| `telegram_notify_orders` | Boolean default True | вимикач без видалення env-токена |

---

## 7. i18n

```python
MODELTRANSLATION_LANGUAGES = ('uk', 'ru')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'uk'
LANGUAGE_CODE = 'uk'
LANGUAGES = [('uk', 'Українська'), ('ru', 'Русский')]
```

`i18n_patterns(..., prefix_default_language=False)` — `uk` без префіксу, `ru` з `/ru/` (lock у `docs/sitemap.md`).

**Перекладені поля:** `Category.name`, `Product.name`/`description`, `ProductImage.alt`, усі `content`-singleton `body`/`intro_text`, `SeoFieldsMixin.*`.
**НЕ перекладені (спільний slug):** `Category.slug`, `Product.slug`.

Порядок `INSTALLED_APPS`: `unfold` → **`modeltranslation` → `django.contrib.admin`** → власні apps. Це відхилення від формулювання в `admin_skill` (там порядок був названий навпаки) — перевірено практично: якщо `django.contrib.admin` йде першим, `admin.autodiscover()` реєструє `ModelAdmin` для `Category`/`Product` до того, як модель зареєстрована для перекладу → `modeltranslation.translator.NotRegistered` при старті (офіційна документація `django-modeltranslation`: «modeltranslation must be put before django.contrib.admin»).

---

## 8. Verify-матриця (Крок 6 — sitemap ↔ таблиці)

| Sitemap / ТЗ рядок | Таблиця/поле | Статус |
|---|---|---|
| `/` Хіти/Новинки динамічно з БД | `Product.is_hit`/`is_new` | ✅ |
| `/catalog/` + 8 категорій, адмін-керовані | `Category.is_active` | ✅ |
| PDP: зміна ціни/артикулу при варіанті | `ProductWeightOption` | ✅ |
| Кошик +/- перерахунок | `CartItem.quantity`, live price з `weight_option` | ✅ |
| Checkout: дані покупця, доставка, оплата | `Order` + `Shipment` + `Payment` | ✅ |
| Мін. сума замовлення 500 грн | `SiteSettings.min_order_amount` | ✅ (поза skill-каноном) |
| GDPR-чекбокс (checkout + контакти) | `Order.consent_gdpr`, `ContactMessage.consent_gdpr` | ✅ |
| Telegram ≤ 1-2 хв | `OrderStatusLog`/`ContactMessage` + notifier-сервіс (без моделі) | ✅ (сервіс поза схемою) |
| Переклад каталогу/CMS uk↔ru в адмінці | modeltranslation на всіх i18n-полях | ✅ |
| Перемикач мов зберігає сторінку | `i18n_patterns` + `set_language` (код, не схема) | — (business-logic фаза) |
| Адмінка: статуси замовлень «Нове/В обробці/Відправлено/Виконано» | `Order.status` choices | ✅ |
| Оплата → «Оплачено»/«Очікує оплати» | `Order.payment_status` | ✅ |
| RBAC менеджерів (7.3 — відкрито) | Django Groups (без нової моделі) | ✅ підготовлено, права — після відповіді клієнта |
| SEO Title/Description/H1 (ТЗ §2.5) | `SeoFieldsMixin` (+ `seo_h1` додано понад канон) | ✅ |
| `/sitemap.xml` + `/robots.txt` | без моделі — Django `sitemaps` framework (SEO-фаза) | — (backlog фази 8) |
| Оптовий лінк на `/contacts/` | `ContactsPage.wholesale_link_url` | ✅ |

Немає жодного рядка sitemap без статусу — крок 6 пройдено.

---

## 9. Lock-лист (Крок 5)

- 8 категорій (зі «Снеками») — не прибирати без нового підтвердження клієнта; лише `is_active=False` для приховування.
- WayForPay — canonical, не переключати на generic-абстракцію без нового рішення.
- Ціни завжди **з ПДВ** — не додавати окреме поле "ціна без ПДВ" без запиту.
- `is_available` (bool) — свідоме відхилення від `stock_qty`; не "покращувати" до кількості без запиту клієнта (3.3 підтверджено).

---

## 10. Backlog (M3+, не мігрувати в ядрі зараз)

| Модуль | Тригер переходу з backlog |
|---|---|
| `stock_qty` (точний залишок) | клієнт захоче точну кількість (зараз — просте boolean) |
| Знижки/акції (`Promotion`) | клієнт підтвердить 3.4 (зараз «поки ні») |
| Накладений платіж / оплата при отриманні | відповідь на 5.2 |
| Кабінет покупця / `Cart.user` активне використання | відповідь на 6.1 (поза MVP) |
| Множинні НП-акаунти (кілька ФОП, [[600j]]) | не релевантно — один ФОП |
| `Attribute`/`AttributeValue` фасетні фільтри | якщо клієнт попросить фільтри окрім категорій |

---

## Перед здачею схеми (чекліст skill)

- [x] Apps = Variant A, свідомо спрощений (без pricing/seo/attribute) — задокументовано в розділі 1
- [x] `tables.md` покриває M0–M2; pricing-формула не потрібна (ціна вручну з ПДВ)
- [x] Матриця ТЗ/sitemap ↔ таблиці пройдена (розділ 8)
- [x] `seo_h1` додано понад канон (ТЗ §2.5)
- [x] Order: recipient/shipment snapshot + status log
- [x] M3+ лише backlog-список (розділ 10)
- [x] Lock-лист клієнта (розділ 9)
- [x] `core.models`: `TimeStampedModel`/`SeoFieldsMixin` — без копіпасту
- [ ] Файли моделей `catalog`/`commerce` — розбити на `models_1.py`/`models_2.py`, якщо >500 рядків (перевірити на етапі скаффолду)
