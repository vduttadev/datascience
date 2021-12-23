
from django.db import models
from django.contrib.postgres import fields as pg_fields


class Message(models.Model):
    message_id = models.UUIDField(primary_key=True)
    input_data = pg_fields.JSONField()
    output_data = pg_fields.JSONField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = "trad_plan_analysis_opportunity"


class ExistingPlan(models.Model):
    id = models.UUIDField(primary_key=True)
    analysis_finished = models.BooleanField(default=False)
    analysis_results = models.TextField()
    opportunity_id = models.UUIDField(primary_key=False)
    benefitplan_id = models.UUIDField(primary_key=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    class Meta:
        db_table = "trad_plan_analysis_existingplan"
