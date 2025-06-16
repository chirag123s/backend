# | Endpoint                    | Method | Purpose                                             | View                    |
# | --------------------------- | ------ | --------------------------------------------------- | ----------------------- |
# | `/create-checkout-session/` | POST   | Initiates a Stripe Checkout session                 | `CreateCheckoutSession` |
# | `/status/?session_id=...`   | GET    | Checks payment status using Stripe session ID       | `PaymentStatusView`     |
# | `/products/`                | GET    | Lists all active products                           | `ProductListView`       |
# | `/config/`                  | GET    | Returns Stripe's publishable key (for frontend use) | `StripeConfigView`      |
# | `/webhook/`                 | POST   | Handles Stripe webhook events                       | `stripe_webhook`        |

# payments/urls.py
from django.urls import path
from .views import (
    CreateCheckoutSession, PaymentStatusView,
    ProductListView, StripeConfigView,
    SubscriptionListView, SubscriptionManagementView, SubscriptionDetailView,
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
    
    # Configuration
    path('config/', StripeConfigView.as_view(), name='stripe-config'),
    
    # Webhooks
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]