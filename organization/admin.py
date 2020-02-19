from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'id',
        'short_name',
        'uid',
        'schema_name',
        'date_joined',
        'is_active',
    )
    list_filter = ('date_joined', 'is_active')
    search_fields = ('name',)