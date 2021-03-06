#
# Copyright 2019 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""Test the AzureReportQueryHandler base class."""
import hashlib
import pkgutil
import random
from collections import UserDict
from datetime import datetime
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from django.db import connection
from faker import Faker
from jinjasql import JinjaSql
from tenant_schemas.utils import tenant_context

from api.iam.serializers import _currency_symbols
from api.utils import DateHelper
from reporting.models import AzureCostEntryBill
from reporting.models import AzureCostEntryLineItemDaily
from reporting.models import AzureCostEntryLineItemDailySummary
from reporting.models import AzureCostEntryProductService
from reporting.models import AzureMeter
from reporting.models import AzureTagsSummary
from reporting_common.models import CostUsageReportManifest
from reporting_common.models import CostUsageReportStatus


# Location list generated by this command:
# az account list-locations -o json | jq ".[].displayName"
#
AZURE_LOCATIONS = [
    "East Asia",
    "Southeast Asia",
    "Central US",
    "East US",
    "East US 2",
    "West US",
    "North Central US",
    "South Central US",
    "North Europe",
    "West Europe",
    "Japan West",
    "Japan East",
    "Brazil South",
    "Australia East",
    "Australia Southeast",
    "South India",
    "Central India",
    "West India",
    "Canada Central",
    "Canada East",
    "UK South",
    "UK West",
    "West Central US",
    "West US 2",
    "Korea Central",
    "Korea South",
    "France Central",
    "France South",
    "Australia Central",
    "Australia Central 2",
    "UAE Central",
    "UAE North",
    "South Africa North",
    "South Africa West",
    "Germany North",
    "Germany West Central",
]

# {Consumed Service: [Resource Type]}
#
AZURE_RESOURCES = {
    "Microsoft.Storage": ["Microsoft.Storage/storageAccounts", "Microsoft.Storage/storageAccounts/blobServices"],
    "Microsoft.Network": [
        "Microsoft.Network/publicIPAddresses",
        "Microsoft.Network/applicationGateways",
        "Microsoft.Network/connections",
        "Microsoft.Network/loadBalancers",
        "Microsoft.Network/dnsZones",
    ],
    "Microsoft.Sql": ["Microsoft.Sql/servers", "Microsoft.Sql/managedInstances"],
    "Microsoft.Compute": [
        "Microsoft.Compute/virtualMachines",
        "Microsoft.Compute/disks",
        "Microsoft.Compute/virtualMachineScaleSets",
        "Microsoft.Compute/snapshots",
    ],
    "microsoft.operationalinsights": ["microsoft.operationalinsights/workspaces"],
    "Microsoft.DBforPostgreSQL": ["Microsoft.DBforPostgreSQL/servers"],
    "Microsoft.DBforMariaDB": ["Microsoft.DBforMariaDB/servers"],
}

# {Name: {Category: [SubCategory]}}
#
AZURE_METERS = {
    "Bandwidth": {"null": ["Data Transfer In", "Data Transfer Out - Free"]},
    "Log Analytics": {"null": ["Data Ingestion"]},
    "SQL Database": {"Single Standard": ["S0 DTUs - Free"]},
    "Storage": {
        "Bandwidth": ["Geo-Replication Data transfer", "Geo-Replication v2 Data transfer"],
        "Files": ["List Operations - Free", "Read Operations - Free"],
        "General Block Blob": [
            "Delete Operations",
            "GRS Write Operations",
            "List and Create Container Operations",
            "Read Operations",
            "Write Operations",
        ],
        "Premium SSD Managed Disks": ["P10 Disks"],
        "Queues v2": ["GRS Class 1 Operations"],
        "Standard Page Blob": ["Disk Read Operations", "Disk Write Operations", "LRS Data Stored"],
        "Standard SSD Managed Disks": ["Disk Operations", "E4 Disks"],
        "Tables": [
            "Batch Write Operations",
            "GRS Batch Write Operations",
            "LRS Data Stored",
            "RA-GRS Data Stored",
            "Read Operations",
            "Scan Operations",
            "Write Operations",
        ],
        "Tiered Block Blob": [
            "All Other Operations",
            "Hot GRS Write Operations",
            "Hot RA-GRS Data Stored",
            "Hot Read Operations - Free",
        ],
    },
    "Virtual Machines": {"A Series": ["A0"], "BS Series": ["B2s"]},
    "Virtual Network": {"IP Addresses": ["Dynamic Public IP - Free"]},
}

