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

def create_admin():
    print("Création d'un administrateur...")
    
    # Créer un admin avec des identifiants spécifiques
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
        print("✅ Administrateur créé avec succès!")
        print("📧 Email: admin@ecole.com")
        print("🔑 Mot de passe: admin123")
    else:
        print("ℹ️ L'administrateur existe déjà")
        print("📧 Email: admin@ecole.com")
        print("🔑 Mot de passe: admin123")
    
    print("\n=== INFORMATIONS DE CONNEXION ===")
    print("URL: http://127.0.0.1:8000/login/")
    print("Email: admin@ecole.com")
    print("Mot de passe: admin123")
    print("Rôle: Administrateur")
    print("\nVous pouvez maintenant vous connecter!")

if __name__ == '__main__':
    create_admin() 