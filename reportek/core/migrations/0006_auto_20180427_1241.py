# Generated by Django 2.0.4 on 2018-04-27 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_envelope_reporting_cycle'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='envelope',
            options={'ordering': ('created',)},
        ),
        migrations.AlterField(
            model_name='envelope',
            name='assigned_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