# {Service Name: [Service Tier]}
#
AZURE_SERVICES = {
    "Bandwidth": ["Bandwidth"],
    "Log Analytics": ["Log Analytics"],
    "SQL Database": ["SQL DB Single Std"],
    "Storage": [
        "Blob Storage",
        "Files",
        "General Block Blob",
        "Premium SSD Managed Disks",
        "Queues v2",
        "Standard Page Blob",
        "Standard SSD Managed Disks",
        "Storage - Bandwidth",
        "Tables",
    ],
    "Virtual Machines": ["A Series", "A Series VM", "BS Series VM"],
    "Virtual Network": ["IP Addresses"],
}

# Instance Type list generated by this command:
# az vm list-sizes -o json --location 'East US' | jq '.[].name'
#
AZURE_INSTANCE_TYPES = [
    "Standard_B1ls",
    "Standard_B1ms",
    "Standard_B1s",
    "Standard_B2ms",
    "Standard_B2s",
    "Standard_B4ms",
    "Standard_B8ms",
    "Standard_B12ms",
    "Standard_B16ms",
    "Standard_B20ms",
    "Standard_A1_v2",
    "Standard_A2m_v2",
    "Standard_A2_v2",
    "Standard_A4m_v2",
    "Standard_A4_v2",
    "Standard_A8m_v2",
    "Standard_A8_v2",
    "Basic_A0",
    "Basic_A1",
    "Basic_A2",
    "Basic_A3",
    "Basic_A4",
    "Standard_A8",
    "Standard_A9",
    "Standard_A10",
    "Standard_A11",
]


# pylint: disable=access-member-before-definition, attribute-defined-outside-init, too-many-instance-attributes
class FakeAzureConfig(UserDict):
    """Azure Configuration Data Mocker.

    This object holds any values that may need to be preserved across multiple
    generated line items. The AzureReportDataGenerator does its own
    randomization of the fields where state never needs to be preserved.
    """

    fake = Faker()
    dh = DateHelper()

    def _get_prop(self, name, default):
        """Get property value or use provided default."""
        if name not in self.data:
            self.data[name] = default
        return self.data.get(name)

    @property
    def billing_period_start(self):
        """Return the datetime."""
        return self._get_prop("billing_period_start", self.dh.this_month_start)

    @property
    def billing_period_end(self):
        """Return the datetime."""
        return self._get_prop("billing_period_end", self.dh.this_month_end)

    @property
    def instance_id(self):
        """Return the instance_id."""
        template = "/subscriptions/{uuid}/resourceGroups/{group}/providers/" + "{service}/{resource_type}/{name}"

        return self._get_prop(
            "instance_id",
            template.format(
                uuid=self.subscription_guid,
                group=self.fake.word(),
                name=self.fake.word(),
                service=self.resource_service,
                resource_type=self.resource_type,
            ),
        )

    @property
    def instance_type(self):
        """Return the instance type."""
        return self._get_prop("instance_type", random.choice(AZURE_INSTANCE_TYPES))

    @property
    def meter_category(self):
        """Return the meter category."""
        return self._get_prop("meter_category", random.choice(list(AZURE_METERS[self.meter_name].keys())))

    @property
    def meter_name(self):
        """Return the meter name."""
        return self._get_prop("meter_name", random.choice(list(AZURE_METERS.keys())))

    @property
    def meter_rate(self):
        """Return the meter rate."""
        return self._get_prop("meter_rate", random.random())

    @property
    def meter_subcategory(self):
        """Return the meter subcategory."""
        return self._get_prop(
            "meter_subcategory", random.choice(list(AZURE_METERS[self.meter_name][self.meter_category]))
        )

    @property
    def resource(self):
        """Return the resource name."""
        return self._get_prop("resource", random.choice(AZURE_RESOURCES[self.resource_service]))

    @property
    def resource_location(self):
        """Return the location."""
        return self._get_prop("resource_location", random.choice(AZURE_LOCATIONS))

    @property
    def resource_service(self):
        """Return the service name."""
        return self._get_prop("resource_service", random.choice(list(AZURE_RESOURCES.keys())))

    @property
    def resource_type(self):
        """Return the resource type."""
        return self._get_prop("resource_type", str(self.resource).split("/")[-1])

    @property
    def tags(self):
        """Return the list of tag dicts."""
        new_tags = {key: self.fake.word() for key in {self.fake.word() for _ in range(0, random.randrange(4, 10))}}
        return self._get_prop("tags", new_tags)

    @property
    def service_name(self):
        """Return the service name."""
        return self._get_prop("service_name", random.choice(list(AZURE_SERVICES.keys())))

    @service_name.setter
    def service_name(self, name):
        """Set the service name."""
        self.data["service_name"] = name

    @property
    def service_tier(self):
        """Return the service tier."""
        return self._get_prop("service_tier", random.choice(AZURE_SERVICES[self.service_name]))

    @property
    def subscription_guid(self):
        """Return the uuid."""
        return self._get_prop("subscription_guid", uuid4())


