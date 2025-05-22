# payments/admin.py
from django.contrib import admin
from .models import Product, Customer, Payment, PaymentLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'active', 'created_at')
    list_filter = ('active', 'currency')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'stripe_customer_id', 'created_at')
    search_fields = ('email', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    # Changed 'id' to 'pk' in list_display
    list_display = ('pk', 'customer', 'product', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'payment_type', 'currency')
    search_fields = ('stripe_session_id', 'stripe_payment_intent_id')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    # Changed 'id' to 'pk' here as well
    list_display = ('pk', 'payment', 'event_type', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('payment__stripe_session_id', 'event_type')
    readonly_fields = ('created_at',)