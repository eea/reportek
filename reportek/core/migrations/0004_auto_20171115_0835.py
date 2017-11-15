# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-15 08:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20171115_0819'),
    ]

    operations = [
        migrations.AddField(
            model_name='envelope',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='envelope',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='envelope',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
