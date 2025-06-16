# payments/admin.py
from django.contrib import admin
from .models import Product, Customer, Payment, PaymentLog, Subscription

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'currency', 'product_type', 'billing_interval', 'active', 'created_at')
    list_filter = ('active', 'currency', 'product_type', 'billing_interval')
    search_fields = ('name', 'description', 'stripe_product_id', 'stripe_price_id')
    readonly_fields = ('stripe_product_id', 'stripe_price_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'currency', 'active')
        }),
        ('Product Type', {
            'fields': ('product_type', 'billing_interval', 'billing_interval_count')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'user_id', 'stripe_customer_id', 'created_at')
    search_fields = ('email', 'user_id', 'stripe_customer_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('email', 'user_id')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'customer', 'product', 'amount_total', 'currency', 'payment_status', 'payment_type', 'created_at')
    list_filter = ('payment_status', 'payment_type', 'currency', 'created_at')
    search_fields = ('uuid', 'session_id', 'stripe_payment_intent_id', 'stripe_subscription_id')
    readonly_fields = ('uuid', 'session_id', 'stripe_payment_intent_id', 'stripe_subscription_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('uuid', 'customer', 'product', 'amount_total', 'currency', 'payment_status', 'payment_type')
        }),
        ('Stripe Integration', {
            'fields': ('session_id', 'stripe_payment_intent_id', 'stripe_subscription_id')
        }),
        ('Subscription Details', {
            'fields': ('subscription_status', 'current_period_start', 'current_period_end', 'cancel_at_period_end'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'product')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('stripe_subscription_id', 'customer', 'product', 'status', 'current_period_start', 'current_period_end', 'cancel_at_period_end')
    list_filter = ('status', 'cancel_at_period_end', 'created_at')
    search_fields = ('stripe_subscription_id', 'customer__email', 'product__name')
    readonly_fields = ('stripe_subscription_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Subscription Information', {
            'fields': ('stripe_subscription_id', 'customer', 'product', 'payment', 'status')
        }),
        ('Billing Periods', {
            'fields': ('current_period_start', 'current_period_end', 'cancel_at_period_end', 'canceled_at')
        }),
        ('Trial Period', {
            'fields': ('trial_start', 'trial_end'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'product', 'payment')

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'subscription', 'event_type', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('payment__uuid', 'subscription__stripe_subscription_id', 'event_type')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Log Information', {
            'fields': ('payment', 'subscription', 'event_type')
        }),
        ('Event Data', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'subscription')