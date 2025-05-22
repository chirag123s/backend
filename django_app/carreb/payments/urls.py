# | Endpoint                    | Method | Purpose                                             | View                    |
# | --------------------------- | ------ | --------------------------------------------------- | ----------------------- |
# | `/create-checkout-session/` | POST   | Initiates a Stripe Checkout session                 | `CreateCheckoutSession` |
# | `/status/?session_id=...`   | GET    | Checks payment status using Stripe session ID       | `PaymentStatusView`     |
# | `/products/`                | GET    | Lists all active products                           | `ProductListView`       |
# | `/config/`                  | GET    | Returns Stripe's publishable key (for frontend use) | `StripeConfigView`      |
# | `/webhook/`                 | POST   | Handles Stripe webhook events                       | `stripe_webhook`        |

from django.urls import path
from .views import (
    CreateCheckoutSession, PaymentStatusView,
    ProductListView, StripeConfigView,
    stripe_webhook
)

urlpatterns = [
    path('create-checkout-session/', CreateCheckoutSession.as_view(), name='create-checkout-session'),
    path('status/', PaymentStatusView.as_view(), name='payment-status'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('config/', StripeConfigView.as_view(), name='stripe-config'),
    path('webhook/', stripe_webhook, name='stripe-webhook'),
]