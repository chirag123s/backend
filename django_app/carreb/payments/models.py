# payments/models.py
from django.db import models
from django.utils import timezone
import uuid

class Product(models.Model):
    """Product model for items that can be purchased"""
    PRODUCT_TYPE_CHOICES = (
        ('one_time', 'One-time Payment'),
        ('subscription', 'Subscription'),
    )
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='aud')
    active = models.BooleanField(default=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='one_time')
    
    # Stripe-specific fields for subscriptions
    stripe_product_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_price_id = models.CharField(max_length=255, null=True, blank=True)
    billing_interval = models.CharField(max_length=20, null=True, blank=True)  # 'month', 'year', etc.
    billing_interval_count = models.IntegerField(default=1)  # e.g., 1 for monthly, 12 for yearly
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        
    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"

class Customer(models.Model):
    """Customer model for tracking user purchases"""
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        
    def __str__(self):
        return self.email

class Payment(models.Model):
    """Payment model for tracking payments and subscriptions"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('canceled', 'Canceled'),
    )
    
    PAYMENT_TYPE_CHOICES = (
        ('one_time', 'One-time Payment'),
        ('subscription', 'Subscription'),
    )
    
    uuid = models.UUIDField(primary_key=True, default=None, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    amount_total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='aud')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='one_time')
    
    # Stripe session and payment intent
    session_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Subscription-specific fields
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)
    subscription_status = models.CharField(max_length=50, null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        
    def __str__(self):
        return f"Payment {self.uuid} - {self.amount_total} {self.currency} - {self.payment_status}"
    
    def save(self, *args, **kwargs):
        if self.uuid is None:
            self.uuid = uuid.uuid4()
        super().save(*args, **kwargs)

class Subscription(models.Model):
    """Separate model to track subscription details"""
    SUBSCRIPTION_STATUS_CHOICES = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('paused', 'Paused'),
    )
    
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, null=True, blank=True)
    
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, choices=SUBSCRIPTION_STATUS_CHOICES)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_start = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscriptions'
        
    def __str__(self):
        return f"Subscription {self.stripe_subscription_id} - {self.status}"

class PaymentLog(models.Model):
    """Log for payment-related events"""
    id = models.AutoField(primary_key=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        
    def __str__(self):
        return f"PaymentLog {self.id} - {self.event_type}"