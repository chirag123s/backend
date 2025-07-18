# Generated by Django 4.2.21 on 2025-06-13 10:10

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_remove_vehicles_image_name_carsearchlog_vehicle_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='carmakes',
            old_name='popular',
            new_name='is_popular',
        ),
        migrations.AddField(
            model_name='carmakes',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='carmakes',
            name='grok_json',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='carmakes',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.CreateModel(
            name='CarVariants',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('model', models.CharField(max_length=255)),
                ('variant', models.CharField(max_length=255)),
                ('image_url', models.URLField(blank=True, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='car_variants/')),
                ('sub_variants', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('car_make', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='api.carmakes')),
            ],
            options={
                'db_table': 'car_variants',
                'unique_together': {('car_make', 'model', 'variant')},
            },
        ),
    ]
