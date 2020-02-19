from datetime import datetime

from django.contrib.auth import user_logged_in
from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from organization.models import Organization
from staffProfile.models import StaffProfile
from userProfile.models import UserProfile
from users.models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, *args, **kwargs):
    # Notice that we're checking for `created` here. We only want to do this
    # the first time the `User` instance is created. If the save that caused
    # this signal to be run was an update action, we know the user already
    # has a profile.

    if instance and created:
        if instance.is_staff:
            instance.profile = StaffProfile.objects.create(user=instance)
        else:
            org = Organization.objects.get(schema_name=instance.temp_name)
            connection.set_tenant(org)
            instance.profile = UserProfile.objects.create(user=instance)
            connection.set_schema_to_public()


@receiver(user_logged_in, sender=User)
def log_user_logged_in(sender, user, request, **kwargs):
    user.last_login = datetime.now()


@receiver(post_save, sender=Organization)
def active_inactive_users(sender, instance, created, *args, **kwargs):

    if not created and instance:
        schema_name = instance.short_name + 'schema'
        # print(instance.is_active)
        User.objects.filter(temp_name=schema_name).update(is_verified=instance.is_active)
        
