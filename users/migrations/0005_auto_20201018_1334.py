# Generated by Django 3.1.1 on 2020-10-18 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20200930_1959'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='storage',
            field=models.IntegerField(default=2),
        ),
    ]
