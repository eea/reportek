# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-10 09:30
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20171110_0859'),
    ]

    operations = [
        migrations.RenameField(
            model_name='baseworkflow',
            old_name='state',
            new_name='current_state',
        ),
    ]
