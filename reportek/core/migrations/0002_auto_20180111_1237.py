# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-11 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='obligationspec',
            options={'verbose_name': 'Obligation Specification'},
        ),
        migrations.AlterModelOptions(
            name='reportersubdivision',
            options={'verbose_name': 'Reporter Subdivision'},
        ),
        migrations.AlterModelOptions(
            name='reportersubdivisioncategory',
            options={'verbose_name': 'Reporter Subdivision Category', 'verbose_name_plural': 'Reporter Subdivision Categories'},
        ),
        migrations.AlterUniqueTogether(
            name='obligationspec',
            unique_together=set([('obligation', 'version')]),
        ),
    ]
