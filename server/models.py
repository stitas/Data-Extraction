from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id_ = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    
    def is_authenticated(self):
        return True

    # When false user is banned and cant log in
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id_)

    def __repr__(self):
        return '<User %r>' % (self.username)

class Extractor(db.Model):
    __tablename__ = 'Extractor'
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    sample_file_path = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('User.id_'))
    
    def __init__(self, name, sample_file_path, user_id):
        self.name = name
        self.sample_file_path = sample_file_path
        self.user_id = user_id

class TextField(db.Model):
    __tablename__ = 'TextField'
    id_ = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100))
    extractor_id = db.Column(db.Integer, db.ForeignKey('Extractor.id_'))

    def __init__(self, key, extractor_id):
        self.key = key
        self.extractor_id = extractor_id

class Text(db.Model):
    id_ = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Text())
    text_field_id = db.Column(db.Integer, db.ForeignKey('TextField.id_'))
    x1 = db.Column(db.Double())
    y1 = db.Column(db.Double())
    x2 = db.Column(db.Double())
    y2 = db.Column(db.Double())
    page = db.Column(db.Integer)
    
    def __init__(self, value, text_field_id, x1, y1, x2, y2, page):
        self.value = value
        self.text_field_id = text_field_id
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.page = page
    

class FormField(db.Model):
    __tablename__ = 'FormField'
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    extractor_id = db.Column(db.Integer, db.ForeignKey('Extractor.id_'))
    
    def __init__(self, name, extractor_id):
        self.name = name
        self.extractor_id = extractor_id
        
class KeyValuePairs(db.Model):
    id_ = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.Text())
    key_confidence = db.Column(db.Double())
    value = db.Column(db.Text())
    value_confidence = db.Column(db.Double())
    form_field_id = db.Column(db.Integer, db.ForeignKey('FormField.id_'))
    
    def __init__(self, key, key_confidence, value, value_confidence, form_field_id):
        self.key = key
        self.key_confidence = key_confidence
        self.value = value
        self.value_confidence = value_confidence
        self.form_field_id = form_field_id
    
class TableField(db.Model):
    __tablename__ = 'TableField'
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    extractor_id = db.Column(db.Integer, db.ForeignKey('Extractor.id_'))
    
    def __init__(self, name, extractor_id):
        self.name = name
        self.extractor_id = extractor_id
        
class Table(db.Model):
    id_ = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    path = db.Column(db.String(100))
    x1 = db.Column(db.Double())
    y1 = db.Column(db.Double())
    x2 = db.Column(db.Double())
    y2 = db.Column(db.Double())
    table_field_id = db.Column(db.Integer, db.ForeignKey('TableField.id_'))
    
    def __init__(self, name, path, table_id, x1, y1, x2, y2):
        self.name = name
        self.path = path
        self.table_field_id = table_id
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2