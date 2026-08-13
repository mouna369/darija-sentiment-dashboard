# from pymongo import MongoClient
# from werkzeug.security import generate_password_hash, check_password_hash
# from datetime import datetime

# class DatabaseManager:
#     def __init__(self):
#         try:
#             self.client = MongoClient('mongodb://localhost:27018/?directConnection=true')
#             self.db = self.client['telecom_admin']
#             self.collection = self.db['dashbo_admin']
#             print("✅ Connexion MongoDB réussie")
#         except Exception as e:
#             print(f"❌ Erreur MongoDB: {e}")
#             raise
    
#     def _serialize_user(self, user):
#         if user:
#             if '_id' in user:
#                 user['_id'] = str(user['_id'])
#             if 'created_at' in user and user['created_at']:
#                 user['created_at'] = user['created_at'].isoformat()
#         return user
    
#     def register_user(self, user_data):
#         try:
#             if self.collection.find_one({'email': user_data['email']}):
#                 return {'success': False, 'message': 'Cet email est déjà utilisé'}
            
#             user_data['password'] = generate_password_hash(user_data['password'])
#             user_data['created_at'] = datetime.now()
#             user_data['is_active'] = True
            
#             result = self.collection.insert_one(user_data)
#             return {'success': True, 'message': 'Inscription réussie', 'user_id': str(result.inserted_id)}
#         except Exception as e:
#             return {'success': False, 'message': str(e)}
    
#     def login_user(self, email, password):
#         try:
#             user = self.collection.find_one({'email': email})
#             if not user or not check_password_hash(user['password'], password):
#                 return {'success': False, 'message': 'Email ou mot de passe incorrect'}
            
#             user.pop('password', None)
#             return {'success': True, 'message': 'Connexion réussie', 'user': self._serialize_user(user)}
#         except Exception as e:
#             return {'success': False, 'message': str(e)}


            

# db_manager = DatabaseManager()
# config/db_config.py
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        try:
            self.client = MongoClient('mongodb://localhost:27018/?directConnection=true')
            self.db = self.client['telecom_admin']
            self.collection = self.db['dashbo_admin']
            print("✅ Connexion MongoDB réussie")
        except Exception as e:
            print(f"❌ Erreur MongoDB: {e}")
            raise
    
    def _serialize_user(self, user):
        if user:
            if '_id' in user:
                user['_id'] = str(user['_id'])
            if 'created_at' in user and user['created_at']:
                user['created_at'] = user['created_at'].isoformat()
        return user
    
    def register_user(self, user_data):
        try:
            if self.collection.find_one({'email': user_data['email']}):
                return {'success': False, 'message': 'Cet email est déjà utilisé'}
            
            user_data['password'] = generate_password_hash(user_data['password'])
            user_data['created_at'] = datetime.now()
            user_data['is_active'] = True
            user_data['role'] = 'user'
            
            result = self.collection.insert_one(user_data)
            return {'success': True, 'message': 'Inscription réussie', 'user_id': str(result.inserted_id)}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def login_user(self, email, password):
        try:
            user = self.collection.find_one({'email': email})
            if not user or not check_password_hash(user['password'], password):
                return {'success': False, 'message': 'Email ou mot de passe incorrect'}
            
            user.pop('password', None)
            return {'success': True, 'message': 'Connexion réussie', 'user': self._serialize_user(user)}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_user_profile(self, email, update_data):
        """
        Mettre à jour le profil utilisateur dans MongoDB
        """
        try:
            # Construire l'objet de mise à jour
            updates = {}
            if 'firstname' in update_data and update_data['firstname']:
                updates['firstname'] = update_data['firstname']
            if 'lastname' in update_data and update_data['lastname']:
                updates['lastname'] = update_data['lastname']
            if 'phone' in update_data and update_data['phone']:
                updates['phone'] = update_data['phone']
            if 'wilaya' in update_data and update_data['wilaya']:
                updates['wilaya'] = update_data['wilaya']
            
            if not updates:
                return {'success': False, 'message': 'Aucune donnée à mettre à jour'}
            
            # Mettre à jour dans MongoDB
            result = self.collection.update_one(
                {'email': email},
                {'$set': updates}
            )
            
            if result.modified_count > 0:
                print(f"✅ MongoDB: Profil mis à jour pour {email} - {updates}")
                return {'success': True, 'message': 'Profil mis à jour avec succès'}
            else:
                print(f"⚠️ MongoDB: Aucune modification pour {email}")
                return {'success': False, 'message': 'Aucune modification effectuée'}
                
        except Exception as e:
            print(f"❌ MongoDB Erreur update_user_profile: {e}")
            return {'success': False, 'message': str(e)}
    
    def change_user_password(self, email, old_password, new_password):
        """
        Changer le mot de passe d'un utilisateur
        """
        try:
            user = self.collection.find_one({'email': email})
            
            if not user:
                return {'success': False, 'message': 'Utilisateur non trouvé'}
            
            if not check_password_hash(user['password'], old_password):
                return {'success': False, 'message': 'Ancien mot de passe incorrect'}
            
            hashed_password = generate_password_hash(new_password)
            
            result = self.collection.update_one(
                {'email': email},
                {'$set': {'password': hashed_password}}
            )
            
            if result.modified_count > 0:
                print(f"✅ MongoDB: Mot de passe changé pour {email}")
                return {'success': True, 'message': 'Mot de passe changé avec succès'}
            else:
                return {'success': False, 'message': 'Erreur lors du changement'}
                
        except Exception as e:
            print(f"❌ MongoDB Erreur change_user_password: {e}")
            return {'success': False, 'message': str(e)}
    
    def get_user_by_email(self, email):
        """Récupérer un utilisateur par son email"""
        try:
            user = self.collection.find_one({'email': email})
            if user:
                user.pop('password', None)
                return self._serialize_user(user)
            return None
        except Exception as e:
            print(f"❌ Erreur get_user_by_email: {e}")
            return None

# Instance globale
db_manager = DatabaseManager()