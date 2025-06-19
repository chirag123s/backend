# payments/migrations/0004_add_subscription_changes.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_add_subscription_support'),
    ]

    operations = [
        # Add new fields to Product model
        migrations.AddField(
            model_name='product',
            name='plan_tier',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='plan_metadata',
            field=models.JSONField(blank=True, null=True),
        ),
        
        # Create SubscriptionChange model
        migrations.CreateModel(
            name='SubscriptionChange',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_email', models.EmailField(max_length=254)),
                ('stripe_subscription_id', models.CharField(max_length=255)),
                ('old_price_id', models.CharField(max_length=255)),
                ('new_price_id', models.CharField(max_length=255)),
                ('change_type', models.CharField(choices=[('upgrade', 'Upgrade'), ('downgrade', 'Downgrade'), ('retention', 'Retention')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('effective_date', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('proration_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('schedule_id', models.CharField(blank=True, max_length=255, null=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('old_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='old_changes', to='payments.product')),
                ('new_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='new_changes', to='payments.product')),
            ],
            options={
                'db_table': 'subscription_changes',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create RetentionOffer model
        migrations.CreateModel(
            name='RetentionOffer',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('user_email', models.EmailField(max_length=254)),
                ('stripe_subscription_id', models.CharField(max_length=255)),
                ('offer_type', models.CharField(choices=[('discount', 'Discount'), ('free_month', 'Free Month'), ('feature_unlock', 'Feature Unlock'), ('custom', 'Custom Offer')], max_length=50)),
                ('offer_details', models.JSONField()),
                ('accepted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('coupon_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_promotion_code', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'db_table': 'retention_offers',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add subscription_change foreign key to PaymentLog
        migrations.AddField(
            model_name='paymentlog',
            name='subscription_change',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='payments.subscriptionchange'),
        ),
        
        # Add indexes for better query performance
        migrations.RunSQL(
            "CREATE INDEX idx_subscription_changes_email_status ON subscription_changes(user_email, status);",
            reverse_sql="DROP INDEX IF EXISTS idx_subscription_changes_email_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX idx_retention_offers_email_accepted ON retention_offers(user_email, accepted);",
            reverse_sql="DROP INDEX IF EXISTS idx_retention_offers_email_accepted;"
        ),
    ]