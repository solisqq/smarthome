from django.db import models

# Create your models here.
class KnownDevice(models.Model):
    prod_id = models.CharField(max_length=64)
    name = models.CharField(max_length=128)