import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic.edit import FormMixin
from django_htmx.http import HttpResponseClientRedirect

from src.content.models import SiteSettings
from src.shipping import services as np_services

from . import selectors, services
from .exceptions import CartError
from .forms import CheckoutForm
from .models import Order, Payment
from .services_wayforpay import apply_wayforpay_result, get_wayforpay_service
from .utils import get_or_create_session_key, parse_quantity

logger = logging.getLogger("src.commerce.views")


def _render_cart_fragment(request, *, target: str = "drawer"):
    session_key = get_or_create_session_key(request)
    cart = services.get_or_create_cart(session_key)
    totals = selectors.get_cart_totals(cart)
    context = {**totals, "cart": cart, "min_order_amount": SiteSettings.load().min_order_amount}
    template = "commerce/partials/cart_page_items.html" if target == "page" else "partials/cart_drawer_content.html"
    return render(request, template, context)


class CartPageView(TemplateView):
    """`/cart/` — окрема сторінка кошика (рішення користувача: popup + сторінка)."""

    template_name = "commerce/cart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_key = get_or_create_session_key(self.request)
        cart = services.get_or_create_cart(session_key)
        ctx.update(selectors.get_cart_totals(cart))
        ctx["cart"] = cart
        ctx["min_order_amount"] = SiteSettings.load().min_order_amount
        ctx["page_title"] = _("Кошик")
        return ctx


class CartAddView(View):
    """POST htmx — додає товар. `redirect=checkout` («Купити зараз») веде одразу на checkout,
    інакше повертає оновлений drawer (PDP/PLP `data-cart-open`)."""

    def post(self, request, product_id, weight_option_id):
        quantity = parse_quantity(request.POST.get("quantity"), default="1")
        session_key = get_or_create_session_key(request)
        try:
            services.add_to_cart(session_key, product_id, weight_option_id, quantity)
        except CartError as exc:
            messages.error(request, str(exc))
            return _render_cart_fragment(request, target="drawer")

        if request.POST.get("redirect") == "checkout":
            checkout_url = reverse("commerce:checkout")
            if request.htmx:
                return HttpResponseClientRedirect(checkout_url)
            return redirect(checkout_url)

        return _render_cart_fragment(request, target="drawer")


class CartItemUpdateView(View):
    def post(self, request, item_id):
        quantity = parse_quantity(request.POST.get("quantity"), default="0")
        session_key = get_or_create_session_key(request)
        services.update_cart_item_quantity(session_key, item_id, quantity)
        target = "page" if request.POST.get("render") == "page" else "drawer"
        return _render_cart_fragment(request, target=target)


class CartItemRemoveView(View):
    def post(self, request, item_id):
        session_key = get_or_create_session_key(request)
        services.remove_cart_item(session_key, item_id)
        target = "page" if request.POST.get("render") == "page" else "drawer"
        return _render_cart_fragment(request, target=target)


class CartSummaryView(View):
    """GET htmx — рендер drawer без мутацій (відкриття попапу)."""

    def get(self, request):
        return _render_cart_fragment(request, target="drawer")


