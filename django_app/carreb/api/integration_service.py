"""
Integration Service for CarReb
Handles the flow of search -> payment -> subscription -> garage
"""

import logging
from django.db import transaction
from django.utils import timezone
from .models import CarSearchLog, MyGarage, UserSubscription
from payments.models import Payment

logger = logging.getLogger(__name__)


class CarRebIntegrationService:
    """Service to handle integration between search, payments, and garage"""
    
    @staticmethod
    def process_successful_payment(payment_uuid, user_id, user_email):
        """
        Process a successful payment and move search to garage if applicable
        
        Args:
            payment_uuid: UUID of the successful payment
            user_id: Auth0 user ID
            user_email: User's email address
            
        Returns:
            dict: Result of the operation
        """
        try:
            with transaction.atomic():
                # Get payment details
                payment = Payment.objects.get(uuid=payment_uuid)
                metadata = payment.metadata or {}
                search_uid = metadata.get('search_uid')
                plan_name = metadata.get('plan', 'Unknown Plan')
                
                # Create subscription record
                subscription = UserSubscription.objects.create(
                    user_id=user_id,
                    user_email=user_email,
                    payment_uuid=str(payment_uuid),
                    search_uid=search_uid,
                    plan_name=plan_name
                )
                
                garage_entry = None
                
                # If there's a search_uid, move the search to garage
                if search_uid:
                    try:
                        search_log = CarSearchLog.objects.get(uid=search_uid)
                        
                        garage_entry = MyGarage.objects.create(
                            user_id=user_id,
                            user_email=user_email,
                            save_money=search_log.save_money,
                            greener_car=search_log.greener_car,
                            good_all_rounder=search_log.good_all_rounder,
                            budget=search_log.budget,
                            state=search_log.state,
                            have_car=search_log.have_car,
                            make=search_log.make,
                            model=search_log.model,
                            year=search_log.year,
                            engine_type=search_log.engine_type,
                            vehicle_id=search_log.vehicle_id,
                            original_search_uid=search_uid,
                            is_current_car=search_log.have_car,  # If they have a car, mark it as current
                            nickname=f"{search_log.make} {search_log.model}" if search_log.make else "My Car",
                            ip_address=search_log.ip_address,
                            user_agent=search_log.user_agent
                        )
                        
                        logger.info(f"Moved search {search_uid} to garage for user {user_id}")
                        
                    except CarSearchLog.DoesNotExist:
                        logger.warning(f"Search log not found for uid: {search_uid}")
                
                return {
                    'status': 'success',
                    'subscription_id': subscription.id,
                    'garage_entry_id': garage_entry.id if garage_entry else None,
                    'search_moved': bool(garage_entry),
                    'message': 'Payment processed and user setup completed successfully'
                }
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {payment_uuid}")
            return {
                'status': 'error',
                'message': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Error processing successful payment: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error processing payment: {str(e)}'
            }
    
    @staticmethod
    def get_user_dashboard_data(user_id):
        """
        Get comprehensive dashboard data for a user
        
        Args:
            user_id: Auth0 user ID
            
        Returns:
            dict: Dashboard data including garage, subscriptions, etc.
        """
        try:
            # Get user's garage
            garage_entries = MyGarage.objects.filter(user_id=user_id).order_by('-created_at')
            
            # Get user's subscriptions
            subscriptions = UserSubscription.objects.filter(user_id=user_id).order_by('-created_at')
            
            # Get current car (if any)
            current_car = garage_entries.filter(is_current_car=True).first()
            
            # Get search history linked to garage entries
            search_uids = [entry.original_search_uid for entry in garage_entries if entry.original_search_uid]
            search_history = CarSearchLog.objects.filter(uid__in=search_uids).order_by('-created_at')
            
            return {
                'status': 'success',
                'garage_count': garage_entries.count(),
                'garage_entries': [
                    {
                        'id': entry.id,
                        'nickname': entry.nickname,
                        'make': entry.make,
                        'model': entry.model,
                        'year': entry.year,
                        'is_current_car': entry.is_current_car,
                        'created_at': entry.created_at
                    } for entry in garage_entries
                ],
                'current_car': {
                    'id': current_car.id,
                    'nickname': current_car.nickname,
                    'make': current_car.make,
                    'model': current_car.model,
                    'year': current_car.year
                } if current_car else None,
                'active_subscription': {
                    'plan_name': subscriptions.first().plan_name,
                    'created_at': subscriptions.first().created_at
                } if subscriptions.exists() else None,
                'search_history_count': search_history.count()
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error retrieving dashboard data: {str(e)}'
            }
    
    @staticmethod
    def create_shareable_link(search_uid):
        """
        Create a shareable link for a search result
        
        Args:
            search_uid: UID of the search
            
        Returns:
            dict: Shareable link data
        """
        try:
            search_log = CarSearchLog.objects.get(uid=search_uid)
            
            # Basic shareable data (no sensitive information)
            shareable_data = {
                'search_uid': search_uid,
                'budget': float(search_log.budget) if search_log.budget else None,
                'state': search_log.state,
                'preferences': {
                    'save_money': search_log.save_money,
                    'greener_car': search_log.greener_car,
                    'good_all_rounder': search_log.good_all_rounder
                },
                'created_at': search_log.created_at.isoformat()
            }
            
            if search_log.have_car and search_log.make:
                shareable_data['current_car'] = {
                    'make': search_log.make,
                    'model': search_log.model,
                    'year': search_log.year
                }
            
            return {
                'status': 'success',
                'shareable_url': f"/smart-car-finder?sid={search_uid}",
                'data': shareable_data
            }
            
        except CarSearchLog.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Search not found'
            }
        except Exception as e:
            logger.error(f"Error creating shareable link: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error creating shareable link: {str(e)}'
            }