import random
from datetime import datetime

def fake_evaluate_prognosis(image_path, clinical_path):
    """
    Simule un modèle de pronostic AVC.
    À remplacer plus tard par le vrai pipeline (chargement modèle + inférence).
    """
    score = round(random.uniform(0, 1), 2)

    if score < 0.33:
        risk_level = "Faible"
    elif score < 0.66:
        risk_level = "Modéré"
    else:
        risk_level = "Élevé"

    return {
        "score": score,
        "risk_level": risk_level,
        "mask_path": "masks/sub-stroke0001_ses-01_lesion-msk.nii",  # temporaire, en attendant le vrai modèle
    }
