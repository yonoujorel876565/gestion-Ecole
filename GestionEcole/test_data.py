#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionEcole.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from Ecole.models import *

def create_test_data():
    print("Création des données de test...")
    
    # Créer les sessions
    session_fr, created = Session.objects.get_or_create(nom='francophone')
    session_en, created = Session.objects.get_or_create(nom='anglophone')
    print(f"Sessions créées: {session_fr}, {session_en}")
    
    # Créer les classes
    classes_fr = ['6e', '5e', '4e', '3e', '2nde', '1ere', 'Terminale']
    classes_en = ['Form1', 'Form2', 'Form3', 'Form4', 'Form5', 'Form6', 'Form7']
    
    for nom in classes_fr:
        Classe.objects.get_or_create(nom=nom, session=session_fr)
    for nom in classes_en:
        Classe.objects.get_or_create(nom=nom, session=session_en)
    print("Classes créées")
    
    # Créer les matières
    matieres = ['Mathématiques', 'Français', 'Anglais', 'Histoire', 'Géographie', 'Sciences', 'Physique', 'Chimie']
    for nom in matieres:
        Matiere.objects.get_or_create(nom=nom)
    print("Matières créées")
    
    # Créer un admin
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Admin',
            'last_name': 'Ecole',
            'email': 'admin@ecole.com',
            'password': make_password('admin123'),
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        Profile.objects.create(user=admin_user, role='admin')
        print("Admin créé: admin/admin123")
    
    # Créer un enseignant
    enseignant_user, created = User.objects.get_or_create(
        username='enseignant',
        defaults={
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@ecole.com',
            'password': make_password('enseignant123')
        }
    )
    if created:
        Profile.objects.create(user=enseignant_user, role='enseignant')
        Enseignant.objects.create(user=enseignant_user, specialite='Mathématiques', telephone='0123456789')
        print("Enseignant créé: enseignant/enseignant123")
    
    # Créer un élève
    eleve_user, created = User.objects.get_or_create(
        username='eleve',
        defaults={
            'first_name': 'Marie',
            'last_name': 'Martin',
            'email': 'marie.martin@ecole.com',
            'password': make_password('eleve123')
        }
    )
    if created:
        Profile.objects.create(user=eleve_user, role='eleve')
        eleve = Eleve.objects.create(
            user=eleve_user,
            matricule='ELEVE001',
            date_naissance='2010-05-15',
            telephone='0987654321'
        )
        print("Élève créé: eleve/eleve123")
    
    # Créer un parent
    parent_user, created = User.objects.get_or_create(
        username='parent',
        defaults={
            'first_name': 'Pierre',
            'last_name': 'Martin',
            'email': 'pierre.martin@email.com',
            'password': make_password('parent123')
        }
    )
    if created:
        Profile.objects.create(user=parent_user, role='parent')
        parent = Parent.objects.create(
            user=parent_user,
            telephone='0555666777'
        )
        if 'eleve' in locals():
            parent.enfants.add(eleve)
        print("Parent créé: parent/parent123")
    
    # Créer des cours
    classe_6e = Classe.objects.get(nom='6e', session=session_fr)
    matiere_math = Matiere.objects.get(nom='Mathématiques')
    enseignant = Enseignant.objects.get(user=enseignant_user)
    
    cours, created = Cours.objects.get_or_create(
        matiere=matiere_math,
        classe=classe_6e,
        enseignant=enseignant,
        jour='lundi',
        heure_debut='08:00',
        heure_fin='09:00'
    )
    if created:
        print("Cours créé: Mathématiques 6e")
    
    # Créer une inscription pour l'élève
    if 'eleve' in locals():
        inscription, created = Inscription.objects.get_or_create(
            eleve=eleve,
            classe=classe_6e,
            annee_scolaire='2024-2025',
            defaults={'accepte': True}
        )
        if created:
            print("Inscription créée pour l'élève")
    
    # Créer un examen
    examen, created = Examen.objects.get_or_create(
        nom='Contrôle Mathématiques',
        date='2024-12-15',
        session=session_fr,
        classe=classe_6e,
        matiere=matiere_math
    )
    if created:
        print("Examen créé")
    
    # Créer une note pour l'élève
    if 'eleve' in locals():
        note, created = Note.objects.get_or_create(
            eleve=eleve,
            examen=examen,
            defaults={'valeur': 15.5, 'type_evaluation': 'composition'}
        )
        if created:
            print("Note créée pour l'élève")
    
    print("\n=== DONNÉES DE TEST CRÉÉES ===")
    print("Comptes de test:")
    print("- Admin: admin/admin123")
    print("- Enseignant: enseignant/enseignant123")
    print("- Élève: eleve/eleve123")
    print("- Parent: parent/parent123")
    print("\nL'application est prête pour les tests!")

if __name__ == '__main__':
    create_test_data() 