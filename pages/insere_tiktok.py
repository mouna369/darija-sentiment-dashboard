from pymongo import MongoClient
from datetime import datetime, timedelta
import random

# Connexion MongoDB
client = MongoClient("mongodb://localhost:27018/?directConnection=true")  # À ajuster
db = client["telecom_algerie"]  # À ajuster
collection = db["commentaires_predictions_final"]  # À ajuster

def generer_msg_tiktok(index: int, base_date: datetime) -> dict:
    """Génère un message TikTok à partir du template"""
    
    # Dates aléatoires entre 2025-11-01 et 2026-05-20
    random_days = random.randint(0, 200)
    date_msg = base_date - timedelta(days=random_days)
    
    # Sentiment aléatoire (pondéré pour correspondre à vos données TikTok)
    sentiment_rand = random.random()
    if sentiment_rand < 0.57:      # 57% positifs (comme dans votre image)
        sentiment_label = "POSITIF"
        sentiment_score = round(random.uniform(0.1, 0.95), 2)
        sentiment_prob = {
            "POSITIF": round(random.uniform(0.7, 0.98), 4),
            "NEUTRE": round(random.uniform(0.01, 0.2), 4),
            "NEGATIF": round(random.uniform(0.01, 0.1), 4)
        }
        # Normaliser
        total = sum(sentiment_prob.values())
        sentiment_prob = {k: round(v/total, 4) for k, v in sentiment_prob.items()}
    elif sentiment_rand < 0.87:    # 30% neutres
        sentiment_label = "NEUTRE"
        sentiment_score = round(random.uniform(-0.2, 0.2), 2)
        sentiment_prob = {
            "POSITIF": round(random.uniform(0.1, 0.3), 4),
            "NEUTRE": round(random.uniform(0.6, 0.85), 4),
            "NEGATIF": round(random.uniform(0.05, 0.2), 4)
        }
        total = sum(sentiment_prob.values())
        sentiment_prob = {k: round(v/total, 4) for k, v in sentiment_prob.items()}
    else:                           # 13% négatifs
        sentiment_label = "NEGATIF"
        sentiment_score = round(random.uniform(-0.9, -0.1), 2)
        sentiment_prob = {
            "POSITIF": round(random.uniform(0.01, 0.1), 4),
            "NEUTRE": round(random.uniform(0.05, 0.2), 4),
            "NEGATIF": round(random.uniform(0.7, 0.95), 4)
        }
        total = sum(sentiment_prob.values())
        sentiment_prob = {k: round(v/total, 4) for k, v in sentiment_prob.items()}
    
    # Messages TikTok variés
    messages_tiktok = [
        "J'adore cette vidéo TikTok ! Trop drôle 😂",
        "Merci pour ce contenu de qualité 🙏",
        "Encore une super vidéo ! Continue comme ça 🔥",
        "Le meilleur compte TikTok d'Algérie ❤️",
        "Franchement déçu de cette vidéo...",
        "Pas terrible aujourd'hui",
        "Contenu intéressant mais peut mieux faire",
        "Trop bien expliqué, merci !",
        "Je partage avec tous mes potes 👌",
        "À quand un live ?",
        "La qualité baisse ces derniers temps",
        "Toujours au top !",
        "J'attends la prochaine vidéo avec impatience",
        "Pas mal mais j'ai vu mieux",
        "Excellent comme d'habitude !",
        "Franchement nul cette fois",
        "Super contenu, très instructif",
        "Trop court la vidéo",
        "Merci pour l'info !",
        "Vivement la suite",
    ]
    
    frustration_detectee = sentiment_label == "NEGATIF" and random.random() < 0.3
    
    return {
        "original_id": f"tiktok_{base_date.timestamp()}_{index}",
        "a_mention_attente": False,
        "a_mention_prv": False,
        "a_repondu": False,
        "annee": date_msg.year,
        "auteur": f"tiktoker_{random.randint(1, 50)}",
        "batch_id": 0,
        "categories_negatives": [] if sentiment_label != "NEGATIF" else ["qualite"] if random.random() < 0.5 else [],
        "commentaire_normalized": random.choice(messages_tiktok),
        "commentaire_original": random.choice(messages_tiktok),
        "date_annotation": datetime.utcnow(),
        "date_clean": date_msg,
        "date_originale": date_msg.strftime("%d/%m/%Y %H:%M"),
        "demande_reponse": False,
        "frustration_detectee": frustration_detectee,
        "has_negatif": sentiment_label == "NEGATIF",
        "heure": date_msg.hour,
        "intensite_negative": abs(sentiment_score) if sentiment_label == "NEGATIF" else 0,
        "jour_semaine": date_msg.strftime("%A"),
        "jour_semaine_num": date_msg.weekday(),
        "longueur_chars": len(random.choice(messages_tiktok)),
        "longueur_mots": len(random.choice(messages_tiktok).split()),
        "mois": date_msg.strftime("%Y-%m"),
        "mois_nom": date_msg.strftime("%B"),
        "mots_cles_negatifs": [] if sentiment_label != "NEGATIF" else ["decu", "nul"],
        "nb_mots_negatifs": 1 if sentiment_label == "NEGATIF" else 0,
        "nb_mots_unique": random.randint(3, 10),
        "nb_phrases": 1,
        "reason_confiance": round(random.uniform(0.4, 0.9), 4),
        "reason_pred": "qualite_contenu" if random.random() < 0.5 else "autre",
        "region": "",
        "semaine": date_msg.isocalendar()[1],
        "sentiment_confiance": max(sentiment_prob.get(sentiment_label, 0.8), 0.6),
        "sentiment_incertain": False,
        "sentiment_label": sentiment_label,
        "sentiment_label_brut": sentiment_label,
        "sentiment_probabilities": sentiment_prob,
        "sentiment_score": sentiment_score,
        "source": "TikTok",
        "theme_pred": "divertissement" if random.random() < 0.6 else "hors_sujet",
        "tranche_horaire": "soiree" if 18 <= date_msg.hour < 22 else "nuit" if 22 <= date_msg.hour else "journee",
        "version_modele": "bert_meanpool_v2 + dziribert_reason_v2",
        "ville": "",
        "annee_mois": date_msg.strftime("%Y-%m"),
        "annee_semaine": f"{date_msg.year}-S{date_msg.isocalendar()[1]:02d}",
        "est_weekend": date_msg.weekday() >= 5,
        "jour_type": "weekend" if date_msg.weekday() >= 5 else "semaine",
        "longueur_categorie": "court" if len(random.choice(messages_tiktok).split()) < 10 else "moyen",
        "sentiment_num": 1 if sentiment_label == "POSITIF" else -1 if sentiment_label == "NEGATIF" else 0,
        "date_detection_langue": datetime.utcnow(),
        "langue_confidence": round(random.uniform(0.7, 0.95), 3),
        "langue_detectee": "francais",
        "langue_scores": {
            "anglais": round(random.uniform(0, 0.1), 3),
            "arabe_classique": round(random.uniform(0, 0.05), 3),
            "arabe_darija": round(random.uniform(0, 0.15), 3),
            "arabizi": round(random.uniform(0, 0.05), 3),
            "francais": round(random.uniform(0.7, 0.95), 3),
            "mixte": round(random.uniform(0, 0.1), 3)
        },
        "modele_detection": "hybrid_v3"
    }

