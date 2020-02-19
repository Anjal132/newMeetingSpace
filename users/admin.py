from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'id',
        'uid',
        'last_login',
        'date_joined',
        'is_staff',
        'is_active',
        'is_verified',
        'is_superuser',
    )
    list_filter = (
        'last_login',
        'is_superuser',
        'is_staff',
        'is_active',
        'is_verified',
        'date_joined',
    )
    # raw_id_fields = ('groups', 'user_permissions', 'belongs_to')