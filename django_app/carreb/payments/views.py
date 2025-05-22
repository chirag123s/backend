import stripe
import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Payment
from .serializers import (
    ProductSerializer, PaymentSerializer,
    CheckoutSessionCreateSerializer
)
from .services import StripeService

logger = logging.getLogger(__name__)
stripe_service = StripeService()

class CreateCheckoutSession(APIView):
    """Create a Stripe Checkout Session"""

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
            
            status_info = {
                'session_id': session.id,
                'payment_status': session.payment_status,
                'payment_intent': session.payment_intent,
                'customer_email': session.customer_email,
                'amount_total': session.amount_total,
                'currency': session.currency,
            }

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
            products = Product.objects.filter(active=True)
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}", exc_info=True)
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
