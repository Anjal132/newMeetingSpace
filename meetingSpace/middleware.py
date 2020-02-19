from tenant_schemas.middleware import BaseTenantMiddleware
from tenant_schemas.utils import get_public_schema_name

class CustomHeaderMiddleware(BaseTenantMiddleware):
    def get_tenant(self, model, hostname, request):
        print(request.META.get('HTTP_X_DTS_SCHEMA'))
        # print(request.headers)
        schema_name = request.META.get('HTTP_X_DTS_SCHEMA', get_public_schema_name())
        return model.objects.get(schema_name=schema_name)