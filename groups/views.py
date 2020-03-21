from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from groups.models import Group
from groups.serializers import GroupSerializer, GroupDetailSerializer
from permission.permissions import IsEmployee
from users.models import User
from utils.utils import get_user

class GroupAPIView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = GroupSerializer

    def list(self, request):
        try:
            queryset = self.get_queryset()
            serializer = GroupDetailSerializer(queryset, many=True)
            if not serializer.data:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError:
            return Response({'Message': 'Validation Error. Please retry again later'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        user = get_user(request)
        try:
            all_members = request.data['group_members']

            for group_member in all_members:
                member = User.objects.get(id=group_member)

                if user == member:
                    return Response({'Message': 'Cannot add yourself to group'}, status=status.HTTP_406_NOT_ACCEPTABLE)

                if user.temp_name != member.temp_name:
                    return Response({'Message': 'All members must be of the same organization'}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response({'Message': 'Group Successfully created'}, status=status.HTTP_201_CREATED)

        except KeyError:
            return Response({'Message': 'Why are you trying to create a group without any members?'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        except ObjectDoesNotExist:
            return Response({'Message': 'Error while adding group members'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({'Message': 'Cannot validate data'}, status=status.HTTP_400_BAD_REQUEST)


    def get_queryset(self):
        user = get_user(self.request)
        return Group.objects.filter(leader=user)

    def get_serializer_context(self):
        user = get_user(self.request)
        return {'leader': user}
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return GroupDetailSerializer

        if self.request.method == 'POST':
            return GroupSerializer
        return GroupSerializer


class RemoveGroupAPIView(RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated, IsEmployee]
    serializer_class = GroupSerializer
    
    def get_queryset(self):
        user = get_user(self.request)
        group_id = self.kwargs['pk']

        if group_id is not None:
            group = Group.objects.filter(id=group_id)

            if group.exists() and group[0].leader == user:
                return Group.objects.filter(id=group_id)
        return Group.objects.none()