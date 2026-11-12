# accounts/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Password Reset
    path('reset_password/', 
        auth_views.PasswordResetView.as_view(), name="reset_password"),
    path('reset_password_sent/', 
        auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset_password_complete/', 
        auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
            path('products/', views.products, name='products'),
    path('billing/', views.billing, name='billing'),
    
     path('logout/', views.logout_view, name='logout'),  # 🔁 Added this
        path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('billing/', views.billing, name='billing'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
 path('generate-invoice/', views.generate_invoice, name='generate_invoice'),
path('invoices/', views.invoice_list, name='invoice_list'),

   
    path('invoice/<int:pk>/view/', views.view_invoice, name='view_invoice'),


    path('invoice/<int:pk>/edit/', views.edit_invoice, name='edit_invoice'),
    path('invoice/<int:pk>/delete/', views.delete_invoice, name='delete_invoice'),
       path('out-of-stock/', views.out_of_stock_products, name='out_of_stock_products'),
         path('expired/', views.expired_products, name='expired_products'),
          path('invoice/<int:invoice_id>/download/', views.invoice_download, name='invoice_download'),
          path('invoice/<int:pk>/delete/', views.delete_invoice, name='delete_invoice'),
           path('update-stock/<int:product_id>/', views.update_stock, name='update_stock'),
           path('get-product/<int:product_id>/', views.get_product, name='get_product'),
path('update-product/', views.update_product, name='update_product'),

]




