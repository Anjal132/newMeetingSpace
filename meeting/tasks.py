from __future__ import absolute_import, unicode_literals

from celery import task
from django.db import connection
from ccalendar.models import Google
from ccalendar.utils import refresh_token_from_google
from organization.models import Organization


@task
def refresh_token_google():
    redirect_uri = 'http://localhost:8000/api/calendar'
    connection.set_schema_to_public()

    all_schemas = Organization.objects.all()

    for schema in all_schemas:
        schema_name = schema.schema_name
        connection.set_schema(schema_name=schema_name)

        if schema_name != 'public':
            user_tokens = Google.objects.all()

            for tokens in user_tokens:
                refresh_token = tokens.refresh
                token = refresh_token_from_google(refresh_token, redirect_uri)
                tokens.access = token['access_token']
                tokens.save()
