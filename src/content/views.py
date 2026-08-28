import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView

from .forms import ContactForm
from .models import AboutPage, ContactMessage, ContactsPage, DeliveryPage, OfferPage, PrivacyPage

logger = logging.getLogger("src.content.views")


class SingletonPageView(TemplateView):
    template_name = "content/page.html"
    model = None
    page_title = ""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = self.model.load()
        ctx["page"] = page
        # Хлібні крихти — людська назва; title/og беруть seo_title у шаблоні.
        ctx["page_title"] = self.page_title
        return ctx


class AboutView(SingletonPageView):
    model = AboutPage
    page_title = _("Про нас")


class DeliveryView(SingletonPageView):
    model = DeliveryPage
    page_title = _("Доставка і оплата")


class OfferView(SingletonPageView):
    model = OfferPage
    page_title = _("Оферта")


class PrivacyView(SingletonPageView):
    model = PrivacyPage
    page_title = _("Політика конфіденційності")


class ContactsView(FormView):
    """`/contacts/` — інфо + форма звернення + business-лінк на rk-arctica.com.ua (sitemap-lock)."""

    template_name = "content/contacts.html"
    form_class = ContactForm
    success_url = reverse_lazy("content:contacts")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["contacts_page"] = ContactsPage.load()
        ctx["page_title"] = _("Контакти")
        return ctx

    def form_valid(self, form):
        message = ContactMessage.objects.create(
            name=form.cleaned_data["name"],
            phone=form.cleaned_data.get("phone", ""),
            email=form.cleaned_data.get("email", ""),
            message=form.cleaned_data["message"],
            consent_gdpr=form.cleaned_data["consent_gdpr"],
        )
        try:
            from src.core.services.telegram import notify_contact_message

            notify_contact_message(message)
        except Exception:  # noqa: BLE001
            logger.exception("Не вдалося надіслати сповіщення про звернення %s", message.pk)
        messages.success(self.request, _("Дякуємо! Ваше повідомлення надіслано, ми зв'яжемось з вами найближчим часом."))
        return super().form_valid(form)
