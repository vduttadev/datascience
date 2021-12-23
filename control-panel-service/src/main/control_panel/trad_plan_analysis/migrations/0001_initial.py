# Generated by Django 2.2 on 2019-08-28 22:30

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('message_id', models.UUIDField(primary_key=True, serialize=False)),
                ('input_data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('output_data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('status', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'trad_plan_analysis_opportunity',
            },
        ),
        migrations.CreateModel(
            name='ExistingPlan',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('analysis_finished', models.BooleanField(default=False)),
                ('analysis_results', models.TextField()),
                ('opportunity_id', models.UUIDField()),
                ('benefitplan_id', models.UUIDField()),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trad_plan_analysis.Message')),
            ],
            options={
                'db_table': 'trad_plan_analysis_existingplan',
            },
        ),
    ]