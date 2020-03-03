# Generated by Django 2.2.9 on 2020-01-21 20:34
import json
import pkgutil
import uuid

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations
from django.db import models


# Functions from the following migrations need manual copying.
# Move them and any dependencies into this file, then update the
# RunPython operations to refer to the local versions:

# api.migrations.0029_cloud_account_seeder
def seed_cost_management_aws_account_id(apps, schema_editor):
    """Create a cloud account, using the historical CloudAccount model."""
    CloudAccount = apps.get_model("api", "CloudAccount")
    cloud_account = CloudAccount.objects.create(
        name="AWS", value="589173575009", description="Cost Management's AWS account ID"
    )
    cloud_account.save()


# api.migrations.0040_auto_20191121_2154
def load_openshift_metric_map(apps, schema_editor):
    """Load AWS Cost Usage report to database mapping."""
    CostModelMetricsMap = apps.get_model("api", "CostModelMetricsMap")
    CostModelMetricsMap.objects.all().delete()

    data = pkgutil.get_data("api", "metrics/data/cost_models_metric_map.json")

    data = json.loads(data)

    for entry in data:
        # Deleting this entry as it does not exist in the table/model at this point in migrations
        del entry["default_cost_type"]
        map = CostModelMetricsMap(**entry)
        map.save()


