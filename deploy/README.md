# Деплой Arctica (Docker + nginx)

Архітектура: `Internet → nginx:80 → backend:8000 (gunicorn) → Django`, `static/`+`media/` — shared volumes, `db` — PostgreSQL 16.

## Локальний запуск (override + runserver)

```bash
cp .env.example .env   # заповнити SECRET_KEY, POSTGRES_PASSWORD
docker compose up --build
```

Сайт: http://localhost:8000/ (backend напряму) або http://localhost/ (через nginx).

## Dev з hot-reload (mount коду)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Production (перший деплой — HTTP-only)

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

`.env` на сервері (не в git):

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=...
ALLOWED_HOSTS=<домен>,<IP droplet>,127.0.0.1,localhost,backend
CSRF_TRUSTED_ORIGINS=
USE_HTTPS=False
POSTGRES_DB=arctica
POSTGRES_USER=arctica
POSTGRES_PASSWORD=...
POSTGRES_HOST=db
SITE_DOMAIN=<домен>
SITE_PROTOCOL=http
```

Перевірка: `curl -sf http://<IP-або-домен>/healthz/` → `ok`.

## Перехід на HTTPS (після certbot) — `django-docker-ssl`

1. DNS: `A @` і `A www` → IP дроплета, дочекатись поширення.
2. Переконатись, що HTTP-деплой вище вже працює на домені.
3. Certbot **на хості** (не в контейнері):

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.prod.yml stop nginx
   apt install -y certbot
   certbot certonly --standalone -d <домен> -d www.<домен> --agree-tos -m admin@<домен>
   ```

4. Скопіювати `deploy/nginx/default.prod.conf.example` → `deploy/nginx/default.prod.conf`, замінити `example.com` на реальний домен.
5. У `docker-compose.prod.yml` для `nginx` додати:

   ```yaml
   nginx:
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./deploy/nginx/default.prod.conf:/etc/nginx/conf.d/default.conf:ro
       - /etc/letsencrypt:/etc/letsencrypt:ro
   ```

6. У `.env`: `USE_HTTPS=True`, `SITE_PROTOCOL=https`, `CSRF_TRUSTED_ORIGINS=https://<домен>,https://www.<домен>`.
7. `git add` + commit усі зміни (nginx-конфіг, compose) — **не редагувати вручну на сервері**, лише `git pull`.
8. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.
9. Перевірка: `curl -sfk https://<домен>/healthz/`, `certbot renew --dry-run`.

### Чому `USE_HTTPS=False` до certbot

Якщо `SECURE_SSL_REDIRECT=True` без реального TLS у nginx, будь-який внутрішній HTTP-запит (напр. healthcheck) отримує `301 → https://...` і падає. `config/settings/production.py` тримає `SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/HSTS під єдиним флагом `USE_HTTPS` (env), щоб не патчити код при go-live — лише `.env`.

## Типові проблеми

| Симптом | Причина | Фікс |
|---|---|---|
| 502 Bad Gateway | backend ще стартує / migrate падає | `docker compose logs backend` |
| Static/Media 404 | nginx `alias` ≠ `STATIC_ROOT`/`MEDIA_ROOT` | шляхи мають бути `/app/staticfiles/`, `/app/media/` |
| CSRF failed | немає `CSRF_TRUSTED_ORIGINS` | додати `https://домен` після SSL |
| DB connection refused | backend стартував раніше за `db` | вже покрито `depends_on: condition: service_healthy` |
| `web`/`backend` unhealthy, логи 301 | `USE_HTTPS=True` без реального TLS | `USE_HTTPS=False` доки немає certbot |

## Перед першим go-live (django_verification_skill)

- [ ] Згенерувати новий `SECRET_KEY` (не `change-me-in-production`): `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- [ ] Змінити `ADMIN_URL` з дефолтного `admin/` на випадковий шлях (SEC-08)
- [ ] `POSTGRES_PASSWORD` — реальний пароль, не `change-me`
- [ ] `WAYFORPAY_MERCHANT_LOGIN`/`WAYFORPAY_MERCHANT_SECRET_KEY` — реальні (sandbox) ключі клієнта
- [ ] `RECAPTCHA_PUBLIC_KEY`/`RECAPTCHA_PRIVATE_KEY` — якщо форми мають бути захищені з першого дня
- [ ] `manage.py check --deploy` — без WARNINGS (крім SECRET_KEY, якщо ще дефолтний)
- [ ] `manage.py migrate --noinput`, `manage.py collectstatic --noinput`, `manage.py compilemessages -l ru` — без помилок
- [ ] `curl -sf http://<домен-або-IP>/healthz/` → `ok`
