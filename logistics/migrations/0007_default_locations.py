# Generated by Django 4.0.3 on 2022-04-21 16:50

from django.db import migrations


def create_locations(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    # noinspection PyPep8Naming
    Location = apps.get_model("logistics", "Location")
    Location.objects.using(db_alias).create(name="Donor")
    Location.objects.using(db_alias).create(name="Requester")


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0006_shipment_current_location'),
    ]

    operations = [
        migrations.RunPython(create_locations),
    ]
