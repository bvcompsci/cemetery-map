import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'to-be-determined'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # HS_IMAGE_TARGET can be set to either 'db' or 'file' depending on
    # where we wish to store images, either a LargeBinary in the database
    # or in the filesystem.
    HS_IMAGE_TARGET = 'db'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
