from django.urls import path
from .views import (
    CreateCheckoutSession, PaymentStatusView,
    ProductListView, StripeConfigView,
    SubscriptionListView, SubscriptionManagementView, SubscriptionDetailView,
    UserSubscriptionStatusView, UserSubscriptionPlansView,
    PaymentSuccessCallbackView, RefreshSubscriptionStatusView,  # Added new views
    stripe_webhook
)

urlpatterns = [
    # Checkout and payment
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('status/', PaymentStatusView.as_view(), name='payment-status'),
    path('success-callback/', PaymentSuccessCallbackView.as_view(), name='payment-success-callback'),  # NEW
    
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # Subscriptions
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('subscriptions/manage/', SubscriptionManagementView.as_view(), name='subscription-manage'),
    path('subscriptions/<str:subscription_id>/', SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # User subscription status
    path('user/subscription-status/', UserSubscriptionStatusView.as_view(), name='user-subscription-status'),
    path('user/subscription-plans/', UserSubscriptionPlansView.as_view(), name='user-subscription-plans'),
    path('user/refresh-subscription/', RefreshSubscriptionStatusView.as_view(), name='refresh-subscription-status'),  # NEW
    
    # Configuration
    path('config/', StripeConfigView.as_view(), name='stripe-config'),
    
    # Webhooks
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]