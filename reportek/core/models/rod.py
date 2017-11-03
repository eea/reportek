from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=20)


class Country(models.Model):
    # root URL http://rod.eionet.europa.eu/spatial/
    class Meta:
        verbose_name_plural = 'countries'
    iso = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=60)


class Issue(models.Model):
    """Environmental issues"""
    name = models.CharField(max_length=60)

# class Obligation(models.Model):


