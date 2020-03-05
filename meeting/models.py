import uuid

from django.contrib.postgres.fields import ArrayField
from django.db import models

from property.models import Room
from users.models import User


class Host(models.Model):

    '''
    This is the model for hosting meeting
    '''

    MEETING_STATUS = (
        ('DR', 'Draft'),
        ('IN', 'Initiated'),
        ('CO', 'Completed'),
        ('FI', 'Finalized'),
        ('ON', 'Ongoing'),
        ('CA', 'Canceled')
    )

    MEETING_TYPE = (
        ('PV', 'Private'),
        ('PU', 'Public'),
        ('CF', 'Conference')
    )

    host = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='host')
    title = models.CharField(max_length=250)
    uid = models.UUIDField(default=uuid.uuid4, db_index=True,
                           primary_key=True, editable=False)
    agenda = models.TextField()
    duration = models.DurationField()
    start_date = models.DateField()
    end_date = models.DateField()
    meeting_status = models.CharField(
        max_length=2, choices=MEETING_STATUS, default='DR')
    type = models.CharField(max_length=2, choices=MEETING_TYPE, default='PU')
    participant = models.ManyToManyField(
        User, related_name='participant', through='Status')
    participant_email = ArrayField(models.EmailField(), blank=True, null=True)
    timezone = models.CharField(max_length=50)
    updated_at = models.DateTimeField(auto_now=True)

    def get_title(self):
        return self.title

    def get_host(self):
        return self.host

    class Meta:
        get_latest_by = "start_date"


class Status(models.Model):
    PARTICIPANT_STATUS = (
        ('PE', 'Pending'),
        ('AC', 'Accepted'),
        ('DE', 'Declined'),
        ('PO', 'Postponed')
    )

    meeting_host = models.ForeignKey(
        Host, on_delete=models.CASCADE, related_name='meeting_to_participant')
    participant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='participant_to_meeting')
    participant_status = models.CharField(
        max_length=2, choices=PARTICIPANT_STATUS, default='PE')
    participant_message = models.TextField(blank=True, null=True)


class Details(models.Model):
    meeting = models.OneToOneField(Host, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
