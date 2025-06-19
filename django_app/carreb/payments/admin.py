# payments/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Product, Customer, Payment, PaymentLog, Subscription, SubscriptionChange, RetentionOffer

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'currency', 'product_type', 'plan_tier', 'active', 'created_at']
    list_filter = ['product_type', 'plan_tier', 'active', 'currency']
    search_fields = ['name', 'description', 'stripe_product_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'currency', 'active')
        }),
        ('Product Type & Plan', {
            'fields': ('product_type', 'plan_tier', 'plan_metadata')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_product_id', 'stripe_price_id', 'billing_interval', 'billing_interval_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['email', 'user_id', 'stripe_customer_id', 'created_at']
    search_fields = ['email', 'user_id', 'stripe_customer_id']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'customer_email', 'amount_total', 'currency', 'payment_status', 'payment_type', 'created_at']
    list_filter = ['payment_status', 'payment_type', 'currency', 'created_at']
    search_fields = ['uuid', 'session_id', 'stripe_payment_intent_id', 'customer__email']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    
    def customer_email(self, obj):
        return obj.customer.email if obj.customer else 'N/A'
    customer_email.short_description = 'Customer Email'

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['stripe_subscription_id', 'customer_email', 'product_name', 'status', 'cancel_at_period_end', 'current_period_end']
    list_filter = ['status', 'cancel_at_period_end', 'created_at']
    search_fields = ['stripe_subscription_id', 'customer__email', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def customer_email(self, obj):
        return obj.customer.email if obj.customer else 'N/A'
    customer_email.short_description = 'Customer Email'
    
    def product_name(self, obj):
        return obj.product.name if obj.product else 'N/A'
    product_name.short_description = 'Product'

@admin.register(SubscriptionChange)
class SubscriptionChangeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'change_type', 'status', 'old_product_name', 
        'new_product_name', 'effective_date', 'created_at'
    ]
    list_filter = ['change_type', 'status', 'created_at', 'effective_date']
    search_fields = ['user_email', 'stripe_subscription_id', 'old_price_id', 'new_price_id']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('Change Information', {
            'fields': ('user_email', 'stripe_subscription_id', 'change_type', 'status')
        }),
        ('Plan Details', {
            'fields': ('old_product', 'new_product', 'old_price_id', 'new_price_id')
        }),
        ('Timing & Execution', {
            'fields': ('effective_date', 'created_at', 'completed_at')
        }),
        ('Financial & Technical', {
            'fields': ('proration_amount', 'schedule_id', 'metadata'),
            'classes': ('collapse',)
        })
    )
    
    def old_product_name(self, obj):
        return obj.old_product.name if obj.old_product else obj.old_price_id
    old_product_name.short_description = 'From Plan'
    
    def new_product_name(self, obj):
        return obj.new_product.name if obj.new_product else obj.new_price_id
    new_product_name.short_description = 'To Plan'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('old_product', 'new_product')

@admin.register(RetentionOffer)
class RetentionOfferAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'offer_type', 'offer_title', 'accepted', 
        'created_at', 'accepted_at'
    ]
    list_filter = ['offer_type', 'accepted', 'created_at']
    search_fields = ['user_email', 'stripe_subscription_id']
    readonly_fields = ['created_at', 'accepted_at']
    
    fieldsets = (
        ('Offer Information', {
            'fields': ('user_email', 'stripe_subscription_id', 'offer_type', 'offer_details')
        }),
        ('Status', {
            'fields': ('accepted', 'created_at', 'accepted_at')
        }),
        ('Stripe Integration', {
            'fields': ('coupon_id', 'stripe_promotion_code'),
            'classes': ('collapse',)
        })
    )
    
    def offer_title(self, obj):
        return obj.offer_details.get('title', 'N/A') if obj.offer_details else 'N/A'
    offer_title.short_description = 'Offer Title'
    
    def accepted_status(self, obj):
        if obj.accepted:
            return format_html(
                '<span style="color: green;">✓ Accepted</span>'
            )
        return format_html(
            '<span style="color: orange;">⏳ Pending</span>'
        )
    accepted_status.short_description = 'Status'

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_type', 'related_object', 'created_at']
    list_filter = ['event_type', 'created_at']
    search_fields = ['event_type', 'payment__uuid', 'subscription__stripe_subscription_id']
    readonly_fields = ['created_at']
    
    def related_object(self, obj):
        if obj.payment:
            return f"Payment: {obj.payment.uuid}"
        elif obj.subscription:
            return f"Subscription: {obj.subscription.stripe_subscription_id}"
        elif obj.subscription_change:
            return f"Change: {obj.subscription_change.id}"
        return "N/A"
    related_object.short_description = 'Related Object'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'payment', 'subscription', 'subscription_change'
        )

# Custom admin site configuration
admin.site.site_header = "CarReb Payment Administration"
admin.site.site_title = "CarReb Payments"
admin.site.index_title = "Payment Management Dashboard"