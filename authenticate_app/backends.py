from django.contrib.auth.backends import ModelBackend
from authenticate_app.models import User

class TenantUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, organization=None, **kwargs):
        try:
            # Lookup scoped to org — username only unique WITHIN an org
            # __iexact means "admin" and "Admin" both work
            user = User.objects.get(username__iexact=username, organization=organization)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None