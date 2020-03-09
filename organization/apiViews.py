from django.db.models import Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.apiSerializers import (CompanyProfileSerializer,
                                         CompanyStatusSerializer,
                                         CreateCompanySerializer)
from organization.models import Organization
from permission.permissions import IsCompanyAdmin, IsStaffUser
from meeting.models import Host, Status, Details
from property.models import Room, RoomBooking
from users.models import User
from utils.otherUtils import send_mail_admin
from utils.utils import get_user
import datetime
import pytz

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
        print(self.request.data)
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
    


'''
Super admin dashboard
'''
class CompanyDashboardAPIVew(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]
    
    def get(self, request, *args, **kwargs):
        limit = request.query_params.get('limit', None)

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
                'active_users': User.objects.filter(is_active=True, temp_name=company.schema_name).count(),
                'on_trial': company.on_trial
            }
            company_users_count.append(data)

        company_users_count = sorted(company_users_count, key=lambda i: i['active_users'],reverse=True)
        
        if limit is not None:
            try:
                limit = int(limit)
                company_users_count = company_users_count[:limit]
            except ValueError:
                return Response({'Message': 'limit must be int'}, status=status.HTTP_400_BAD_REQUEST)
        
        response = {
            'total_companies': total_companies,
            'active_companies': active_companies,
            'on_trial_companies': on_trial_companies,
            'total_users': total_users,
            'total_active_users': total_active_users,
            'company_users': company_users_count
        }

        return Response(response, status=status.HTTP_200_OK)


'''
Company Admin Dashboard
'''

class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompanyAdmin]
    def get(self, request, *args, **kwargs):
        limit = request.query_params.get('limit', None)
        year = request.query_params.get('year', None)

        if year is not None:
            try:
                year = int(year)
            except ValueError:
                return Response({'Message': 'Year must be string'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            year = datetime.datetime.now(pytz.UTC)
            year = year.year



        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                return Response({'Message': 'limit must be integer or None'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            limit = 50

        room_bookings = RoomBooking.objects.values_list('room').annotate(room_count=Count('room')).order_by('-room_count')
        
        room_with_most_meetings = []
        
        total_number_of_meetings = 0
        for key, value in room_bookings:
            total_number_of_meetings += value

            

        for room_booking in room_bookings:
            room = Room.objects.get(id=room_booking[0])

            most_used_room = {
                'room_number': room.room_number,
                'building': room.property.name,
                'floor': room.floor,
                'number_of_meetings_held': room_booking[1],
                'percent_of_meetings_held': '{0}'.format(round((room_booking[1]/total_number_of_meetings)*100, 0)),
                'capacity': room.room_capacity
            }
            
            room_with_most_meetings.append(most_used_room)
        
        all_meetings = Host.objects.exclude(meeting_status__in=['DR', 'CA'])

        members = 0
        for meeting in all_meetings:
            if meeting.participant_email is not None:
                members += len(meeting.participant_email)
            
            participants = Status.objects.filter(meeting_host=meeting).count()
            members = participants + members + 1
        

        number_of_meetings_per_month = []
        number_of_meetings_per_month.append({'year': year})
        
        for i in range(1, 13):
            meetings_in_month = Details.objects.filter(meeting_date__year=year, meeting_date__month=i).count()

            meeting_per_month = {
                'month': '{0}'.format(i),
                'meetings_in_month': meetings_in_month,
            }

            number_of_meetings_per_month.append(meeting_per_month)
        return Response({
            'rooms_with_most_meetings': room_with_most_meetings[:limit],
            'average_number_of_users_per_meeting': round(members/len(all_meetings), 2),
            'meetings_per_month': number_of_meetings_per_month,
            'number_of_ongoing_meetings': 5,
            'booked_rooms': 10
        }, status=status.HTTP_200_OK)
