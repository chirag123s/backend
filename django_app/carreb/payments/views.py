from datetime import datetime, timezone
import stripe
import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone as django_timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Product, Payment, Subscription, Customer, SubscriptionChange, RetentionOffer
from .serializers import (
    ProductSerializer, PaymentSerializer, SubscriptionSerializer,
    CheckoutSessionCreateSerializer, SubscriptionManagementSerializer,
    PlanChangeRequestSerializer, RetentionOfferRequestSerializer, 
    RetentionOfferAcceptSerializer, SubscriptionChangeSerializer,
    RetentionOfferSerializer
)
from .services import StripeService

logger = logging.getLogger(__name__)
stripe_service = StripeService()

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

class SubscriptionManagementView(APIView):
    """Enhanced subscription management with plan changes"""

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
                'result': result
            })
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error managing subscription: {str(e)}", exc_info=True)
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
    """
    OPTIMIZED: Refresh subscription from Stripe (email-based)
    """
    
    def post(self, request):
        try:
            customer_email = request.data.get('user_email') or request.data.get('customer_email')
            
            # Find customer by EMAIL FIRST
            customer = None
            if customer_email:
                customer = Customer.objects.filter(email=customer_email).first()
            
            if not customer:
                return Response({
                    'has_subscription': False,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan',
                    'message': 'Customer not found'
                })
            
            # Force refresh from Stripe
            subscription_data = self._force_refresh_from_stripe(customer)
            
            return Response({
                **subscription_data,
                'message': 'Subscription status refreshed from Stripe'
            })
            
        except Exception as e:
            logger.error(f"Error refreshing subscription: {str(e)}", exc_info=True)
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _force_refresh_from_stripe(self, customer):
        """Force refresh all subscriptions from Stripe"""
        if not customer.stripe_customer_id:
            return {
                'has_subscription': False,
                'plan_type': 'free',
                'plan_name': 'Free Plan',
                'subscriptions': []
            }
        
        try:
            # Get all subscriptions for this customer from Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_subscriptions = stripe.Subscription.list(
                customer=customer.stripe_customer_id,
                status='all'
            )
            
            updated_count = 0
            active_subscriptions = []
            
            for stripe_sub in stripe_subscriptions.data:
                # Update or create local subscription
                local_sub = stripe_service._update_local_subscription(stripe_sub)
                updated_count += 1
                
                if local_sub.status in ['active', 'trialing', 'past_due']:
                    active_subscriptions.append(local_sub)
            
            # Return status similar to the main endpoint
            has_active = len(active_subscriptions) > 0
            current_subscription = active_subscriptions[0] if active_subscriptions else None
            
            plan_type = 'free'
            plan_name = 'Free Plan'
            
            if current_subscription and current_subscription.product:
                product_price = float(current_subscription.product.price)
                if product_price >= 14.99:
                    plan_type = 'pro'
                    plan_name = 'Pro Plan'
                elif product_price >= 6.99:
                    plan_type = 'smart'
                    plan_name = 'Smart Plan'
            
            return {
                'has_subscription': has_active,
                'plan_type': plan_type,
                'plan_name': plan_name,
                'subscriptions': [SubscriptionSerializer(sub).data for sub in active_subscriptions],
                'current_subscription': SubscriptionSerializer(current_subscription).data if current_subscription else None,
                'sync_info': {
                    'subscriptions_updated': updated_count,
                    'stripe_subscriptions_found': len(stripe_subscriptions.data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching from Stripe: {str(e)}", exc_info=True)
            return {
                'has_subscription': False,
                'plan_type': 'free',
                'plan_name': 'Free Plan',
                'subscriptions': [],
                'error': 'Failed to sync with Stripe'
            }

class EmailBasedStripeSync(APIView):
    """
    NEW: Sync specific customer by email with Stripe data
    Useful for migrating from user_id to email-based system
    """
    
    def post(self, request):
        try:
            customer_email = request.data.get('email')
            
            if not customer_email:
                return Response({
                    'error': 'email is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Find or create customer
            customer, created = Customer.objects.get_or_create(
                email=customer_email,
                defaults={'updated_at': timezone.now()}
            )
            
            # Search Stripe for customers with this email
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_customers = stripe.Customer.search(
                query=f"email:'{customer_email}'"
            )
            
            if not stripe_customers.data:
                return Response({
                    'message': 'No Stripe customer found with this email',
                    'customer_created': created
                })
            
            # Use the first matching Stripe customer
            stripe_customer = stripe_customers.data[0]
            
            # Update local customer record
            if not customer.stripe_customer_id:
                customer.stripe_customer_id = stripe_customer.id
                customer.save()
            
            # Sync all subscriptions for this customer
            stripe_subscriptions = stripe.Subscription.list(
                customer=stripe_customer.id,
                status='all'
            )
            
            synced_subscriptions = []
            for stripe_sub in stripe_subscriptions.data:
                local_sub = stripe_service._update_local_subscription(stripe_sub)
                synced_subscriptions.append(local_sub)
            
            return Response({
                'message': 'Customer synced successfully',
                'customer': {
                    'id': customer.id,
                    'email': customer.email,
                    'stripe_customer_id': customer.stripe_customer_id,
                    'created': created
                },
                'subscriptions_synced': len(synced_subscriptions),
                'active_subscriptions': len([s for s in synced_subscriptions if s.status in ['active', 'trialing', 'past_due']])
            })
            
        except Exception as e:
            logger.error(f"Error syncing customer by email: {str(e)}", exc_info=True)
            return Response({
                'error': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubscriptionChangeView(APIView):
    """Handle subscription plan changes (upgrades/downgrades)"""
    
    def post(self, request):
        serializer = PlanChangeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = stripe_service.subscription_change_service.handle_plan_change(
                subscription_id=serializer.validated_data['subscription_id'],
                new_price_id=serializer.validated_data['new_price_id'],
                change_type=serializer.validated_data['change_type'],
                user_email=serializer.validated_data['user_email'],
                metadata=serializer.validated_data.get('metadata')
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"Plan change validation error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Plan change error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to change subscription plan'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RetentionOfferView(APIView):
    """Handle retention offers for downgrade attempts"""
    
    def post(self, request):
        serializer = RetentionOfferRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            offers = stripe_service.subscription_change_service.generate_retention_offers(
                subscription_id=serializer.validated_data['subscription_id'],
                user_email=serializer.validated_data['user_email'],
                current_plan_type=serializer.validated_data.get('current_plan_type')
            )
            
            return Response({
                'offers': offers,
                'subscription_id': serializer.validated_data['subscription_id'],
                'message': 'Retention offers generated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Retention offer error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to generate retention offers'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RetentionOfferAcceptView(APIView):
    """Accept a retention offer"""
    
    def post(self, request):
        serializer = RetentionOfferAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = stripe_service.subscription_change_service.apply_retention_offer(
                subscription_id=serializer.validated_data['subscription_id'],
                offer_id=serializer.validated_data['offer_id'],
                user_email=serializer.validated_data['user_email']
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.warning(f"Retention offer acceptance error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Retention offer acceptance error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to apply retention offer'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubscriptionChangesHistoryView(APIView):
    """Get subscription change history for a user"""
    
    def get(self, request):
        user_email = request.query_params.get('user_email')
        subscription_id = request.query_params.get('subscription_id')
        
        if not user_email:
            return Response({
                'error': 'user_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            queryset = SubscriptionChange.objects.filter(user_email=user_email)
            
            if subscription_id:
                queryset = queryset.filter(stripe_subscription_id=subscription_id)
            
            changes = queryset.order_by('-created_at')
            serializer = SubscriptionChangeSerializer(changes, many=True)
            
            return Response({
                'changes': serializer.data,
                'count': changes.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching subscription changes: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to fetch subscription changes'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserRetentionOffersView(APIView):
    """Get retention offers for a user"""
    
    def get(self, request):
        user_email = request.query_params.get('user_email')
        subscription_id = request.query_params.get('subscription_id')
        
        if not user_email:
            return Response({
                'error': 'user_email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            queryset = RetentionOffer.objects.filter(user_email=user_email)
            
            if subscription_id:
                queryset = queryset.filter(stripe_subscription_id=subscription_id)
            
            offers = queryset.order_by('-created_at')
            serializer = RetentionOfferSerializer(offers, many=True)
            
            return Response({
                'offers': serializer.data,
                'count': offers.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error fetching retention offers: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to fetch retention offers'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class DirectStripeSubscriptionView(APIView):
    """Enhanced subscription view with pending changes and offers"""
    
    def get(self, request):
        user_email = request.query_params.get('user_email')
        
        if not user_email:
            return Response({
                'error': 'user_email parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self._get_enhanced_subscription_status(user_email)
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error fetching subscription status: {str(e)}", exc_info=True)
            return Response({
                'error': 'Failed to fetch subscription status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_enhanced_subscription_status(self, user_email):
        """Get subscription status with pending changes and offers"""
        try:
            # Get customer and subscriptions (existing logic)
            customer = Customer.objects.filter(email=user_email).first()
            
            if not customer or not customer.stripe_customer_id:
                return {
                    'has_subscription': False,
                    'plan_type': 'free',
                    'plan_name': 'Free Plan',
                    'subscriptions': [],
                    'current_subscription': None,
                    'pending_changes': [],
                    'recent_offers': []
                }
            
            # Sync with Stripe and get subscriptions
            stripe.api_key = settings.STRIPE_SECRET_KEY
            stripe_subscriptions = stripe.Subscription.list(
                customer=customer.stripe_customer_id,
                status='all'
            )
            
            # Update local subscriptions
            updated_count = 0
            active_subscriptions = []
            
            for stripe_sub in stripe_subscriptions.data:
                local_sub = stripe_service._update_local_subscription(stripe_sub)
                if local_sub:
                    updated_count += 1
                if stripe_sub.status in ['active', 'trialing', 'past_due']:
                    active_subscriptions.append(local_sub)
            
            # Get basic subscription info
            has_active = len(active_subscriptions) > 0
            current_subscription = active_subscriptions[0] if active_subscriptions else None
            
            plan_type = 'free'
            plan_name = 'Free Plan'
            
            if current_subscription and current_subscription.product:
                product_price = float(current_subscription.product.price)
                if product_price >= 29.99:
                    plan_type = 'pro'
                    plan_name = 'Full Insight Pro'
                elif product_price >= 14.99:
                    plan_type = 'core'
                    plan_name = 'CORE Advantage'
                elif product_price >= 6.99:
                    plan_type = 'smart'
                    plan_name = 'Smart Choice'
            
            # Get pending changes
            pending_changes = []
            if current_subscription:
                changes = SubscriptionChange.objects.filter(
                    stripe_subscription_id=current_subscription.stripe_subscription_id,
                    status='pending'
                ).order_by('-created_at')
                pending_changes = SubscriptionChangeSerializer(changes, many=True).data
            
            # Get recent retention offers
            recent_offers = []
            offers = RetentionOffer.objects.filter(
                user_email=user_email,
                created_at__gte=django_timezone.now() - django_timezone.timedelta(days=30)
            ).order_by('-created_at')[:5]
            recent_offers = RetentionOfferSerializer(offers, many=True).data
            
            return {
                'has_subscription': has_active,
                'plan_type': plan_type,
                'plan_name': plan_name,
                'subscriptions': [SubscriptionSerializer(sub).data for sub in active_subscriptions],
                'current_subscription': SubscriptionSerializer(current_subscription).data if current_subscription else None,
                'pending_changes': pending_changes,
                'recent_offers': recent_offers,
                'sync_info': {
                    'subscriptions_updated': updated_count,
                    'stripe_subscriptions_found': len(stripe_subscriptions.data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching enhanced subscription status: {str(e)}", exc_info=True)
            return {
                'has_subscription': False,
                'plan_type': 'free',
                'plan_name': 'Free Plan',
                'subscriptions': [],
                'current_subscription': None,
                'pending_changes': [],
                'recent_offers': [],
                'error': 'Failed to sync with Stripe'
            }

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

# Enhanced webhook handler
@csrf_exempt
def stripe_webhook(request):
    """Enhanced webhook handler with subscription change events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        result = stripe_service.handle_webhook_event(payload, sig_header)
        return HttpResponse(status=200)
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {str(e)}", exc_info=True)
        return HttpResponse(status=500)