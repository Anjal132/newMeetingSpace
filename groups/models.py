from django.db import models
from users.models import User

class Group(models.Model):
    group_name = models.CharField(max_length=50)
    leader = models.ForeignKey(User, on_delete=models.CASCADE)
    group_members = models.ManyToManyField(User, related_name='group_members')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.group_name
