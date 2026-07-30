from models.database import get_connections
import psycopg2


def add_patient(medecin_id, nom, prenom, age, sexe):
    conn = get_connections()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO patients (medecin_id, nom, prenom, age, sexe)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, created_at;
        """, (medecin_id, nom, prenom, age, sexe))
        result = cur.fetchone()
        conn.commit()
        return result  # (id, created_at)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_patients_by_medecin(medecin_id):
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nom, prenom, age, sexe, created_at
        FROM patients
        WHERE medecin_id = %s
        ORDER BY created_at DESC;
    """, (medecin_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows