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

from .models import Product, Payment, Subscription, Customer  # Added missing Customer import
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
        
class UserSubscriptionStatusView(APIView):
    """Get current user's subscription status"""

    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            user_email = request.query_params.get('user_email')
            
            if not user_id and not user_email:
                return Response({
                    'error': 'Either user_id or user_email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find customer record
            customer = None
            if user_id:
                customer = Customer.objects.filter(user_id=user_id).first()
            elif user_email:
                customer = Customer.objects.filter(email=user_email).first()
            
            if not customer:
                return Response({
                    'has_subscription': False,
                    'subscription': None,
                    'customer': None,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan'
                })
            
            # Get active subscriptions
            active_subscriptions = Subscription.objects.filter(
                customer=customer,
                status__in=['active', 'trialing', 'past_due']
            ).order_by('-created_at')
            
            subscription_data = []
            for subscription in active_subscriptions:
                # Sync with Stripe to get latest status
                try:
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    stripe_subscription = stripe.Subscription.retrieve(
                        subscription.stripe_subscription_id
                    )
                    
                    # Update local record
                    stripe_service._update_local_subscription(stripe_subscription)
                    subscription.refresh_from_db()
                    
                    # Include product details
                    subscription_info = {
                        'id': subscription.id,
                        'stripe_subscription_id': subscription.stripe_subscription_id,
                        'status': subscription.status,
                        'current_period_start': subscription.current_period_start,
                        'current_period_end': subscription.current_period_end,
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'canceled_at': subscription.canceled_at,
                        'trial_start': subscription.trial_start,
                        'trial_end': subscription.trial_end,
                        'product': ProductSerializer(subscription.product).data if subscription.product else None,
                        'stripe_data': {
                            'current_period_start': stripe_subscription.current_period_start,
                            'current_period_end': stripe_subscription.current_period_end,
                            'items': [
                                {
                                    'price_id': item.price.id,
                                    'product_id': item.price.product,
                                    'quantity': item.quantity,
                                    'amount': item.price.unit_amount,
                                    'currency': item.price.currency,
                                    'interval': item.price.recurring.interval if item.price.recurring else None,
                                } for item in stripe_subscription.items.data
                            ]
                        }
                    }
                    subscription_data.append(subscription_info)
                    
                except stripe.error.InvalidRequestError:
                    # Subscription not found in Stripe, mark as canceled
                    subscription.status = 'canceled'
                    subscription.save()
                except Exception as e:
                    logger.warning(f"Error syncing subscription {subscription.stripe_subscription_id}: {str(e)}")
                    # Still include local data even if Stripe sync fails
                    subscription_info = {
                        'id': subscription.id,
                        'stripe_subscription_id': subscription.stripe_subscription_id,
                        'status': subscription.status,
                        'current_period_start': subscription.current_period_start,
                        'current_period_end': subscription.current_period_end,
                        'cancel_at_period_end': subscription.cancel_at_period_end,
                        'product': ProductSerializer(subscription.product).data if subscription.product else None,
                        'sync_error': True
                    }
                    subscription_data.append(subscription_info)
            
            # Filter only truly active subscriptions
            active_subscriptions_data = [
                sub for sub in subscription_data 
                if sub['status'] in ['active', 'trialing', 'past_due']
            ]
            
            # Determine plan type and name
            plan_type = 'free'
            plan_name = 'Free Plan'
            
            if active_subscriptions_data:
                # Get the highest tier subscription
                highest_subscription = max(active_subscriptions_data, 
                    key=lambda x: float(x['product']['price']) if x['product'] else 0
                )
                
                if highest_subscription['product']:
                    plan_name = highest_subscription['product']['name']
                    # Determine plan type based on product metadata or name
                    product_metadata = highest_subscription['product'].get('metadata', {})
                    if 'tier' in product_metadata:
                        plan_type = product_metadata['tier']
                    else:
                        # Fallback to determine by price or name
                        price = float(highest_subscription['product']['price'])
                        if price >= 25:
                            plan_type = 'pro'
                        elif price >= 10:
                            plan_type = 'core'
                        else:
                            plan_type = 'smart'
            
            return Response({
                'has_subscription': len(active_subscriptions_data) > 0,
                'subscriptions': active_subscriptions_data,
                'plan_type': plan_type,
                'plan_name': plan_name,
                'customer': {
                    'id': customer.id,
                    'user_id': customer.user_id,
                    'email': customer.email,
                    'stripe_customer_id': customer.stripe_customer_id
                }
            })
            
        except Exception as e:
            logger.error(f"Error checking user subscription status: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserSubscriptionPlansView(APIView):
    """Get subscription plans available for upgrade/downgrade"""
    
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            user_email = request.query_params.get('user_email')
            
            # Get current subscription status
            current_subscription = None
            if user_id or user_email:
                customer = None
                if user_id:
                    customer = Customer.objects.filter(user_id=user_id).first()
                elif user_email:
                    customer = Customer.objects.filter(email=user_email).first()
                
                if customer:
                    current_subscription = Subscription.objects.filter(
                        customer=customer,
                        status__in=['active', 'trialing', 'past_due']
                    ).first()
            
            # Get all available subscription products
            subscription_products = Product.objects.filter(
                product_type='subscription',
                active=True
            ).order_by('price')
            
            plans = []
            for product in subscription_products:
                plan_info = ProductSerializer(product).data
                
                # Add recommendation status
                if current_subscription and current_subscription.product:
                    current_price = float(current_subscription.product.price)
                    product_price = float(product.price)
                    
                    if product.id == current_subscription.product.id:
                        plan_info['is_current'] = True
                        plan_info['recommendation'] = 'current'
                    elif product_price > current_price:
                        plan_info['is_current'] = False
                        plan_info['recommendation'] = 'upgrade'
                    elif product_price < current_price:
                        plan_info['is_current'] = False
                        plan_info['recommendation'] = 'downgrade'
                    else:
                        plan_info['is_current'] = False
                        plan_info['recommendation'] = 'alternative'
                else:
                    plan_info['is_current'] = False
                    plan_info['recommendation'] = 'available'
                
                plans.append(plan_info)
            
            return Response({
                'plans': plans,
                'current_subscription': SubscriptionSerializer(current_subscription).data if current_subscription else None
            })
            
        except Exception as e:
            logger.error(f"Error getting subscription plans: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentSuccessCallbackView(APIView):
    """Handle post-payment success callback and sync subscription status"""
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            user_id = request.data.get('user_id')
            user_email = request.data.get('user_email')
            search_uid = request.data.get('search_uid')
            
            if not session_id:
                return Response({
                    'error': 'session_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get payment from database
            payment = Payment.objects.filter(session_id=session_id).first()
            if not payment:
                return Response({
                    'error': 'Payment not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get latest session status from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_session = stripe.checkout.Session.retrieve(session_id)
            
            # Update customer info if provided
            if payment.customer and (user_id or user_email):
                if user_id and not payment.customer.user_id:
                    payment.customer.user_id = user_id
                if user_email and payment.customer.email != user_email:
                    payment.customer.email = user_email
                payment.customer.save()
            
            # Handle search integration if search_uid provided
            search_result = None
            if search_uid:
                search_result = self._handle_search_to_garage_migration(
                    search_uid, payment.customer, payment
                )
            
            # Get updated subscription status
            subscription_status = self._get_user_subscription_status(
                payment.customer.user_id if payment.customer else user_id,
                payment.customer.email if payment.customer else user_email
            )
            
            response_data = {
                'status': 'success',
                'payment': {
                    'uuid': str(payment.uuid),
                    'session_id': session_id,
                    'payment_status': stripe_session.payment_status,
                    'mode': stripe_session.mode,
                    'amount_total': stripe_session.amount_total,
                    'currency': stripe_session.currency,
                },
                'subscription_status': subscription_status,
            }
            
            if search_result:
                response_data['search_migration'] = search_result
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in payment success callback: {str(e)}", exc_info=True)
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_search_to_garage_migration(self, search_uid, customer, payment):
        """Migrate search result to user's garage"""
        try:
            # Import here to avoid circular imports
            from api.models import CarSearchLog
            
            # Find the search log
            search_log = CarSearchLog.objects.filter(uid=search_uid).first()
            if not search_log:
                return {'status': 'search_not_found'}
            
            # Update search log with customer info
            if customer:
                search_log.customer_id = customer.id
                search_log.payment_id = str(payment.uuid)
                search_log.save()
            
            return {
                'status': 'migrated',
                'search_id': search_uid,
                'vehicle_id': search_log.vehicle_id,
                'customer_id': customer.id if customer else None
            }
            
        except Exception as e:
            logger.warning(f"Error migrating search to garage: {str(e)}")
            return {'status': 'migration_failed', 'error': str(e)}
    
    def _get_user_subscription_status(self, user_id, user_email):
        """Get current subscription status for user"""
        try:
            # Find customer
            customer = None
            if user_id:
                customer = Customer.objects.filter(user_id=user_id).first()
            elif user_email:
                customer = Customer.objects.filter(email=user_email).first()
            
            if not customer:
                return {
                    'has_subscription': False,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan'
                }
            
            # Get active subscriptions
            active_subscriptions = Subscription.objects.filter(
                customer=customer,
                status__in=['active', 'trialing', 'past_due']
            ).order_by('-created_at')
            
            if not active_subscriptions.exists():
                return {
                    'has_subscription': False,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan'
                }
            
            # Get the highest tier subscription
            highest_subscription = max(active_subscriptions, 
                key=lambda x: float(x.product.price) if x.product else 0
            )
            
            plan_type = 'free'
            plan_name = 'Free Plan'
            
            if highest_subscription.product:
                plan_name = highest_subscription.product.name
                # Determine plan type based on price or metadata
                price = float(highest_subscription.product.price)
                if price >= 25:
                    plan_type = 'pro'
                elif price >= 10:
                    plan_type = 'core'
                else:
                    plan_type = 'smart'
            
            return {
                'has_subscription': True,
                'plan_type': plan_type,
                'plan_name': plan_name,
                'subscription_id': highest_subscription.stripe_subscription_id,
                'current_period_end': highest_subscription.current_period_end.isoformat() if highest_subscription.current_period_end else None
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            return {
                'has_subscription': False,
                'plan_type': 'free',
                'plan_name': 'Free Plan'
            }


class RefreshSubscriptionStatusView(APIView):
    """Force refresh subscription status from Stripe"""
    
    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            user_email = request.data.get('user_email')
            
            if not user_id and not user_email:
                return Response({
                    'error': 'Either user_id or user_email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find customer
            customer = None
            if user_id:
                customer = Customer.objects.filter(user_id=user_id).first()
            elif user_email:
                customer = Customer.objects.filter(email=user_email).first()
            
            if not customer:
                return Response({
                    'has_subscription': False,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan',
                    'message': 'Customer not found'
                })
            
            # Get all subscriptions for this customer
            subscriptions = Subscription.objects.filter(customer=customer)
            
            updated_count = 0
            for subscription in subscriptions:
                try:
                    # Get latest data from Stripe
                    stripe.api_key = settings.STRIPE_SECRET_KEY
                    stripe_subscription = stripe.Subscription.retrieve(
                        subscription.stripe_subscription_id
                    )
                    
                    # Update local record
                    stripe_service._update_local_subscription(stripe_subscription)
                    updated_count += 1
                    
                except stripe.error.InvalidRequestError:
                    # Subscription not found in Stripe, mark as canceled
                    subscription.status = 'canceled'
                    subscription.save()
                except Exception as e:
                    logger.warning(f"Error syncing subscription {subscription.stripe_subscription_id}: {str(e)}")
            
            # Get updated status
            subscription_status = self._get_updated_subscription_status(customer)
            
            return Response({
                **subscription_status,
                'sync_info': {
                    'subscriptions_updated': updated_count,
                    'total_subscriptions': subscriptions.count()
                }
            })
            
        except Exception as e:
            logger.error(f"Error refreshing subscription status: {str(e)}", exc_info=True)
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_updated_subscription_status(self, customer):
        """Get updated subscription status after sync"""
        active_subscriptions = Subscription.objects.filter(
            customer=customer,
            status__in=['active', 'trialing', 'past_due']
        ).order_by('-created_at')
        
        if not active_subscriptions.exists():
            return {
                'has_subscription': False,
                'plan_type': 'free',
                'plan_name': 'Free Plan'
            }
        
        # Get the highest tier subscription
        highest_subscription = max(active_subscriptions, 
            key=lambda x: float(x.product.price) if x.product else 0
        )
        
        plan_type = 'free'
        plan_name = 'Free Plan'
        
        if highest_subscription.product:
            plan_name = highest_subscription.product.name
            price = float(highest_subscription.product.price)
            if price >= 25:
                plan_type = 'pro'
            elif price >= 10:
                plan_type = 'core'
            else:
                plan_type = 'smart'
        
        return {
            'has_subscription': True,
            'plan_type': plan_type,
            'plan_name': plan_name,
            'subscription_id': highest_subscription.stripe_subscription_id,
            'current_period_end': highest_subscription.current_period_end.isoformat() if highest_subscription.current_period_end else None,
            'subscriptions': [
                {
                    'id': sub.id,
                    'stripe_subscription_id': sub.stripe_subscription_id,
                    'status': sub.status,
                    'product_name': sub.product.name if sub.product else None,
                    'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None
                } for sub in active_subscriptions
            ]
        }

class StripeConfigView(APIView):
    """Expose Stripe publishable key to the frontend"""

    def get(self, request):
        return Response({
            'publishableKey': settings.STRIPE_PUBLISHABLE_KEY
        })

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