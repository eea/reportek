# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2017-12-14 13:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20171214_0858'),
    ]

    operations = [
        migrations.AddField(
            model_name='qajob',
            name='qa_script_id',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='qajob',
            name='qa_script_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]