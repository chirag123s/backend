
from django.urls import path
from .views import (
    CreateCheckoutSession, DirectStripeSubscriptionView, PaymentStatusView,
    ProductListView, StripeConfigView,
    SubscriptionManagementView,
    RefreshSubscriptionStatusView,
    PaymentSuccessCallbackView,
    stripe_webhook
)

urlpatterns = [
    # Core payment endpoints
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('status/', PaymentStatusView.as_view(), name='payment-status'),
    path('success-callback/', PaymentSuccessCallbackView.as_view(), name='payment-success-callback'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # subscription endpoints (email-based)
    path('user/refresh-subscription/', RefreshSubscriptionStatusView.as_view(), name='refresh-subscription-status'),  
    path('user/subscription-direct/', DirectStripeSubscriptionView.as_view(), name='direct-stripe'),
    
    # Subscription management 
    path('subscriptions/manage/', SubscriptionManagementView.as_view(), name='subscription-manage'),
    
    # Configuration
    path('config/', StripeConfigView.as_view(), name='stripe-config'),
    
    # Webhooks 
    path('webhook/', stripe_webhook, name='stripe-webhook'),

]