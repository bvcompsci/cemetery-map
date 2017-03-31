import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'to-be-determined'
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    GOOGLE_MAPS_KEY = os.environ['GOOGLE_MAPS_KEY']
    GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
    GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
    GOOGLE_ADMIN_EMAIL_LIST = []
    if 'GOOGLE_ADMIN_EMAIL_LIST' in os.environ:
        GOOGLE_ADMIN_EMAIL_LIST = eval(os.environ['GOOGLE_ADMIN_EMAIL_LIST'])
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
