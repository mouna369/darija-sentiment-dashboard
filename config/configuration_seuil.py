# config/configuration_seuil.py

# ─── Valeurs par défaut (fallback si MongoDB KO) ─────────────
SEUIL_NEGATIF      = 78
SEUIL_TAUX_JOUR    = 20
SEUIL_VOLUME_JOUR  = 5
SEUIL_PIC_CRITIQUE = 30

def load_seuils_from_db():
    """Charge les seuils depuis MongoDB si disponibles."""
    global SEUIL_NEGATIF, SEUIL_TAUX_JOUR, SEUIL_VOLUME_JOUR, SEUIL_PIC_CRITIQUE
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27018/?directConnection=true')
        doc = client['telecom_admin']['config_seuils'].find_one({"_id": "seuils_alerte"})
        if doc:
            SEUIL_NEGATIF      = doc.get('SEUIL_NEGATIF',      SEUIL_NEGATIF)
            SEUIL_TAUX_JOUR    = doc.get('SEUIL_TAUX_JOUR',    SEUIL_TAUX_JOUR)
            SEUIL_VOLUME_JOUR  = doc.get('SEUIL_VOLUME_JOUR',  SEUIL_VOLUME_JOUR)
            SEUIL_PIC_CRITIQUE = doc.get('SEUIL_PIC_CRITIQUE', SEUIL_PIC_CRITIQUE)
            print(f"✅ Seuils chargés depuis MongoDB: NEG={SEUIL_NEGATIF}% JOUR={SEUIL_TAUX_JOUR}% VOL={SEUIL_VOLUME_JOUR}")
        client.close()
    except Exception as e:
        print(f"⚠️ Seuils MongoDB KO, valeurs par défaut utilisées: {e}")

# Charger au démarrage automatiquement
load_seuils_from_db()