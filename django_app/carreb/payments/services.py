# payments/services.py
import stripe
import logging
from datetime import datetime

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import Product, Customer, Payment, PaymentLog, Subscription

logger = logging.getLogger(__name__)


class StripeService:
    """Service class for Stripe operations"""

    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY

    # In django_app/carreb/payments/services.py
    # Update the create_checkout_session method around line 25-65

    def create_checkout_session(self, **kwargs):
        """Create checkout session for both one-time payments and subscriptions"""
        try:
            product_id = kwargs.get("product_id")
            amount = kwargs.get("amount")
            product_name = kwargs.get("product_name")
            customer_email = kwargs.get("customer_email")
            metadata = kwargs.get("metadata", {})
            success_url = kwargs.get("success_url", settings.PAYMENT_SUCCESS_URL)
            cancel_url = kwargs.get("cancel_url", settings.PAYMENT_CANCEL_URL)
            payment_type = kwargs.get("payment_type", "one_time")
            trial_period_days = kwargs.get("trial_period_days")

            # Extract search_uid from metadata for tracking
            search_uid = metadata.get("search_uid")

            # Ensure session_id placeholder is in success_url
            if "{CHECKOUT_SESSION_ID}" not in success_url:
                success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"

            # Add search_uid to success_url if present
            if search_uid:
                success_url = f"{success_url}&sid={search_uid}"

            # Handle product and pricing - UPDATED to handle both local IDs and Stripe IDs
            product = None
            if product_id:
                try:
                    # First try to find by local integer ID
                    if product_id.isdigit():
                        product = Product.objects.get(id=int(product_id), active=True)
                    else:
                        # Try to find by Stripe product ID
                        product = Product.objects.get(
                            stripe_product_id=product_id, active=True
                        )

                    if (
                        payment_type == "subscription"
                        and product.product_type != "subscription"
                    ):
                        raise ValueError(
                            f"Product {product_id} is not configured for subscriptions"
                        )

                    amount = product.price
                    product_name = product.name
                    currency = product.currency

                    # For subscriptions, we need Stripe price ID
                    if payment_type == "subscription":
                        if not product.stripe_price_id:
                            # Create Stripe product and price if not exists
                            stripe_product, stripe_price = (
                                self._create_stripe_subscription_product(product)
                            )
                            product.stripe_product_id = stripe_product.id
                            product.stripe_price_id = stripe_price.id
                            product.save()

                except Product.DoesNotExist:
                    raise ValueError(
                        f"Product with ID {product_id} not found or inactive"
                    )
            else:
                if not amount or not product_name:
                    raise ValueError(
                        "Both amount and product_name are required when product_id is not provided"
                    )
                currency = getattr(settings, "PAYMENT_CURRENCY", "aud")

            # Create or get customer
            customer = None
            if customer_email:
                customer, created = Customer.objects.get_or_create(
                    email=customer_email, defaults={"updated_at": timezone.now()}
                )

                # Create or get Stripe customer
                if not customer.stripe_customer_id:
                    stripe_customer = self.stripe.Customer.create(
                        email=customer_email,
                        metadata={"internal_customer_id": customer.id},
                    )
                    customer.stripe_customer_id = stripe_customer.id
                    customer.save()

            # Create checkout session based on payment type
            if payment_type == "subscription":
                checkout_session = self._create_subscription_checkout_session(
                    product,
                    customer,
                    metadata,
                    success_url,
                    cancel_url,
                    trial_period_days,
                )
            else:
                checkout_session = self._create_one_time_checkout_session(
                    amount,
                    currency,
                    product_name,
                    customer,
                    metadata,
                    success_url,
                    cancel_url,
                )

            # Create payment record - use product.id if we found a product
            with transaction.atomic():
                payment = Payment.objects.create(
                    customer=customer,
                    product_id=product.id if product else None,
                    amount_total=amount,
                    currency=currency,
                    session_id=checkout_session.id,
                    payment_type=payment_type,
                    metadata=metadata,
                )

            logger.info(
                f"Checkout session created: {checkout_session.id} (type: {payment_type}) with search_uid: {search_uid}"
            )

            return {
                "id": checkout_session.id,
                "url": checkout_session.url,
                "payment_id": str(payment.uuid),
            }

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}", exc_info=True)
            raise

    def _create_subscription_checkout_session(
        self,
        product,
        customer,
        metadata,
        success_url,
        cancel_url,
        trial_period_days=None,
    ):
        """Create subscription checkout session"""
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": product.stripe_price_id,
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata,
        }

        if customer and customer.stripe_customer_id:
            session_params["customer"] = customer.stripe_customer_id
        elif customer:
            session_params["customer_email"] = customer.email

        # Add trial period if specified
        if trial_period_days:
            session_params["subscription_data"] = {
                "trial_period_days": trial_period_days,
                "metadata": metadata,
            }

        return self.stripe.checkout.Session.create(**session_params)

    def _create_one_time_checkout_session(
        self,
        amount,
        currency,
        product_name,
        customer,
        metadata,
        success_url,
        cancel_url,
    ):
        """Create one-time payment checkout session"""
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": product_name,
                        },
                        "unit_amount": int(float(amount) * 100),
                    },
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata,
        }

        if customer and customer.stripe_customer_id:
            session_params["customer"] = customer.stripe_customer_id
        elif customer:
            session_params["customer_email"] = customer.email

        return self.stripe.checkout.Session.create(**session_params)

    def _create_stripe_subscription_product(self, product):
        """Create Stripe product and price for subscription"""
        # Create Stripe product
        stripe_product = self.stripe.Product.create(
            name=product.name,
            description=product.description,
        )

        # Create Stripe price
        stripe_price = self.stripe.Price.create(
            unit_amount=int(float(product.price) * 100),
            currency=product.currency,
            recurring={
                "interval": product.billing_interval or "month",
                "interval_count": product.billing_interval_count or 1,
            },
            product=stripe_product.id,
        )

        return stripe_product, stripe_price

    def manage_subscription(self, subscription_id, action, **kwargs):
        """Manage subscription operations"""
        try:
            if action == "cancel":
                return self._cancel_subscription(
                    subscription_id, kwargs.get("cancel_at_period_end", True)
                )
            elif action == "pause":
                return self._pause_subscription(subscription_id)
            elif action == "resume":
                return self._resume_subscription(subscription_id)
            elif action == "update":
                return self._update_subscription(subscription_id, kwargs)
            else:
                raise ValueError(f"Unknown action: {action}")
        except Exception as e:
            logger.error(
                f"Error managing subscription {subscription_id}: {str(e)}",
                exc_info=True,
            )
            raise

    def _cancel_subscription(self, subscription_id, cancel_at_period_end=True):
        """Cancel a subscription"""
        if cancel_at_period_end:
            subscription = self.stripe.Subscription.modify(
                subscription_id, cancel_at_period_end=True
            )
        else:
            subscription = self.stripe.Subscription.delete(subscription_id)

        # Update local subscription record
        self._update_local_subscription(subscription)
        return subscription

    def _pause_subscription(self, subscription_id):
        """Pause a subscription"""
        subscription = self.stripe.Subscription.modify(
            subscription_id, pause_collection={"behavior": "void"}
        )
        self._update_local_subscription(subscription)
        return subscription

    def _resume_subscription(self, subscription_id):
        """Resume a paused subscription"""
        subscription = self.stripe.Subscription.modify(
            subscription_id, pause_collection=""
        )
        self._update_local_subscription(subscription)
        return subscription

    def _update_subscription(self, subscription_id, kwargs):
        """Update subscription (e.g., change price)"""
        update_params = {}

        if kwargs.get("new_price_id"):
            # Get current subscription
            subscription = self.stripe.Subscription.retrieve(subscription_id)

            update_params["items"] = [
                {
                    "id": subscription["items"]["data"][0].id,
                    "price": kwargs["new_price_id"],
                }
            ]

        if kwargs.get("proration_behavior"):
            update_params["proration_behavior"] = kwargs["proration_behavior"]

        subscription = self.stripe.Subscription.modify(subscription_id, **update_params)
        self._update_local_subscription(subscription)
        return subscription

    def _update_local_subscription(self, stripe_subscription):
        """Update local subscription record from Stripe data"""
        try:
            local_subscription = Subscription.objects.get(
                stripe_subscription_id=stripe_subscription.id
            )

            local_subscription.status = stripe_subscription.status
            local_subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start, tz=timezone.utc
            )
            local_subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            )
            local_subscription.cancel_at_period_end = (
                stripe_subscription.cancel_at_period_end
            )

            if stripe_subscription.canceled_at:
                local_subscription.canceled_at = datetime.fromtimestamp(
                    stripe_subscription.canceled_at, tz=timezone.utc
                )

            local_subscription.save()

        except Subscription.DoesNotExist:
            logger.warning(
                f"Local subscription not found for Stripe ID: {stripe_subscription.id}"
            )

    def handle_webhook_event(self, payload, signature):
        """Handle webhook events for both payments and subscriptions"""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )

            event_type = event["type"]
            event_data = event["data"]["object"]

            logger.info(f"Processing Stripe webhook: {event_type}")

            # Payment events
            if event_type == "checkout.session.completed":
                self._handle_checkout_session_completed(event_data)
            elif event_type == "payment_intent.succeeded":
                self._handle_payment_intent_succeeded(event_data)
            elif event_type == "payment_intent.payment_failed":
                self._handle_payment_intent_failed(event_data)
            elif event_type == "charge.refunded":
                self._handle_charge_refunded(event_data)

            # Subscription events
            elif event_type == "customer.subscription.created":
                self._handle_subscription_created(event_data)
            elif event_type == "customer.subscription.updated":
                self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                self._handle_subscription_deleted(event_data)
            elif event_type == "invoice.payment_succeeded":
                self._handle_invoice_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                self._handle_invoice_payment_failed(event_data)

            return {"status": "success", "type": event_type}

        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
            raise

    def _handle_checkout_session_completed(self, session):
        """Handle checkout session completion for both payment types"""
        try:
            session_id = session.get("id")
            mode = session.get("mode")
            payment_intent_id = session.get("payment_intent")
            subscription_id = session.get("subscription")

            with transaction.atomic():
                payment = Payment.objects.filter(session_id=session_id).first()
                if payment:
                    payment.payment_status = "paid"
                    payment.stripe_payment_intent_id = payment_intent_id

                    if mode == "subscription" and subscription_id:
                        payment.stripe_subscription_id = subscription_id
                        payment.payment_type = "subscription"

                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type="checkout.session.completed",
                        data={
                            "session_id": session_id,
                            "payment_intent_id": payment_intent_id,
                            "subscription_id": subscription_id,
                            "mode": mode,
                        },
                    )
                else:
                    logger.error(f"Payment not found for session ID {session_id}")

        except Exception as e:
            logger.error(
                f"Error processing checkout.session.completed: {str(e)}", exc_info=True
            )
            raise

    def _handle_subscription_created(self, subscription_data):
        """Handle subscription creation"""
        try:
            subscription_id = subscription_data.get("id")
            customer_id = subscription_data.get("customer")

            with transaction.atomic():
                # Find customer
                customer = Customer.objects.filter(
                    stripe_customer_id=customer_id
                ).first()
                if not customer:
                    logger.warning(
                        f"Customer not found for subscription: {subscription_id}"
                    )
                    return

                # Find associated payment
                payment = Payment.objects.filter(
                    stripe_subscription_id=subscription_id
                ).first()

                # Create subscription record
                subscription = Subscription.objects.create(
                    customer=customer,
                    payment=payment,
                    stripe_subscription_id=subscription_id,
                    status=subscription_data.get("status"),
                    current_period_start=datetime.fromtimestamp(
                        subscription_data.get("current_period_start"), tz=timezone.utc
                    ),
                    current_period_end=datetime.fromtimestamp(
                        subscription_data.get("current_period_end"), tz=timezone.utc
                    ),
                    cancel_at_period_end=subscription_data.get(
                        "cancel_at_period_end", False
                    ),
                )

                if subscription_data.get("trial_start"):
                    subscription.trial_start = datetime.fromtimestamp(
                        subscription_data.get("trial_start"), tz=timezone.utc
                    )
                if subscription_data.get("trial_end"):
                    subscription.trial_end = datetime.fromtimestamp(
                        subscription_data.get("trial_end"), tz=timezone.utc
                    )

                subscription.save()

                PaymentLog.objects.create(
                    subscription=subscription,
                    event_type="customer.subscription.created",
                    data=subscription_data,
                )

        except Exception as e:
            logger.error(
                f"Error processing subscription creation: {str(e)}", exc_info=True
            )
            raise

    def _handle_subscription_updated(self, subscription_data):
        """Handle subscription updates"""
        try:
            subscription_id = subscription_data.get("id")

            with transaction.atomic():
                subscription = Subscription.objects.filter(
                    stripe_subscription_id=subscription_id
                ).first()

                if subscription:
                    subscription.status = subscription_data.get("status")
                    subscription.current_period_start = datetime.fromtimestamp(
                        subscription_data.get("current_period_start"), tz=timezone.utc
                    )
                    subscription.current_period_end = datetime.fromtimestamp(
                        subscription_data.get("current_period_end"), tz=timezone.utc
                    )
                    subscription.cancel_at_period_end = subscription_data.get(
                        "cancel_at_period_end", False
                    )

                    if subscription_data.get("canceled_at"):
                        subscription.canceled_at = datetime.fromtimestamp(
                            subscription_data.get("canceled_at"), tz=timezone.utc
                        )

                    subscription.save()

                    PaymentLog.objects.create(
                        subscription=subscription,
                        event_type="customer.subscription.updated",
                        data=subscription_data,
                    )

        except Exception as e:
            logger.error(
                f"Error processing subscription update: {str(e)}", exc_info=True
            )
            raise

    def _handle_subscription_deleted(self, subscription_data):
        """Handle subscription cancellation"""
        try:
            subscription_id = subscription_data.get("id")

            with transaction.atomic():
                subscription = Subscription.objects.filter(
                    stripe_subscription_id=subscription_id
                ).first()

                if subscription:
                    subscription.status = "canceled"
                    subscription.canceled_at = timezone.now()
                    subscription.save()

                    PaymentLog.objects.create(
                        subscription=subscription,
                        event_type="customer.subscription.deleted",
                        data=subscription_data,
                    )

        except Exception as e:
            logger.error(
                f"Error processing subscription deletion: {str(e)}", exc_info=True
            )
            raise

    def _handle_invoice_payment_succeeded(self, invoice_data):
        """Handle successful subscription payment"""
        try:
            subscription_id = invoice_data.get("subscription")

            if subscription_id:
                PaymentLog.objects.create(
                    subscription_id=subscription_id,
                    event_type="invoice.payment_succeeded",
                    data=invoice_data,
                )

        except Exception as e:
            logger.error(
                f"Error processing invoice payment success: {str(e)}", exc_info=True
            )
            raise

    def _handle_invoice_payment_failed(self, invoice_data):
        """Handle failed subscription payment"""
        try:
            subscription_id = invoice_data.get("subscription")

            if subscription_id:
                PaymentLog.objects.create(
                    subscription_id=subscription_id,
                    event_type="invoice.payment_failed",
                    data=invoice_data,
                )

        except Exception as e:
            logger.error(
                f"Error processing invoice payment failure: {str(e)}", exc_info=True
            )
            raise

    # Keep existing one-time payment handlers
    def _handle_payment_intent_succeeded(self, payment_intent):
        """Handle successful payment intent"""
        try:
            payment_intent_id = payment_intent.get("id")

            with transaction.atomic():
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()
                if payment:
                    payment.payment_status = "paid"
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type="payment_intent.succeeded",
                        data={"payment_intent_id": payment_intent_id},
                    )
                else:
                    logger.warning(
                        f"PaymentIntent succeeded but no payment found: {payment_intent_id}"
                    )

        except Exception as e:
            logger.error(
                f"Error processing payment_intent.succeeded: {str(e)}", exc_info=True
            )
            raise

    def _handle_payment_intent_failed(self, payment_intent):
        """Handle failed payment intent"""
        try:
            payment_intent_id = payment_intent.get("id")

            with transaction.atomic():
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()
                if payment:
                    payment.payment_status = "failed"
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type="payment_intent.payment_failed",
                        data={"payment_intent_id": payment_intent_id},
                    )
                else:
                    logger.warning(
                        f"Failed payment intent not matched: {payment_intent_id}"
                    )

        except Exception as e:
            logger.error(
                f"Error processing payment_intent.payment_failed: {str(e)}",
                exc_info=True,
            )
            raise

    def _handle_charge_refunded(self, charge):
        """Handle charge refund"""
        try:
            payment_intent_id = charge.get("payment_intent")

            with transaction.atomic():
                payment = Payment.objects.filter(
                    stripe_payment_intent_id=payment_intent_id
                ).first()
                if payment:
                    payment.payment_status = "refunded"
                    payment.updated_at = timezone.now()
                    payment.save()

                    PaymentLog.objects.create(
                        payment=payment,
                        event_type="charge.refunded",
                        data={"payment_intent_id": payment_intent_id},
                    )
                else:
                    logger.warning(
                        f"Refund received but payment not found: {payment_intent_id}"
                    )

        except Exception as e:
            logger.error(f"Error processing charge.refunded: {str(e)}", exc_info=True)
            raise
