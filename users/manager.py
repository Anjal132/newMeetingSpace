from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import Group
from django.utils.crypto import get_random_string
from utils.otherUtils import send_mail_employee


class UsersManager(BaseUserManager):
    '''
    This is the custom User Manager, inherited from `BaseUserManager` for our custom user model.

    This Manager handles the creation of Super User, Staff user, and other types of user.
    '''

    def create_user(self, email, organization, password=None):
        """Create and return a `User` with an email."""
        
        if email is None:
            raise TypeError('Users must have an email address.')
        
        user = self.model(email=self.normalize_email(email))
        user.set_password(get_random_string())
        user.temp_name = organization.schema_name

        user.save(using=self._db)
        user.belongs_to.add(organization)


        employee_group, created = Group.objects.get_or_create(name='Employee_User')
        employee_group.user_set.add(user)

        send_mail_employee(user, organization)

        return user
        

    def create_company_admin(self, email, organization, password=None):
        """Create and return a `User` with an email."""
        
        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(email=self.normalize_email(email))
        user.set_password(get_random_string())
        user.temp_name = organization.schema_name

        user.save(using=self._db)
        user.belongs_to.add(organization)

        admin_group, created = Group.objects.get_or_create(name='Admin_User')
        admin_group.user_set.add(user)

        employee_group, created = Group.objects.get_or_create(name='Employee_User')
        employee_group.user_set.add(user)


        return user


    def create_staff(self, email, password):
        """
        Create and return a `User` with Staff (admin) permissions.
        """
        if password is None:
            raise TypeError('Staff Users must have a password.')

        user = self.model(email=self.normalize_email(email))
        user.set_password(get_random_string())
        user.temp_name = 'public'
        user.is_staff       = True
        user.is_active      = True
        user.is_verified    = True
        user.is_superuser   = False

        user.save(using=self._db)

        staff_group, created = Group.objects.get_or_create(name='Staff_User')
        staff_group.user_set.add(user)

        return user

    
    def create_superuser(self, email, password):
        """
        Create and return a `User` with superuser (admin) permissions.
        """
        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)
        user.temp_name = 'public'
        user.is_superuser   = True
        user.is_staff       = True
        user.is_active      = True
        user.is_verified    = True

        user.save(using=self._db)

        super_user_group, created = Group.objects.get_or_create(name='Super_User')
        super_user_group.user_set.add(user)

        staff_group, created = Group.objects.get_or_create(name='Staff_User')
        staff_group.user_set.add(user)

        return user