class CheckoutView(FormMixin, TemplateView):
    template_name = "commerce/checkout.html"
    form_class = CheckoutForm

    def get(self, request, *args, **kwargs):
        session_key = get_or_create_session_key(request)
        cart = services.get_or_create_cart(session_key)
        if not cart.items.exists():
            messages.info(request, _("Кошик порожній — додайте товари перед оформленням замовлення."))
            return redirect("catalog:list")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        session_key = get_or_create_session_key(request)
        cart = services.get_or_create_cart(session_key)
        if not cart.items.exists():
            messages.info(request, _("Кошик порожній."))
            return redirect("catalog:list")

        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        city_id = form.cleaned_data.get("np_city_id")
        warehouse_id = form.cleaned_data.get("np_warehouse_id")
        city = np_services.NPCity.objects.filter(pk=city_id).first() if city_id else None
        warehouse = np_services.NPWarehouse.objects.filter(pk=warehouse_id).first() if warehouse_id else None

        customer_data = {
            "customer_name": form.cleaned_data["customer_name"],
            "customer_phone": form.cleaned_data["customer_phone"],
            "customer_email": form.cleaned_data.get("customer_email") or None,
            "np_city_name": form.cleaned_data["np_city_name"],
            "np_warehouse_name": form.cleaned_data["np_warehouse_name"],
            "np_city_ref": city,
            "np_warehouse_ref": warehouse,
            "consent_gdpr": form.cleaned_data["consent_gdpr"],
            "comment": form.cleaned_data.get("comment", ""),
        }

        try:
            order = services.place_order(session_key=session_key, cart=cart, customer_data=customer_data)
        except CartError as exc:
            form.add_error(None, str(exc))
            return self.render_to_response(self.get_context_data(form=form))

        request.session["last_order_id"] = order.id
        return redirect(reverse("commerce:order_success", kwargs={"order_id": order.id}))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session_key = get_or_create_session_key(self.request)
        cart = services.get_or_create_cart(session_key)
        ctx.update(selectors.get_cart_totals(cart))
        ctx["cart"] = cart
        ctx["min_order_amount"] = SiteSettings.load().min_order_amount
        ctx["page_title"] = _("Оформлення замовлення")
        from django.conf import settings as dj_settings

        ctx["np_require_ref_selection"] = dj_settings.NP_REQUIRE_REF_SELECTION
        return ctx


class OrderSuccessView(TemplateView):
    """`session['last_order_id']` (ERR-BIZ-09) + SEC-01.

    Після WayForPay returnUrl браузер часто приходить уже з *новою* сесією
    (SameSite=Lax не віддає cookie на cross-site POST) — тоді доступ дає
    ``wfp_return_order_id``, виставлений лише після збігу orderReference.
    """

    template_name = "commerce/order_success.html"

    def get(self, request, *args, **kwargs):
        session_key = get_or_create_session_key(request)
        order_id = kwargs["order_id"]
        order = selectors.get_order_for_guest(order_id, session_key)
        last_id = request.session.get("last_order_id")
        if order is None and last_id == order_id and request.session.get("wfp_return_order_id") == order_id:
            order = (
                Order.objects.filter(pk=order_id)
                .prefetch_related("items", "shipment")
                .first()
            )
        if not order or last_id != order.id:
            return redirect("core:home")
        self.order = order
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["order"] = self.order
        ctx["page_title"] = _("Замовлення %(number)s прийнято") % {"number": self.order.order_number}
        return ctx


class PaymentInitView(TemplateView):
    """`/order/<id>/pay/` — форма автосабміту на WayForPay (за паттерном liqpay_skill Step 6.1)."""

    template_name = "commerce/payment_init.html"

    def get(self, request, *args, **kwargs):
        session_key = get_or_create_session_key(request)
        order_id = kwargs["order_id"]
        order = selectors.get_order_for_guest(order_id, session_key)
        if order is None and request.session.get("last_order_id") == order_id:
            if request.session.get("wfp_return_order_id") == order_id:
                order = Order.objects.filter(pk=order_id).prefetch_related("items").first()
        if not order or order.payment_status == "paid":
            return redirect("commerce:order_success", order_id=order_id)

        service = get_wayforpay_service()
        if service is None:
            messages.info(request, _("Онлайн-оплата тимчасово недоступна — менеджер зв'яжеться для оплати при отриманні."))
            return redirect("commerce:order_success", order_id=order.id)

        payment = services.prepare_payment_attempt(order)
        items = list(order.items.all())
        # WayForPay відхиляє дробовий productCount (кг) з 1113 Invalid signature.
        # Одна позиція = count 1 + ціна = line_total; кількість у назві для чека.
        form_data = service.build_purchase_form(
            order_reference=payment.order_reference,
            order_date=int(order.created_at.timestamp()),
            amount=str(order.total_amount),
            currency="UAH",
            product_names=[f"{item.product_name} · {item.quantity_display}" for item in items],
            product_counts=[1] * len(items),
            product_prices=[str(item.line_total) for item in items],
            service_url=request.build_absolute_uri(reverse("wayforpay_webhook")),
            return_url=request.build_absolute_uri(
                reverse("commerce:payment_return", kwargs={"order_id": order.id})
            ),
        )
        return self.render_to_response({"order": order, "form_data": form_data, "page_title": _("Оплата")})


