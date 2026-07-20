import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'farm-rental-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'farm_rental.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER_EQUIPMENT = os.path.join(basedir, 'static', 'uploads', 'equipment')
    UPLOAD_FOLDER_AVATARS = os.path.join(basedir, 'static', 'uploads', 'avatars')
    UPLOAD_FOLDER_INVOICES = os.path.join(basedir, 'static', 'uploads', 'invoices')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PER_PAGE = 12


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
