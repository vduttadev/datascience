from django.db import models
from django.contrib.postgres import fields as pg_fields


class Message(models.Model):
    message_id = models.UUIDField(primary_key=True)
    opportunity_id = models.UUIDField(primary_key=False)
    input_data = pg_fields.JSONField()
    output_data = pg_fields.JSONField()
    status = models.CharField(max_length=20)

    class Meta:
        db_table = "bind_plan_analysis_opportunity"
