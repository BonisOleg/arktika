# ERR-132 / SEC-08: не /admin/ і не шаблонний manage/.
ADMIN_URL_FALLBACK = "kryha-desk"


def resolve_admin_url(raw: str, fallback: str = ADMIN_URL_FALLBACK) -> str:
    path = (raw or "").strip().strip("/")
    if not path or path.lower() == "admin":
        path = fallback
    return f"{path}/"
