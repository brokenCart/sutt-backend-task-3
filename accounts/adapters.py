from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import PermissionDenied

ALLOWED_DOMAINS = {
    'pilani.bits-pilani.ac.in',
    'goa.bits-pilani.ac.in',
    'hyderabad.bits-pilani.ac.in'
}

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.account.extra_data.get("email")

        if not email:
            raise PermissionDenied('No email received from Google.')

        domain = email.split('@')[-1]
        if domain not in ALLOWED_DOMAINS:
            raise PermissionDenied('Only BITS Pilani Google accounts are allowed.')
