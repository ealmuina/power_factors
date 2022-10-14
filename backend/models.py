from django.db import models


class Plant(models.Model):
    name = models.CharField(max_length=256)


class Datapoint(models.Model):
    plant = models.ForeignKey('Plant', on_delete=models.CASCADE, related_name='datapoints')
    timestamp = models.DateTimeField(db_index=True)

    energy_expected = models.FloatField()
    energy_observed = models.FloatField()
    irradiation_expected = models.FloatField()
    irradiation_observed = models.FloatField()

    class Meta:
        unique_together = ('plant', 'timestamp')
