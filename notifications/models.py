from django.db import models
from users.models import User
from meeting.models import Details

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notfication_by')
    title = models.CharField(max_length=50)
    meeting = models.ForeignKey(Details, null=True, blank=True, on_delete=models.CASCADE)
    message = models.TextField()
    notification_type = models.CharField(max_length=50)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message
