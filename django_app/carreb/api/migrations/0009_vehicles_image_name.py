# Generated by Django 4.2.20 on 2025-05-23 00:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_rename_cardetail_cardetails_rename_carmake_carmakes_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicles',
            name='image_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
