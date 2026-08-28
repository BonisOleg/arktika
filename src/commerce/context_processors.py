from . import selectors
from .utils import get_or_create_session_key


def cart_summary(request):
    """Кількість товарів у кошику — бейдж на іконці в шапці (усі шаблони)."""
    session_key = get_or_create_session_key(request)
    return {"cart_items_count": selectors.get_cart_items_count(session_key)}