class AzureReportDataGenerator:
    """Populate the database with Azure fake report data."""

    def __init__(self, tenant, provider, current_month_only=False, config=None):
        """Set up the class."""
        self.tenant = tenant
        self.config = config if config else FakeAzureConfig()
        self.fake = Faker()
        self.dh = DateHelper()
        self.provider_uuid = provider.uuid

        # generate a list of dicts with unique keys.
        self.period_ranges, self.report_ranges = self.report_period_and_range(current_month_only=current_month_only)

    def _randomize_line_item(self, retained_fields=None):
        """Update our FakeAzureConfig to generate a new line item."""
        DEFAULT_FIELDS = ["subscription_guid", "resource_location", "tags"]
        if not retained_fields:
            retained_fields = DEFAULT_FIELDS

        config_dict = {}
        for field in retained_fields:
            if field in self.config:
                config_dict[field] = getattr(self.config, field)
        self.config = FakeAzureConfig(**config_dict)

    def report_period_and_range(self, current_month_only=False):
        """Return the report period and range."""
        period = []
        ranges = []
        if current_month_only:
            report_days = 10
            diff_from_first = self.dh.today - self.dh.this_month_start
            if diff_from_first.days < 10:
                report_days = 1 + diff_from_first.days
                period = [(self.dh.this_month_start, self.dh.this_month_end)]
                ranges = [list(self.dh.this_month_start + relativedelta(days=i) for i in range(report_days))]
            else:
                period = [(self.dh.this_month_start, self.dh.this_month_end)]
                ranges = [list(self.dh.today - relativedelta(days=i) for i in range(report_days))]

        else:
            period = [
                (self.dh.last_month_start, self.dh.last_month_end),
                (self.dh.this_month_start, self.dh.this_month_end),
            ]

            one_month_ago = self.dh.today - relativedelta(months=1)
            diff_from_first = self.dh.today - self.dh.this_month_start
            if diff_from_first.days < 10:
                report_days = 1 + diff_from_first.days
                ranges = [
                    list(self.dh.last_month_start + relativedelta(days=i) for i in range(report_days)),
                    list(self.dh.this_month_start + relativedelta(days=i) for i in range(report_days)),
                ]
            else:
                ranges = [
                    list(one_month_ago - relativedelta(days=i) for i in range(10)),
                    list(self.dh.today - relativedelta(days=i) for i in range(10)),
                ]
        return (period, ranges)

    def add_data_to_tenant(self, fixed_fields=None):
        """Populate tenant with data.

        Args:
            provider_uuid (uuid) - provider uuid
            fixed_fields (list) - a list of field names the data generator should NOT randomize.

        """
        with tenant_context(self.tenant):
            for i, period in enumerate(self.period_ranges):
                manifest = self._manifest(period[0], self.provider_uuid)
                self._report_status(manifest.billing_period_start_datetime, manifest.id)
                for report_date in self.report_ranges[i]:
                    self._randomize_line_item(retained_fields=fixed_fields)
                    self._cost_entry_line_item_daily_summary(report_date)
            self._tag_summary()

    def remove_data_from_tenant(self):
        """Remove the added data."""
        with tenant_context(self.tenant):
            for table in (
                AzureCostEntryLineItemDaily,
                AzureCostEntryLineItemDailySummary,
                AzureCostEntryBill,
                AzureCostEntryProductService,
                AzureMeter,
                AzureTagsSummary,
            ):
                table.objects.all().delete()

    # pylint: disable=no-self-use
    def remove_data_from_reporting_common(self):
        """Remove the public report statistics."""
        for table in (CostUsageReportManifest, CostUsageReportStatus):
            table.objects.all().delete()

    # pylint: disable=no-self-use
    def _manifest(self, start, provider_uuid):
        """Populate a report manifest entry."""
        manifest_creation_datetime = start + relativedelta(days=random.randint(1, 27))
        manifest_updated_datetime = manifest_creation_datetime + relativedelta(days=random.randint(1, 2))
        data = {
            "assembly_id": uuid4(),
            "manifest_creation_datetime": manifest_creation_datetime,
            "manifest_updated_datetime": manifest_updated_datetime,
            "billing_period_start_datetime": start,
            "num_processed_files": 1,
            "num_total_files": 1,
            "provider_id": provider_uuid,
        }
        manifest_entry = CostUsageReportManifest(**data)
        manifest_entry.save()
        return manifest_entry

    # pylint: disable=no-self-use
    def _report_status(self, billing_period_start, manifest_id):
        """Populate a report status entry."""
        etag_hash = hashlib.new("ripemd160")
        etag_hash.update(bytes(str(billing_period_start), "utf-8"))

        last_started_datetime = billing_period_start + relativedelta(days=random.randint(1, 3))
        last_completed_datetime = last_started_datetime + relativedelta(days=1)
        data = {
            "report_name": uuid4(),
            "last_completed_datetime": last_completed_datetime,
            "last_started_datetime": last_started_datetime,
            "etag": etag_hash.hexdigest(),
            "manifest_id": manifest_id,
        }
        status_entry = CostUsageReportStatus(**data)
        status_entry.save()
        return status_entry

    def _cost_entry_bill(self, report_date=None):
        """Populate AzureCostEntryBill."""
        billing_period_start = self.config.billing_period_start
        billing_period_end = self.config.billing_period_end
        if report_date:
            billing_period_start = report_date.replace(day=1)
            last_day = self.dh.days_in_month(report_date)
            billing_period_end = report_date.replace(day=last_day)

        obj, _ = AzureCostEntryBill.objects.get_or_create(
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            summary_data_creation_datetime=self.dh.today,
            summary_data_updated_datetime=self.dh.today,
            finalized_datetime=None,
            derived_cost_datetime=self.dh.today,
            provider_id=self.provider_uuid,
        )
        # obj.save()
        return obj

    def _cost_entry_product(self):
        """Populate AzureCostEntryProduct."""
        fake_dict = {self.fake.word(): self.fake.word()}
        obj = AzureCostEntryProductService(
            instance_id=self.config.instance_id,
            resource_location=self.config.resource_location,
            consumed_service=self.config.resource_service,
            resource_type=self.config.resource_type,
            resource_group=self.fake.word(),
            additional_info=fake_dict,
            service_name=self.config.service_name,
            service_tier=self.config.service_tier,
            service_info1=random.choice([None, self.fake.word()]),
            service_info2=random.choice([None, self.fake.word()]),
        )
        obj.save()
        return obj

    def _meter(self):
        """Populate AzureMeter."""
        obj = AzureMeter(
            meter_id=uuid4(),
            meter_name=self.config.meter_name,
            meter_category=self.config.meter_category,
            meter_subcategory=self.config.meter_subcategory,
            meter_region=self.config.resource_location,
            resource_rate=random.random(),
            currency=random.choice(_currency_symbols()),
        )
        obj.save()
        return obj

    def _cost_entry_line_item_daily(self, report_date=None):
        """Populate AzureCostEntryLineItemDaily."""
        if report_date:
            usage_dt = report_date
        else:
            usage_dt = self.fake.date_time_between_dates(self.dh.this_month_start, self.dh.today)
        usage_qty = random.random() * random.randrange(0, 100)
        obj = AzureCostEntryLineItemDaily(
            cost_entry_bill=self._cost_entry_bill(report_date),
            cost_entry_product=self._cost_entry_product(),
            meter=self._meter(),
            subscription_guid=self.config.subscription_guid,
            tags=self.select_tags(),
            usage_date=usage_dt.date() if isinstance(usage_dt, datetime) else usage_dt,
            usage_quantity=usage_qty,
            pretax_cost=usage_qty * self.config.meter_rate,
            offer_id=random.choice([None, self.fake.pyint()]),
        )
        obj.save()
        return obj

    def _cost_entry_line_item_daily_summary(self, report_date=None):
        """Populate AzureCostEntryLineItemDailySummary."""
        line_item = self._cost_entry_line_item_daily(report_date)
        obj = AzureCostEntryLineItemDailySummary(
            cost_entry_bill=line_item.cost_entry_bill,
            meter=line_item.meter,
            subscription_guid=line_item.subscription_guid,
            instance_type=self.config.instance_type,
            service_name=line_item.cost_entry_product.service_name,
            resource_location=line_item.cost_entry_product.resource_location,
            tags=line_item.tags,
            usage_start=line_item.usage_date,
            usage_end=line_item.usage_date,
            usage_quantity=line_item.usage_quantity,
            pretax_cost=line_item.pretax_cost,
            markup_cost=line_item.pretax_cost * 0.1,
            offer_id=line_item.offer_id,
        )
        obj.save()
        return obj

    def _tag_summary(self):
        """Populate AzureTagsSummary."""
        agg_sql = pkgutil.get_data("masu.database", "sql/reporting_azuretags_summary.sql")
        agg_sql = agg_sql.decode("utf-8")
        agg_sql_params = {"schema": connection.schema_name}
        agg_sql, agg_sql_params = JinjaSql().prepare_query(agg_sql, agg_sql_params)

        with connection.cursor() as cursor:
            cursor.execute(agg_sql)

    def select_tags(self):
        """Return a random selection of the defined tags."""
        return {
            key: self.config.tags[key]
            for key in random.choices(
                list(self.config.tags.keys()), k=random.randrange(2, len(self.config.tags.keys()))
            )
        }
