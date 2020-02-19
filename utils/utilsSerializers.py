from django.core.serializers.python import Serializer
import json
from uuid import UUID


class GroupSerializer(Serializer):
    """
        This is the serializer to get the list of groups for the user
    """
    def end_object( self, obj ):
        self.objects.append( self._current )


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)



class UserSerializer(Serializer):
    
    def get_dump_object(self, obj):
        mapped_object = {
            'access': obj.access_token,
            'refresh': obj.refresh_token,
            'expiry': obj.access_token
        }

        return mapped_object