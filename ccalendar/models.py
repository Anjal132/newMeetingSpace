from django.db import models
from users.models import User

# Create your models here.
class Google(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()
    email = models.EmailField(unique=True)
    # timezone = models.CharField(max_length=50, blank=True, null=True)


class Outlook(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()
    # email = models.EmailField(unique=True)