import mysql.connector
from mysql.connector import Error
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            database=os.getenv('MYSQL_DATABASE', 'seasonal_market'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            charset='utf8mb4',
            connection_timeout=int(os.getenv('MYSQL_CONNECT_TIMEOUT', '3'))
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=None):
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)
        result = cursor.fetchall()
        cursor.close()
        connection.close()
        return result
    except Error as e:
        print(f"Query execution error: {e}")
        connection.close()
        return None

def execute_non_query(query, params=None):
    connection = get_connection()
    if not connection:
        return -1
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params)
        connection.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        return affected_rows
    except Error as e:
        print(f"Non-query execution error: {e}")
        connection.rollback()
        connection.close()
        return -1

def execute_procedure(proc_name, params=None):
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.callproc(proc_name, params)
        connection.commit()
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        cursor.close()
        connection.close()
        return results
    except Error as e:
        print(f"Procedure execution error: {e}")
        connection.rollback()
        connection.close()
        return None
