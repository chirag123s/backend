import stripe
import logging

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import Product, Customer, Payment, PaymentLog

logger = logging.getLogger(__name__)

class StripeService:
    """Service class for Stripe operations"""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(self, **kwargs):
    try:
        product_id = kwargs.get('product_id')
        amount = kwargs.get('amount')
        product_name = kwargs.get('product_name')
        customer_email = kwargs.get('customer_email')
        metadata = kwargs.get('metadata', {})
        success_url = kwargs.get('success_url', settings.PAYMENT_SUCCESS_URL)
        cancel_url = kwargs.get('cancel_url', settings.PAYMENT_CANCEL_URL)
        
        # Extract search_uid from metadata for tracking
        search_uid = metadata.get('search_uid')
        
        if '{CHECKOUT_SESSION_ID}' not in success_url:
            success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
            
        # Add search_uid to success_url if present
        if search_uid:
            success_url = f"{success_url}&sid={search_uid}"

        if product_id:
            try:
                product = Product.objects.get(id=product_id, active=True)
                amount = product.price
                product_name = product.name
                currency = product.currency
            except Product.DoesNotExist:
                raise ValueError(f"Product with ID {product_id} not found or inactive")
        else:
            if not amount or not product_name:
                raise ValueError("Both amount and product_name are required when product_id is not provided")
            currency = getattr(settings, 'PAYMENT_CURRENCY', 'usd')

        session_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': product_name,
                    },
                    'unit_amount': int(float(amount) * 100),
                },
                'quantity': 1,
            }],
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata,  # This will include search_uid and other data
        }

        if customer_email:
            session_params['customer_email'] = customer_email

        checkout_session = self.stripe.checkout.Session.create(**session_params)

        customer = None
        if customer_email:
            customer, _ = Customer.objects.get_or_create(
                email=customer_email,
                defaults={'updated_at': timezone.now()}
            )

        with transaction.atomic():
            payment = Payment.objects.create(
                customer=customer,
                product_id=product_id if product_id else None,
                amount=amount,
                currency=currency,
                stripe_session_id=checkout_session.id,
                metadata=metadata,  # Store metadata including search_uid
            )

        logger.info(f"Checkout session created: {checkout_session.id} with search_uid: {search_uid}")

        return {
            'id': checkout_session.id,
            'url': checkout_session.url,
            'payment_id': str(payment.uuid),
        }

    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}", exc_info=True)
        raise

    def handle_webhook_event(self, payload, signature):
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )

            event_type = event['type']
            event_data = event['data']['object']

            logger.info(f"Processing Stripe webhook: {event_type}")

            if event_type == 'checkout.session.completed':
                self._handle_checkout_session_completed(event_data)
            elif event_type == 'payment_intent.succeeded':
                self._handle_payment_intent_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                self._handle_payment_intent_failed(event_data)
            elif event_type == 'charge.refunded':
                self._handle_charge_refunded(event_data)

            return {'status': 'success', 'type': event_type}

        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
            raise

    def _handle_checkout_session_completed(self, session):
        try:
            session_id = session.get('id')
            payment_intent_id = session.get('payment_intent')

            with transaction.atomic():
                payment = Payment.objects.filter(stripe_session_id=session_id).first()
                if payment:
                    payment.status = 'completed'
                    payment.stripe_payment_intent_id = payment_intent_id
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type='checkout.session.completed',
                        data={
                            'session_id': session_id,
                            'payment_intent_id': payment_intent_id,
                        }
                    )
                else:
                    logger.error(f"Payment not found for session ID {session_id}")

        except Exception as e:
            logger.error(f"Error processing checkout.session.completed: {str(e)}", exc_info=True)
            raise

    def _handle_payment_intent_succeeded(self, payment_intent):
        try:
            payment_intent_id = payment_intent.get('id')

            with transaction.atomic():
                payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
                if payment:
                    payment.status = 'completed'
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type='payment_intent.succeeded',
                        data={'payment_intent_id': payment_intent_id}
                    )
                else:
                    logger.warning(f"PaymentIntent succeeded but no payment found: {payment_intent_id}")

        except Exception as e:
            logger.error(f"Error processing payment_intent.succeeded: {str(e)}", exc_info=True)
            raise

    def _handle_payment_intent_failed(self, payment_intent):
        try:
            payment_intent_id = payment_intent.get('id')

            with transaction.atomic():
                payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
                if payment:
                    payment.status = 'failed'
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type='payment_intent.payment_failed',
                        data={'payment_intent_id': payment_intent_id}
                    )
                else:
                    logger.warning(f"Failed payment intent not matched: {payment_intent_id}")

        except Exception as e:
            logger.error(f"Error processing payment_intent.payment_failed: {str(e)}", exc_info=True)
            raise

    def _handle_charge_refunded(self, charge):
        try:
            payment_intent_id = charge.get('payment_intent')

            with transaction.atomic():
                payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
                if payment:
                    payment.status = 'refunded'
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type='charge.refunded',
                        data={'payment_intent_id': payment_intent_id}
                    )
                else:
                    logger.warning(f"Refund received but payment not found: {payment_intent_id}")

        except Exception as e:
            logger.error(f"Error processing charge.refunded: {str(e)}", exc_info=True)
            raise
