# payments/services.py
import stripe
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import Product, Customer, Payment, PaymentLog, Subscription, SubscriptionChange, RetentionOffer

logger = logging.getLogger(__name__)


class SubscriptionChangeService:
    """Service class for handling subscription plan changes"""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY

    def handle_plan_change(self, subscription_id, new_price_id, change_type, user_email, metadata=None):
        """Handle subscription plan changes (upgrades/downgrades)"""
        try:
            with transaction.atomic():
                # Get current subscription from Stripe
                current_subscription = self.stripe.Subscription.retrieve(subscription_id)
                current_price_id = current_subscription['items']['data'][0]['price']['id']
                
                # Get products from database
                old_product = Product.objects.filter(stripe_price_id=current_price_id).first()
                new_product = Product.objects.filter(stripe_price_id=new_price_id).first()
                
                if not new_product:
                    raise ValueError(f"Product not found for price ID: {new_price_id}")
                
                # Create subscription change record
                change_record = SubscriptionChange.objects.create(
                    user_email=user_email,
                    stripe_subscription_id=subscription_id,
                    old_price_id=current_price_id,
                    new_price_id=new_price_id,
                    old_product=old_product,
                    new_product=new_product,
                    change_type=change_type,
                    effective_date=timezone.now(),
                    metadata=metadata
                )
                
                if change_type == 'upgrade':
                    result = self._handle_upgrade(current_subscription, new_price_id, change_record)
                elif change_type == 'downgrade':
                    result = self._handle_downgrade(current_subscription, new_price_id, change_record, user_email)
                else:
                    raise ValueError(f"Invalid change type: {change_type}")
                
                return result
                
        except Exception as e:
            logger.error(f"Plan change error: {str(e)}", exc_info=True)
            raise

    def _handle_upgrade(self, current_subscription, new_price_id, change_record):
        """Handle immediate upgrade with proration"""
        try:
            # Update subscription immediately with proration
            updated_subscription = self.stripe.Subscription.modify(
                current_subscription.id,
                items=[{
                    'id': current_subscription['items']['data'][0].id,
                    'price': new_price_id,
                }],
                proration_behavior='create_prorations',
                billing_cycle_anchor='unchanged'
            )
            
            # Update change record
            change_record.status = 'completed'
            change_record.completed_at = timezone.now()
            change_record.save()
            
            # Log the change
            PaymentLog.objects.create(
                subscription_change=change_record,
                event_type='subscription.upgrade.completed',
                data={
                    'subscription_id': current_subscription.id,
                    'old_price_id': change_record.old_price_id,
                    'new_price_id': new_price_id,
                    'proration_behavior': 'create_prorations'
                }
            )
            
            return {
                'success': True,
                'message': 'Subscription upgraded successfully',
                'subscription': updated_subscription,
                'effective_immediately': True,
                'change_id': change_record.id
            }
            
        except Exception as e:
            change_record.status = 'failed'
            change_record.save()
            raise

    def _handle_downgrade(self, current_subscription, new_price_id, change_record, user_email):
        """Handle end-of-period downgrade using subscription schedules"""
        try:
            # Create subscription schedule for downgrade
            schedule = self.stripe.SubscriptionSchedule.create(
                from_subscription=current_subscription.id,
            )
            
            # Get current phase
            current_phase = schedule.phases[0]
            
            # Update schedule with downgrade phase
            updated_schedule = self.stripe.SubscriptionSchedule.modify(
                schedule.id,
                phases=[
                    {
                        'items': [{
                            'price': current_phase.items[0].price,
                            'quantity': 1
                        }],
                        'start_date': current_phase.start_date,
                        'end_date': current_phase.end_date
                    },
                    {
                        'items': [{
                            'price': new_price_id,
                            'quantity': 1
                        }],
                        'proration_behavior': 'none'
                    }
                ]
            )
            
            # Update change record with schedule ID
            change_record.schedule_id = schedule.id
            change_record.effective_date = datetime.fromtimestamp(
                current_subscription.current_period_end, tz=timezone.utc
            )
            change_record.save()
            
            # Log the change
            PaymentLog.objects.create(
                subscription_change=change_record,
                event_type='subscription.downgrade.scheduled',
                data={
                    'subscription_id': current_subscription.id,
                    'schedule_id': schedule.id,
                    'effective_date': change_record.effective_date.isoformat(),
                    'old_price_id': change_record.old_price_id,
                    'new_price_id': new_price_id
                }
            )
            
            return {
                'success': True,
                'message': 'Downgrade scheduled for next billing period',
                'subscription': current_subscription,
                'effective_immediately': False,
                'effective_date': current_subscription.current_period_end,
                'schedule_id': schedule.id,
                'change_id': change_record.id
            }
            
        except Exception as e:
            change_record.status = 'failed'
            change_record.save()
            raise

    def generate_retention_offers(self, subscription_id, user_email, current_plan_type=None):
        """Generate retention offers for downgrade attempts"""
        try:
            # Get subscription and customer info
            subscription = self.stripe.Subscription.retrieve(subscription_id)
            customer = self.stripe.Customer.retrieve(subscription.customer)
            
            current_price = subscription.items.data[0].price.unit_amount / 100
            
            offers = []
            
            # Offer 1: 25% Discount for 3 months
            offers.append({
                'type': 'discount',
                'title': '25% Off for 3 Months',
                'description': f'Continue with your current plan at ${current_price * 0.75:.2f}/month for 3 months',
                'discount_percent': 25,
                'duration_months': 3,
                'savings': f'${current_price * 0.25 * 3:.2f}',
                'coupon_config': {
                    'percent_off': 25,
                    'duration': 'repeating',
                    'duration_in_months': 3
                }
            })
            
            # Offer 2: Free month
            offers.append({
                'type': 'free_month',
                'title': 'One Month Free',
                'description': 'Get one month free when you stay on your current plan',
                'free_months': 1,
                'savings': f'${current_price:.2f}',
                'coupon_config': {
                    'percent_off': 100,
                    'duration': 'once'
                }
            })
            
            # Offer 3: Feature-based retention (for higher tier plans)
            if current_price >= 14.99:  # Core or Pro plans
                offers.append({
                    'type': 'feature_unlock',
                    'title': 'Exclusive Early Access',
                    'description': 'Keep your plan and get early access to our upcoming premium features',
                    'features': ['AI-powered car recommendations', 'Advanced market analytics', 'Priority customer support'],
                    'duration_months': 6,
                    'value': 'Priceless'
                })
            
            # Store offers in database
            for offer_data in offers:
                RetentionOffer.objects.create(
                    user_email=user_email,
                    stripe_subscription_id=subscription_id,
                    offer_type=offer_data['type'],
                    offer_details=offer_data
                )
            
            return offers
            
        except Exception as e:
            logger.error(f"Error generating retention offers: {str(e)}", exc_info=True)
            raise

    def apply_retention_offer(self, subscription_id, offer_id, user_email):
        """Apply accepted retention offer"""
        try:
            with transaction.atomic():
                # Get offer
                offer = RetentionOffer.objects.get(
                    id=offer_id,
                    user_email=user_email,
                    stripe_subscription_id=subscription_id,
                    accepted=False
                )
                
                if offer.offer_type in ['discount', 'free_month']:
                    # Create and apply coupon
                    coupon_config = offer.offer_details.get('coupon_config', {})
                    
                    # Create coupon in Stripe
                    coupon = self.stripe.Coupon.create(
                        id=f"retention_{offer.id}_{int(timezone.now().timestamp())}",
                        name=offer.offer_details['title'],
                        **coupon_config
                    )
                    
                    # Apply coupon to subscription
                    self.stripe.Subscription.modify(
                        subscription_id,
                        coupon=coupon.id
                    )
                    
                    offer.coupon_id = coupon.id
                
                # Mark offer as accepted
                offer.accepted = True
                offer.accepted_at = timezone.now()
                offer.save()
                
                # Log the retention
                PaymentLog.objects.create(
                    event_type='retention.offer.accepted',
                    data={
                        'subscription_id': subscription_id,
                        'offer_id': offer.id,
                        'offer_type': offer.offer_type,
                        'user_email': user_email,
                        'coupon_id': getattr(offer, 'coupon_id', None)
                    }
                )
                
                return {
                    'success': True,
                    'message': 'Retention offer applied successfully',
                    'offer': offer.offer_details,
                    'coupon_applied': bool(getattr(offer, 'coupon_id', None))
                }
                
        except RetentionOffer.DoesNotExist:
            raise ValueError("Retention offer not found or already accepted")
        except Exception as e:
            logger.error(f"Error applying retention offer: {str(e)}", exc_info=True)
            raise


