import bcrypt

def hash_password(password: str) -> str:
    # Transforme le mot de passe en hash sécurisé
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    # Vérifie si le mot de passe entré correspond au hash stocké
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

