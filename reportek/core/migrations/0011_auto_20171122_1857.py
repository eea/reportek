# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-22 18:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20171122_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='obligationgroup',
            name='next_reporting_start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='obligationgroup',
            name='reporting_duration_months',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='reportingperiod',
            name='obligation_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reporting_period_set', to='core.ObligationGroup'),
        ),
    ]