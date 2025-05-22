from db import db
from sqlalchemy import Column, DateTime
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'
   
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    username = db.Column(db.String(200), nullable=False)
    name =db.Column(db.String(200), nullable=False)
    date_creation=db.Column(DateTime, default=datetime.utcnow)

    def serialize(self):
            return{
                 "id": self.id,
                 "name" : self.name,
                 "email" : self.email,
                 "username" : self.username,
                 "role" : self.role,
            }
   
    def __repr__(self):
        return f'<User {self.email}>'