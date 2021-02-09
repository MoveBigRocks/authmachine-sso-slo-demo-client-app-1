from oic.oic import Client
from oic.utils.authn.client import ClientSecretBasic, ClientSecretPost

AUTHMACHINE_URL = "http://localhost:8000/"
AUTHMACHINE_CLIENT_ID = "test"
AUTHMACHINE_CLIENT_SECRET = "test"
AUTHMACHINE_API_TOKEN = ""


def get_client():
    client = Client(client_authn_method={
        'client_secret_post': ClientSecretPost,
        'client_secret_basic': ClientSecretBasic
    })
    client.provider_config(AUTHMACHINE_URL)
    client.client_id = AUTHMACHINE_CLIENT_ID
    client.client_secret = AUTHMACHINE_CLIENT_SECRET
    return client


def clear_user_session(request):
    if "user_info" in request.session:
        request.session.modified = True
        del request.session["user_info"]
        if "token" in request.session:
            del request.session["token"]
