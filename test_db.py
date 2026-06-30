from db import get_connection

print("Testing database connection...")
conn = get_connection()
print("Connection:", conn)
if conn:
    print("Success! Closing connection...")
    conn.close()
else:
    print("Failed!")