class StripeService:
    """Service class for Stripe operations"""

    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = settings.STRIPE_SECRET_KEY
        self.subscription_change_service = SubscriptionChangeService()

    # Existing methods... (keeping all existing functionality)
    
    def create_checkout_session(self, **kwargs):
        """Create checkout session for both one-time payments and subscriptions"""
        try:
            product_id = kwargs.get("product_id")
            amount = kwargs.get("amount")
            product_name = kwargs.get("product_name")
            customer_email = kwargs.get("customer_email")
            user_id = kwargs.get("user_id")
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

            # Add search_uid to success_url if provided
            if search_uid:
                separator = "&" if "?" in success_url else "?"
                success_url = f"{success_url}{separator}search_uid={search_uid}"

            # Get or create customer using either email or user_id
            customer = None
            if customer_email:
                customer, created = Customer.objects.get_or_create(
                    email=customer_email,
                    defaults={"user_id": user_id}
                )
            elif user_id:
                customer, created = Customer.objects.get_or_create(
                    user_id=user_id,
                    defaults={"email": f"user_{user_id}@placeholder.com"}
                )

            if payment_type == "subscription":
                return self._create_subscription_checkout_session(
                    product_id, customer, metadata, success_url, cancel_url, trial_period_days, kwargs
                )
            else:
                return self._create_one_time_checkout_session(
                    amount, "aud", product_name, customer, metadata, success_url, cancel_url
                )

        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}", exc_info=True)
            raise

    def manage_subscription(self, subscription_id, action, **kwargs):
        """Enhanced subscription management with plan changes"""
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
            elif action == "change_plan":
                return self.subscription_change_service.handle_plan_change(
                    subscription_id,
                    kwargs.get("new_price_id"),
                    kwargs.get("change_type"),
                    kwargs.get("user_email"),
                    kwargs.get("metadata")
                )
            elif action == "apply_retention":
                return self.subscription_change_service.apply_retention_offer(
                    subscription_id,
                    kwargs.get("offer_id"),
                    kwargs.get("user_email")
                )
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error managing subscription: {str(e)}", exc_info=True)
            raise

    # Keep all existing methods (abbreviated for space)
    def _cancel_subscription(self, subscription_id, cancel_at_period_end=True):
        """Cancel subscription"""
        subscription = self.stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=cancel_at_period_end
        )
        self._update_local_subscription(subscription)
        return subscription

    def _resume_subscription(self, subscription_id):
        """Resume subscription"""
        subscription = self.stripe.Subscription.modify(
            subscription_id, cancel_at_period_end=False
        )
        self._update_local_subscription(subscription)
        return subscription

    def _update_local_subscription(self, stripe_subscription):
        """Update local subscription record"""
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
            local_subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end

            if stripe_subscription.canceled_at:
                local_subscription.canceled_at = datetime.fromtimestamp(
                    stripe_subscription.canceled_at, tz=timezone.utc
                )

            local_subscription.save()
            return local_subscription

        except Subscription.DoesNotExist:
            logger.warning(f"Local subscription not found for Stripe ID: {stripe_subscription.id}")
            return None

    def handle_webhook_event(self, payload, signature):
        """Enhanced webhook handling with subscription changes"""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )

            event_type = event["type"]
            event_data = event["data"]["object"]

            logger.info(f"Processing Stripe webhook: {event_type}")

            # Existing webhook handlers
            if event_type == "checkout.session.completed":
                self._handle_checkout_session_completed(event_data)
            elif event_type == "customer.subscription.updated":
                self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                self._handle_subscription_deleted(event_data)
            elif event_type == "invoice.payment_succeeded":
                self._handle_invoice_payment_succeeded(event_data)
            # NEW: Handle subscription schedule events
            elif event_type == "subscription_schedule.updated":
                self._handle_subscription_schedule_updated(event_data)
            elif event_type == "subscription_schedule.completed":
                self._handle_subscription_schedule_completed(event_data)

            return {"status": "success", "type": event_type}

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            raise

    def _handle_subscription_schedule_updated(self, schedule_data):
        """Handle subscription schedule updates (for downgrades)"""
        try:
            schedule_id = schedule_data.get('id')
            
            # Find associated subscription change
            change = SubscriptionChange.objects.filter(
                schedule_id=schedule_id,
                status='pending'
            ).first()
            
            if change:
                PaymentLog.objects.create(
                    subscription_change=change,
                    event_type='subscription_schedule.updated',
                    data=schedule_data
                )
                
        except Exception as e:
            logger.error(f"Error handling subscription schedule update: {str(e)}", exc_info=True)

    def _handle_subscription_schedule_completed(self, schedule_data):
        """Handle completed subscription schedule (downgrade executed)"""
        try:
            schedule_id = schedule_data.get('id')
            
            # Find and complete subscription change
            change = SubscriptionChange.objects.filter(
                schedule_id=schedule_id,
                status='pending'
            ).first()
            
            if change:
                change.status = 'completed'
                change.completed_at = timezone.now()
                change.save()
                
                PaymentLog.objects.create(
                    subscription_change=change,
                    event_type='subscription_schedule.completed',
                    data=schedule_data
                )
                
        except Exception as e:
            logger.error(f"Error handling subscription schedule completion: {str(e)}", exc_info=True)


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


    def _handle_checkout_session_completed(self, session):
        """Handle checkout session completion for both payment types"""
        try:
            session_id = session.get("id")
            mode = session.get("mode")
            payment_intent_id = session.get("payment_intent")
            subscription_id = session.get("subscription")
            customer_email = session.get("customer_email")
            customer_id = session.get("customer")

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

                    # Update customer with Stripe customer ID if needed
                    if payment.customer and customer_id and not payment.customer.stripe_customer_id:
                        payment.customer.stripe_customer_id = customer_id
                        payment.customer.save()

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
                    self._update_local_subscription(subscription_data)
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
                subscription = Subscription.objects.filter(
                    stripe_subscription_id=subscription_id
                ).first()

                PaymentLog.objects.create(
                    subscription=subscription,
                    event_type="invoice.payment_succeeded",
                    data=invoice_data,
                )

        except Exception as e:
            logger.error(
                f"Error processing invoice payment success: {str(e)}", exc_info=True
            )
            raise
