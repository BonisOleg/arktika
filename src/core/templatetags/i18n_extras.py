"""Template tags для i18n (коректний next= при перемиканні uk↔ru)."""
from django import template
from django.conf import settings

register = template.Library()


def _strip_language_prefix(path: str) -> str:
    """Прибирає /ru/ (або інший не-дефолтний префікс) з початку path."""
    if not path.startswith("/"):
        path = f"/{path}"
    for code, _ in settings.LANGUAGES:
        if code == settings.LANGUAGE_CODE:
            continue
        prefix = f"/{code}/"
        if path.startswith(prefix):
            stripped = path[len(prefix) - 1 :]  # лишаємо leading /
            return stripped or "/"
        if path == f"/{code}":
            return "/"
    return path


def path_for_language(path: str, lang_code: str) -> str:
    """Будує path у цільовій мові з урахуванням prefix_default_language=False.

    Django ``translate_url`` ненадійно знімає /ru/ при переході на uk і
    інколи не додає /ru/ залежно від активного override — тому префікс
    ставимо/знімаємо явно.
    """
    bare = _strip_language_prefix(path)
    if lang_code == settings.LANGUAGE_CODE:
        return bare
    if bare == "/":
        return f"/{lang_code}/"
    return f"/{lang_code}{bare}"


@register.simple_tag(takes_context=True)
def language_next(context, lang_code: str) -> str:
    """URL для hidden next= у формі set_language."""
    request = context.get("request")
    full = request.get_full_path() if request is not None else "/"
    query = ""
    if "?" in full:
        path, query = full.split("?", 1)
        query = f"?{query}"
    else:
        path = full
    return f"{path_for_language(path, lang_code)}{query}"
