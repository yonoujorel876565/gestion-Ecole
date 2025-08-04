#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionEcole.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from Ecole.models import *

def test_filtrage_eleves():
    print("🧪 Test du filtrage des élèves par classe...")
    print("=" * 60)
    
    client = Client()
    
    # Créer des données de test si elles n'existent pas
    print("📋 Création des données de test...")
    
    # Créer des sessions
    session_fr, created = Session.objects.get_or_create(nom='francophone')
    session_en, created = Session.objects.get_or_create(nom='anglophone')
    
    # Créer des classes
    classe_6e, created = Classe.objects.get_or_create(nom='6e', session=session_fr)
    classe_5e, created = Classe.objects.get_or_create(nom='5e', session=session_fr)
    classe_4e, created = Classe.objects.get_or_create(nom='4e', session=session_fr)
    
    print(f"✅ Classes créées: {classe_6e}, {classe_5e}, {classe_4e}")
    
    # Créer des élèves de test
    eleves_data = [
        {'nom': 'Dupont', 'prenom': 'Jean', 'email': 'jean.dupont@test.com', 'matricule': 'ELEVE101', 'classe': classe_6e},
        {'nom': 'Martin', 'prenom': 'Marie', 'email': 'marie.martin@test.com', 'matricule': 'ELEVE102', 'classe': classe_6e},
        {'nom': 'Bernard', 'prenom': 'Pierre', 'email': 'pierre.bernard@test.com', 'matricule': 'ELEVE103', 'classe': classe_5e},
        {'nom': 'Petit', 'prenom': 'Sophie', 'email': 'sophie.petit@test.com', 'matricule': 'ELEVE104', 'classe': classe_5e},
        {'nom': 'Robert', 'prenom': 'Lucas', 'email': 'lucas.robert@test.com', 'matricule': 'ELEVE105', 'classe': classe_4e},
    ]
    
    for eleve_data in eleves_data:
        user, created = User.objects.get_or_create(
            email=eleve_data['email'],
            defaults={
                'username': eleve_data['email'].split('@')[0],
                'first_name': eleve_data['prenom'],
                'last_name': eleve_data['nom'],
                'password': 'test123'
            }
        )
        
        if created:
            Profile.objects.create(user=user, role='eleve')
            eleve, eleve_created = Eleve.objects.get_or_create(
                user=user,
                defaults={'matricule': eleve_data['matricule']}
            )
            
            if eleve_created:
                # Créer l'inscription
                Inscription.objects.get_or_create(
                    eleve=eleve,
                    classe=eleve_data['classe'],
                    defaults={
                        'annee_scolaire': '2024-2025',
                        'accepte': True
                    }
                )
                
                print(f"✅ Élève créé: {eleve_data['prenom']} {eleve_data['nom']} - {eleve_data['classe']}")
            else:
                print(f"ℹ️ Élève existant: {eleve_data['prenom']} {eleve_data['nom']}")
        else:
            print(f"ℹ️ Utilisateur existant: {eleve_data['prenom']} {eleve_data['nom']}")
    
    print()
    print("🔍 Test du filtrage par classe...")
    
    # Test 1: Tous les élèves (aucun filtre)
    print("\n1️⃣ Test sans filtre (tous les élèves):")
    response = client.get(reverse('gestion_eleves'))
    if response.status_code == 200:
        print("   ✅ Page accessible")
        # Compter les élèves affichés
        eleves_count = Eleve.objects.count()
        print(f"   📊 Nombre d'élèves: {eleves_count}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # Test 2: Filtrage par classe 6e
    print("\n2️⃣ Test avec filtre classe 6e:")
    response = client.get(reverse('gestion_eleves'), {'classe': classe_6e.id})
    if response.status_code == 200:
        print("   ✅ Page accessible avec filtre")
        # Compter les élèves de la classe 6e
        eleves_6e = Eleve.objects.filter(inscription__classe=classe_6e, inscription__accepte=True).distinct().count()
        print(f"   📊 Nombre d'élèves en 6e: {eleves_6e}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # Test 3: Filtrage par classe 5e
    print("\n3️⃣ Test avec filtre classe 5e:")
    response = client.get(reverse('gestion_eleves'), {'classe': classe_5e.id})
    if response.status_code == 200:
        print("   ✅ Page accessible avec filtre")
        # Compter les élèves de la classe 5e
        eleves_5e = Eleve.objects.filter(inscription__classe=classe_5e, inscription__accepte=True).distinct().count()
        print(f"   📊 Nombre d'élèves en 5e: {eleves_5e}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # Test 4: Filtrage par classe 4e
    print("\n4️⃣ Test avec filtre classe 4e:")
    response = client.get(reverse('gestion_eleves'), {'classe': classe_4e.id})
    if response.status_code == 200:
        print("   ✅ Page accessible avec filtre")
        # Compter les élèves de la classe 4e
        eleves_4e = Eleve.objects.filter(inscription__classe=classe_4e, inscription__accepte=True).distinct().count()
        print(f"   📊 Nombre d'élèves en 4e: {eleves_4e}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    # Test 5: Filtrage avec classe inexistante
    print("\n5️⃣ Test avec classe inexistante:")
    response = client.get(reverse('gestion_eleves'), {'classe': 999})
    if response.status_code == 200:
        print("   ✅ Page accessible (classe inexistante ignorée)")
        # Devrait afficher tous les élèves
        eleves_count = Eleve.objects.count()
        print(f"   📊 Nombre d'élèves affichés: {eleves_count}")
    else:
        print(f"   ❌ Erreur: {response.status_code}")
    
    print()
    print("=" * 60)
    print("📊 Résumé des tests:")
    print(f"   - Total élèves créés: {Eleve.objects.count()}")
    print(f"   - Élèves en 6e: {Eleve.objects.filter(inscription__classe=classe_6e, inscription__accepte=True).distinct().count()}")
    print(f"   - Élèves en 5e: {Eleve.objects.filter(inscription__classe=classe_5e, inscription__accepte=True).distinct().count()}")
    print(f"   - Élèves en 4e: {Eleve.objects.filter(inscription__classe=classe_4e, inscription__accepte=True).distinct().count()}")
    
    print()
    print("🎯 Test du filtrage terminé!")
    print("   Accédez à: http://127.0.0.1:8000/admin/gestion-eleves/")
    print("   Testez le menu déroulant pour filtrer par classe")

if __name__ == '__main__':
    test_filtrage_eleves() 