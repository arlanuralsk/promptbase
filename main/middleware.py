from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


class RequireLoginMiddleware:
    """Redirect guests to the welcome auth screen before using the app."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path

        if path == "/":
            return self.get_response(request)

        if path.startswith("/accounts/login/") or path.startswith("/accounts/signup/"):
            return self.get_response(request)

        if path.startswith("/admin/") or path.startswith("/static/"):
            return self.get_response(request)

        if path.startswith("/payments/webhook/"):
            return self.get_response(request)

        query = urlencode({"tab": "login", "next": request.get_full_path()})
        return redirect(f"{reverse('main:home')}?{query}")
