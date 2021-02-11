## AuthMachine Demo Client App: Django 

Link to application: [https://authmachine-client-example-1.herokuapp.com](https://authmachine-client-example-1.herokuapp.com/)



## Getting Started with OpenID Connect: Python (Django)

### Prerequisites


In this article we will use [Python](https://www.python.org/) (the code should be compatible with versions 3.5-3.7), 
[Django](https://www.djangoproject.com/) and [pyoidc](https://github.com/OpenIDC/pyoidc) library. Assuming you already 
have Python and pipenv installed, you can initialize your environment as:

`pipenv install Django oic`

### Authentication using the "Authorization Code" Flow
The authorization code flow works as follows:
- The client app redirects the user to authorization endpoint of AuthMachine
- AuthMachine performs the authentication and redirects user back to client app
- The client app queries the token endpoint of AuthMachine and gets an access token from it
- The client app queries the userinfo endpoint of AuthMachine using the access token and gets user's information from 
  it (profile, email, permissions, extra fields, etc)
- The client can check if the user is logged out from AuthMachine and finish client session

### Configuration
The client app requires the following configuration parameters set:
- AuthMachine URL
- AuthMachine Client ID
- AuthMachine Client Secret

Also optional parameters are
- AuthMachine API Token (in case you need to perform API requests)
In this example we'll set them using dotenv file:

```
AUTHMACHINE_URL=http://localhost:8000/
AUTHMACHINE_CLIENT_ID=test
AUTHMACHINE_CLIENT_SECRET=test
AUTHMACHINE_API_TOKEN=
```

In your code you can read these environment variables as follows (in settings.py file):

```
import os
AUTHMACHINE_URL = os.environ['AUTHMACHINE_URL']
AUTHMACHINE_CLIENT_ID = os.environ['AUTHMACHINE_CLIENT_ID']
AUTHMACHINE_CLIENT_SECRET = os.environ['AUTHMACHINE_CLIENT_SECRET']
AUTHMACHINE_API_TOKEN = os.environ.get('AUTHMACHINE_API_TOKEN')
```

### Identity Provider Discovery
AuthMachine supports dynimac discovery of Identity Provider configuration. This is very 
handy because you don't need to hardcode all AuthMachine endpoints in your client 
app - you just need to query the discovery URL once.

The code to perform the discovery is the following:

```
from django.conf import settings
from oic.oic import Client
from oic.utils.authn.client import ClientSecretBasic, ClientSecretPost

def get_client(self):
    client = Client(client_authn_method={
        'client_secret_post': ClientSecretPost,
        'client_secret_basic': ClientSecretBasic
    })
    client.provider_config(settings.AUTHMACHINE_URL)
    client.client_id = settings.AUTHMACHINE_CLIENT_ID
    client.client_secret = settings.AUTHMACHINE_CLIENT_SECRET
    client.verify_ssl = True
    return client
```

### Authorization Query
After you configured the client object you can get the Authorization URL to which you need to redirect the user to 
perform the authorization:

```
from oic import rndstr

def get_authorization_url(self):
    nonce = rndstr()

    args = {
        'client_id': self.client.client_id,
        'response_type': 'code',
        'scope': settings.AUTHMACHINE_SCOPE,
        'claims': json.dumps({
            'authmachine_permissions': ['object1', 'object2'],
        }),
        'nonce': nonce,
        'redirect_uri': self.host + reverse('auth_callback'),
        'state': 'some-state-which-will-be-returned-unmodified'
    }
    url = self.client.provider_info['authorization_endpoint'] + '?' + urlencode(args, True)
    return url
```

The authmachine_permissions claim is optional. For more info about it please refer to the 
[AuthMachine Permission System](https://authmachine.com/docs/authmachine-access-control-system/) doc.

The view code would look like:

```
**views.py**
from django.views.generic import View
from authmachine_example_client_app.authmachine_client import AuthMachineClient

class LoginView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        return redirect(client.get_authorization_url())

**urls.py**

from django.urls import path

from authmachine_example_client_app import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="login"),
]

```

### Decoding Authorization Response
Now you need to create a handler for the redirect URI, to which AuthMachine will redirect the user after the 
authorization procedure is completed. In this handler you need to obtain the access token and request user information. 
Let's create a method for it:

```
from oic.oauth2 import AuthorizationResponse

def get_authorization_response(self, client):
    authorization_response = client.parse_response(
        AuthorizationResponse,
        info=request.args,
        sformat='dict')
    return authorization_response
```

Let's create methods for obtaining Access Token and User Information:

```
def get_access_token(self, aresp):
    args = {
        'code': aresp['code'],
        'client_id': self.client.client_id,
        'client_secret': self.client.client_secret,
        'redirect_uri': self.host + reverse('auth_callback')
    }

    return self.client.do_access_token_request(
        scope=settings.AUTHMACHINE_SCOPE,
        state=aresp['state'],
        request_args=args,
        authn_method='client_secret_post')

def get_userinfo(self, authorization_response):
    user_info = self.client.do_user_info_request(
        state=authorization_response['state'],
        authn_method='client_secret_post')
    return user_info.to_dict()
```
Now we can assemble everything together in the redirect handler:
```
**urls.py**

urlpatterns += [
    path("oidc-callback", views.OIDCallbackView.as_view(), name="auth_callback"),
]

**views.py**
class OIDCallbackView(View):

    def get(self, request):
        client = AuthMachineClient(request)
        aresp = client.get_authorization_response()
        token = client.get_access_token(aresp)
        request.session["token"] = token.to_json()
        request.session["user_info"] = client.get_userinfo(aresp)
        return redirect(reverse("index"))
```

### Logout from the application
Now for logout you need to create a handler for logout redirect URL, to which AuthMachine will redirect the user after 
the logout procedure is completed. In this handler you need to obtain the access token and request user information. 
Let's create a method for it:

```
def get_logout_url(self):
    args = {
        'scope': settings.AUTHMACHINE_SCOPE,
        'post_logout_redirect_uri': self.host + reverse('auth_logout_callback'),
        'state': 'some-state-which-will-be-returned-unmodified',
        'revoke_tokens': 1 # optional params (set 1 if you want to revoke all session tokens, if not - set 0 or not user this param)
    }
    url = self.client.provider_info['end_session_endpoint'] + '?' + urlencode(args, True)
    return url
```
Now we can assemble everything together in the redirect handler:
```
**urls.py**

urlpatterns += [
    path("oidc-logout-callback", views.OIDLogoutCallbackView.as_view(), name="auth_logout_callback"),
]

**views.py**

class OIDLogoutCallbackView(View):

    def get(self, request):
        clear_user_session(request)
        return redirect(reverse("index"))
```

### Check token status
You can check if auth tokens still working (not revoked) in the AuthMachine. The AuthMachine provide URL which user 
can check token status. In this handler you need to obtain the access token, request user information and 
set the "check_token_revoked" value for "grant_type" property. 
Let's create a method for it:
```
def check_token_revoked_status(self, access_token):
    args = {
        'client_id': self.client.client_id,
        'client_secret': self.client.client_secret,
        'access_token': access_token,
        'grant_type': 'check_token_revoked',
    }
    response = requests.request(method="POST",
                                url=os.path.join(settings.AUTHMACHINE_URL, "oidc/token"),
                                data=args)

    if response.status_code == 200:
        data = response.json()
        return data["revoked"] if "revoked" in data else False
    else:
        return False
```
