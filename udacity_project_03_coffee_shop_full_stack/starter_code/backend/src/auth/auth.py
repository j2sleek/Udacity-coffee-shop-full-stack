import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen
from ..settings import AUTH0_TENANT_DOMAIN, AUTH0_ALGORITHMS, AUTH0_API_AUDIENCE


AUTH0_DOMAIN = AUTH0_TENANT_DOMAIN
ALGORITHMS = AUTH0_ALGORITHMS
API_AUDIENCE = AUTH0_API_AUDIENCE

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    try:
        # Retrieve authentication header
        auth_header = request.headers['Authorization']
        # Split the auth_header
        auth_split = auth_header.split(' ')
        # Authenticate the value of auth_split. 
        #Value should have only 2 parts starting with bearer
        if auth_split[0].lower() != 'bearer':
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization header must begin with "Bearer".'
            }, 401)
        elif len(auth_split)== 1:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Token not found.'
            }, 401)
        elif len(auth_split)> 2:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization header must be bearer token.'
            }, 401)
        token = auth_split[1]
        return token
    except Exception:
        raise AuthError({
            'code': 'no_header_found',
            'description': 'No authorization header found.'
        }, 401)


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    # Check if payload contains permissions
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'not_authorized',
            'description': 'User not authorized.'
        }, 400)
    # Check if the requested permission is in the payload
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'not_authorized',
            'description': 'User not authorized.'
        }, 403)
    # Return True if the no errors found in the check above
    return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    # Get the public key url
    public_url = urlopen('https://'+ AUTH0_DOMAIN + '/.well-known/jwks.json')
    # Store the public key
    public_key = json.loads(public_url.read())
    # Extract the private key from the token
    private_key = jwt.get_unverified_header(token)
    # Intitalise the rsa key needed for decoding
    rsa_key = {}

    # Authenticate the private key
    if 'kid' not in private_key:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization error'
        }, 401)
    # Itirate through the public key if kid in public key matches kid in private key
    for key in public_key['keys']:
        if key['kid'] == private_key['kid']:
            # If there is a match, populate the rsa object with public key credientials
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    # Check if there is an rsa object returned
    if rsa_key:
        try:
            # If an rsa_key is confirmed, decode and store in payload
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://'+ AUTH0_DOMAIN + '/',
            )
            return payload
        #If any error is encountered, raise an exception
        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    # If rsa_key not found
    else:
        raise AuthError({
            'code': 'invalid_token',
            'description': 'Authorization error'
        }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator

