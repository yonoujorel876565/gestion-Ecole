from django.db import models
from django.contrib.auth.models import User

# Profils pour différencier les rôles
class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('eleve', 'Élève'),
        ('parent', 'Parent'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

class Eleve(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    matricule = models.CharField(max_length=30, unique=True)
    date_naissance = models.DateField(null=True, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    # À compléter avec classe, session, etc.

    def __str__(self):
        return self.user.get_full_name() if self.user else f"Élève {self.matricule}"

class Enseignant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    specialite = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    # À compléter avec matières, classes, etc.

    def __str__(self):
        return self.user.get_full_name() if self.user else f"Enseignant {self.specialite}"

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    enfants = models.ManyToManyField(Eleve, related_name='parents', blank=True)

    def __str__(self):
        return self.user.get_full_name() if self.user else "Parent"

class Session(models.Model):
    SESSION_CHOICES = [
        ('francophone', 'Francophone'),
        ('anglophone', 'Anglophone'),
    ]
    nom = models.CharField(max_length=20, choices=SESSION_CHOICES, unique=True)

    def __str__(self):
        return self.get_nom_display()

class Classe(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    nom = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.nom} ({self.session})"

class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.nom

class Inscription(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    annee_scolaire = models.CharField(max_length=9)  # ex: 2024-2025
    date_inscription = models.DateField(auto_now_add=True)
    accepte = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.eleve} - {self.classe} ({self.annee_scolaire})"

class Preinscription(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    date_preinscription = models.DateField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    def __str__(self):
        return f"Préinscription: {self.nom} {self.prenom} - {self.classe}"

class Paiement(models.Model):
    inscription = models.ForeignKey(Inscription, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(auto_now_add=True)
    TYPE_CHOICES = [
        ('frais_scolarite', 'Frais de scolarité'),
        ('inscription', 'Frais d\'inscription'),
        ('autre', 'Autre'),
    ]
    type_paiement = models.CharField(max_length=30, choices=TYPE_CHOICES)
    statut = models.CharField(max_length=20, choices=[('valide', 'Validé'), ('en_attente', 'En attente')], default='valide')

    def __str__(self):
        return f"{self.inscription.eleve} - {self.type_paiement} - {self.montant} FCFA"

class Cours(models.Model):
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    jour = models.CharField(max_length=10, choices=[
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
    ])
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    def __str__(self):
        return f"{self.matiere} - {self.classe} ({self.jour} {self.heure_debut}-{self.heure_fin})"

class Examen(models.Model):
    nom = models.CharField(max_length=100)
    date = models.DateField()
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nom} - {self.classe} - {self.matiere} ({self.date})"

class Note(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    valeur = models.DecimalField(max_digits=5, decimal_places=2)
    type_evaluation = models.CharField(max_length=30, choices=[
        ('devoir', 'Devoir'),
        ('composition', 'Composition'),
        ('oral', 'Oral'),
        ('autre', 'Autre'),
    ])

    def __str__(self):
        return f"{self.eleve} - {self.examen} : {self.valeur}"

class Bulletin(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE)
    periode = models.CharField(max_length=30)  # ex: Trimestre 1, 2, 3
    total = models.DecimalField(max_digits=6, decimal_places=2)
    appreciation = models.TextField(blank=True)
    date_edition = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Bulletin {self.eleve} - {self.periode}"

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    sujet = models.CharField(max_length=200)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation: {self.sujet}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"Message de {self.expediteur} - {self.date_envoi}"

class Notification(models.Model):
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Avertissement'),
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('system', 'Système'),
    ]
    
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    date_creation = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    lien = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.destinataire}"

class Horaire(models.Model):
    JOUR_CHOICES = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi'),
        ('dimanche', 'Dimanche'),
    ]
    
    nom = models.CharField(max_length=100)  # ex: "Horaire normal", "Horaire examens"
    jour = models.CharField(max_length=10, choices=JOUR_CHOICES)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    pause_debut = models.TimeField(null=True, blank=True)
    pause_fin = models.TimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['jour', 'heure_debut']
    
    def __str__(self):
        return f"{self.nom} - {self.get_jour_display()} ({self.heure_debut}-{self.heure_fin})"

class Sauvegarde(models.Model):
    TYPE_CHOICES = [
        ('complete', 'Sauvegarde complète'),
        ('partielle', 'Sauvegarde partielle'),
        ('automatique', 'Sauvegarde automatique'),
    ]
    
    nom = models.CharField(max_length=200)
    type_sauvegarde = models.CharField(max_length=20, choices=TYPE_CHOICES)
    fichier = models.FileField(upload_to='sauvegardes/')
    taille_fichier = models.BigIntegerField(help_text='Taille en octets')
    date_creation = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    reussi = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.date_creation.strftime('%d/%m/%Y %H:%M')}"
    
    def taille_mb(self):
        return round(self.taille_fichier / (1024 * 1024), 2)
