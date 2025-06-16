# payments/views.py
import stripe
import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Payment, Subscription
from .serializers import (
    ProductSerializer, PaymentSerializer, SubscriptionSerializer,
    CheckoutSessionCreateSerializer, SubscriptionManagementSerializer
)
from .services import StripeService

logger = logging.getLogger(__name__)
stripe_service = StripeService()

class CreateCheckoutSession(APIView):
    """Create a Stripe Checkout Session for both one-time payments and subscriptions"""

    def post(self, request):
        serializer = CheckoutSessionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Checkout session validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = stripe_service.create_checkout_session(**serializer.validated_data)
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            logger.warning(f"Invalid input: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(APIView):
    """Retrieve payment status from Stripe using session ID"""

    def get(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch session from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Get local payment record
            local_payment = Payment.objects.filter(session_id=session_id).first()
            
            status_info = {
                'uuid': str(local_payment.uuid) if local_payment else None,
                'session_id': session.id,
                'payment_status': session.payment_status,
                'payment_intent': session.payment_intent,
                'subscription': session.subscription,
                'customer_email': session.customer_email,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'mode': session.mode,
                'created_at': local_payment.created_at.isoformat() if local_payment else None,
            }

            # Add subscription details if it's a subscription payment
            if session.mode == 'subscription' and session.subscription:
                try:
                    subscription = stripe.Subscription.retrieve(session.subscription)
                    local_subscription = Subscription.objects.filter(
                        stripe_subscription_id=session.subscription
                    ).first()
                    
                    status_info['subscription_details'] = {
                        'id': subscription.id,
                        'status': subscription.status,
                        'current_period_start': subscription.current_period_start,
                        'current_period_end': subscription.current_period_end,
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'trial_start': subscription.trial_start,
                        'trial_end': subscription.trial_end,
                        'local_subscription_id': local_subscription.id if local_subscription else None,
                    }
                except Exception as e:
                    logger.warning(f"Could not retrieve subscription details: {str(e)}")

            return Response(status_info)
        except stripe.error.InvalidRequestError:
            logger.warning(f"Stripe session not found: {session_id}")
            return Response({'error': 'Session not found in Stripe'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving payment status: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductListView(APIView):
    """List all active products"""

    def get(self, request):
        try:
            product_type = request.query_params.get('type')  # 'one_time' or 'subscription'
            
            queryset = Product.objects.filter(active=True)
            if product_type:
                queryset = queryset.filter(product_type=product_type)
            
            products = queryset.order_by('product_type', 'name')
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionListView(APIView):
    """List user's subscriptions"""

    def get(self, request):
        try:
            customer_email = request.query_params.get('customer_email')
            customer_id = request.query_params.get('customer_id')
            
            if not customer_email and not customer_id:
                return Response({
                    'error': 'Either customer_email or customer_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = Subscription.objects.all()
            
            if customer_email:
                queryset = queryset.filter(customer__email=customer_email)
            elif customer_id:
                queryset = queryset.filter(customer__id=customer_id)
            
            subscriptions = queryset.order_by('-created_at')
            serializer = SubscriptionSerializer(subscriptions, many=True)
            
            return Response({
                'subscriptions': serializer.data
            })
        except Exception as e:
            logger.error(f"Error listing subscriptions: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionManagementView(APIView):
    """Manage subscription operations (cancel, pause, resume, update)"""

    def post(self, request):
        serializer = SubscriptionManagementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            subscription_id = serializer.validated_data['subscription_id']
            action = serializer.validated_data['action']
            
            # Verify subscription exists locally
            local_subscription = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()
            
            if not local_subscription:
                return Response({
                    'error': 'Subscription not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Perform the requested action
            result = stripe_service.manage_subscription(
                subscription_id, action, **serializer.validated_data
            )

            return Response({
                'status': 'success',
                'subscription': {
                    'id': result.id,
                    'status': result.status,
                    'cancel_at_period_end': result.cancel_at_period_end,
                    'current_period_end': result.current_period_end,
                }
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error managing subscription: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionDetailView(APIView):
    """Get subscription details"""

    def get(self, request, subscription_id):
        try:
            # Get from local database
            local_subscription = Subscription.objects.filter(
                stripe_subscription_id=subscription_id
            ).first()
            
            if not local_subscription:
                return Response({
                    'error': 'Subscription not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get latest data from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)

            # Update local record with latest Stripe data
            stripe_service._update_local_subscription(stripe_subscription)
            
            # Refresh local subscription
            local_subscription.refresh_from_db()
            
            serializer = SubscriptionSerializer(local_subscription)
            
            # Add Stripe-specific data
            subscription_data = serializer.data
            subscription_data['stripe_data'] = {
                'latest_invoice': stripe_subscription.latest_invoice,
                'default_payment_method': stripe_subscription.default_payment_method,
                'items': [
                    {
                        'id': item.id,
                        'price_id': item.price.id,
                        'quantity': item.quantity,
                    } for item in stripe_subscription.items.data
                ]
            }

            return Response(subscription_data)
        except Exception as e:
            logger.error(f"Error retrieving subscription details: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Stripe webhook endpoint to handle events"""

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if not sig_header:
        logger.error("Missing Stripe signature header")
        return HttpResponse(status=400)

    try:
        stripe_service.handle_webhook_event(payload, sig_header)
        return HttpResponse(status=200)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe signature: {str(e)}", exc_info=True)
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Stripe webhook processing error: {str(e)}", exc_info=True)
        return HttpResponse(status=500)


class StripeConfigView(APIView):
    """Expose Stripe publishable key to the frontend"""

    def get(self, request):
        return Response({
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEY
        })