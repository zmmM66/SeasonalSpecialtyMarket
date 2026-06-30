import mysql.connector
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def execute_sql_file(file_path):
    cnx = mysql.connector.connect(
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        charset='utf8mb4'
    )
    cursor = cnx.cursor()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    delimiter = ';'
    statements = []
    current_stmt = ''
    
    lines = sql_content.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('DELIMITER'):
            delimiter = stripped.split()[1]
            continue
        
        if delimiter in line:
            current_stmt += line.split(delimiter)[0]
            statements.append(current_stmt.strip())
            current_stmt = line.split(delimiter)[1]
        else:
            current_stmt += line + '\n'
    
    if current_stmt.strip():
        statements.append(current_stmt.strip())
    
    for stmt in statements:
        stmt = stmt.strip()
        if stmt:
            try:
                cursor.execute(stmt)
                cnx.commit()
            except Exception as e:
                print(f"Error executing: {stmt[:100]}...")
                print(f"Error: {e}")
                raise
    
    cursor.close()
    cnx.close()
    print("SQL script executed successfully!")

if __name__ == '__main__':
    execute_sql_file('seasonal_market.sql')
