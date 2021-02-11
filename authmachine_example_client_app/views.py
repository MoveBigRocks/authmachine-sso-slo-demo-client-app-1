import json

from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import View, TemplateView

from authmachine_example_client_app.authmachine_client import AuthMachineClient
from authmachine_example_client_app.utils import clear_user_session


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        session = request.session
        if "user_info" in session and "token" in session:
            client = AuthMachineClient(self.request)
            token = session["token"]
            user_session = client.check_token_revoked_status(json.loads(token))
            if user_session and user_session["revoked"]:
                clear_user_session(request)
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
        clear_user_session(request)
        return redirect(reverse("index"))


class OIDCallbackView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        a_resp = client.get_authorization_response()
        token = client.get_access_token(a_resp)
        request.session["token"] = token.to_json()
        request.session["user_info"] = client.get_userinfo(a_resp)
        return redirect(reverse("index"))
