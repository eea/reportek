# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-07 14:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import reportek.core.models.reports.catalog


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('core', '0006_auto_20171106_1116'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('core.reportone', 'report one')], db_index=True, max_length=255)),
                ('name', models.CharField(max_length=100)),
                ('obligation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.Obligation')),
            ],
            options={
                'db_table': 'core_reports',
            },
        ),
        migrations.CreateModel(
            name='TransitionLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transition', models.CharField(db_index=True, max_length=255, verbose_name='transition')),
                ('from_state', models.CharField(db_index=True, max_length=255, verbose_name='from state')),
                ('to_state', models.CharField(db_index=True, max_length=255, verbose_name='to state')),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='performed at')),
                ('content_id', models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name='Content id')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='Content type')),
            ],
            options={
                'verbose_name': 'XWorkflow transition log',
                'verbose_name_plural': 'XWorkflow transition logs',
                'ordering': ('-timestamp', 'transition'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WFState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('title', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'workflow state',
                'verbose_name_plural': 'workflow states',
            },
        ),
        migrations.CreateModel(
            name='WFTransition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.WFState')),
            ],
            options={
                'verbose_name': 'workflow transition',
                'verbose_name_plural': 'workflow transitions',
            },
        ),
        migrations.CreateModel(
            name='WFTransitionSource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.WFState')),
                ('transition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='core.WFTransition')),
            ],
            options={
                'verbose_name': 'workflow transition source',
                'verbose_name_plural': 'workflow transition sources',
            },
        ),
        migrations.CreateModel(
            name='WorkFlow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('initial_state', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='workflows_initiated', to='core.WFState')),
            ],
            options={
                'verbose_name': 'workflow',
                'verbose_name_plural': 'workflows',
            },
        ),
        migrations.AddField(
            model_name='wftransition',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transitions', to='core.WorkFlow'),
        ),
        migrations.AddField(
            model_name='wfstate',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='core.WorkFlow'),
        ),
        migrations.AddField(
            model_name='basereport',
            name='wf_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.WFState'),
        ),
        migrations.AddField(
            model_name='basereport',
            name='workflow',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.WorkFlow'),
        ),
        migrations.CreateModel(
            name='ReportOne',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('core.basereport', reportek.core.models.reports.catalog.FinishMixin),
        ),
        migrations.AlterUniqueTogether(
            name='wftransitionsource',
            unique_together=set([('transition', 'state')]),
        ),
    ]
