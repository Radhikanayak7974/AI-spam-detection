"""
SQLAlchemy database instance.
Shared across the application to avoid circular imports.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
