# Generated by Django 4.2.20 on 2025-04-16 06:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_state'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('year', models.CharField(blank=True, max_length=5, null=True)),
                ('make', models.CharField(blank=True, max_length=255, null=True)),
                ('make_name', models.CharField(blank=True, max_length=255, null=True)),
                ('model', models.CharField(blank=True, max_length=255, null=True)),
                ('vehicle_class', models.CharField(blank=True, max_length=50, null=True)),
                ('body', models.CharField(blank=True, max_length=50, null=True)),
                ('doors', models.IntegerField()),
                ('seats', models.IntegerField()),
                ('engine', models.CharField(blank=True, max_length=255, null=True)),
                ('engine_capacity', models.CharField(blank=True, max_length=100, null=True)),
                ('engine_cylinder', models.CharField(blank=True, max_length=50, null=True)),
                ('induction', models.CharField(blank=True, max_length=100, null=True)),
                ('engine_type', models.CharField(blank=True, max_length=100, null=True)),
                ('fuel_grade', models.CharField(blank=True, max_length=50, null=True)),
                ('transmission', models.CharField(blank=True, max_length=255, null=True)),
                ('transmission_speed', models.IntegerField()),
                ('transmission_type', models.CharField(blank=True, max_length=50, null=True)),
                ('drivetrain', models.CharField(blank=True, max_length=50, null=True)),
                ('tailpipe_comb', models.CharField(blank=True, max_length=100, null=True)),
                ('tailpipe_comb_value', models.CharField(blank=True, max_length=50, null=True)),
                ('tailpipe_comb_note', models.CharField(blank=True, max_length=100, null=True)),
                ('tailpipe_urban', models.CharField(blank=True, max_length=100, null=True)),
                ('tailpipe_urban_value', models.CharField(blank=True, max_length=50, null=True)),
                ('tailpipe_urban_note', models.CharField(blank=True, max_length=100, null=True)),
                ('tailpipe_extra', models.CharField(blank=True, max_length=100, null=True)),
                ('tailpipe_extra_value', models.CharField(blank=True, max_length=50, null=True)),
                ('tailpipe_extra_note', models.CharField(blank=True, max_length=100, null=True)),
                ('annual_cost', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fuel_consumption_comb', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fuel_consumption_urban', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fuel_consumption_extra', models.DecimalField(decimal_places=2, max_digits=12)),
                ('energy_consumption', models.DecimalField(decimal_places=2, max_digits=12)),
                ('electric_range', models.DecimalField(decimal_places=2, max_digits=12)),
                ('air_pollution_standard', models.CharField(blank=True, max_length=100, null=True)),
                ('annual_tailpipe_co2', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fuel_lifecycle_co2', models.IntegerField()),
                ('noise_data', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'vehicle',
            },
        ),
    ]
