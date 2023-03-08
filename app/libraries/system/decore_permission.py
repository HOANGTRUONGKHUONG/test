from functools import wraps

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims

from app.libraries.http.response import status_code_400

EDIT_ROLE = ['admin', 'editable']
ADMIN_ROLE = ['admin']


def edit_role_require(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] not in EDIT_ROLE:
            return status_code_400("Don't have permission, edit role require")
        else:
            return fn(*args, **kwargs)

    return wrapper


def admin_role_require(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] not in ADMIN_ROLE:
            return status_code_400("Don't have permission, admin require")
        else:
            return fn(*args, **kwargs)

    return wrapper
