import psycopg2


def get_connections():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="neuropronostic_db",
        user="postgres",
        password="youssef"  
    )