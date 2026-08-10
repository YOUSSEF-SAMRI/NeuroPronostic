import json
import pandas as pd
from models.database import get_connections  # même import que patients.py
import numpy as np


CSV_TO_DB_COLUMNS = {
    "Center": "center",
    "Atrial fibrillation": "atrial_fibrillation",
    "Hypertension": "hypertension",
    "Diabetes": "diabetes",
    "Hyperlipidemia": "hyperlipidemia",
    "Anticoagulation": "anticoagulation",
    "Lipid lowering drugs": "lipid_lowering_drugs",
    "PAIs": "pais",
    "Glucose": "glucose",
    "Leucocytes": "leucocytes",
    "CRP": "crp",
    "INR": "inr",
    "Wake-up": "wake_up",
    "In-House": "in_house",
    "Referral": "referral",
    "Onset to door": "onset_to_door",
    "Alert to door": "alert_to_door",
    "NIHSS at admission": "nihss_admission",
    "mRS at admission": "mrs_admission",
    "mRS premorbid": "mrs_premorbid",
    "Door to imaging": "door_to_imaging",
    "Door to groin": "door_to_groin",
    "Door to first series": "door_to_first_series",
    "Time of intervention": "time_of_intervention",
    "Door to recanalization": "door_to_recanalization",
}

import json
import pandas as pd

def add_evaluation(patient_id, image_path, clinical_csv_path, result):
    df = pd.read_csv(clinical_csv_path, sep=None, engine="python")
    row = df.iloc[0]  # une seule ligne clinique par patient
    
    BOOLEAN_DB_COLUMNS = {
    "atrial_fibrillation", "hypertension", "diabetes", "hyperlipidemia",
    "anticoagulation", "lipid_lowering_drugs", "wake_up", "in_house",
    }

    def to_native(value, is_boolean=False):
        """Convertit les types numpy en types Python natifs."""
        if pd.isna(value):
            return None
        if is_boolean:
            return bool(int(value))
        if isinstance(value, (np.integer,)):
            return int(value)
        if isinstance(value, (np.floating,)):
            return float(value)
        if isinstance(value, (np.bool_,)):
            return bool(value)
        return value
    
    values = {}
    for csv_col, db_col in CSV_TO_DB_COLUMNS.items():
        raw = row[csv_col] if csv_col in df.columns else None
        is_bool = db_col in BOOLEAN_DB_COLUMNS
        values[db_col] = to_native(raw, is_boolean=is_bool) if raw is not None else None
        
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO evaluations (
            patient_id, center, atrial_fibrillation, hypertension, diabetes,
            hyperlipidemia, anticoagulation, lipid_lowering_drugs, pais,
            glucose, leucocytes, crp, inr, wake_up, in_house, referral,
            onset_to_door, alert_to_door, nihss_admission, mrs_admission,
            mrs_premorbid, door_to_imaging, door_to_groin, door_to_first_series,
            time_of_intervention, door_to_recanalization,
            image_path, clinical_csv_path, result
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """, (
        patient_id, values["center"], values["atrial_fibrillation"], values["hypertension"],
        values["diabetes"], values["hyperlipidemia"], values["anticoagulation"],
        values["lipid_lowering_drugs"], values["pais"], values["glucose"],
        values["leucocytes"], values["crp"], values["inr"], values["wake_up"],
        values["in_house"], values["referral"], values["onset_to_door"],
        values["alert_to_door"], values["nihss_admission"], values["mrs_admission"],
        values["mrs_premorbid"], values["door_to_imaging"], values["door_to_groin"],
        values["door_to_first_series"], values["time_of_intervention"],
        values["door_to_recanalization"], image_path, clinical_csv_path,
        json.dumps(result)
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_evaluations_by_medecin(medecin_id):
    conn = get_connections()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, p.nom, p.prenom, e.result, e.created_at,
               e.image_path, e.clinical_csv_path
        FROM evaluations e
        JOIN patients p ON p.id = e.patient_id
        WHERE p.medecin_id = %s
        ORDER BY e.created_at DESC
    """, (medecin_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_last_evaluation_by_patient(patient_id):
    conn = get_connections()
    cur = conn.cursor()

    cur.execute("""
        SELECT result
        FROM evaluations
        WHERE patient_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (patient_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        return None

    return row[0]