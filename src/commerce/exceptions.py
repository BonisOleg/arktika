from django.utils.translation import gettext_lazy as _


class CartError(Exception):
    """Базова помилка кошика/checkout — перехоплюється у views для user-friendly повідомлення."""


class MinOrderNotReachedError(CartError):
    def __init__(self, min_amount, current_amount):
        self.min_amount = min_amount
        self.current_amount = current_amount
        super().__init__(_("Мінімальна сума замовлення %(min)s ₴, зараз %(current)s ₴") % {
            "min": min_amount, "current": current_amount,
        })


class EmptyCartError(CartError):
    def __init__(self):
        super().__init__(_("Кошик порожній"))


class ProductUnavailableError(CartError):
    def __init__(self, product_name: str):
        self.product_name = product_name
        super().__init__(_("«%(name)s» більше не в наявності") % {"name": product_name})
