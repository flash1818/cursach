# Generated manually for ListingStats

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("listings", "0005_notification_kind_and_related_client"),
    ]

    operations = [
        migrations.CreateModel(
            name="ListingStats",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("view_count", models.PositiveIntegerField(default=0)),
                ("inquiry_count", models.PositiveIntegerField(default=0)),
                ("first_view_at", models.DateTimeField(blank=True, null=True)),
                ("last_view_at", models.DateTimeField(blank=True, null=True)),
                (
                    "property",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="listing_stats",
                        to="listings.property",
                    ),
                ),
            ],
            options={
                "verbose_name": "Статистика объявления",
                "verbose_name_plural": "Статистика объявлений",
            },
        ),
    ]
