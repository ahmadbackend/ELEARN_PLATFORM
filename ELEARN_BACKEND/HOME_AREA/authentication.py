"""
JWT authentication for the REST API.

The platform has two user tables (STUDENT and INSTRUCTOR) that do not extend
AbstractBaseUser, so the usual JWT packages cannot be dropped in. Tokens are therefore
minted here: a standard HS256 JWT signed with SECRET_KEY, no extra dependency, no token
table, and a password change invalidates every token issued before it.

Claims: sub (user id), cat ("student" | "instructor"), iat, exp, pw (password fingerprint).
A plain-JS client can read `exp` and `cat` from the payload without any library.

Usage from the SPA (header only, never cookies):
    POST /api/v1/auth/login/  ->  {"token": "...", ...}
    Authorization: Bearer <token>            (http)
    ws://host/ws/peerchat/a/b/?token=<token> (websocket)
"""
import base64
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs

from django.conf import settings
from django.utils.crypto import salted_hmac
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from INSTRUCTOR.models import INSTRUCTOR
from STUDENT.models import STUDENT

TOKEN_SALT = 'HOME_AREA.api.jwt'
# seconds a token stays valid, overridable from settings
TOKEN_MAX_AGE = getattr(settings, 'API_TOKEN_MAX_AGE', 60 * 60 * 24 * 7)

USER_MODELS = {'student': STUDENT, 'instructor': INSTRUCTOR}


def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _unb64(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def _sign(signing_input):
    # keyed off SECRET_KEY through django's salted hmac so the raw key is never the hmac key
    return _b64(salted_hmac(TOKEN_SALT, signing_input, algorithm='sha256').digest())


_HEADER = _b64(json.dumps({'alg': 'HS256', 'typ': 'JWT'}, separators=(',', ':')).encode())


def _password_fingerprint(user):
    # short digest of the stored password: baked into the token so a reset kills old tokens
    return hashlib.sha256(user.PASSWORD.encode()).hexdigest()[:16]


def issue_token(user):
    now = int(time.time())
    payload = {'sub': user.id, 'cat': user.user_cat, 'iat': now, 'exp': now + TOKEN_MAX_AGE,
               'pw': _password_fingerprint(user)}
    body = _b64(json.dumps(payload, separators=(',', ':')).encode())
    return f'{_HEADER}.{body}.{_sign(f"{_HEADER}.{body}".encode())}'


def decode_token(token):
    """Verified, unexpired payload of `token`, or None."""
    try:
        header, body, signature = token.split('.')
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(f'{header}.{body}'.encode())):
        return None
    try:
        header_data = json.loads(_unb64(header))
        payload = json.loads(_unb64(body))
    except (ValueError, UnicodeDecodeError):
        return None
    if header_data.get('alg') != 'HS256' or not isinstance(payload, dict):
        return None
    if payload.get('exp', 0) < time.time():
        return None
    return payload


def resolve_token(token):
    """Returns the STUDENT/INSTRUCTOR behind `token`, or None when it is invalid/expired."""
    payload = decode_token(token)
    if payload is None:
        return None
    model = USER_MODELS.get(payload.get('cat'))
    if model is None:
        return None
    user = model.objects.filter(pk=payload.get('sub'), Isactive=True).first()
    if user is None or _password_fingerprint(user) != payload.get('pw'):
        return None
    return user


class JWTAuthentication(BaseAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) != 2:
            raise AuthenticationFailed('Invalid Authorization header. Expected "Bearer <token>".')
        token = auth[1].decode()
        user = resolve_token(token)
        if user is None:
            raise AuthenticationFailed('Invalid or expired token.')
        return (user, token)

    def authenticate_header(self, request):
        return self.keyword


# lets the swagger UI show the "Authorize" button for our scheme
try:
    from drf_spectacular.extensions import OpenApiAuthenticationExtension

    class JWTScheme(OpenApiAuthenticationExtension):
        target_class = 'HOME_AREA.authentication.JWTAuthentication'
        name = 'BearerAuth'

        def get_security_definition(self, auto_schema):
            return {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}
except ImportError:  # drf-spectacular is optional at runtime
    pass


class TokenAuthMiddleware:
    """
    Channels middleware: authenticates a websocket from `?token=` in the query string.
    Placed inside AuthMiddlewareStack so a session login keeps working for the MVT pages
    and a token, when present, wins.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        from channels.db import database_sync_to_async

        token = parse_qs(scope.get('query_string', b'').decode()).get('token', [None])[0]
        if token:
            user = await database_sync_to_async(resolve_token)(token)
            if user is not None:
                scope = dict(scope, user=user)
        return await self.inner(scope, receive, send)
