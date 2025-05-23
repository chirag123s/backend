# Generated by Django 4.2.20 on 2025-03-19 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CarMake',
            fields=[
                ('car_make_id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.CharField(max_length=255)),
                ('popular', models.BooleanField(default=0)),
                ('active', models.BooleanField(default=1)),
            ],
            options={
                'db_table': '"car_make"',
            },
        ),
    ]
