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
    
    # NEW: Plan hierarchy and metadata
    plan_tier = models.CharField(max_length=20, null=True, blank=True)  # 'free', 'smart', 'core', 'pro'
    plan_metadata = models.JSONField(null=True, blank=True)  # Store plan features, limits, etc.
    
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

# NEW MODELS FOR SUBSCRIPTION CHANGES

class SubscriptionChange(models.Model):
    """Track subscription plan changes and their status"""
    CHANGE_TYPES = [
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('retention', 'Retention'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    id = models.AutoField(primary_key=True)
    user_email = models.EmailField()
    stripe_subscription_id = models.CharField(max_length=255)
    old_price_id = models.CharField(max_length=255)
    new_price_id = models.CharField(max_length=255)
    old_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_changes')
    new_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='new_changes')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    effective_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Store additional change details
    proration_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    schedule_id = models.CharField(max_length=255, null=True, blank=True)  # Stripe subscription schedule ID
    metadata = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'subscription_changes'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.change_type.title()} - {self.user_email} - {self.status}"

class RetentionOffer(models.Model):
    """Track retention offers presented to users attempting to downgrade"""
    OFFER_TYPES = [
        ('discount', 'Discount'),
        ('free_month', 'Free Month'),
        ('feature_unlock', 'Feature Unlock'),
        ('custom', 'Custom Offer'),
    ]
    
    id = models.AutoField(primary_key=True)
    user_email = models.EmailField()
    stripe_subscription_id = models.CharField(max_length=255)
    offer_type = models.CharField(max_length=50, choices=OFFER_TYPES)
    offer_details = models.JSONField()  # Store offer configuration
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Track offer outcome
    coupon_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_promotion_code = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        db_table = 'retention_offers'
        ordering = ['-created_at']
        
    def __str__(self):
        status = "Accepted" if self.accepted else "Pending"
        return f"{self.offer_type} - {self.user_email} - {status}"

class PaymentLog(models.Model):
    """Log for payment-related events"""
    id = models.AutoField(primary_key=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, null=True, blank=True)
    subscription_change = models.ForeignKey(SubscriptionChange, on_delete=models.CASCADE, null=True, blank=True)  # NEW
    event_type = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        
    def __str__(self):
        return f"PaymentLog {self.id} - {self.event_type}"