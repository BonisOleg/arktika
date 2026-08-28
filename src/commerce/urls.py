from django.urls import path

from . import views

app_name = "commerce"

urlpatterns = [
    path("cart/", views.CartPageView.as_view(), name="cart"),
    path("cart/summary/", views.CartSummaryView.as_view(), name="cart_summary"),
    path("cart/add/<int:product_id>/<int:weight_option_id>/", views.CartAddView.as_view(), name="cart_add"),
    path("cart/item/<int:item_id>/update/", views.CartItemUpdateView.as_view(), name="cart_item_update"),
    path("cart/item/<int:item_id>/remove/", views.CartItemRemoveView.as_view(), name="cart_item_remove"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("order/<int:order_id>/success/", views.OrderSuccessView.as_view(), name="order_success"),
    path("order/<int:order_id>/pay/", views.PaymentInitView.as_view(), name="payment_init"),
    path("order/<int:order_id>/pay/return/", views.PaymentReturnView.as_view(), name="payment_return"),
    path("np/cities/", views.NPCitySearchView.as_view(), name="np_cities"),
    path("np/warehouses/", views.NPWarehouseSearchView.as_view(), name="np_warehouses"),
]
