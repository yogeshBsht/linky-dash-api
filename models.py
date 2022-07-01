from flask import request, url_for
from api import db
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from ua_parser import user_agent_parser


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    links = db.relationship('Link', backref='creator', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        user = {
            'username': self.username,
            'links': [link.link_name for link in self.links]
        }
        return user


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_name = db.Column(db.String(120), index=True)
    link_url = db.Column(db.String(120))  
    description = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    visitors = db.relationship('Visitor', backref='link', lazy='dynamic')

    def __repr__(self):
        return '<Link {} created by user>'.format(self.link_url)

    def to_dict(self):
        link = {
            'id': self.id,
            'link_name': self.link_name,
            'link_url': self.link_url,
            'description': self.description,
            'user_id': self.user_id,
            'unique_visitor_count': self.visitors.count(),
            '_links': {
                'visitors': url_for('visitor_info', link_id=self.id),
            }
        }
        total_visitor_count, country_count = 0, {}
        for v in Visitor.query.all():
            if v.link_id == self.id:
                total_visitor_count += v.total_visits
                if v.country not in country_count:
                    country_count[v.country] = v.total_visits
                else:
                    country_count[v.country] += v.total_visits
        link['total_visitor_count'] = total_visitor_count
        link['most_visited_country'] = ''
        if country_count:
            link['most_visited_country'] = max(country_count, key=country_count.get)
        return link

    def from_dict(self, data, user):
        for field in ['link_name', 'description']:
            if field in data:
                setattr(self, field, data[field])
        self.link_url = '/' + user.username + '/' + self.link_name
        self.user_id = user.id

    
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64))
    first_visit = db.Column(db.DateTime, default=datetime.utcnow)
    last_visit = db.Column(db.DateTime, default=datetime.utcnow)
    total_visits = db.Column(db.Integer)
    country = db.Column(db.String(64))
    browser = db.Column(db.String(64))
    device = db.Column(db.String(64))
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'))

    def __repr__(self):
        return '<Visitor with IP {} visited>'.format(self.ip)

    def to_dict(self):
        visitor = {
            'visitor_id': self.id,
            'first_visit': self.first_visit,
            'last_visit': self.last_visit,
            'total_visits': self.total_visits,
            'country': self.country,
            'browser': self.browser,
            'device': self.device,
            'link_id': self.link_id
        }
        return visitor
    
    def from_dict(self, data, link_id=None, new_visitor=False):
        if new_visitor:
            self.ip = data['ip']
            self.first_visit = date.today()
            self.total_visits = 0
            self.country = data['country']
            self.link_id = link_id
            ua_info = self.get_ua_info()
            self.browser = ua_info['browser']
            self.device = ua_info['device']
        self.total_visits += 1
        self.last_visit = date.today()

    def get_ua_info(self):
        ua_string = request.headers.get('User-Agent')
        parsed_string = user_agent_parser.Parse(ua_string)
        info = {
            'device': parsed_string['os']['family'],
            'browser': parsed_string['user_agent']['family']
        }
        return info