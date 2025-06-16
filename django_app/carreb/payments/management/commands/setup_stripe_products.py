# payments/management/commands/setup_stripe_products.py
import stripe
import os
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from payments.models import Product

class Command(BaseCommand):
    help = 'Set up Stripe products and prices for CarReb subscription plans'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-products',
            action='store_true',
            help='Create CarReb subscription products',
        )
        parser.add_argument(
            '--sync-existing',
            action='store_true',
            help='Sync existing local products with Stripe',
        )
        parser.add_argument(
            '--list-products',
            action='store_true',
            help='List existing Stripe products',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing products with new data',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompts (use with caution in production)',
        )
        parser.add_argument(
            '--environment',
            type=str,
            choices=['development', 'staging', 'production'],
            help='Specify environment to ensure correct Stripe keys are used',
        )

    def handle(self, *args, **options):
        # Validate environment and Stripe configuration
        if not self.validate_environment(options.get('environment')):
            return
        
        # Initialize Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Validate Stripe connection
        if not self.validate_stripe_connection():
            return
        
        if options['list_products']:
            self.list_stripe_products()
            return
        
        if options['create_products']:
            self.create_carreb_products(options.get('force', False))
        
        if options['sync_existing']:
            self.sync_existing_products(options.get('force', False))
        
        if options['update_existing']:
            self.update_existing_products(options.get('force', False))
        
        self.stdout.write(
            self.style.SUCCESS('Stripe product setup completed successfully!')
        )

    def validate_environment(self, specified_env):
        """Validate environment and Stripe configuration"""
        if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY:
            self.stdout.write(
                self.style.ERROR('STRIPE_SECRET_KEY not found in settings. Please configure Stripe keys.')
            )
            return False
        
        # Check if we're in production based on Stripe key
        is_production = not settings.STRIPE_SECRET_KEY.startswith('sk_test_')
        
        if is_production:
            self.stdout.write(
                self.style.WARNING('🚨 PRODUCTION ENVIRONMENT DETECTED 🚨')
            )
            self.stdout.write(
                self.style.WARNING('You are about to modify LIVE Stripe products!')
            )
            
            if specified_env != 'production':
                self.stdout.write(
                    self.style.ERROR(
                        'Production Stripe key detected but environment not specified as "production".\n'
                        'Please add --environment=production to confirm you want to modify live products.'
                    )
                )
                return False
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Test environment detected - safe to proceed')
            )
        
        return True
    
    def validate_stripe_connection(self):

        try:
            # Test the connection by fetching account info
            account = stripe.Account.retrieve()
            
            # Safely get account name
            account_name = None
            if hasattr(account, 'business_profile') and account.business_profile:
                if hasattr(account.business_profile, 'name'):
                    account_name = account.business_profile.name
            
            # Fallback to account ID if no business name
            display_name = account_name or account.id
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Connected to Stripe account: {display_name}')
            )
            
            # Show additional account info for debugging
            self.stdout.write(f'   Account ID: {account.id}')
            self.stdout.write(f'   Country: {getattr(account, "country", "Unknown")}')
            self.stdout.write(f'   Type: {getattr(account, "type", "Unknown")}')
            
            return True
            
        except stripe.error.AuthenticationError:
            self.stdout.write(
                self.style.ERROR('❌ Stripe authentication failed. Please check your API keys.')
            )
            return False
        except stripe.error.PermissionError:
            self.stdout.write(
                self.style.ERROR('❌ Stripe permission error. Your API key might not have sufficient permissions.')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to connect to Stripe: {str(e)}')
            )
            # Show more details for debugging
            self.stdout.write(f'   Error type: {type(e).__name__}')
            return False

    def confirm_action(self, message, force=False):
        """Get user confirmation for actions"""
        if force:
            return True
        
        response = input(f"{message} (y/N): ").lower().strip()
        return response == 'y' or response == 'yes'

    def create_carreb_products(self, force=False):
        """Create CarReb subscription products (monthly only)"""
        
        # CarReb subscription products - Monthly only
        carreb_products = [
            {
                'name': 'CarReb Smart Choice',
                'description': 'Compare up to 3 CORE ratings and access smarter search tools. Perfect for budget-conscious car buyers ready to make informed decisions.',
                'price': Decimal('6.99'),
                'currency': 'aud',
                'product_type': 'subscription',
                'billing_interval': 'month',
                'billing_interval_count': 1,
                'features': [
                    'Up to 3 vehicle comparisons',
                    'CORE Pure Cost & COOL views',
                    'Financing options',
                    '2 current vehicle entries',
                    'Full CORE rating with rationale',
                    'Limited Smart Car Finder access',
                    'Save shortlist for later'
                ],
                'metadata': {
                    'plan_slug': 'smart-choice',
                    'garage_vehicles': '3',
                    'current_vehicle_entries': '2',
                    'tier': 'smart'
                }
            },
            {
                'name': 'CarReb CORE Advantage',
                'description': 'Unlock all car views including resale impact analysis. Get up to 10 vehicle comparisons with comprehensive insights for long-term savings.',
                'price': Decimal('14.99'),
                'currency': 'aud',
                'product_type': 'subscription',
                'billing_interval': 'month',
                'billing_interval_count': 1,
                'features': [
                    'Up to 10 vehicle comparisons',
                    'All CORE views including resale impact',
                    'Full financing options',
                    '5 current vehicle entries',
                    'Complete CORE rating system',
                    'Full Smart Car Finder + AI Smart Match',
                    'Advanced shortlist management',
                    'Resale value impact analysis'
                ],
                'metadata': {
                    'plan_slug': 'core-advantage',
                    'garage_vehicles': '10',
                    'current_vehicle_entries': '5',
                    'tier': 'core'
                }
            },
            {
                'name': 'CarReb Full Insight Pro',
                'description': 'Complete access to every tool, view, and vehicle comparison. Ideal for automotive professionals, fleet managers, and households with multiple car decisions.',
                'price': Decimal('29.99'),
                'currency': 'aud',
                'product_type': 'subscription',
                'billing_interval': 'month',
                'billing_interval_count': 1,
                'features': [
                    'Unlimited vehicle comparisons',
                    'All premium features unlocked',
                    'Advanced fleet management tools',
                    '20 current vehicle entries',
                    'Priority customer support',
                    'Advanced analytics and reporting',
                    'API access for integrations',
                    'White-label options'
                ],
                'metadata': {
                    'plan_slug': 'full-insight-pro',
                    'garage_vehicles': '30',
                    'current_vehicle_entries': '20',
                    'tier': 'pro'
                }
            }
        ]

        if not self.confirm_action(
            f"This will create {len(carreb_products)} CarReb subscription products in Stripe.", 
            force
        ):
            self.stdout.write("Operation cancelled.")
            return

        created_count = 0
        for product_data in carreb_products:
            try:
                # Check if product already exists locally
                existing_product = Product.objects.filter(
                    name=product_data['name']
                ).first()
                
                if existing_product:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Product '{product_data['name']}' already exists locally")
                    )
                    
                    if existing_product.stripe_product_id:
                        self.stdout.write("   Stripe product already linked, skipping...")
                        continue
                    else:
                        self.stdout.write("   No Stripe product linked, creating...")

                # Extract metadata and features before creating local product
                metadata = product_data.pop('metadata', {})
                features = product_data.pop('features', [])

                # Create or update local product
                if existing_product:
                    # Update existing product
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    local_product = existing_product
                else:
                    # Create new product
                    local_product = Product.objects.create(**product_data)
                
                # Create Stripe product and price
                stripe_product, stripe_price = self.create_stripe_product_and_price(
                    local_product, metadata, features
                )
                
                # Update local product with Stripe IDs
                local_product.stripe_product_id = stripe_product.id
                local_product.stripe_price_id = stripe_price.id
                local_product.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {local_product.name}")
                )
                self.stdout.write(f"   Stripe Product ID: {stripe_product.id}")
                self.stdout.write(f"   Stripe Price ID: {stripe_price.id}")
                
                created_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to create product '{product_data['name']}': {str(e)}")
                )
                # Clean up local product if Stripe creation failed
                if 'local_product' in locals() and not existing_product:
                    local_product.delete()

        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Successfully created {created_count} products!")
        )

    def sync_existing_products(self, force=False):
        """Sync existing local products with Stripe"""
        products = Product.objects.filter(
            product_type='subscription',
            active=True,
            stripe_product_id__isnull=True
        )
        
        if not products.exists():
            self.stdout.write("No products found that need syncing with Stripe.")
            return
        
        if not self.confirm_action(
            f"This will sync {products.count()} local products with Stripe.", 
            force
        ):
            self.stdout.write("Operation cancelled.")
            return
        
        synced_count = 0
        for product in products:
            try:
                stripe_product, stripe_price = self.create_stripe_product_and_price(product)
                
                product.stripe_product_id = stripe_product.id
                product.stripe_price_id = stripe_price.id
                product.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Synced: {product.name}")
                )
                synced_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to sync product {product.name}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Successfully synced {synced_count} products!")
        )

    def update_existing_products(self, force=False):
        """Update existing Stripe products"""
        products = Product.objects.filter(
            stripe_product_id__isnull=False,
            active=True
        )
        
        if not products.exists():
            self.stdout.write("No products found with Stripe IDs to update.")
            return
        
        if not self.confirm_action(
            f"This will update {products.count()} existing Stripe products.", 
            force
        ):
            self.stdout.write("Operation cancelled.")
            return
        
        updated_count = 0
        for product in products:
            try:
                # Update Stripe product
                stripe.Product.modify(
                    product.stripe_product_id,
                    name=product.name,
                    description=product.description,
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Updated: {product.name}")
                )
                updated_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to update product {product.name}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Successfully updated {updated_count} products!")
        )

    def create_stripe_product_and_price(self, local_product, metadata=None, features=None):
        """Create Stripe product and price for a local product"""
        
        # Prepare product metadata
        product_metadata = {
            'local_product_id': str(local_product.id),
            'billing_interval': local_product.billing_interval,
            'billing_interval_count': str(local_product.billing_interval_count),
            'currency': local_product.currency,
            'product_type': local_product.product_type,
        }
        
        if metadata:
            product_metadata.update(metadata)
        
        # Add features to description if provided
        description = local_product.description
        if features:
            features_text = "\n\nFeatures:\n" + "\n".join([f"• {feature}" for feature in features])
            description += features_text

        # Create Stripe product
        stripe_product = stripe.Product.create(
            name=local_product.name,
            description=description,
            metadata=product_metadata,
            # Add product images if you have them
            # images=['https://your-domain.com/product-image.png'],
        )

        # Create Stripe price
        price_metadata = {
            'local_product_id': str(local_product.id),
            'product_name': local_product.name,
        }
        
        if metadata:
            price_metadata.update({k: v for k, v in metadata.items() if k.startswith('price_')})

        stripe_price = stripe.Price.create(
            unit_amount=int(float(local_product.price) * 100),  # Convert to cents
            currency=local_product.currency,
            recurring={
                'interval': local_product.billing_interval,
                'interval_count': local_product.billing_interval_count,
            },
            product=stripe_product.id,
            metadata=price_metadata,
        )

        return stripe_product, stripe_price

    def list_stripe_products(self):
        """List existing Stripe products with detailed information"""
        try:
            products = stripe.Product.list(limit=100, active=True)
            
            self.stdout.write("\n" + "="*80)
            self.stdout.write("STRIPE PRODUCTS SUMMARY")
            self.stdout.write("="*80)
            
            if not products.data:
                self.stdout.write("No active products found in Stripe.")
                return
            
            for i, product in enumerate(products.data, 1):
                self.stdout.write(f"\n{i}. {product.name}")
                self.stdout.write(f"   ID: {product.id}")
                self.stdout.write(f"   Created: {self.format_timestamp(product.created)}")
                self.stdout.write(f"   Active: {'✅' if product.active else '❌'}")
                
                if hasattr(product, 'description') and product.description:
                    desc = product.description[:100] + "..." if len(product.description) > 100 else product.description
                    self.stdout.write(f"   Description: {desc}")
                
                # Get prices for this product
                prices = stripe.Price.list(product=product.id, limit=10, active=True)
                
                if prices.data:
                    self.stdout.write("   Prices:")
                    for price in prices.data:
                        amount = price.unit_amount / 100 if price.unit_amount else 0
                        if price.recurring:
                            interval = price.recurring['interval']
                            interval_count = price.recurring.get('interval_count', 1)
                            billing = f"{interval_count} {interval}{'s' if interval_count > 1 else ''}"
                        else:
                            billing = 'one-time'
                        
                        self.stdout.write(f"     • ${amount:.2f} {price.currency.upper()} / {billing}")
                        self.stdout.write(f"       Price ID: {price.id}")
                
                # Show metadata if present
                if product.metadata:
                    self.stdout.write("   Metadata:")
                    for key, value in product.metadata.items():
                        self.stdout.write(f"     • {key}: {value}")
            
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"Total active products: {len(products.data)}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to list Stripe products: {str(e)}")
            )

    def format_timestamp(self, timestamp):
        """Format Unix timestamp to readable date"""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')