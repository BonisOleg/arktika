# Деплой Arctica (Docker + nginx)

Архітектура: `Internet → nginx:80 → backend:8000 (gunicorn) → Django`, `static/`+`media/` — shared volumes, `db` — PostgreSQL 16.

Канон: **django-droplet-http-first** → пізніше SSL (**django-docker-ssl**).

| | |
|---|---|
| Тестовий Droplet IP | `157.230.99.135` |
| Шлях на сервері | `/var/www/arctica` |
| URL (HTTP) | http://157.230.99.135/ |

## Локальний запуск (override + runserver)

```bash
cp .env.example .env   # SECRET_KEY, POSTGRES_PASSWORD
cp docker-compose.override.yml.example docker-compose.override.yml   # лише локально
docker compose up --build
```

Сайт: http://localhost:8000/ (backend) або http://localhost/ (nginx).

> `docker-compose.override.yml` **не комітити** і **не тримати на Droplet** — інакше Compose підхопить `runserver` + `develop`.

## Dev з hot-reload

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Тестовий сервер — HTTP по IP (перший залив)

Без git remote — з Mac:

```bash
./deploy/docker/rsync-up.sh root@157.230.99.135
```

На Droplet:

```bash
cd /var/www/arctica
bash deploy/docker/install-docker.sh
bash deploy/docker/gen-env.sh          # .env з унікальними SECRET_KEY / POSTGRES_PASSWORD
# за бажанням: nano .env  (ADMIN_URL, Telegram, …)
bash deploy/docker/deploy.sh
curl -sf -H "Host: 157.230.99.135" http://127.0.0.1/healthz/   # → ok
```

У браузері: http://157.230.99.135/

### Дані з локальної БД (опційно)

```bash
# Mac — після healthz на сервері, ДО createsuperuser якщо дамп уже з юзерами
./deploy/docker/sync-data.sh push root@157.230.99.135:/var/www/arctica --yes
```

Або seed на сервері:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose exec backend python3 manage.py seed_demo
docker compose exec -T backend python3 manage.py createsuperuser
```

### Оновлення коду

```bash
# Mac
./deploy/docker/rsync-up.sh root@157.230.99.135
# Droplet
cd /var/www/arctica && bash deploy/docker/deploy.sh
```

(Коли з’явиться git remote — `git pull` + `deploy.sh`.)

### `.env` на сервері (ключове)

`gen-env.sh` генерує з `.env.docker.example`. Має бути:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
USE_HTTPS=False
SITE_PROTOCOL=http
SITE_DOMAIN=157.230.99.135
ALLOWED_HOSTS=157.230.99.135,127.0.0.1,localhost,backend
CSRF_TRUSTED_ORIGINS=http://157.230.99.135
```

Порожній `CSRF_TRUSTED_ORIGINS` ламає POST (checkout/контакти) у браузері по IP.

## Production compose (вручну)

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
docker compose up -d --build
```

`deploy.sh` виставляє `COMPOSE_FILE` сам і **ігнорує** `override.yml`.

## Перехід на HTTPS (після certbot) — `django-docker-ssl`

1. DNS: `A @` і `A www` → `157.230.99.135`, дочекатись поширення.
2. HTTP-деплой уже працює на домені.
3. Certbot **на хості** (не в контейнері):

   ```bash
   export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
   docker compose stop nginx
   apt install -y certbot
   certbot certonly --standalone -d <домен> -d www.<домен> --agree-tos -m admin@<домен>
   ```

4. Скопіювати `deploy/nginx/default.prod.conf.example` → `deploy/nginx/default.prod.conf`, замінити `example.com`.
5. У `docker-compose.prod.yml` для `nginx` додати `443:443` і mount `/etc/letsencrypt` + prod conf (див. приклад у `default.prod.conf.example` / історію README).
6. У `.env`: `USE_HTTPS=True`, `SITE_PROTOCOL=https`, `CSRF_TRUSTED_ORIGINS=https://<домен>,https://www.<домен>`, `ALLOWED_HOSTS` + домен, `SITE_DOMAIN=<домен>`.
7. Зміни в git → `git pull` на сервері (не правити compose лише на дроплеті).
8. `bash deploy/docker/deploy.sh` (або compose up).
9. `curl -sfk https://<домен>/healthz/`, `certbot renew --dry-run`.

### Чому `USE_HTTPS=False` до certbot

Якщо `SECURE_SSL_REDIRECT=True` без TLS у nginx, внутрішній `/healthz/` отримує `301` і healthcheck падає. У `config/settings/production.py` SSL-прапорці зав’язані на `USE_HTTPS`.

## Типові проблеми

| Симптом | Причина | Фікс |
|---|---|---|
| 502 Bad Gateway | backend ще стартує / migrate | `docker compose logs backend` |
| Static/Media 404 | nginx alias ≠ STATIC_ROOT | `/app/staticfiles/`, `/app/media/` |
| CSRF failed | немає `CSRF_TRUSTED_ORIGINS=http://IP` | додати в `.env` |
| 400 DisallowedHost | IP немає в `ALLOWED_HOSTS` | додати IP |
| develop/runserver на Droplet | є `docker-compose.override.yml` | видалити; `deploy.sh` уже ігнорує через `COMPOSE_FILE` |
| DB connection refused | backend раніше за db | `depends_on: condition: service_healthy` |
| unhealthy / 301 | `USE_HTTPS=True` без TLS | `USE_HTTPS=False` |

## Перед першим go-live

- [ ] `SECRET_KEY` / `POSTGRES_PASSWORD` згенеровані (`gen-env.sh`)
- [ ] `ADMIN_URL` змінено з `admin/` (SEC-08)
- [ ] `USE_HTTPS=False`, `SITE_PROTOCOL=http` для IP
- [ ] `curl -sf -H "Host: 157.230.99.135" http://127.0.0.1/healthz/` → `ok`
- [ ] WayForPay / Telegram / reCAPTCHA — за потреби; WFP по IP обмежений (потрібен домен)
