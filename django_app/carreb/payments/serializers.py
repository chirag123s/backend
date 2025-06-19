# payments/serializers.py
from rest_framework import serializers
from .models import Product, Customer, Payment, PaymentLog, Subscription, SubscriptionChange, RetentionOffer

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('session_id', 'stripe_payment_intent_id', 'payment_status', 'stripe_subscription_id')

class SubscriptionSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'
        read_only_fields = ('created_at',)

# NEW SERIALIZERS FOR SUBSCRIPTION CHANGES

class SubscriptionChangeSerializer(serializers.ModelSerializer):
    old_product = ProductSerializer(read_only=True)
    new_product = ProductSerializer(read_only=True)
    
    class Meta:
        model = SubscriptionChange
        fields = '__all__'
        read_only_fields = ('created_at', 'completed_at')

class RetentionOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetentionOffer
        fields = '__all__'
        read_only_fields = ('created_at', 'accepted_at')

class CheckoutSessionCreateSerializer(serializers.Serializer):
    # Product selection - CHANGED: Now accepts string to handle Stripe product IDs
    product_id = serializers.CharField(max_length=255, required=False)  # Changed from IntegerField
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    product_name = serializers.CharField(max_length=255, required=False)
    
    # Payment type
    payment_type = serializers.ChoiceField(
        choices=[('one_time', 'One-time Payment'), ('subscription', 'Subscription')],
        default='one_time'
    )
    
    # Subscription-specific fields
    billing_interval = serializers.ChoiceField(
        choices=[('month', 'Monthly'), ('year', 'Yearly')],
        required=False,
        allow_null=True
    )
    billing_interval_count = serializers.IntegerField(default=1, required=False)
    trial_period_days = serializers.IntegerField(required=False, allow_null=True)
    
    # Customer and metadata - ADDED user_id support
    customer_email = serializers.EmailField(required=False)
    user_id = serializers.CharField(max_length=255, required=False)  # Added this field
    metadata = serializers.JSONField(required=False)
    
    # URLs
    success_url = serializers.CharField(max_length=2000, required=False)
    cancel_url = serializers.CharField(max_length=2000, required=False)
    
    def validate(self, data):
        """
        Validate based on payment type
        """
        payment_type = data.get('payment_type', 'one_time')
        
        if payment_type == 'subscription':
            # For subscriptions, product_id is required (we need Stripe product/price setup)
            if not data.get('product_id'):
                raise serializers.ValidationError(
                    "product_id is required for subscription payments."
                )
        else:
            # For one-time payments, either product_id or (amount and product_name) are required
            if not data.get('product_id') and not (data.get('amount') and data.get('product_name')):
                raise serializers.ValidationError(
                    "Either product_id or both amount and product_name must be provided for one-time payments."
                )
        
        # Validate customer identification - require either email or user_id
        if not data.get('customer_email') and not data.get('user_id'):
            raise serializers.ValidationError(
                "Either customer_email or user_id must be provided."
            )
        
        return data
    
class SubscriptionManagementSerializer(serializers.Serializer):
    """Serializer for subscription management operations"""
    subscription_id = serializers.CharField(max_length=255)
    action = serializers.ChoiceField(choices=[
        ('cancel', 'Cancel'),
        ('pause', 'Pause'),
        ('resume', 'Resume'),
        ('update', 'Update'),
        ('change_plan', 'Change Plan'),  # NEW
        ('apply_retention', 'Apply Retention'),  # NEW
    ])
    cancel_at_period_end = serializers.BooleanField(required=False, default=True)
    new_price_id = serializers.CharField(max_length=255, required=False)
    proration_behavior = serializers.ChoiceField(
        choices=[('create_prorations', 'Create Prorations'), ('none', 'None')],
        default='create_prorations',
        required=False
    )
    # NEW: For retention offers
    offer_details = serializers.JSONField(required=False)

# NEW SERIALIZERS FOR PLAN CHANGES

class PlanChangeRequestSerializer(serializers.Serializer):
    """Serializer for plan change requests"""
    subscription_id = serializers.CharField(max_length=255)
    new_price_id = serializers.CharField(max_length=255)
    change_type = serializers.ChoiceField(choices=[('upgrade', 'Upgrade'), ('downgrade', 'Downgrade')])
    user_email = serializers.EmailField()
    metadata = serializers.JSONField(required=False)
    
    def validate(self, data):
        if not data.get('subscription_id'):
            raise serializers.ValidationError("subscription_id is required")
        if not data.get('new_price_id'):
            raise serializers.ValidationError("new_price_id is required")
        if not data.get('user_email'):
            raise serializers.ValidationError("user_email is required")
        return data

class RetentionOfferRequestSerializer(serializers.Serializer):
    """Serializer for retention offer requests"""
    subscription_id = serializers.CharField(max_length=255)
    user_email = serializers.EmailField()
    current_plan_type = serializers.CharField(max_length=50, required=False)
    
    def validate(self, data):
        if not data.get('subscription_id'):
            raise serializers.ValidationError("subscription_id is required")
        if not data.get('user_email'):
            raise serializers.ValidationError("user_email is required")
        return data

class RetentionOfferAcceptSerializer(serializers.Serializer):
    """Serializer for accepting retention offers"""
    subscription_id = serializers.CharField(max_length=255)
    offer_id = serializers.IntegerField()
    user_email = serializers.EmailField()

class UserSubscriptionStatusSerializer(serializers.Serializer):
    """Serializer for user subscription status response"""
    has_subscription = serializers.BooleanField()
    plan_type = serializers.CharField(max_length=50)
    plan_name = serializers.CharField(max_length=255)
    subscriptions = SubscriptionSerializer(many=True)
    current_subscription = SubscriptionSerializer(allow_null=True)
    # NEW: Include pending changes
    pending_changes = SubscriptionChangeSerializer(many=True, required=False)
    recent_offers = RetentionOfferSerializer(many=True, required=False)