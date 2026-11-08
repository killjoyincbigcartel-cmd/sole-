import os


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.getenv(
        "JWT_SECRET", "dev-secret-change-me-very-long-for-jwt-signing"
    )


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "sqlite:///dev.db"
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL", "sqlite:///we-sole-test.db"
    )


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}