# payments/serializers.py
from rest_framework import serializers
from .models import Product, Customer, Payment, PaymentLog

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
        read_only_fields = ('stripe_session_id', 'stripe_payment_intent_id', 'status')

class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = '__all__'
        read_only_fields = ('created_at',)

class CheckoutSessionCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    product_name = serializers.CharField(max_length=255, required=False)
    customer_email = serializers.EmailField(required=False)
    metadata = serializers.JSONField(required=False)
    success_url = serializers.CharField(max_length=2000, required=False)
    cancel_url = serializers.CharField(max_length=2000, required=False)
    
    def validate(self, data):
        """
        Validate that either product_id or (amount and product_name) are provided
        """
        if not data.get('product_id') and not (data.get('amount') and data.get('product_name')):
            raise serializers.ValidationError(
                "Either product_id or both amount and product_name must be provided."
            )
        return data