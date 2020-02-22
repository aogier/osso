'''
Created on 17 feb 2020

@author: Alessandro Ogier <alessandro.ogier@gmail.com>
'''

import logging

from authlib.integrations.starlette_client import OAuth
from starlette.applications import Starlette
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette_authlib.middleware import AuthlibMiddleware
import yaml


config = Config(".env")  # pylint: disable=invalid-name
oauth = OAuth(config)

CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

NGINX_QUERY_PARAM = 'rd'

_CONFIG = '''

#TBD
log_level: debug

jwt_secret:
  type: string
  value: a_secret_jwt_secret
#   type: keyfile
#   path: /path/to/x509pem

totp:
  issuer_template: ciaone
  
'''


_POLICIES = '''

default_policy: aieie

access_control:

  google.dev.scimmia.net:
    - name: authenticated admins
      policy: require_2fa
      subjects:
        - group:admin

'''
# XXX: rtfm @https://msg.pyyaml.org/load pylint: disable=fixme
POLICIES = yaml.load(_POLICIES, Loader=yaml.FullLoader)

templates = Jinja2Templates(directory='templates')


async def login(request):

    redirect_uri = request.url_for('auth')

    logging.critical(f'LOGIN REDIR TO {redirect_uri}')

    return await oauth.google.authorize_redirect(request, redirect_uri)


async def auth(request):

    logging.critical(request.headers)
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    request.session['user'] = dict(user)
    return RedirectResponse(url='/')


async def auth_form(request: Request):

    if request.method == 'GET':
        return templates.TemplateResponse('Login_v5/index.html', {'request': request})

    form_data = await request.form()
    request.session['username'] = form_data['username']
    return Response()


async def logout(request: Request):

    del request.session['user']
    return Response()


async def verify(request: Request):

    if request.session.get('user'):
        return Response()

    return Response(status_code=401)


ROUTES = [
    Route('/verify', endpoint=verify),
    Route('/', endpoint=auth_form, name='auth_form', methods=['GET', 'POST']),
    Route('/login', endpoint=login, name='google_login'),
    Route('/auth', endpoint=auth),
    Route('/logout', endpoint=logout),
]

for mount in ['css', 'fonts', 'images', 'js', 'vendor']:
    ROUTES.append(
        Mount(f'/{mount}',
              StaticFiles(directory=f'templates/Login_v5/{mount}'),
              name=f'static-{mount}')
    )

app = Starlette(debug=True, routes=ROUTES)  # pylint: disable=invalid-name

app.add_middleware(AuthlibMiddleware,
                   secret_key=config('COOKIE_SECRET'),
                   domain=config('DOMAIN')
                   )
