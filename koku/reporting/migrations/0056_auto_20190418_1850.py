# Generated by Django 2.2 on 2019-04-18 18:50

import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0055_auto_20190416_2025'),
    ]

    operations = [
        migrations.CreateModel(
            name='OCPAWSCostLineItemProjectDailySummary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cluster_id', models.CharField(max_length=50, null=True)),
                ('cluster_alias', models.CharField(max_length=256, null=True)),
                ('namespace', models.CharField(max_length=253)),
                ('node', models.CharField(max_length=253)),
                ('resource_id', models.CharField(max_length=253, null=True)),
                ('usage_start', models.DateTimeField()),
                ('usage_end', models.DateTimeField()),
                ('product_code', models.CharField(max_length=50)),
                ('product_family', models.CharField(max_length=150, null=True)),
                ('instance_type', models.CharField(max_length=50, null=True)),
                ('usage_account_id', models.CharField(max_length=50)),
                ('availability_zone', models.CharField(max_length=50, null=True)),
                ('region', models.CharField(max_length=50, null=True)),
                ('unit', models.CharField(max_length=63, null=True)),
                ('tags', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('usage_amount', models.DecimalField(decimal_places=9, max_digits=24, null=True)),
                ('normalized_usage_amount', models.FloatField(null=True)),
                ('currency_code', models.CharField(max_length=10, null=True)),
                ('unblended_cost', models.DecimalField(decimal_places=9, max_digits=17, null=True)),
                ('shared_projects', models.IntegerField(default=1)),
                ('project_cost', models.DecimalField(decimal_places=6, max_digits=24, null=True)),
                ('account_alias', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='reporting.AWSAccountAlias')),
            ],
            options={
                'db_table': 'reporting_ocpawscostlineitem_project_daily_summary',
            },
        ),
        migrations.DeleteModel(
            name='OCPAWSStorageLineItemDaily',
        ),
        migrations.DeleteModel(
            name='OCPAWSUsageLineItemDaily',
        ),
        migrations.AddIndex(
            model_name='ocpawscostlineitemprojectdailysummary',
            index=models.Index(fields=['usage_start'], name='cost_proj_sum_ocp_usage_idx'),
        ),
        migrations.AddIndex(
            model_name='ocpawscostlineitemprojectdailysummary',
            index=models.Index(fields=['namespace'], name='cost__proj_sum_namespace_idx'),
        ),
        migrations.AddIndex(
            model_name='ocpawscostlineitemprojectdailysummary',
            index=models.Index(fields=['node'], name='cost_proj_sum_node_idx'),
        ),
        migrations.AddIndex(
            model_name='ocpawscostlineitemprojectdailysummary',
            index=models.Index(fields=['resource_id'], name='cost_proj_sum_resource_idx'),
        ),
        migrations.AddIndex(
            model_name='ocpawscostlineitemprojectdailysummary',
            index=django.contrib.postgres.indexes.GinIndex(fields=['tags'], name='cost_proj_tags_idx'),
        ),
        migrations.RunSQL(
            """
            DROP VIEW IF EXISTS reporting_ocpawsstoragelineitem_daily;
            DROP VIEW IF EXISTS reporting_ocpawsusagelineitem_daily;
            """
        ),
    ]