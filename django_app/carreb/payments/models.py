# payments/models.py
from django.db import models
from django.utils import timezone
import uuid

class Product(models.Model):
    """Product model for items that can be purchased"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='aud')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        
    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"

class Customer(models.Model):
    """Customer model for tracking user purchases"""
    id = models.AutoField(primary_key=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)  # Optional link to Auth0 user
    email = models.EmailField()
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        
    def __str__(self):
        return self.email

class Payment(models.Model):
    """Payment model for tracking payments"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_TYPE_CHOICES = (
        ('one_time', 'One-time Payment'),
        ('subscription', 'Subscription'),
    )
    
    # Change the default from uuid.uuid4 to a string representation of a UUID
    uuid = models.UUIDField(
        primary_key=True,
        default=None,  # Remove the callable default
        editable=False
    )
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='aud')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='one_time')
    stripe_session_id = models.CharField(max_length=255)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        
    def __str__(self):
        return f"Payment {self.uuid} - {self.amount} {self.currency} - {self.status}"
    
    # Add the save method to set UUID before saving
    def save(self, *args, **kwargs):
        if self.uuid is None:
            self.uuid = uuid.uuid4()
        super().save(*args, **kwargs)

class PaymentLog(models.Model):
    """Log for payment-related events"""
    id = models.AutoField(primary_key=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=255)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_logs'
        
    def __str__(self):
        return f"PaymentLog {self.id} - {self.event_type}"