from models.database import get_connections
from utils.security import hash_password
import psycopg2
def create_users_table():
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Table users créée avec succès !")

def add_role_columne():
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS role VARCHAR(10) NOT NULL DEFAULT 'user';
                """)
    conn.commit()
    cur.close()
    conn.close()
    
def add_role_columne():
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
                ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                """)
    conn.commit()
    cur.close()
    conn.close()
   
def create_first_admin(nom,email,password):
    hashed_pass = hash_password(password)
    conn = get_connections()
    cur = conn.cursor()
    try:
        cur.execute("""
                    INSERT INTO users (nom,email,password_hash,role) VALUES (%s,%s,%s,%s)
                    """,(nom,email,hashed_pass,"admin"))
        conn.commit()
        print("Admin cree!")
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print("Cet admin existe deja")
    finally:
        cur.close()
        conn.close()
        
    
    

if __name__ == "__main__":
    create_users_table()
    add_role_columne()
    create_first_admin("EMI_admin", "EMI@gmail.com", "123")
    add_role_columne()
    
    