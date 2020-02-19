from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from organization.apiSerializers import CreateCompanySerializer, CompanyStatusSerializer
from organization.models import Organization
from permission.permissions import IsStaffUser
from utils.otherUtils import send_mail_admin

# Create your views here.


class CreateCompanyAPIView(generics.CreateAPIView):

    permission_classes = (IsAuthenticated, IsStaffUser)
    serializer_class = CreateCompanySerializer

    def perform_create(self, serializer):
        print(self.request.data)
        short_name = self.request.data['short_name']
        schema_name = short_name.lower()+'schema'
        domain_url = 'www.'+short_name+'.com'
        organization = serializer.save(schema_name=schema_name, domain_url=domain_url)
        send_mail_admin(organization.company_admin.all(), organization.name)


class ListCompanyAPIView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsStaffUser)
    serializer_class = CreateCompanySerializer

    def get_queryset(self):
        return Organization.objects.exclude(schema_name='public')


class CompanyDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsStaffUser)

    serializer_class = CompanyStatusSerializer
    lookup_field = 'short_name'

    def get_queryset(self):
        short_name = self.kwargs['short_name']
        return Organization.objects.filter(short_name=short_name)
