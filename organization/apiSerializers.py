from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from organization.models import Organization
# from users.v1.apiSerializers import CreateAdminSerializer
from users.models import User


class CreateAdminSerializer(serializers.ModelSerializer):
    """This is the serializer class to create the `New` user admin for a given company."""

    msg = 'The user with this email is already invited'
    usr = User.objects.all()
    email = serializers.EmailField(required=True, validators=[
                                   UniqueValidator(usr, msg)])

    class Meta:
        """ This is the Meta Class for Model Serializer"""

        model = User
        fields = ['email']

    def create(self, validated_data):
        return User.objects.create_company_admin(**validated_data)


class CreateCompanySerializer(serializers.ModelSerializer):
    """ This is the Serializer class to create a company. """
    company_admin = CreateAdminSerializer(many=True)

    class Meta:
        model = Organization
        fields = ('name', 'short_name', 'company_admin', 'on_trial', 'subscription_expiry', 'is_active')

    def create(self, validated_data):
        admin_list = validated_data.pop('company_admin')
        organization = Organization.objects.create(**validated_data)

        for admin in admin_list:
            email_admin = admin['email']
            admin = User.objects.create_company_admin(email=email_admin, organization=organization)
            organization.company_admin.add(admin)
        return organization

class CompanyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('name', 'short_name')



class CompanyStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('is_active', 'on_trial', 'subscription_expiry')

    