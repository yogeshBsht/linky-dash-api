from flask_httpauth import HTTPBasicAuth
from models import User
from errors import error_response
import base64

basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
# def verify_password(token):
    # base64_bytes = token[6:].encode('utf8')
    # message_bytes = base64.b64decode(base64_bytes)
    # credentials = message_bytes.decode('utf8')
    # [username, password] = credentials.split(':')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return basic_auth_error(401)

@basic_auth.error_handler
def basic_auth_error(status):
    return error_response(status)