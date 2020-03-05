from django.db import models
import datetime
from property.models import Department, Property, Room

# Create your models here.


class UserProfile(models.Model):
    '''
        This is the model to represent the profile of each employee
    '''
    user = models.OneToOneField(
        'users.User', on_delete=models.CASCADE, related_name='userprofile')
    building = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='building', null=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, related_name='department', null=True)
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name='room', null=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    internationalization = models.CharField(max_length=2, default='EN')
    profile_pics = models.ImageField(verbose_name='userPics', blank=True, null=True)
    office_start_time = models.TimeField(default=datetime.time(10, 0))
    office_end_time = models.TimeField(default=datetime.time(17, 0))
    timezone = models.CharField(max_length=50, default='UTC')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email

    @property
    def get_full_name(self):
        if not self.first_name:
            return None

        if self.middle_name:
            return self.first_name + ' ' + self.middle_name + ' ' + self.last_name
        return self.first_name + ' ' + self.last_name

    @property
    def get_room(self):
        return self.room

    @property
    def get_timezone(self):
        return self.timezone
