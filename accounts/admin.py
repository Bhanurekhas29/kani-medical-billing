# # products/admin.py

# from django.contrib import admin
# from .models import Product

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'batch_no', 'price', 'stock', 'expiry_date', 'gst_percent', 'mrp')
#     list_filter = ('gst_percent', 'state')
#     search_fields = ('name', 'batch_no')
#     readonly_fields = ('cgst', 'sgst', 'igst')  # auto-calculated fields

from django.contrib import admin
from .models import Product, Invoice, InvoiceItem, Customer

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'batch_no', 'box_price', 'piece_stock', 'expiry_date', 'gst_percent', 'mrp')
    list_filter = ('gst_percent', 'state')
    search_fields = ('name', 'batch_no')
    readonly_fields = ('cgst', 'sgst', 'igst', 'mrp')


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1  # show one extra empty row
    readonly_fields = ('subtotal',)
    autocomplete_fields = ['product']
    fields = ('product', 'batch_no', 'mrp', 'quantity', 'subtotal')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_date', 'to_name', 'from_name', 'total')
    search_fields = ('invoice_number', 'to_name', 'from_name')
    list_filter = ('invoice_date',)
    inlines = [InvoiceItemInline]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone')
    search_fields = ('name', 'phone')

