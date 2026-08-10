import random

def evaluate_model(clinical_data: dict, image_path: str) -> dict:
    """Simule le modèle IA. À remplacer plus tard par le vrai appel."""
    types_tumeur = ["Gliome", "Méningiome", "Pituitaire", "Aucune anomalie"]
    diagnostic = random.choice(types_tumeur)

    return {
        "diagnostic": diagnostic,
        "confiance": round(random.uniform(0.6, 0.98), 2),
        "stade": random.choice(["Stade I", "Stade II", "Stade III"]) if diagnostic != "Aucune anomalie" else None
    }