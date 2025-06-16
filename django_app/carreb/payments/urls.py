# Update django_app/carreb/payments/urls.py

from django.urls import path
from .views import (
    CreateCheckoutSession, PaymentStatusView,
    ProductListView, StripeConfigView,
    SubscriptionListView, SubscriptionManagementView, SubscriptionDetailView,
    UserSubscriptionStatusView, UserSubscriptionPlansView,  # Add these new imports
    stripe_webhook
)

urlpatterns = [
    # Checkout and payment
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('status/', PaymentStatusView.as_view(), name='payment-status'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # Subscriptions
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/manage/', SubscriptionManagementView.as_view(), name='subscription-manage'),
    path('subscriptions/<str:subscription_id>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # User subscription status - NEW ENDPOINTS
    path('user/subscription-status/', UserSubscriptionStatusView.as_view(), name='user-subscription-status'),
    path('user/subscription-plans/', UserSubscriptionPlansView.as_view(), name='user-subscription-plans'),
    
    # Configuration
    path('config/', StripeConfigView.as_view(), name='stripe-config'),
    
    # Webhooks
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]