"""
Database Utility - SQLite connection manager with query methods.
Provides access to customers, service_plans, and customer_usage tables.
"""


import sqlite3
from config.config import config

class Database:
    def __init__(self, db_path=config.DB_PATH):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def query(self, sql, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or [])
            return cursor.fetchall()
        finally:
            conn.close()

    def query_one(self, sql, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or [])
            return cursor.fetchone()
        finally:
            conn.close()

db = Database()
