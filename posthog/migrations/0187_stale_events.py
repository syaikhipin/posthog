# Generated by Django 3.2.5 on 2021-11-30 08:23
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

from posthog.constants import AnalyticsDBMS


def set_created_at(apps, schema_editor):

    try:
        from ee.clickhouse.client import sync_execute
    except ImportError:
        sync_execute = None  # type: ignore

    EventDefinition = apps.get_model("posthog", "EventDefinition")
    for instance in EventDefinition.objects.filter(created_at=None):
        created_at = None
        if settings.PRIMARY_DB == AnalyticsDBMS.POSTGRES:
            Event = apps.get_model("posthog", "Event")
            event_instance = (
                Event.objects.select("timestamp")
                .filter(team=instance.team, name=instance.name)
                .order_by("timestamp")
                .first()
            )
            if event_instance:
                created_at = event_instance.timestamp
        else:
            if sync_execute:
                result = sync_execute(
                    "SELECT timestamp FROM events where team_id=%(team_id)s AND event=%(event)s"
                    " order by timestamp limit 1",
                    {"team_id": instance.team.pk, "event": instance.name,},
                )
            if result:
                created_at = result[0][0]

        if created_at:
            instance.created_at = created_at
            instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0186_insight_refresh_attempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventdefinition",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AddField(
            model_name="eventdefinition", name="last_seen_at", field=models.DateTimeField(default=None, null=True),
        ),
        migrations.RunPython(set_created_at, migrations.RunPython.noop),
    ]
