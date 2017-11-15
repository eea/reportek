# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-14 17:04
from __future__ import unicode_literals

from django.db import migrations, models
import edw.djutils.protected.fields
import reportek.core.models.reporting


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20171115_0835'),
    ]

    operations = [
        migrations.AddField(
            model_name='envelopefile',
            name='name',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='envelopefile',
            name='file',
            field=edw.djutils.protected.fields.ProtectedFileField(max_length=512, upload_to=reportek.core.models.reporting.EnvelopeFile.get_envelope_directory),
        ),
        migrations.AlterUniqueTogether(
            name='envelopefile',
            unique_together=set([('envelope', 'name')]),
        ),
    ]
