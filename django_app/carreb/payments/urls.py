# payments/urls.py

from django.urls import path
from .views import (
    CreateCheckoutSession, DirectStripeSubscriptionView, PaymentStatusView,
    ProductListView, 
    SubscriptionManagementView,
    RefreshSubscriptionStatusView,
    PaymentSuccessCallbackView,
    stripe_webhook,
    # NEW: Subscription change views
    SubscriptionChangeView,
    RetentionOfferView,
    RetentionOfferAcceptView,
    SubscriptionChangesHistoryView,
    UserRetentionOffersView,
)

urlpatterns = [
    # Core payment endpoints
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('status/', PaymentStatusView.as_view(), name='payment-status'),
    path('success-callback/', PaymentSuccessCallbackView.as_view(), name='payment-success-callback'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # Subscription endpoints (email-based)
    path('user/refresh-subscription/', RefreshSubscriptionStatusView.as_view(), name='refresh-subscription-status'),  
    path('user/direct-stripe-subscription/', DirectStripeSubscriptionView.as_view(), name='direct-stripe-subscription'),
    
    # Subscription management 
    path('subscriptions/manage/', SubscriptionManagementView.as_view(), name='subscription-manage'),
    
    # NEW: Subscription change endpoints
    path('subscriptions/change-plan/', SubscriptionChangeView.as_view(), name='subscription-change-plan'),
    path('subscriptions/retention-offer/', RetentionOfferView.as_view(), name='retention-offer'),
    path('subscriptions/retention-offer/accept/', RetentionOfferAcceptView.as_view(), name='retention-offer-accept'),
    path('subscriptions/changes/history/', SubscriptionChangesHistoryView.as_view(), name='subscription-changes-history'),
    path('subscriptions/retention-offers/', UserRetentionOffersView.as_view(), name='user-retention-offers'),
    
    # Webhooks 
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]