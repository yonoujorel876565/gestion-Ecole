#!/usr/bin/env python
"""
Script pour créer ou réinitialiser des utilisateurs de test pour l'application Gestion École
Crée un enseignant, un élève et un parent avec leurs profils respectifs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionEcole.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from Ecole.models import Profile, Enseignant, Eleve, Parent, Session, Classe, Inscription

def create_test_users():
    print("=== Création ou réinitialisation des utilisateurs de test ===")
    
    # Créer une session et une classe si elles n'existent pas
    session, _ = Session.objects.get_or_create(
        nom='francophone',
        defaults={'nom': 'francophone'}
    )
    classe, _ = Classe.objects.get_or_create(
        nom='6ème A',
        session=session,
        defaults={'nom': '6ème A', 'session': session}
    )
    
    # 1. Enseignant
    print("\n--- Enseignant ---")
    try:
        enseignant_user = User.objects.get(username='enseignant')
        enseignant_user.first_name = 'Marie'
        enseignant_user.last_name = 'Dupont'
        enseignant_user.email = 'enseignant@ecole.com'
        enseignant_user.password = make_password('enseignant123')
        enseignant_user.is_active = True
        enseignant_user.save()
        print("✓ Utilisateur enseignant réinitialisé")
    except User.DoesNotExist:
        enseignant_user = User.objects.create(
            username='enseignant',
            first_name='Marie',
            last_name='Dupont',
            email='enseignant@ecole.com',
            password=make_password('enseignant123'),
            is_active=True
        )
        print("✓ Utilisateur enseignant créé")
    Profile.objects.update_or_create(
        user=enseignant_user,
        defaults={'role': 'enseignant'}
    )
    Enseignant.objects.update_or_create(
        user=enseignant_user,
        defaults={'specialite': 'Mathématiques', 'telephone': '+237 6XX XXX XXX'}
    )
    
    # 2. Élève
    print("\n--- Élève ---")
    try:
        eleve_user = User.objects.get(username='eleve')
        eleve_user.first_name = 'Jean'
        eleve_user.last_name = 'Martin'
        eleve_user.email = 'eleve@ecole.com'
        eleve_user.password = make_password('eleve123')
        eleve_user.is_active = True
        eleve_user.save()
        print("✓ Utilisateur élève réinitialisé")
    except User.DoesNotExist:
        eleve_user = User.objects.create(
            username='eleve',
            first_name='Jean',
            last_name='Martin',
            email='eleve@ecole.com',
            password=make_password('eleve123'),
            is_active=True
        )
        print("✓ Utilisateur élève créé")
    Profile.objects.update_or_create(
        user=eleve_user,
        defaults={'role': 'eleve'}
    )
    eleve, _ = Eleve.objects.update_or_create(
        user=eleve_user,
        defaults={
            'matricule': 'ELEVE001',
            'date_naissance': '2010-05-15',
            'adresse': "123 Rue de l'École, Yaoundé",
            'telephone': '+237 6XX XXX XXX'
        }
    )
    Inscription.objects.update_or_create(
        eleve=eleve,
        classe=classe,
        defaults={'annee_scolaire': '2024-2025', 'accepte': True}
    )
    
    # 3. Parent
    print("\n--- Parent ---")
    try:
        parent_user = User.objects.get(username='parent')
        parent_user.first_name = 'Pierre'
        parent_user.last_name = 'Martin'
        parent_user.email = 'parent@ecole.com'
        parent_user.password = make_password('parent123')
        parent_user.is_active = True
        parent_user.save()
        print("✓ Utilisateur parent réinitialisé")
    except User.DoesNotExist:
        parent_user = User.objects.create(
            username='parent',
            first_name='Pierre',
            last_name='Martin',
            email='parent@ecole.com',
            password=make_password('parent123'),
            is_active=True
        )
        print("✓ Utilisateur parent créé")
    Profile.objects.update_or_create(
        user=parent_user,
        defaults={'role': 'parent'}
    )
    parent, _ = Parent.objects.update_or_create(
        user=parent_user,
        defaults={'telephone': '+237 6XX XXX XXX', 'adresse': "123 Rue de l'École, Yaoundé"}
    )
    parent.enfants.set([eleve])
    parent.save()
    print(f"✓ Enfant {eleve.matricule} associé au parent")
    
    print("\n=== Comptes prêts ===")
    print("👨‍🏫 ENSEIGNANT: enseignant@ecole.com / enseignant123")
    print("👨‍🎓 ÉLÈVE: eleve@ecole.com / eleve123")
    print("👨‍👩‍👧‍👦 PARENT: parent@ecole.com / parent123")
    print("🌐 Accède à http://localhost:8000/login/ pour te connecter")

if __name__ == '__main__':
    create_test_users() 