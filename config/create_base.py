# create_database.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime
import os

def create_database():
    print("🚀 Démarrage de la création de la base de données...")
    print("-" * 50)
    
    # 1. Connexion à MongoDB
    try:
        client = MongoClient('mongodb://localhost:27018/?directConnection=true')
        # Tester la connexion
        client.admin.command('ping')
        print("✅ Connexion à MongoDB réussie !")
    except Exception as e:
        print(f"❌ Erreur de connexion à MongoDB: {e}")
        print("\n💡 Solutions:")
        print("1. Assurez-vous que MongoDB est installé")
        print("2. Démarrez MongoDB avec: mongod")
        print("3. Vérifiez que le port 27017 est disponible")
        return False
    
    # 2. Créer/accéder à la base de données
    db = client['telecom_admin']
    print(f"✅ Base de données 'telecom_admin' créée/accédée")
    
    # 3. Créer/accéder à la collection
    collection = db['dashbo_admin']
    print(f"✅ Collection 'dashbo_admin' créée/accédée")
    
    # 4. Créer un index unique sur l'email (évite les doublons)
    collection.create_index('email', unique=True)
    print("✅ Index unique sur l'email créé")
    
    # 5. Créer un utilisateur admin par défaut
    admin_user = {
        'firstname': 'Admin',
        'lastname': 'Principal',
        'email': 'admin@algerietelecom.dz',
        'password': generate_password_hash('Admin@123'),
        'phone': '+213 00 00 00 00',
        'wilaya': 'Alger',
        'role': 'super_admin',
        'is_active': True,
        'created_at': datetime.now(),
        'email_verified': True
    }
    
    # Vérifier si l'admin existe déjà
    existing_admin = collection.find_one({'email': 'admin@algerietelecom.dz'})
    if not existing_admin:
        collection.insert_one(admin_user)
        print("✅ Utilisateur admin créé avec succès!")
        print("   📧 Email: admin@algerietelecom.dz")
        print("   🔑 Mot de passe: Admin@123")
    else:
        print("⚠️ L'utilisateur admin existe déjà")
    
    # 6. Créer quelques utilisateurs de test (optionnel)
    test_users = [
        {
            'firstname': 'Karim',
            'lastname': 'Benali',
            'email': 'karim@test.com',
            'password': generate_password_hash('Test@123'),
            'phone': '+213 55 12 34 56',
            'wilaya': 'Alger',
            'role': 'user',
            'is_active': True,
            'created_at': datetime.now(),
            'email_verified': True
        },
        {
            'firstname': 'Fatima',
            'lastname': 'Zohra',
            'email': 'fatima@test.com',
            'password': generate_password_hash('Test@123'),
            'phone': '+213 66 78 90 12',
            'wilaya': 'Oran',
            'role': 'user',
            'is_active': True,
            'created_at': datetime.now(),
            'email_verified': True
        }
    ]
    
    for user in test_users:
        existing = collection.find_one({'email': user['email']})
        if not existing:
            collection.insert_one(user)
            print(f"✅ Utilisateur test créé: {user['email']}")
    
    # 7. Afficher les statistiques
    total_users = collection.count_documents({})
    print("-" * 50)
    print(f"📊 Statistiques de la base de données:")
    print(f"   - Base: telecom_admin")
    print(f"   - Collection: dashbo_admin")
    print(f"   - Total utilisateurs: {total_users}")
    print("-" * 50)
    print("✅ Base de données créée avec succès!")
    print("\n💡 Informations de connexion:")
    print("   URI: mongodb://localhost:27017/")
    print("   Database: telecom_admin")
    print("   Collection: dashbo_admin")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*50)
    print("   CRÉATION DE LA BASE DE DONNÉES")
    print("="*50 + "\n")
    
    success = create_database()
    
    if success:
        print("\n🎉 Vous pouvez maintenant lancer votre application Dash!")
        print("   Commandes:")
        print("   1. python app.py  # Pour lancer l'application")
        print("   2. Allez sur http://localhost:8050/register")
    else:
        print("\n❌ La création a échoué. Veuillez:")
        print("   1. Installer MongoDB: https://www.mongodb.com/try/download/community")
        print("   2. Démarrer MongoDB: exécutez 'mongod' dans un terminal")
        print("   3. Réessayer d'exécuter ce script")