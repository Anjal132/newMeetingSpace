from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.apiSerializers import (CompanyProfileSerializer,
                                         CompanyStatusSerializer,
                                         CreateCompanySerializer)
from organization.models import Organization
from permission.permissions import IsCompanyAdmin, IsStaffUser
from users.models import User
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
        print(self.request.data)
        user = get_user(self.request)
        
        if user.temp_name == 'public':
            return Organization.objects.none()
        return Organization.objects.get(schema_name=user.temp_name)
    

class CompanyDashboardAPIVew(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request, *args, **kwargs):
        total_companies = Organization.objects.all().exclude(schema_name='public').count()
        active_companies = Organization.objects.filter(is_active=True).exclude(schema_name='public').count()
        on_trial_companies = Organization.objects.filter(on_trial=True).exclude(schema_name='public').count()
        total_users = User.objects.all().exclude(temp_name='public').count()
        total_active_users = User.objects.filter(is_active=True).exclude(temp_name='public').count()
        company_users_count = []
        all_companies = Organization.objects.all().exclude(schema_name='public')

        for company in all_companies:
            data = {
                'company_name': company.name,
                'active_users': User.objects.filter(is_active=True, temp_name=company.schema_name).count()
            }
            company_users_count.append(data)
        
        return Response({
            'total_companies':total_companies,
            'active_companies': active_companies, 
            'on_trial_companies': on_trial_companies,
            'total_users': total_users,
            'total_active_users': total_active_users,
            'company_users': company_users_count
        }, status=status.HTTP_200_OK)