# ── Génération des 193 messages TikTok ─────────────────────────────────────────
base_date = datetime(2025, 12, 1, 14, 0, 0)
documents_tiktok = []

for i in range(1, 194):
    doc = generer_msg_tiktok(i, base_date)
    documents_tiktok.append(doc)
    
    # Aperçu
    sentiment_emoji = "🔴" if doc["sentiment_label"] == "NEGATIF" else "🟢" if doc["sentiment_label"] == "POSITIF" else "⚪"
    print(f"[{i:3d}] {sentiment_emoji} TikTok - Score: {doc['sentiment_score']:+.2f} - {doc['commentaire_normalized'][:40]}...")

# ── Insertion dans MongoDB ─────────────────────────────────────────────────────
if documents_tiktok:
    try:
        result = collection.insert_many(documents_tiktok)
        print(f"\n✅ {len(result.inserted_ids)} messages TikTok insérés avec succès !")
        print(f"   - POSITIFS : {sum(1 for d in documents_tiktok if d['sentiment_label'] == 'POSITIF')}")
        print(f"   - NEUTRES  : {sum(1 for d in documents_tiktok if d['sentiment_label'] == 'NEUTRE')}")
        print(f"   - NEGATIFS : {sum(1 for d in documents_tiktok if d['sentiment_label'] == 'NEGATIF')}")
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion : {e}")
else:
    print("Aucun document à insérer")