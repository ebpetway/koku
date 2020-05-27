# Generated by Django 2.2.12 on 2020-05-13 19:10
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [("reporting", "0113_aws_organizational_units")]

    operations = [
        migrations.RunSQL(
            # Got to drop these views as we are changing the type of a selected column
            # They will be recreated below
            sql="""
DROP INDEX IF EXISTS aws_cost_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary;

DROP INDEX IF EXISTS aws_cost_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_account;

DROP INDEX IF EXISTS aws_cost_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_service;

DROP INDEX IF EXISTS aws_cost_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_cost_summary_by_region;

DROP INDEX IF EXISTS aws_compute_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary;

DROP INDEX IF EXISTS aws_compute_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_account;

DROP INDEX IF EXISTS aws_compute_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_region;

DROP INDEX IF EXISTS aws_compute_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_compute_summary_by_service;

DROP INDEX IF EXISTS aws_storage_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary;

DROP INDEX IF EXISTS aws_storage_summary_account;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_account;

DROP INDEX IF EXISTS aws_storage_summary_region;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_region;

DROP INDEX IF EXISTS aws_storage_summary_service;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_storage_summary_by_service;

DROP INDEX IF EXISTS aws_database_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_database_summary;

DROP INDEX IF EXISTS aws_network_summary;
DROP MATERIALIZED VIEW IF EXISTS reporting_aws_network_summary;
            """
        ),
        migrations.AddField(
            model_name="awscostentrylineitemdailysummary", name="source_uuid", field=models.UUIDField(null=True)
        ),
        migrations.RunSQL(
            sql="""
CREATE MATERIALIZED VIEW reporting_aws_cost_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start)) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start)
)
;

CREATE UNIQUE INDEX aws_cost_summary
ON reporting_aws_cost_summary (usage_start)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_account AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), usage_account_id, account_alias_id) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        usage_account_id,
        account_alias_id,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), usage_account_id, account_alias_id
)
;

CREATE UNIQUE INDEX aws_cost_summary_account
ON reporting_aws_cost_summary_by_account (usage_start, usage_account_id, account_alias_id)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_service AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        product_family,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code, product_family
)
;

CREATE UNIQUE INDEX aws_cost_summary_service
ON reporting_aws_cost_summary_by_service (usage_start, product_code, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_cost_summary_by_region AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), region, availability_zone) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        region,
        availability_zone,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), region, availability_zone
)
;

CREATE UNIQUE INDEX aws_cost_summary_region
ON reporting_aws_cost_summary_by_region (usage_start, region, availability_zone)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.instance_type) AS id,
       c.usage_start,
       c.usage_start as usage_end,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code,
       c.source_uuid
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code,
                ARRAY_AGG (DISTINCT source_uuid) source_uuid
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) as resource_ids
           FROM (
                  SELECT usage_start,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary
    ON reporting_aws_compute_summary (usage_start, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_account AS (
SELECT ROW_NUMBER() OVER (ORDER BY c.usage_start, c.usage_account_id, c.account_alias_id, c.instance_type) as id,
       c.usage_start,
       c.usage_start AS usage_end,
       c.usage_account_id,
       c.account_alias_id,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code,
       c.source_uuid
  FROM (
         -- this group by gets the counts
         SELECT usage_start,
                usage_account_id,
                account_alias_id,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code,
                ARRAY_AGG (DISTINCT source_uuid) source_uuid
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                usage_account_id,
                account_alias_id,
                instance_type
       ) AS c
  JOIN (
         -- this group by gets the distinct resources running by day
         SELECT usage_start,
                usage_account_id,
                account_alias_id,
                instance_type,
                array_agg(distinct resource_id order by resource_id) as resource_ids
           FROM (
                  SELECT usage_start,
                         usage_account_id,
                         account_alias_id,
                         instance_type,
                         UNNEST(resource_ids) as resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= date_trunc('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
               usage_account_id,
               account_alias_id,
               instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.instance_type = r.instance_type
   AND (
         (c.usage_account_id = r.usage_account_id) OR
         (c.account_alias_id = r.account_alias_id)
       )
     )
  WITH DATA
    ;

CREATE UNIQUE INDEX aws_compute_summary_account
    ON reporting_aws_compute_summary_by_account (usage_start, usage_account_id, account_alias_id, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_region AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.region, c.availability_zone, c.instance_type) AS id,
       c.usage_start,
       c.usage_start AS usage_end,
       c.region,
       c.availability_zone,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code,
       c.source_uuid
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                region,
                availability_zone,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code,
                ARRAY_AGG (DISTINCT source_uuid) source_uuid
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                region,
                availability_zone,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                region,
                availability_zone,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) AS resource_ids
           from (
                  SELECT usage_start,
                         region,
                         availability_zone,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                region,
                availability_zone,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.region = r.region
   AND c.availability_zone = r.availability_zone
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary_region
    ON reporting_aws_compute_summary_by_region (usage_start, region, availability_zone, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_compute_summary_by_service AS(
SELECT ROW_NUMBER() OVER(ORDER BY c.usage_start, c.product_code, c.product_family, c.instance_type) AS id,
       c.usage_start,
       c.usage_start as usage_end,
       c.product_code,
       c.product_family,
       c.instance_type,
       r.resource_ids,
       CARDINALITY(r.resource_ids) AS resource_count,
       c.usage_amount,
       c.unit,
       c.unblended_cost,
       c.markup_cost,
       c.currency_code,
       c.source_uuid
  FROM (
        -- this group by gets the counts
         SELECT usage_start,
                product_code,
                product_family,
                instance_type,
                SUM(usage_amount) AS usage_amount,
                MAX(unit) AS unit,
                SUM(unblended_cost) AS unblended_cost,
                SUM(markup_cost) AS markup_cost,
                MAX(currency_code) AS currency_code,
                ARRAY_AGG (DISTINCT source_uuid) source_uuid
           FROM reporting_awscostentrylineitem_daily_summary
          WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
            AND instance_type IS NOT NULL
          GROUP
             BY usage_start,
                product_code,
                product_family,
                instance_type
       ) AS c
  JOIN (
        -- this group by gets the distinct resources running by day
         SELECT usage_start,
                product_code,
                product_family,
                instance_type,
                ARRAY_AGG(DISTINCT resource_id ORDER BY resource_id) as resource_ids
           from (
                  SELECT usage_start,
                         product_code,
                         product_family,
                         instance_type,
                         UNNEST(resource_ids) AS resource_id
                    FROM reporting_awscostentrylineitem_daily_summary
                   WHERE usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
                     AND instance_type IS NOT NULL
                ) AS x
          GROUP
             BY usage_start,
                product_code,
                product_family,
                instance_type
       ) AS r
    ON c.usage_start = r.usage_start
   AND c.product_code = r.product_code
   AND c.product_family = r.product_family
   AND c.instance_type = r.instance_type
       )
  WITH DATA
       ;

CREATE UNIQUE INDEX aws_compute_summary_service
    ON reporting_aws_compute_summary_by_service (usage_start, product_code, product_family, instance_type)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary
ON reporting_aws_storage_summary (usage_start, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_account AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), usage_account_id, account_alias_id, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        usage_account_id,
        account_alias_id,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), usage_account_id, account_alias_id, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_account
ON reporting_aws_storage_summary_by_account (usage_start, usage_account_id, account_alias_id, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_region AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), region, availability_zone, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        region,
        availability_zone,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), region, availability_zone, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_region
ON reporting_aws_storage_summary_by_region (usage_start, region, availability_zone, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_storage_summary_by_service AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code, product_family) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        product_family,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_family LIKE '%Storage%'
        AND unit = 'GB-Mo'
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code, product_family
)
;

CREATE UNIQUE INDEX aws_storage_summary_service
ON reporting_aws_storage_summary_by_service (usage_start, product_code, product_family)
;

CREATE MATERIALIZED VIEW reporting_aws_database_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_code IN ('AmazonRDS','AmazonDynamoDB','AmazonElastiCache','AmazonNeptune','AmazonRedshift','AmazonDocumentDB')
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code
)
;

CREATE UNIQUE INDEX aws_database_summary
ON reporting_aws_database_summary (usage_start, product_code)
;

CREATE MATERIALIZED VIEW reporting_aws_network_summary AS(
    SELECT row_number() OVER(ORDER BY date(usage_start), product_code) as id,
        date(usage_start) as usage_start,
        date(usage_start) as usage_end,
        product_code,
        sum(usage_amount) as usage_amount,
        max(unit) as unit,
        sum(unblended_cost) as unblended_cost,
        sum(markup_cost) as markup_cost,
        max(currency_code) as currency_code,
        ARRAY_AGG (DISTINCT source_uuid) source_uuid
    FROM reporting_awscostentrylineitem_daily_summary
    -- Get data for this month or last month
    WHERE product_code IN ('AmazonVPC','AmazonCloudFront','AmazonRoute53','AmazonAPIGateway')
        AND usage_start >= DATE_TRUNC('month', NOW() - '1 month'::interval)::date
    GROUP BY date(usage_start), product_code
)
;

CREATE UNIQUE INDEX aws_network_summary
ON reporting_aws_network_summary (usage_start, product_code)
;
"""
        ),
    ]