@method_decorator(csrf_exempt, name="dispatch")
class PaymentReturnView(View):
    """returnUrl WayForPay: POST з Origin: null / без session-cookie (SameSite=Lax).

    1) Знаходить замовлення по URL + orderReference.
    2) Якщо є валідний merchantSignature — оновлює оплату (на localhost webhook
       недоступний).
    3) Виставляє last_order_id + wfp_return_order_id і редіректить на success (GET).
    """

    def get(self, request, order_id):
        return self._complete(request, order_id)

    def post(self, request, order_id):
        return self._complete(request, order_id)

    def _complete(self, request, order_id):
        session_key = get_or_create_session_key(request)
        payload = {k: request.POST.get(k) for k in request.POST.keys()}
        if not payload:
            payload = {k: request.GET.get(k) for k in request.GET.keys()}

        order = Order.objects.filter(pk=order_id).first()
        ref = payload.get("orderReference") or ""
        if ref:
            by_payment = (
                Payment.objects.filter(order_reference=ref).select_related("order").first()
            )
            if by_payment is not None:
                order = by_payment.order
            else:
                # fallback: старі спроби, де ref == order_number
                by_ref = Order.objects.filter(order_number=ref).first()
                if by_ref is not None:
                    order = by_ref
        if order is None:
            messages.info(request, _("Замовлення не знайдено."))
            return redirect("core:home")

        owns_session = order.session_key == session_key
        ref_matches = bool(ref) and (
            Payment.objects.filter(order_reference=ref, order_id=order_id).exists()
            or (ref == order.order_number and order.id == order_id)
        )

        service = get_wayforpay_service()
        signature_ok = False
        if service and payload.get("merchantSignature"):
            # reasonCode / amount інколи приходять числами в інших каналах — уніфікуємо.
            norm = {k: ("" if v is None else str(v)) for k, v in payload.items()}
            signature_ok = service.verify_webhook_signature(norm)
            if signature_ok:
                apply_wayforpay_result(norm, source="return")
            else:
                logger.warning(
                    "WayForPay return: невалідний підпис order_id=%s ref=%s",
                    order_id,
                    ref,
                )

        # Thank-you: своя сесія, або return з orderReference / валідним підписом.
        if not owns_session and not ref_matches and not signature_ok:
            messages.info(request, _("Не вдалося підтвердити повернення з оплати."))
            return redirect("core:home")

        request.session["last_order_id"] = order.id
        if not owns_session and (ref_matches or signature_ok):
            request.session["wfp_return_order_id"] = order.id
        request.session.modified = True
        return redirect("commerce:order_success", order_id=order.id)


class NPCitySearchView(View):
    """htmx автокомпліт міста НП (checkout) — Фаза 0.5, fixture-довідник."""

    def get(self, request):
        query = request.GET.get("np_city_name", "")
        cities = np_services.get_cities(query)
        return render(request, "commerce/partials/np_city_options.html", {"cities": cities})


class NPWarehouseSearchView(View):
    def get(self, request):
        city_id = request.GET.get("np_city_id")
        query = request.GET.get("np_warehouse_name", "")
        warehouses = np_services.get_warehouses(city_id, query) if city_id else []
        return render(request, "commerce/partials/np_warehouse_options.html", {"warehouses": warehouses})
