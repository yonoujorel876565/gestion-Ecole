#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GestionEcole.settings')
django.setup()

from django.urls import reverse, resolve
from django.urls.exceptions import NoReverseMatch, Resolver404

def verifier_urls():
    print("🔍 Vérification des URLs de l'application...")
    print("=" * 60)
    
    # URLs à vérifier
    urls_a_tester = [
        ('home', '/'),
        ('login', '/login/'),
        ('dashboard', '/dashboard/'),
        ('gestion_enseignants', '/admin/gestion-enseignants/'),
        ('gestion_eleves', '/admin/gestion-eleves/'),
        ('gestion_parents', '/admin/gestion-parents/'),
        ('gestion_administrateurs', '/admin/gestion-administrateurs/'),
        ('gestion_matieres', '/admin/gestion-matieres/'),
        ('gestion_cours', '/admin/gestion-cours/'),
        ('gestion_examens', '/admin/gestion-examens/'),
        ('gestion_classes', '/admin/gestion-classes/'),
        ('gestion_frais', '/admin/gestion-frais/'),
        ('gestion_factures', '/admin/factures/'),
        ('rapport_financier', '/admin/rapport-financier/'),
        ('gestion_paiements', '/admin/paiements/'),
        ('liste_preinscriptions', '/admin/preinscriptions/'),
        ('validation_preinscriptions', '/admin/validation-preinscriptions/'),
        ('preinscriptions_validees', '/admin/preinscriptions-validees/'),
        ('generer_bulletins', '/admin/generer-bulletins/'),
        ('mes_paiements', '/mes-paiements/'),
        ('mes_cours', '/mes-cours/'),
        ('mes_notes', '/mes-notes/'),
        ('mes_bulletins', '/mes-bulletins/'),
        ('saisie_notes', '/saisie-notes/'),
        ('emploi_du_temps', '/emploi-du-temps/'),
        ('conversations', '/conversations/'),
        ('nouvelle_conversation', '/nouvelle-conversation/'),
    ]
    
    print("📋 Vérification des URLs:")
    urls_ok = 0
    urls_erreur = 0
    
    for nom, url in urls_a_tester:
        try:
            # Vérifier que l'URL peut être résolue
            resolve(url)
            print(f"   ✅ {nom}: {url}")
            urls_ok += 1
        except Resolver404:
            print(f"   ❌ {nom}: {url} - URL non trouvée")
            urls_erreur += 1
        except Exception as e:
            print(f"   ❌ {nom}: {url} - Erreur: {e}")
            urls_erreur += 1
    
    print()
    print("=" * 60)
    print(f"📊 Résumé: {urls_ok} URLs OK, {urls_erreur} erreurs")
    
    if urls_erreur == 0:
        print("🎉 Toutes les URLs sont correctement configurées!")
    else:
        print("⚠️  Certaines URLs ont des problèmes")
    
    print()
    print("🚀 L'application est prête pour les tests!")
    print("   Accédez à: http://127.0.0.1:8000/login/")
    print()
    print("📝 URLs importantes:")
    print("   - Connexion: http://127.0.0.1:8000/login/")
    print("   - Gestion enseignants: http://127.0.0.1:8000/admin/gestion-enseignants/")
    print("   - Gestion élèves: http://127.0.0.1:8000/admin/gestion-eleves/")
    print("   - Gestion parents: http://127.0.0.1:8000/admin/gestion-parents/")
    print("   - Gestion administrateurs: http://127.0.0.1:8000/admin/gestion-administrateurs/")

if __name__ == '__main__':
    verifier_urls() 