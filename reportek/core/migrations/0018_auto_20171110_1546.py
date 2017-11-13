# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-10 15:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_baseworkflow_previous_state'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transitionlog',
            name='content_type',
        ),
        migrations.DeleteModel(
            name='ReportSimple',
        ),
        migrations.DeleteModel(
            name='ReportWithQA',
        ),
        migrations.RemoveField(
            model_name='basereport',
            name='country',
        ),
        migrations.RemoveField(
            model_name='basereport',
            name='obligation',
        ),
        migrations.AlterField(
            model_name='basereport',
            name='type',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.DeleteModel(
            name='TransitionLog',
        ),
        migrations.DeleteModel(
            name='BaseReport',
        ),
    ]
