import datetime
import uuid
import pytz

from django.db import models
from tenant_schemas.models import TenantMixin


class Organization(TenantMixin):
    """
        This is the model, which represents the company details like, 
            `company_name`, `schema_name`, `company_admin`, `company_unique_identifier`.
    """
    name = models.CharField(max_length=70, blank=False)
    short_name = models.CharField(max_length=15, blank=False, unique=True)
    uid = models.UUIDField(default=uuid.uuid4, unique=True,
                           editable=False, db_index=True)
    company_admin = models.ManyToManyField(
        to='users.User', blank=True, related_name='admin')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    on_trial = models.BooleanField(default=False)
    subscription_expiry = models.DateField(
        default=(datetime.datetime.now(pytz.UTC)+datetime.timedelta(weeks=1)).date())
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(verbose_name='companyLogo', blank=True, null=True)
    street = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=25, blank=True, null=True)
    country = models.CharField(max_length=25, blank=True, null=True)
    color = models.CharField(max_length=25, blank=True, null=True)
    website = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.short_name
