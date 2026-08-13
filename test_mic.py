# Créez un script test_mic.py
import speech_recognition as sr

def list_microphones():
    """Liste tous les microphones disponibles"""
    try:
        mics = sr.Microphone.list_microphone_names()
        print(f"Microphones trouvés: {len(mics)}")
        for i, mic in enumerate(mics):
            print(f"  [{i}] {mic}")
        
        if not mics:
            print("❌ Aucun microphone trouvé!")
            return []
        return mics
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

if __name__ == "__main__":
    list_microphones()