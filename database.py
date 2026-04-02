
import json
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root123",
    "database": "job_tracker",
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def to_json_text(value):
    return json.dumps(value, indent=2) if value not in (None, "") else ""
