# Generated by Django 2.2.4 on 2019-10-30 17:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_auto_20191022_1635'),
        ('reporting', '0078_gcpcostentrybill_gcpcostentrylineitemdaily_gcpproject'),
    ]

    operations = [
        migrations.AddField(
            model_name='azuremeter',
            name='provider',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.Provider'),
        ),
    ]