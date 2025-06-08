import sqlite3

DB_NAME = 'imposto_renda.db'

def get_connection():
    return sqlite3.connect(DB_NAME)
