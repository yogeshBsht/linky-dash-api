from flask import jsonify, request, url_for
from api import db, app
from models import User, Link, Visitor
from errors import bad_request, not_found


@app.route('/login', methods=['POST'])
def login():    
    # BASIC AUTH
    data = request.get_json() or {}
    if 'username' not in data or 'password' not in data:
        return bad_request('Please pass username & password')
    
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return {'token': username},200 


@app.route('/dashboard', methods=['GET'])
def dashboard():
    return {},200


@app.route('/create_link', methods=['POST'])
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
def mylinks():
    username = request.headers.get('x-auth-user')
    user = User.query.filter_by(username=username).first()
    user_links = {}
    if user:
        count = 1
        for l in user.links:
            link = Link.query.filter_by(link_name=l.link_name).first()
            link_data = link.to_dict()
            user_links[count] = link_data
            count += 1
    return user_links


@app.route('/link_info/<int:link_id>', methods=['GET'])
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
    
    link_not_found = True
    for l in user.links.all():
        if l.link_name == link_name:
            link_not_found = False
            break
    if link_not_found:
        return not_found('Link not found')
    
    uuid = request.headers.get('x-client-id')
    ip = request.headers.get('x-client-IP')
    country = request.headers.get('x-client-country')

    # Check if a visitor has already visited the link
    new_visitor = True
    for visitor in Visitor.query.all():
        if visitor.link_id == l.id and visitor.uuid == uuid:
            new_visitor = False
            break
    
    if new_visitor:
        visitor = Visitor()
        visitor.from_dict(uuid, ip, country, l.id, new_visitor=True)
        db.session.add(visitor)
    else:
        visitor.from_dict()
    
    db.session.commit()
    response = jsonify(visitor.to_dict())
    response.status_code = 201
    return response