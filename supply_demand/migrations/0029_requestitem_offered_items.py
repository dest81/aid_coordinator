# Generated by Django 4.0.7 on 2022-09-14 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("supply_demand", "0028_offeritem_rejected"),
    ]

    operations = [
        migrations.AddField(
            model_name="requestitem",
            name="offered_items",
            field=models.ManyToManyField(
                related_name="requested_items",
                through="logistics.Claim",
                to="supply_demand.offeritem",
            ),
        ),
    ]
