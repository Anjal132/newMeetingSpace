from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from permission.permissions import IsEmployee
from utils.utils import get_user

from .models import Google, Outlook
from .serializers import GoogleCalendarSerializer
from .utils import get_token_from_code, get_token_from_code_google

# Create your views here.
class GoogleTokenStoreAPIView(APIView):
    permission_classes = (IsAuthenticated, IsEmployee)
    serializer_class = GoogleCalendarSerializer

    def post(self, request, *args, **kwargs):
        auth_code = request.data['code']
        email = request.data['email']

        redirect_uri = 'http://localhost:8000/api/calendar'
        token = get_token_from_code_google(auth_code, redirect_uri)

        user = get_user(request)

        try:
            google = Google(user=user, access=token['access_token'], refresh=token['refresh_token'], email=email)
            google.save()

            return JsonResponse({'Message': 'Successfully Authenticated'}, status=201)
        except IntegrityError:
            return JsonResponse({'Message': 'The email has already been added. Please add a new email.'}, status=400)
        except:
            return JsonResponse({'Message': 'An Internal error occured. Please try again later'}, status=400)

    def get(self, request, *args, **kwargs):
        return JsonResponse({'Status': 400, 'Message': 'Get method not allowed'}, status=400)


class GoogleLogoutAPIView(APIView):
    permission_classes = (IsAuthenticated, IsEmployee)

    def delete(self, request, *args, **kwargs):
        user = get_user(request)

        try:
            Google.objects.get(user=user).delete()
            return JsonResponse({'Status': 200, 'Message': 'Successfully removed Google account'}, status=201)
        except:
            return JsonResponse({'Status': 400, 'Message': 'Error while removing Google account'}, status=400)


class OutlookTokenStoreAPIView(APIView):
    # authentication_classes = (IsAuthenticated, IsEmployee)
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        auth_code = request.data['auth_code']

        redirect_uri = 'http://localhost:8050/tutorial/gettoken'

        token = get_token_from_code(auth_code, redirect_uri)

        user = get_user(request)
        
        try:
            outlook = Outlook(user=user, access=token['access_token'], refresh=token['refresh_token'])
            outlook.save()

            return JsonResponse({'Message': 'Successfully Authenticated'}, status=201)
        except:
            return JsonResponse({'Message': 'An error occured. Please try again.'}, status=400)


    def get(self, request, *args, **kwargs):
        return JsonResponse({'Status':400, 'Message': 'Get method not allowed'}, status=400)
