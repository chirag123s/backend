# Generated by Django 4.2.21 on 2025-06-14 22:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_alter_carvariants_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carvariants',
            name='sub_variant',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
