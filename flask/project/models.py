# models.py

from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, name, password):
        self.id = name
        self.password = password

class Target():
    def __init__(self, uuid, name, hosts, owner):
        self.uuid = uuid
        self.name = name
        self.hosts = hosts
        self.owner = owner

class Scan():
    def __init__(self, name, target, uuid, owner):
        self.name = name
        self.target = target
        self.uuid = uuid
        self.owner = owner

class Report():
    def __init__(self, uuid, owner, task, time):
        self.uuid = uuid
        self.owner = owner
        self.task = task
        self.time = time
