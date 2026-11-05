from django.contrib import admin
from django.urls import path
from cafe import views

urlpatterns = [
    path("healthz/", views.health, name="health"),
    path("admin/", admin.site.urls),
    path("", views.catalog, name="catalog"),
    path("cart/", views.cart, name="cart"),
    path("cart/<int:dish_id>/", views.cart_add, name="cart_add"),
    path("cart/<int:dish_id>/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/<uuid:order_id>/", views.receipt, name="receipt"),
]
admin.site.site_header = "Dunganka · кабинет кафе"
admin.site.site_title = "Dunganka"
admin.site.index_title = "Заказы и меню"
