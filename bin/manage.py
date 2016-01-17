#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Flask-Diamond (c) Ian Dennis Miller

import sys
import traceback
sys.path.insert(0, '.')

from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import Migrate, MigrateCommand
import alembic
import alembic.config
from flask_diamond import create_app, db, security, models

app = create_app()
migrate = Migrate(app, db, directory="flask_diamond/migrations")


def _make_context():
    return {
        "app": app,
        "db": db,
        "user_datastore": security.Security.user_datastore,
        "models": models,
        "migrate": MigrateCommand,
    }

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))
manager.add_command("runserver", Server(port=app.config['PORT']))
manager.add_command("publicserver", Server(port=app.config['PORT'], host="0.0.0.0"))
manager.add_command('db', MigrateCommand)


@manager.option('-e', '--email', help='email address', required=True)
@manager.option('-p', '--password', help='password', required=True)
@manager.option('-a', '--admin', help='make user an admin user', action='store_true', default=None)
def useradd(email, password, admin):
    "add a user to the database"
    if admin:
        roles = ["Admin"]
    else:
        roles = ["User"]
    models.User.register(
        email=email,
        password=password,
        confirmed=True,
        roles=roles
    )


@manager.option('-e', '--email', help='email address', required=True)
def userdel(email):
    "delete a user from the database"
    obj = models.User.find(email=email)
    if obj:
        obj.delete()
        print("Deleted")
    else:
        print("User not found")


@manager.command
def init_db():
    "drop all databases, instantiate schemas"
    db.drop_all()
    db.create_all()
    db.session.commit()
    cfg = alembic.config.Config("flask_diamond/migrations/alembic.ini")
    alembic.command.stamp(cfg, "head")


@manager.command
def populate_db():
    "insert a default set of objects"
    models.User.add_system_users()


if __name__ == "__main__":
    try:
        manager.run()
    except Exception, e:
        ex_type, ex, tb = sys.exc_info()
        traceback.print_tb(tb)
        print "Error: %s" % e
        print "Line: %d" % sys.exc_traceback.tb_lineno
