# Generated by Django 2.2.11 on 2020-03-25 18:39
import django.contrib.postgres.fields.jsonb
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0102_auto_20200228_1812")]

    operations = [
        migrations.CreateModel(
            name="OCPComputeSummary",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("cluster_id", models.CharField(max_length=50, null=True)),
                ("cluster_alias", models.CharField(max_length=256, null=True)),
                (
                    "resource_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=256), null=True, size=None
                    ),
                ),
                ("resource_count", models.IntegerField(null=True)),
                ("data_source", models.CharField(max_length=64, null=True)),
                ("namespace", models.CharField(max_length=253, null=True)),
                ("usage_start", models.DateField()),
                ("usage_end", models.DateField()),
                ("supplementary_usage_cost", django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ("infrastructure_raw_cost", models.DecimalField(decimal_places=15, max_digits=33, null=True)),
                ("infrastructure_usage_cost", django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ("infrastructure_markup_cost", models.DecimalField(decimal_places=15, max_digits=33, null=True)),
                ("pod_usage_cpu_core_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("pod_request_cpu_core_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("pod_limit_cpu_core_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("pod_usage_memory_gigabyte_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("pod_request_memory_gigabyte_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("pod_limit_memory_gigabyte_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("cluster_capacity_cpu_core_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                ("total_capacity_cpu_core_hours", models.DecimalField(decimal_places=9, max_digits=27, null=True)),
                (
                    "total_capacity_memory_gigabyte_hours",
                    models.DecimalField(decimal_places=9, max_digits=27, null=True),
                ),
            ],
            options={"db_table": "reporting_ocp_compute_summary", "managed": False},
        ),
        migrations.CreateModel(
            name="OCPVolumeSummary",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("cluster_id", models.CharField(max_length=50, null=True)),
                ("cluster_alias", models.CharField(max_length=256, null=True)),
                (
                    "resource_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=256), null=True, size=None
                    ),
                ),
                ("resource_count", models.IntegerField(null=True)),
                ("data_source", models.CharField(max_length=64, null=True)),
                ("namespace", models.CharField(max_length=253, null=True)),
                ("usage_start", models.DateField()),
                ("usage_end", models.DateField()),
                ("supplementary_usage_cost", django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ("infrastructure_raw_cost", models.DecimalField(decimal_places=15, max_digits=33, null=True)),
                ("infrastructure_usage_cost", django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ("infrastructure_markup_cost", models.DecimalField(decimal_places=15, max_digits=33, null=True)),
                (
                    "persistentvolumeclaim_usage_gigabyte_months",
                    models.DecimalField(decimal_places=9, max_digits=27, null=True),
                ),
                (
                    "volume_request_storage_gigabyte_months",
                    models.DecimalField(decimal_places=9, max_digits=27, null=True),
                ),
                (
                    "persistentvolumeclaim_capacity_gigabyte_months",
                    models.DecimalField(decimal_places=9, max_digits=27, null=True),
                ),
            ],
            options={"db_table": "reporting_ocp_volume_summary", "managed": False},
        ),
        migrations.RunSQL(
            sql="""
            CREATE MATERIALIZED VIEW reporting_ocp_compute_summary AS(
                SELECT row_number() OVER(ORDER BY date(usage_start), cluster_id, cluster_alias, namespace) as id,
                    date(usage_start) as usage_start,
                    date(usage_start) as usage_end,
                    cluster_id,
                    cluster_alias,
                    namespace,
                    max(data_source) as data_source,
                    array_agg(DISTINCT resource_id) as resource_ids,
                    count(DISTINCT resource_id) as resource_count,
                    json_build_object('cpu', sum((supplementary_usage_cost->>'cpu')::decimal),
                                    'memory', sum((supplementary_usage_cost->>'memory')::decimal),
                                    'storage', sum((supplementary_usage_cost->>'storage')::decimal)) as supplementary_usage_cost,
                    json_build_object('cpu', sum((infrastructure_usage_cost->>'cpu')::decimal),
                                    'memory', sum((infrastructure_usage_cost->>'memory')::decimal),
                                    'storage', sum((infrastructure_usage_cost->>'storage')::decimal)) as infrastructure_usage_cost,
                    sum(infrastructure_raw_cost) as infrastructure_raw_cost,
                    sum(infrastructure_markup_cost) as infrastructure_markup_cost,
                    sum(pod_usage_cpu_core_hours) as pod_usage_cpu_core_hours,
                    sum(pod_request_cpu_core_hours) as pod_request_cpu_core_hours,
                    sum(pod_limit_cpu_core_hours) as pod_limit_cpu_core_hours,
                    sum(cluster_capacity_cpu_core_hours) as cluster_capacity_cpu_core_hours,
                    sum(total_capacity_cpu_core_hours) as total_capacity_cpu_core_hours,
                    sum(pod_usage_memory_gigabyte_hours) as pod_usage_memory_gigabyte_hours,
                    sum(pod_request_memory_gigabyte_hours) as pod_request_memory_gigabyte_hours,
                    sum(pod_limit_memory_gigabyte_hours) as pod_limit_memory_gigabyte_hours,
                    sum(total_capacity_memory_gigabyte_hours) as total_capacity_memory_gigabyte_hours
                FROM reporting_ocpusagelineitem_daily_summary
                -- Get data for this month or last month
                WHERE date_trunc('month', usage_start) = date_trunc('month', now()) AND data_source = 'Pod'
                    OR date_trunc('month', usage_start) = date_trunc('month', date_trunc('month', now()) - INTERVAL '1' DAY) AND data_source = 'Pod'
                GROUP BY date(usage_start), cluster_id, cluster_alias, namespace
            )
            ;

            CREATE UNIQUE INDEX ocp_compute_summary
            ON reporting_ocp_compute_summary (usage_start, cluster_id, cluster_alias, namespace)
            ;

            CREATE MATERIALIZED VIEW reporting_ocp_volume_summary AS(
                SELECT row_number() OVER(ORDER BY date(usage_start), cluster_id, cluster_alias, namespace) as id,
                    date(usage_start) as usage_start,
                    date(usage_start) as usage_end,
                    cluster_id,
                    cluster_alias,
                    namespace,
                    max(data_source) as data_source,
                    array_agg(DISTINCT resource_id) as resource_ids,
                    count(DISTINCT resource_id) as resource_count,
                    json_build_object('cpu', sum((supplementary_usage_cost->>'cpu')::decimal),
                                    'memory', sum((supplementary_usage_cost->>'memory')::decimal),
                                    'storage', sum((supplementary_usage_cost->>'storage')::decimal)) as supplementary_usage_cost,
                    json_build_object('cpu', sum((infrastructure_usage_cost->>'cpu')::decimal),
                                    'memory', sum((infrastructure_usage_cost->>'memory')::decimal),
                                    'storage', sum((infrastructure_usage_cost->>'storage')::decimal)) as infrastructure_usage_cost,
                    sum(infrastructure_raw_cost) as infrastructure_raw_cost,
                    sum(infrastructure_markup_cost) as infrastructure_markup_cost,
                    sum(persistentvolumeclaim_usage_gigabyte_months) as persistentvolumeclaim_usage_gigabyte_months,
                    sum(volume_request_storage_gigabyte_months) as volume_request_storage_gigabyte_months,
                    sum(persistentvolumeclaim_capacity_gigabyte_months) as persistentvolumeclaim_capacity_gigabyte_months
                FROM reporting_ocpusagelineitem_daily_summary
                -- Get data for this month or last month
                WHERE date_trunc('month', usage_start) = date_trunc('month', now()) AND data_source = 'Storage'
                    OR date_trunc('month', usage_start) = date_trunc('month', date_trunc('month', now()) - INTERVAL '1' DAY) AND data_source = 'Storage'
                GROUP BY date(usage_start), cluster_id, cluster_alias, namespace
            )
            ;

            CREATE UNIQUE INDEX ocp_volume_summary
            ON reporting_ocp_volume_summary (usage_start, cluster_id, cluster_alias, namespace)
            ;
            """
        ),
    ]