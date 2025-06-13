from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # Public views (no login required)
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('menu/', views.menu_view, name='menu'),
    path('menu/<int:table_number>/', views.menu_view, name='menu_with_table'),
    path('menu/<int:table_number>/place-order/', views.place_order, name='place_order'),
    path('menu/<int:table_number>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('menu/<int:table_number>/remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('menu/<int:table_number>/cart-summary/', views.cart_summary, name='cart_summary'),
    path('tables/', views.table_management, name='table_management'),
    path('tables/update-status/', views.update_table_status, name='update_table_status'),
    path('tables/assign-server/', views.assign_server, name='assign_server'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('call-waiter/', views.call_waiter, name='call_waiter'),
    path('cancel-order/', views.cancel_order, name='cancel_order'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Staff views (login required)
    path('tables/', login_required(views.table_management), name='table_management'),
    path('tables/update-status/', login_required(views.update_table_status), name='update_table_status'),
    path('tables/assign-server/', login_required(views.assign_server), name='assign_server'),
    path('orders/', login_required(views.order_list), name='order_list'),
    path('orders/<int:order_id>/', login_required(views.order_detail), name='order_detail'),
    path('kitchen/', login_required(views.kitchen_display), name='kitchen_display'),

    # Admin views (login required)
    path('admin/dashboard/', login_required(views.admin_dashboard), name='admin_dashboard'),
    path('admin/menu/', login_required(views.manage_menu), name='manage_menu'),
    path('payment/<int:table_id>/', views.payment_view, name='payment'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('process-payment/<int:order_id>/', views.process_payment, name='process_payment'),
    path('payment-status/<int:order_id>/', views.get_payment_status, name='get_payment_status'),
    path('order-details/<int:order_id>/', views.get_order_details, name='get_order_details'),
    path('tables/<int:table_id>/orders/', views.table_orders_api, name='table_orders_api'),
    path('tables/<int:table_id>/orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
    path('permission-denied/', views.custom_permission_denied_view, name='permission_denied'),
]
