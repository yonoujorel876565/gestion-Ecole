from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Preinscription, Classe, Session, Eleve, Inscription
from django.test import Client
import datetime

# Create your tests here.

class ValiderPreinscriptionTestCase(TestCase):
    def setUp(self):
        self.session = Session.objects.create(nom='francophone')
        self.classe = Classe.objects.create(nom='6e', session=self.session)
        self.preinsc = Preinscription.objects.create(
            nom='Test',
            prenom='Eleve',
            date_naissance=datetime.date(2010, 1, 1),
            telephone='0600000000',
            email='testeleve@example.com',
            session=self.session,
            classe=self.classe
        )
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.client = Client()
        self.client.force_login(self.admin)

    def test_valider_preinscription_cree_eleve_et_inscription(self):
        url = reverse('valider_preinscription', args=[self.preinsc.id])
        try:
            response = self.client.post(url)
        except Exception as e:
            import traceback; traceback.print_exc(); raise
        self.preinsc.refresh_from_db()
        self.assertTrue(self.preinsc.traite)
        user = User.objects.get(email='testeleve@example.com')
        eleve = Eleve.objects.get(user=user)
        inscription = Inscription.objects.get(eleve=eleve, classe=self.classe)
        self.assertEqual(user.first_name, 'Eleve')
        self.assertEqual(user.last_name, 'Test')
        self.assertTrue(inscription.accepte)
        self.assertRedirects(response, reverse('liste_preinscriptions'))
