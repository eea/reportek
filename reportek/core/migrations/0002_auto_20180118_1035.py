# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-18 10:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='obligationspecreporter',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='obligationspecreporter',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]