from flask import jsonify, request, url_for
from api import db, app
from models import User, Link, Visitor
from errors import bad_request, not_found
import urllib.request, json
from urllib.parse import unquote

# encoded_array = "[%225%22%2C%2210%22%2C%221%22]"

# from auth import basic_auth
# from auth import verify_password


@app.route('/login', methods=['POST'])
def login():
    
    # data = json.loads(request.data) or {}

    # decoded_string = unquote(request.data)
    # data = json.loads(decoded_string)
    # if 'username' not in data or 'password' not in data:
    #     return bad_request('Please pass username & password')
    
    # username = data['username']
    # password = data['password']
    
    # user = User.query.filter_by(username=username).first()
    # if user and user.check_password(password):
    #     return {'token': user.username},200

    data = request.get_json() or {}
    if data['username']+'@' != data['password']:
        return bad_request('Invalid password')
    username = data['username']
    # user = User.query.filter_by(username=username).first()
    # if not user:
        # create user
    return {'token':username},200


@app.route('/dashboard', methods=['GET'])
def dashboard():
    return {},200


@app.route('/create_link', methods=['POST'])
# @basic_auth.login_required
def create_link():
    data = request.get_json() or {}
    username = request.headers.get('x-auth-user')
    user = User.query.filter_by(username=username).first()

    for l in user.links:
        if l.link_name == data['link_name']:
            return bad_request('Link name already exists')
    
    link = Link()
    link.from_dict(data, user)
    db.session.add(link)
    db.session.commit()
    response = jsonify(link.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('update_visitor', username=user.username, link_name=link.link_name)
    return response


@app.route('/mylinks', methods=['GET'])
# @basic_auth.login_required
def mylinks():
    username = request.headers.get('x-auth-user')
    user = User.query.filter_by(username=username).first()
    user_links = {}
    if user:
        link_count = user.links.count()
        count = 1
        for l in user.links:
            link = Link.query.filter_by(link_name=l.link_name).first()
            link_data = link.to_dict()
            user_links[count] = link_data
            count += 1
    return user_links


@app.route('/link_info/<int:link_id>', methods=['GET'])
# @basic_auth.login_required
def link_info(link_id):
    username = request.headers.get('x-auth-user')
    user = User.query.filter_by(username=username).first()
    link_data = {}
    if user:
        link = Link.query.filter_by(id=link_id).first()
        link_data = link.to_dict()
    response = jsonify(link_data)
    return response


@app.route('/visitor_info/<int:link_id>', methods=['GET'])
def visitor_info(link_id):
    link = Link.query.filter_by(id=link_id).first()
    count = 1
    link_visitors = {}
    for v in Visitor.query.all():
        if v.link_id == link_id:
            link_visitors[count] = v.to_dict()
            count += 1
    response = jsonify(link_visitors)
    return response


@app.route('/<username>/<link_name>', methods=['GET'])
def update_visitor(username, link_name):
    user = User.query.filter_by(username=username).first()
    if not user:
        return not_found('User not found')
    
    link_not_found = 1
    for l in user.links.all():
        if l.link_name == link_name:
            link_not_found = 0
            break
    if link_not_found:
        return not_found('Link not found')
    
    url = "https://api.country.is"
    response = urllib.request.urlopen(url)
    data = response.read()
    ip_dict = json.loads(data)

    # Check if a visitor has already visited the link
    new_visitor = True
    for visitor in Visitor.query.all():
        if visitor.link_id == l.id and visitor.ip == ip_dict['ip']:
            new_visitor = False
            break
    
    if new_visitor:
        visitor = Visitor()
        visitor.from_dict(ip_dict, l.id, new_visitor=True)
        db.session.add(visitor)
    else:
        visitor.from_dict(ip_dict)
    
    db.session.commit()
    response = jsonify(visitor.to_dict())
    response.status_code = 201
    # response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

# @app.route('/dashboard/<username>')
# @basic_auth.login_required
# def dashboard(username):
#     user = User.query.filter_by(username=username).first()
#     user_dict = user.to_dict() or {}
#     if user:
#         for l in user.links:
#             link = Link.query.filter_by(link_name=l.link_name).first()
#             if link:
#                 visitors = link.visitors
#                 for v in visitors:
#                     visitor = Visitor.query.filter_by(id=v.id).first()
#                 visitor_dict = visitor.to_dict()
#     user_dict['visitors'] = visitor_dict or {}
#     return user_dict


# @app.route('/dashboard/<username>/create_link', methods=['POST'])
# @basic_auth.login_required
# def create_link(username):
#     user = User.query.filter_by(username=username).first()
#     data = request.get_json() or {}
#     if 'link_name' not in data:
#         return bad_request('Link_name missing')

#     for l in user.links:
#         if l.link_name == data['link_name']:
#             return bad_request('Link_name already exists')
    
#     link = Link()
#     link.from_dict(data, user)
#     db.session.add(link)
#     db.session.commit()
#     response = jsonify(link.to_dict())
#     response.status_code = 201
#     response.headers['Location'] = url_for('update_visitor', username=user.username, link_name=link.link_name)
#     return response