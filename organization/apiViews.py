from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from organization.apiSerializers import (CompanyProfileSerializer,
                                         CompanyStatusSerializer,
                                         CreateCompanySerializer)
from organization.models import Organization
from permission.permissions import IsCompanyAdmin, IsStaffUser
from utils.otherUtils import send_mail_admin
from utils.utils import get_user

# Create your views here.


class CreateCompanyAPIView(generics.CreateAPIView):

    permission_classes = (IsAuthenticated, IsStaffUser)
    serializer_class = CreateCompanySerializer

    def perform_create(self, serializer):
        print(self.request.data)
        short_name = self.request.data['short_name']
        short_name = short_name.replace(" ", "")
        schema_name = short_name.lower()+'schema'
        domain_url = 'www.'+short_name+'.com'
        organization = serializer.save(
            schema_name=schema_name, domain_url=domain_url)
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


class CompanyProfileAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsCompanyAdmin)
    serializer_class = CompanyProfileSerializer

    def get_object(self):
        user = get_user(self.request)
        
        if user.temp_name == 'public':
            return Organization.objects.none()
        return Organization.objects.get(schema_name=user.temp_name)
