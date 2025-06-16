from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_remove_vehicles_image_name_carsearchlog_vehicle_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='carsearchlog',
            name='customer_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='carsearchlog',
            name='payment_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='carsearchlog',
            name='is_migrated_to_garage',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='carsearchlog',
            name='migrated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]