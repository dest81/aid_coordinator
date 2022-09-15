# Generated by Django 4.0.7 on 2022-09-17 16:35

from django.db import migrations


def fill_shipment_locations(apps, schema_editor):
    Shipment = apps.get_model("logistics", "Shipment")

    for shipment in Shipment.objects.all():
        shipment.to_location_id = 3
        shipment.from_location_id = 5


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0024_remove_shipment_current_location_and_more'),
    ]

    operations = [
        migrations.RunPython(fill_shipment_locations),
    ]
