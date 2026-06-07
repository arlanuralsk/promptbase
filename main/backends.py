from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .auth_utils import looks_like_email, normalize_phone
from .models import UserProfile


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = (username or kwargs.get("email") or "").strip()
        if not identifier or password is None:
            return None

        UserModel = get_user_model()
        candidates = []

        if looks_like_email(identifier):
            candidates.extend(UserModel.objects.filter(email__iexact=identifier))
            candidates.extend(UserModel.objects.filter(username__iexact=identifier))
        else:
            phone = normalize_phone(identifier)
            profile_user_ids = UserProfile.objects.filter(phone=phone).values_list("user_id", flat=True)
            candidates.extend(UserModel.objects.filter(id__in=profile_user_ids))
            candidates.extend(UserModel.objects.filter(username__iexact=phone))

        seen = set()
        for user in candidates:
            if user.pk in seen:
                continue
            seen.add(user.pk)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
