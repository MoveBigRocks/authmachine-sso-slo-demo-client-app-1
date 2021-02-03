from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View, TemplateView

from authmachine_example_client_app.authmachine_client import AuthMachineClient


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_info"] = self.request.session.get("user_info")
        return context


class LoginView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        return redirect(client.get_authorization_url())


class LogoutView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        return redirect(client.get_logout_url())


class OIDLogoutCallbackView(View):

    def get(self, request):
        if "user_info" in request.session:
            request.session.modified = True
            del request.session["user_info"]
        return redirect(reverse("index"))


class OIDCallbackView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        aresp = client.get_authorization_response()
        request.session["user_info"] = client.get_userinfo(aresp)
        return redirect(reverse("index"))
