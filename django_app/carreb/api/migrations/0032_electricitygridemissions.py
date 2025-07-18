# Generated by Django 4.2.21 on 2025-06-26 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0031_carvariants_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElectricityGridEmissions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(max_length=50, unique=True)),
                ('emissions_factor_kg_per_kwh', models.DecimalField(decimal_places=4, max_digits=10)),
            ],
            options={
                'db_table': 'electricity_grid_emissions',
            },
        ),
    ]
