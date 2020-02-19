from django.contrib.postgres.fields import JSONField
from django.db import models


class Property(models.Model):
    IS_AVAILABLE = (
        ('A', 'Available'),
        ('UC', 'Under Construction'),
        ('UR', 'Under Renovation'),
        ('SD', 'Shut Down'),
    )
    name = models.CharField(max_length=100, blank=False)
    street = models.CharField(max_length=100, blank=False)
    zip_code = models.CharField(max_length=15, blank=False)
    city = models.CharField(max_length=25, blank=False)
    country = models.CharField(max_length=25, blank=False)
    latitude = models.CharField(max_length=50, blank=True, null=True)
    longitude = models.CharField(max_length=50, blank=True, null=True)
    is_shared = models.BooleanField(default=False)
    no_of_floors = models.CharField(max_length=25, blank=True, null=False)
    shared_company_floors = JSONField(blank=True, null=True)
    is_available = models.CharField(max_length=2, choices=IS_AVAILABLE)

    def __str__(self):
        return self.name


class Department(models.Model):
    department_name = models.CharField(max_length=50)

    def __str__(self):
        return self.department_name


class Room(models.Model):
    ROOM_TYPE = (
        ('CR', 'Confrence Room'),
        ('MR', 'Meeting Room'),
        ('PO', 'Private Office'),
        ('DH', 'Discussion Hall'),
        ('BR', 'Break Room')
    )

    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='room')
    room_number = models.CharField(max_length=50)
    floor = models.CharField(max_length=50)
    room_amenity = JSONField(blank=True, null=True)
    room_type = models.CharField(max_length=2, choices=ROOM_TYPE)
    room_description = models.TextField(blank=True, null=True)
    room_capacity = models.IntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.room_number
