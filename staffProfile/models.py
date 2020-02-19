from django.db import models

class StaffProfile(models.Model):
    '''
        This is the model to represent the profile of each employee
    '''
    user = models.OneToOneField(
        to='users.User', on_delete=models.CASCADE, related_name='staffprofile')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    internationalization = models.CharField(max_length=2)
    profile_pics = models.ImageField(verbose_name='userPics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email