class Migration(migrations.Migration):

    replaces = [
        ("api", "0009_providerstatus"),
        ("api", "0010_costmodelmetricsmap"),
        ("api", "0011_auto_20190613_1554"),
        ("api", "0012_auto_20190723_1655"),
        ("api", "0013_auto_20190812_1815"),
        ("api", "0014_auto_20190807_1420"),
        ("api", "0015_dataexportrequest"),
        ("api", "0016_dataexportrequest_bucket_name"),
        ("api", "0017_auto_20190823_1442"),
        ("api", "0018_auto_20190827_1536"),
        ("api", "0019_auto_20190912_1853"),
        ("api", "0020_sources"),
        ("api", "0021_auto_20190917_1757"),
        ("api", "0022_auto_20190923_1410"),
        ("api", "0023_auto_20190923_1810"),
        ("api", "0024_auto_20190925_1914"),
        ("api", "0025_sources_endpoint_id"),
        ("api", "0026_auto_20191003_2339"),
        ("api", "0027_auto_20191008_1905"),
        ("api", "0028_cloud_account"),
        ("api", "0029_cloud_account_seeder"),
        ("api", "0030_auto_20191022_1602"),
        ("api", "0031_auto_20191022_1615"),
        ("api", "0032_auto_20191022_1620"),
        ("api", "0033_auto_20191022_1635"),
        ("api", "0034_provider_active"),
        ("api", "0035_auto_20191108_1914"),
        ("api", "0036_auto_20191113_2029"),
        ("api", "0037_auto_20191120_1538"),
        ("api", "0038_sources_source_uuid"),
        ("api", "0039_auto_20191121_2154"),
        ("api", "0040_auto_20191121_2154"),
        ("api", "0041_sources_account_id"),
        ("api", "0042_auto_20200116_2048"),
    ]

    dependencies = [
        ("api", "0001_initial_squashed_0008_auto_20190305_2015"),
        ("reporting_common", "0001_initial_squashed_0007_auto_20190208_0316_squashed_0019_auto_20191022_1602"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderStatus",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (0, "New"),
                            (1, "Ready"),
                            (33, "Warning"),
                            (98, "Disabled: Error"),
                            (99, "Disabled: Admin"),
                        ],
                        default=0,
                    ),
                ),
                ("last_message", models.CharField(max_length=256)),
                ("timestamp", models.DateTimeField()),
                ("retries", models.IntegerField(default=0)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.Provider")),
            ],
        ),
        migrations.CreateModel(
            name="CostModelMetricsMap",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("AWS", "AWS"),
                            ("OCP", "OCP"),
                            ("Azure", "Azure"),
                            ("GCP", "GCP"),
                            ("AWS-local", "AWS-local"),
                            ("Azure-local", "Azure-local"),
                            ("GCP-local", "GCP-local"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "metric",
                    models.CharField(
                        choices=[
                            ("cpu_core_usage_per_hour", "cpu_core_usage_per_hour"),
                            ("cpu_core_request_per_hour", "cpu_core_request_per_hour"),
                            ("memory_gb_usage_per_hour", "memory_gb_usage_per_hour"),
                            ("memory_gb_request_per_hour", "memory_gb_request_per_hour"),
                            ("storage_gb_usage_per_month", "storage_gb_usage_per_month"),
                            ("storage_gb_request_per_month", "storage_gb_request_per_month"),
                            ("node_cost_per_month", "node_cost_per_month"),
                        ],
                        max_length=256,
                    ),
                ),
                ("label_metric", models.CharField(max_length=256)),
                ("label_measurement", models.CharField(max_length=256)),
                ("label_measurement_unit", models.CharField(max_length=64)),
            ],
            options={"db_table": "cost_models_metrics_map", "unique_together": {("source_type", "metric")}},
        ),
        migrations.CreateModel(
            name="DataExportRequest",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("created_timestamp", models.DateTimeField(auto_now_add=True)),
                ("updated_timestamp", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("processing", "Processing"),
                            ("waiting", "Waiting"),
                            ("complete", "Complete"),
                            ("error", "Error"),
                        ],
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.User")),
            ],
            options={"ordering": ("created_timestamp",)},
        ),
        migrations.AddField(
            model_name="dataexportrequest",
            name="bucket_name",
            field=models.CharField(default="", max_length=63),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="Sources",
            fields=[
                ("source_id", models.IntegerField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=256, null=True)),
                ("source_type", models.CharField(max_length=50)),
                ("authentication", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ("billing_source", django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True)),
                ("koku_uuid", models.CharField(max_length=512, null=True)),
                ("auth_header", models.TextField(null=True)),
                ("pending_delete", models.BooleanField(default=False)),
                ("offset", models.IntegerField()),
                ("endpoint_id", models.IntegerField(null=True)),
                ("pending_update", models.BooleanField(default=False)),
                ("source_uuid", models.UUIDField(null=True, unique=True)),
                ("account_id", models.CharField(max_length=150, null=True)),
            ],
            options={"db_table": "api_sources"},
        ),
        # This is here to ensure that the constraint name on this ticket branch matches the
        # name that exists on the master branch and in production
        migrations.RunSQL(
            sql="""
            alter table public.api_sources
              add constraint api_sources_koku_uuid_ed719dad_uniq unique (koku_uuid);

            CREATE INDEX api_sources_koku_uuid_ed719dad_like
                ON public.api_sources USING btree (koku_uuid varchar_pattern_ops);
            """
        ),
        migrations.CreateModel(
            name="CloudAccount",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(help_text="The name of the attribute", max_length=255)),
                ("value", models.TextField(null=True)),
                ("description", models.TextField(null=True)),
                ("updated_timestamp", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ProviderInfrastructureMap",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "infrastructure_type",
                    models.CharField(
                        choices=[
                            ("AWS", "AWS"),
                            ("Azure", "Azure"),
                            ("GCP", "GCP"),
                            ("AWS-local", "AWS-local"),
                            ("Azure-local", "Azure-local"),
                            ("GCP-local", "GCP-local"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "infrastructure_provider",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="api.Provider"),
                ),
            ],
        ),
        # ==============================
        # CIRCULAR FK HERE!
        # ==============================
        migrations.AddField(
            model_name="provider",
            name="infrastructure",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="api.ProviderInfrastructureMap"
            ),
        ),
        migrations.RunPython(code=seed_cost_management_aws_account_id),
        migrations.RunPython(code=load_openshift_metric_map),
    ]
