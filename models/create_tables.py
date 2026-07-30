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
                ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
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
        
def create_patients_table():
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id SERIAL PRIMARY KEY,
                    medecin_id INTEGER NOT NULL REFERENCES users(id),
                    nom VARCHAR(30) NOT NULL,
                    prenom VARCHAR(30) NOT NULL,
                    age INTEGER,
                    sexe VARCHAR(1),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
    conn.commit()
    cur.close
    conn.close()
    print("patient cree avec succes")
    
    
def create_evaluations_table():
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluations (
            id SERIAL PRIMARY KEY,
            patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,

            center VARCHAR(100),
            atrial_fibrillation BOOLEAN,
            hypertension BOOLEAN,
            diabetes BOOLEAN,
            hyperlipidemia BOOLEAN,
            anticoagulation BOOLEAN,
            lipid_lowering_drugs BOOLEAN,
            pais VARCHAR(50),
            glucose FLOAT,
            leucocytes FLOAT,
            crp FLOAT,
            inr FLOAT,
            wake_up BOOLEAN,
            in_house BOOLEAN,
            referral VARCHAR(100),
            onset_to_door INTEGER,
            alert_to_door INTEGER,
            nihss_admission INTEGER,
            mrs_admission INTEGER,
            mrs_premorbid INTEGER,
            door_to_imaging INTEGER,
            door_to_groin INTEGER,
            door_to_first_series INTEGER,
            time_of_intervention INTEGER,
            door_to_recanalization INTEGER,

            image_path VARCHAR(255),
            clinical_csv_path VARCHAR(255),
            result JSONB,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
        
    
    

if __name__ == "__main__":
    create_users_table()
    add_role_columne()
    add_role_columne()
    create_patients_table()
    create_evaluations_table()
    
    