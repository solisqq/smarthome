from django.db import models

# Create your models here.
class KnownDevices(models.Model):
    name = models.CharField(max_length=128)
    uid = models.CharField(max_length=64)

class Patterns(models.Model):
    name = models.CharField(max_length=256)
    data = models.CharField(max_length=2048)
    deviceType = models.CharField(max_length=256)