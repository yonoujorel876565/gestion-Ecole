from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.forms import modelformset_factory
from django.db.models import Avg, Sum, Count
from django.utils import timezone
from .models import *
from django import forms
import random
import string

# Create your views here.

class LoginForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('eleve', 'Élève'),
        ('parent', 'Parent'),
    ]
    
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Entrez votre adresse email'
        })
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Entrez votre mot de passe'
        })
    )
    role = forms.ChoiceField(
        label='Rôle',
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

def home(request):
    return render(request, 'home.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            
            # Authentification de l'utilisateur avec email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user is not None:
                    # Vérification du rôle
                    try:
                        profile = Profile.objects.get(user=user)
                        if profile.role == role:
                            login(request, user)
                            messages.success(request, f'Connexion réussie ! Bienvenue {user.get_full_name()}')
                            return redirect('dashboard')
                        else:
                            role_display = dict(form.fields['role'].choices)[role]
                            messages.error(request, f'Ce compte n\'a pas le rôle "{role_display}". Veuillez sélectionner le bon rôle.')
                    except Profile.DoesNotExist:
                        messages.error(request, 'Profil utilisateur introuvable.')
                else:
                    messages.error(request, 'Adresse email ou mot de passe incorrect.')
            except User.DoesNotExist:
                messages.error(request, 'Aucun compte trouvé avec cette adresse email.')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')

@login_required
def dashboard(request):
    profile = Profile.objects.get(user=request.user)
    
    if profile.role == 'admin':
        # Statistiques pour l'admin
        total_eleves = Eleve.objects.count()
        total_enseignants = Enseignant.objects.count()
        total_classes = Classe.objects.count()
        total_matieres = Matiere.objects.count()
        preinscriptions_en_attente = Preinscription.objects.filter(traite=False).count()
        total_cours = Cours.objects.count()
        total_examens = Examen.objects.count()
        total_paiements = Paiement.objects.count()
        total_bulletins = Bulletin.objects.count()
        
        # Statistiques financières
        total_montant_paiements = Paiement.objects.filter(statut='valide').aggregate(total=models.Sum('montant'))['total'] or 0
        
        context = {
            'total_eleves': total_eleves,
            'total_enseignants': total_enseignants,
            'total_classes': total_classes,
            'total_matieres': total_matieres,
            'preinscriptions_en_attente': preinscriptions_en_attente,
            'total_cours': total_cours,
            'total_examens': total_examens,
            'total_paiements': total_paiements,
            'total_bulletins': total_bulletins,
            'total_montant_paiements': total_montant_paiements,
        }
        return render(request, 'dashboards/admin_dashboard.html', context)
    
    elif profile.role == 'enseignant':
        enseignant = Enseignant.objects.get(user=request.user)
        cours = Cours.objects.filter(enseignant=enseignant)
        cours_count = cours.count()
        
        # Compter les élèves
        classes_enseignees = cours.values_list('classe', flat=True).distinct()
        eleves_count = Eleve.objects.filter(inscription__classe__in=classes_enseignees, inscription__accepte=True).count()
        
        # Calculer les heures par semaine
        heures_count = cours.count()  # Simplifié pour l'exemple
        
        # Messages non lus
        messages_count = Message.objects.filter(conversation__participants=request.user, lu=False).count()
        
        # Notes récentes
        recent_notes = Note.objects.filter(examen__matiere__in=cours.values('matiere')).order_by('-examen__date')[:5]
        
        context = {
            'cours_count': cours_count,
            'eleves_count': eleves_count,
            'heures_count': heures_count,
            'messages_count': messages_count,
            'recent_notes': recent_notes,
        }
        return render(request, 'dashboards/enseignant_dashboard.html', context)
    
    elif profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        inscription = Inscription.objects.filter(eleve=eleve, accepte=True).first()
        
        if inscription:
            cours_count = Cours.objects.filter(classe=inscription.classe).count()
            notes_count = Note.objects.filter(eleve=eleve).count()
            moyenne = Note.objects.filter(eleve=eleve).aggregate(moyenne=Avg('valeur'))['moyenne'] or 0
            messages_count = Message.objects.filter(conversation__participants=request.user, lu=False).count()
            
            context = {
                'cours_count': cours_count,
                'notes_count': notes_count,
                'moyenne': round(moyenne, 2),
                'messages_count': messages_count,
                'classe': inscription.classe,
            }
        else:
            context = {
                'cours_count': 0,
                'notes_count': 0,
                'moyenne': 0,
                'messages_count': 0,
                'classe': None,
            }
        return render(request, 'dashboards/eleve_dashboard.html', context)
    
    elif profile.role == 'parent':
        parent = Parent.objects.get(user=request.user)
        enfants = parent.enfants.all()
        enfants_count = enfants.count()
        
        # Calculer la moyenne générale des enfants
        toutes_notes = Note.objects.filter(eleve__in=enfants)
        moyenne_generale = toutes_notes.aggregate(moyenne=Avg('valeur'))['moyenne'] or 0
        
        # Compter les paiements
        inscriptions = Inscription.objects.filter(eleve__in=enfants)
        paiements_count = Paiement.objects.filter(inscription__in=inscriptions).count()
        
        # Messages non lus
        messages_count = Message.objects.filter(conversation__participants=request.user, lu=False).count()
        
        # Préparer les données des enfants
        for enfant in enfants:
            enfant.moyenne = Note.objects.filter(eleve=enfant).aggregate(moyenne=Avg('valeur'))['moyenne'] or 0
            enfant.notes_count = Note.objects.filter(eleve=enfant).count()
        
        context = {
            'enfants_count': enfants_count,
            'moyenne_generale': round(moyenne_generale, 2),
            'paiements_count': paiements_count,
            'messages_count': messages_count,
            'enfants': enfants,
            'recent_activities': [],  # À implémenter si nécessaire
        }
        return render(request, 'dashboards/parent_dashboard.html', context)
    
    else:
        return render(request, 'home.html')

class PreinscriptionForm(forms.ModelForm):
    class Meta:
        model = Preinscription
        fields = ['nom', 'prenom', 'date_naissance', 'telephone', 'email', 'session', 'classe']
        labels = {
            'nom': 'Nom de famille',
            'prenom': 'Prénom',
            'date_naissance': 'Date de naissance',
            'telephone': 'Numéro de téléphone',
            'email': 'Adresse email',
            'session': 'Session',
            'classe': 'Classe souhaitée'
        }
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Entrez votre nom de famille'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Entrez votre prénom'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: +237 6XX XXX XXX'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'exemple@email.com'
            }),
            'session': forms.Select(attrs={
                'class': 'form-select'
            }),
            'classe': forms.Select(attrs={
                'class': 'form-select'
            })
        }

def preinscription(request):
    if request.method == 'POST':
        form = PreinscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'preinscription_success.html')
    else:
        form = PreinscriptionForm()
    return render(request, 'preinscription.html', {'form': form})

def liste_preinscriptions(request):
    if not request.user.is_staff:
        return redirect('home')
    preinscriptions = Preinscription.objects.filter(traite=False)
    return render(request, 'liste_preinscriptions.html', {'preinscriptions': preinscriptions})

@staff_member_required
def validation_preinscriptions(request):
    """Vue dédiée pour la validation des préinscriptions avec interface moderne"""
    preinscriptions = Preinscription.objects.filter(traite=False).order_by('-date_preinscription')
    
    # Statistiques pour le dashboard
    total_preinscriptions = preinscriptions.count()
    preinscriptions_aujourd_hui = preinscriptions.filter(date_preinscription=timezone.now().date()).count()
    
    context = {
        'preinscriptions': preinscriptions,
        'total_preinscriptions': total_preinscriptions,
        'preinscriptions_aujourd_hui': preinscriptions_aujourd_hui,
    }
    return render(request, 'validation_preinscriptions.html', context)

# ==================== VUES DE GESTION ADMINISTRATIVE ====================

@staff_member_required
def gestion_matieres(request):
    """Gestion des matières"""
    matieres = Matiere.objects.all().order_by('nom')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            nom = request.POST.get('nom')
            description = request.POST.get('description')
            Matiere.objects.create(nom=nom, description=description)
            messages.success(request, f'Matière "{nom}" ajoutée avec succès.')
        elif action == 'modifier':
            matiere_id = request.POST.get('matiere_id')
            matiere = Matiere.objects.get(id=matiere_id)
            matiere.nom = request.POST.get('nom')
            matiere.description = request.POST.get('description')
            matiere.save()
            messages.success(request, f'Matière "{matiere.nom}" modifiée avec succès.')
        elif action == 'supprimer':
            matiere_id = request.POST.get('matiere_id')
            matiere = Matiere.objects.get(id=matiere_id)
            nom = matiere.nom
            matiere.delete()
            messages.success(request, f'Matière "{nom}" supprimée avec succès.')
    
    return render(request, 'admin/gestion_matieres.html', {'matieres': matieres})

@staff_member_required
def gestion_cours(request):
    """Gestion des cours"""
    cours = Cours.objects.all().select_related('matiere', 'classe', 'enseignant').order_by('classe', 'jour', 'heure_debut')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            matiere_id = request.POST.get('matiere')
            classe_id = request.POST.get('classe')
            enseignant_id = request.POST.get('enseignant')
            jour = request.POST.get('jour')
            heure_debut = request.POST.get('heure_debut')
            heure_fin = request.POST.get('heure_fin')
            
            Cours.objects.create(
                matiere_id=matiere_id,
                classe_id=classe_id,
                enseignant_id=enseignant_id,
                jour=jour,
                heure_debut=heure_debut,
                heure_fin=heure_fin
            )
            messages.success(request, 'Cours ajouté avec succès.')
        elif action == 'supprimer':
            cours_id = request.POST.get('cours_id')
            cours_obj = Cours.objects.get(id=cours_id)
            cours_obj.delete()
            messages.success(request, 'Cours supprimé avec succès.')
    
    matieres = Matiere.objects.all()
    classes = Classe.objects.all()
    enseignants = Enseignant.objects.all()
    
    return render(request, 'admin/gestion_cours.html', {
        'cours': cours,
        'matieres': matieres,
        'classes': classes,
        'enseignants': enseignants
    })

@staff_member_required
def gestion_examens(request):
    """Gestion des examens"""
    examens = Examen.objects.all().select_related('session', 'classe', 'matiere').order_by('-date')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            nom = request.POST.get('nom')
            date = request.POST.get('date')
            session_id = request.POST.get('session')
            classe_id = request.POST.get('classe')
            matiere_id = request.POST.get('matiere')
            
            Examen.objects.create(
                nom=nom,
                date=date,
                session_id=session_id,
                classe_id=classe_id,
                matiere_id=matiere_id
            )
            messages.success(request, f'Examen "{nom}" ajouté avec succès.')
        elif action == 'supprimer':
            examen_id = request.POST.get('examen_id')
            examen = Examen.objects.get(id=examen_id)
            nom = examen.nom
            examen.delete()
            messages.success(request, f'Examen "{nom}" supprimé avec succès.')
    
    sessions = Session.objects.all()
    classes = Classe.objects.all()
    matieres = Matiere.objects.all()
    
    return render(request, 'admin/gestion_examens.html', {
        'examens': examens,
        'sessions': sessions,
        'classes': classes,
        'matieres': matieres
    })

@staff_member_required
def gestion_classes(request):
    """Gestion des classes"""
    classes = Classe.objects.all().select_related('session').order_by('session', 'nom')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            nom = request.POST.get('nom')
            session_id = request.POST.get('session')
            Classe.objects.create(nom=nom, session_id=session_id)
            messages.success(request, f'Classe "{nom}" ajoutée avec succès.')
        elif action == 'modifier':
            classe_id = request.POST.get('classe_id')
            classe = Classe.objects.get(id=classe_id)
            classe.nom = request.POST.get('nom')
            classe.session_id = request.POST.get('session')
            classe.save()
            messages.success(request, f'Classe "{classe.nom}" modifiée avec succès.')
        elif action == 'supprimer':
            classe_id = request.POST.get('classe_id')
            classe = Classe.objects.get(id=classe_id)
            nom = classe.nom
            classe.delete()
            messages.success(request, f'Classe "{nom}" supprimée avec succès.')
    
    sessions = Session.objects.all()
    
    return render(request, 'admin/gestion_classes.html', {
        'classes': classes,
        'sessions': sessions
    })

@staff_member_required
def gestion_frais(request):
    """Gestion des frais de scolarité"""
    # Cette vue gère les frais de scolarité par classe
    classes = Classe.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'definir_frais':
            classe_id = request.POST.get('classe')
            frais_inscription = request.POST.get('frais_inscription')
            frais_scolarite = request.POST.get('frais_scolarite')
            # Ici vous pourriez créer un modèle FraisScolarite pour stocker ces données
            messages.success(request, 'Frais définis avec succès.')
    
    return render(request, 'admin/gestion_frais.html', {'classes': classes})

@staff_member_required
def gestion_enseignants(request):
    """Gestion des enseignants"""
    enseignants = Enseignant.objects.all().select_related('user').order_by('user__last_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            specialite = request.POST.get('specialite')
            telephone = request.POST.get('telephone')
            password = User.objects.make_random_password()
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            
            Profile.objects.create(user=user, role='enseignant')
            Enseignant.objects.create(
                user=user,
                specialite=specialite,
                telephone=telephone
            )
            
            messages.success(request, f'Enseignant "{first_name} {last_name}" ajouté avec succès. Mot de passe: {password}')
        elif action == 'supprimer':
            enseignant_id = request.POST.get('enseignant_id')
            enseignant = Enseignant.objects.get(id=enseignant_id)
            nom = f"{enseignant.user.first_name} {enseignant.user.last_name}"
            enseignant.user.delete()  # Cela supprime aussi le profil et l'enseignant
            messages.success(request, f'Enseignant "{nom}" supprimé avec succès.')
    
    return render(request, 'admin/gestion_enseignants.html', {'enseignants': enseignants})

@staff_member_required
def gestion_eleves(request):
    """Gestion des élèves"""
    # Récupérer toutes les classes pour le menu déroulant
    classes = Classe.objects.all().order_by('session__nom', 'nom')
    
    # Récupérer tous les élèves avec leurs inscriptions
    eleves = Eleve.objects.all().select_related('user').prefetch_related('inscription_set__classe').order_by('user__last_name')
    
    # Filtrage par classe si spécifié
    classe_id = request.GET.get('classe')
    if classe_id and classe_id != '':
        try:
            classe = Classe.objects.get(id=classe_id)
            # Filtrer les élèves qui ont une inscription dans cette classe
            eleves = eleves.filter(inscription__classe=classe, inscription__accepte=True).distinct()
        except Classe.DoesNotExist:
            pass
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            matricule = request.POST.get('matricule')
            date_naissance = request.POST.get('date_naissance')
            adresse = request.POST.get('adresse')
            telephone = request.POST.get('telephone')
            password = User.objects.make_random_password()
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            
            Profile.objects.create(user=user, role='eleve')
            Eleve.objects.create(
                user=user,
                matricule=matricule,
                date_naissance=date_naissance,
                adresse=adresse,
                telephone=telephone
            )
            
            messages.success(request, f'Élève "{first_name} {last_name}" ajouté avec succès. Mot de passe: {password}')
        elif action == 'supprimer':
            eleve_id = request.POST.get('eleve_id')
            eleve = Eleve.objects.get(id=eleve_id)
            nom = f"{eleve.user.first_name} {eleve.user.last_name}"
            eleve.user.delete()
            messages.success(request, f'Élève "{nom}" supprimé avec succès.')
    
    context = {
        'eleves': eleves,
        'classes': classes,
        'classe_selectionnee': classe_id
    }
    
    return render(request, 'admin/gestion_eleves.html', context)

@staff_member_required
def gestion_parents(request):
    """Gestion des parents"""
    parents = Parent.objects.all().select_related('user').order_by('user__last_name')
    eleves = Eleve.objects.all().order_by('user__last_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            enfants_ids = request.POST.getlist('enfants')
            password = User.objects.make_random_password()
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password
            )
            
            Profile.objects.create(user=user, role='parent')
            parent = Parent.objects.create(
                user=user,
                telephone=telephone,
                adresse=adresse
            )
            
            # Ajouter les enfants sélectionnés
            if enfants_ids:
                enfants = Eleve.objects.filter(id__in=enfants_ids)
                parent.enfants.set(enfants)
            
            messages.success(request, f'Parent "{first_name} {last_name}" ajouté avec succès. Mot de passe: {password}')
        elif action == 'supprimer':
            parent_id = request.POST.get('parent_id')
            parent = Parent.objects.get(id=parent_id)
            nom = f"{parent.user.first_name} {parent.user.last_name}"
            parent.user.delete()
            messages.success(request, f'Parent "{nom}" supprimé avec succès.')
        elif action == 'modifier_enfants':
            parent_id = request.POST.get('parent_id')
            enfants_ids = request.POST.getlist('enfants')
            parent = Parent.objects.get(id=parent_id)
            
            if enfants_ids:
                enfants = Eleve.objects.filter(id__in=enfants_ids)
                parent.enfants.set(enfants)
            else:
                parent.enfants.clear()
            
            messages.success(request, f'Enfants du parent "{parent.user.first_name} {parent.user.last_name}" modifiés avec succès.')
    
    return render(request, 'admin/gestion_parents.html', {'parents': parents, 'eleves': eleves})

@staff_member_required
def gestion_administrateurs(request):
    """Gestion des administrateurs"""
    admins = Profile.objects.filter(role='admin').select_related('user').order_by('user__last_name')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            username = request.POST.get('username')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = User.objects.make_random_password()
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )
            
            Profile.objects.create(user=user, role='admin')
            
            messages.success(request, f'Administrateur "{first_name} {last_name}" ajouté avec succès. Mot de passe: {password}')
        elif action == 'supprimer':
            admin_id = request.POST.get('admin_id')
            admin_profile = Profile.objects.get(id=admin_id)
            nom = f"{admin_profile.user.first_name} {admin_profile.user.last_name}"
            admin_profile.user.delete()
            messages.success(request, f'Administrateur "{nom}" supprimé avec succès.')
    
    return render(request, 'admin/gestion_administrateurs.html', {'admins': admins})

@staff_member_required
def gestion_factures(request):
    """Gestion des factures"""
    # Cette vue gère les factures générées pour les paiements
    paiements = Paiement.objects.all().select_related('inscription__eleve__user', 'inscription__classe').order_by('-date_paiement')
    
    return render(request, 'admin/gestion_factures.html', {'paiements': paiements})

@staff_member_required
def rapport_financier(request):
    """Rapport financier"""
    # Statistiques financières
    total_paiements = Paiement.objects.filter(statut='valide').aggregate(total=Sum('montant'))['total'] or 0
    paiements_par_type = Paiement.objects.filter(statut='valide').values('type_paiement').annotate(
        total=Sum('montant'),
        count=Count('id')
    )
    
    # Paiements par mois
    paiements_par_mois = Paiement.objects.filter(statut='valide').extra(
        select={'mois': "strftime('%Y-%m', date_paiement)"}
    ).values('mois').annotate(
        total=Sum('montant'),
        count=Count('id')
    ).order_by('mois')
    
    # Paiements par classe
    paiements_par_classe = Paiement.objects.filter(statut='valide').values(
        'inscription__classe__nom'
    ).annotate(
        total=Sum('montant'),
        count=Count('id')
    )
    
    context = {
        'total_paiements': total_paiements,
        'paiements_par_type': paiements_par_type,
        'paiements_par_mois': paiements_par_mois,
        'paiements_par_classe': paiements_par_classe,
    }
    
    return render(request, 'admin/rapport_financier.html', context)

@staff_member_required
def gestion_paiements(request):
    """Gestion des paiements"""
    paiements = Paiement.objects.all().select_related(
        'inscription__eleve__user', 
        'inscription__classe'
    ).order_by('-date_paiement')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'valider_paiement':
            paiement_id = request.POST.get('paiement_id')
            paiement = Paiement.objects.get(id=paiement_id)
            paiement.statut = 'valide'
            paiement.save()
            messages.success(request, 'Paiement validé avec succès.')
        elif action == 'rejeter_paiement':
            paiement_id = request.POST.get('paiement_id')
            paiement = Paiement.objects.get(id=paiement_id)
            paiement.statut = 'en_attente'
            paiement.save()
            messages.success(request, 'Paiement rejeté.')
    
    return render(request, 'admin/gestion_paiements.html', {'paiements': paiements})

@staff_member_required
def preinscriptions_validees(request):
    """Liste des préinscriptions validées"""
    preinscriptions = Preinscription.objects.filter(traite=True).order_by('-date_preinscription')
    
    return render(request, 'admin/preinscriptions_validees.html', {'preinscriptions': preinscriptions})

@staff_member_required
def valider_preinscription(request, preinscription_id):
    preinsc = Preinscription.objects.get(id=preinscription_id)
    if request.method == 'POST':
        # Création du compte utilisateur élève
        username = preinsc.nom.lower() + preinsc.prenom.lower()
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user = User.objects.create_user(
            username=username,
            first_name=preinsc.prenom,
            last_name=preinsc.nom,
            email=preinsc.email,
            password=password
        )
        # Création du profil élève
        eleve = Eleve.objects.create(user=user)
        # Création de l'inscription
        Inscription.objects.create(
            eleve=eleve,
            classe=preinsc.classe,
            annee_scolaire='2024-2025',
            accepte=True
        )
        preinsc.traite = True
        preinsc.save()
        messages.success(request, f"Compte élève créé. Identifiant: {username}, mot de passe: {password}")
        return redirect('liste_preinscriptions')
    return render(request, 'valider_preinscription.html', {'preinscription': preinsc})

@login_required
def mes_paiements(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        inscriptions = Inscription.objects.filter(eleve=eleve)
        paiements = Paiement.objects.filter(inscription__in=inscriptions)
    elif profile.role == 'parent':
        parent = Parent.objects.get(user=request.user)
        inscriptions = Inscription.objects.filter(eleve__in=parent.enfants.all())
        paiements = Paiement.objects.filter(inscription__in=inscriptions)
    else:
        paiements = []
    return render(request, 'mes_paiements.html', {'paiements': paiements})

@login_required
def mes_cours(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == 'enseignant':
        enseignant = Enseignant.objects.get(user=request.user)
        cours = Cours.objects.filter(enseignant=enseignant)
    elif profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        inscription = Inscription.objects.filter(eleve=eleve, accepte=True).first()
        cours = Cours.objects.filter(classe=inscription.classe) if inscription else []
    else:
        cours = []
    return render(request, 'mes_cours.html', {'cours': cours})

@login_required
def mes_notes(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        notes = Note.objects.filter(eleve=eleve)
    elif profile.role == 'parent':
        parent = Parent.objects.get(user=request.user)
        notes = Note.objects.filter(eleve__in=parent.enfants.all())
    else:
        notes = []
    return render(request, 'mes_notes.html', {'notes': notes})

@login_required
def mes_bulletins(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        bulletins = Bulletin.objects.filter(eleve=eleve)
    elif profile.role == 'parent':
        parent = Parent.objects.get(user=request.user)
        bulletins = Bulletin.objects.filter(eleve__in=parent.enfants.all())
    else:
        bulletins = []
    return render(request, 'mes_bulletins.html', {'bulletins': bulletins})

class GenerationBulletinForm(forms.Form):
    classe = forms.ModelChoiceField(queryset=Classe.objects.all())
    periode = forms.CharField(max_length=30)

@staff_member_required
def generer_bulletins(request):
    bulletins_generes = []
    
    if request.method == 'POST':
        form = GenerationBulletinForm(request.POST)
        if form.is_valid():
            classe = form.cleaned_data['classe']
            periode = form.cleaned_data['periode']
            eleves = Eleve.objects.filter(inscription__classe=classe, inscription__accepte=True)
            
            for eleve in eleves:
                notes = Note.objects.filter(eleve=eleve, examen__classe=classe)
                if notes.exists():
                    total = notes.aggregate(moyenne=Avg('valeur'))['moyenne'] or 0
                    appreciation = "Très bien" if total >= 16 else ("Bien" if total >= 14 else ("Assez bien" if total >= 12 else ("Passable" if total >= 10 else "Insuffisant")))
                    
                    bulletin, created = Bulletin.objects.update_or_create(
                        eleve=eleve,
                        periode=periode,
                        defaults={
                            'total': total,
                            'appreciation': appreciation
                        }
                    )
                    bulletins_generes.append(bulletin)
            
            if bulletins_generes:
                messages.success(request, f"{len(bulletins_generes)} bulletins ont été générés avec succès pour la classe {classe} - {periode}")
            else:
                messages.warning(request, "Aucun bulletin généré. Vérifiez que les élèves ont des notes pour cette classe et période.")
    else:
        form = GenerationBulletinForm()
    
    context = {
        'form': form,
        'bulletins_generes': bulletins_generes,
    }
    return render(request, 'generation_bulletins.html', context)

@login_required
def emploi_du_temps(request):
    profile = Profile.objects.get(user=request.user)
    jours = [
        ('lundi', 'Lundi'),
        ('mardi', 'Mardi'),
        ('mercredi', 'Mercredi'),
        ('jeudi', 'Jeudi'),
        ('vendredi', 'Vendredi'),
        ('samedi', 'Samedi')
    ]
    creneaux = [
        ('08:00', '09:00'),
        ('09:00', '10:00'),
        ('10:00', '11:00'),
        ('11:00', '12:00'),
        ('14:00', '15:00'),
        ('15:00', '16:00'),
        ('16:00', '17:00'),
    ]
    
    if profile.role == 'eleve':
        eleve = Eleve.objects.get(user=request.user)
        inscription = Inscription.objects.filter(eleve=eleve, accepte=True).first()
        cours = Cours.objects.filter(classe=inscription.classe) if inscription else []
    elif profile.role == 'enseignant':
        enseignant = Enseignant.objects.get(user=request.user)
        cours = Cours.objects.filter(enseignant=enseignant)
    elif profile.role == 'parent':
        parent = Parent.objects.get(user=request.user)
        enfants = parent.enfants.all()
        inscriptions = Inscription.objects.filter(eleve__in=enfants, accepte=True)
        cours = Cours.objects.filter(classe__in=inscriptions.values('classe'))
    else:
        cours = []
    
    # Organiser les cours par jour
    emploi = {}
    for jour_code, jour_nom in jours:
        emploi[jour_code] = cours.filter(jour=jour_code).order_by('heure_debut')
    
    return render(request, 'emploi_du_temps.html', {
        'emploi': emploi,
        'jours': jours,
        'creneaux': creneaux
    })

@login_required
def saisir_notes(request):
    profile = Profile.objects.get(user=request.user)
    if profile.role != 'enseignant':
        return redirect('dashboard')
    enseignant = Enseignant.objects.get(user=request.user)
    cours_list = Cours.objects.filter(enseignant=enseignant)
    examens = Examen.objects.filter(classe__in=cours_list.values('classe'), matiere__in=cours_list.values('matiere'))
    NoteFormSet = modelformset_factory(Note, fields=('valeur',), extra=0)

    if request.method == 'POST':
        examen_id = request.POST.get('examen')
        examen = Examen.objects.get(id=examen_id)
        notes = Note.objects.filter(examen=examen)
        formset = NoteFormSet(request.POST, queryset=notes)
        if formset.is_valid():
            formset.save()
            return render(request, 'saisie_notes_success.html')
    else:
        examen_id = request.GET.get('examen')
        formset = None
        if examen_id:
            examen = Examen.objects.get(id=examen_id)
            notes = Note.objects.filter(examen=examen)
            if not notes.exists():
                # Créer les notes pour chaque élève de la classe si elles n'existent pas
                eleves = Eleve.objects.filter(inscription__classe=examen.classe, inscription__accepte=True)
                for eleve in eleves:
                    Note.objects.get_or_create(eleve=eleve, examen=examen, defaults={'valeur': 0, 'type_evaluation': 'composition'})
                notes = Note.objects.filter(examen=examen)
            formset = NoteFormSet(queryset=notes)
    return render(request, 'saisie_notes.html', {'cours_list': cours_list, 'examens': examens, 'formset': formset})

@login_required
def conversations(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-date_creation')
    return render(request, 'conversations.html', {'conversations': conversations})

@login_required
def conversation_detail(request, conversation_id):
    conversation = Conversation.objects.get(id=conversation_id, participants=request.user)
    if request.method == 'POST':
        contenu = request.POST.get('contenu')
        if contenu:
            Message.objects.create(
                conversation=conversation,
                expediteur=request.user,
                contenu=contenu
            )
            # Marquer les messages comme lus
            conversation.messages.filter(expediteur__in=conversation.participants.exclude(id=request.user.id)).update(lu=True)
    messages = conversation.messages.all().order_by('date_envoi')
    return render(request, 'conversation_detail.html', {'conversation': conversation, 'messages': messages})

@login_required
def nouvelle_conversation(request):
    if request.method == 'POST':
        sujet = request.POST.get('sujet')
        destinataire_id = request.POST.get('destinataire')
        message = request.POST.get('message')
        
        if sujet and destinataire_id and message:
            destinataire = get_object_or_404(User, id=destinataire_id)
            conversation = Conversation.objects.create(sujet=sujet)
            conversation.participants.add(request.user, destinataire)
            
            Message.objects.create(
                conversation=conversation,
                expediteur=request.user,
                contenu=message
            )
            
            messages.success(request, 'Conversation créée avec succès.')
            return redirect('conversation_detail', conversation_id=conversation.id)
    
    # Liste des utilisateurs pour le formulaire
    utilisateurs = User.objects.exclude(id=request.user.id)
    return render(request, 'nouvelle_conversation.html', {'utilisateurs': utilisateurs})

# Vues pour les notifications
@staff_member_required
def gestion_notifications(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'envoyer':
            titre = request.POST.get('titre')
            message = request.POST.get('message')
            type_notif = request.POST.get('type_notification')
            destinataires = request.POST.getlist('destinataires')
            
            if titre and message and destinataires:
                for user_id in destinataires:
                    user = User.objects.get(id=user_id)
                    Notification.objects.create(
                        destinataire=user,
                        titre=titre,
                        message=message,
                        type_notification=type_notif
                    )
                messages.success(request, f'Notification envoyée à {len(destinataires)} destinataire(s).')
                return redirect('gestion_notifications')
        
        elif action == 'supprimer':
            notif_id = request.POST.get('notification_id')
            if notif_id:
                Notification.objects.filter(id=notif_id).delete()
                messages.success(request, 'Notification supprimée.')
                return redirect('gestion_notifications')
    
    notifications = Notification.objects.all().order_by('-date_creation')
    utilisateurs = User.objects.all()
    
    context = {
        'notifications': notifications,
        'utilisateurs': utilisateurs,
        'types_notification': Notification.TYPE_CHOICES,
    }
    return render(request, 'admin/notifications.html', context)

@login_required
def mes_notifications(request):
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            notification = get_object_or_404(Notification, id=notif_id, destinataire=request.user)
            notification.lu = True
            notification.save()
            return redirect('mes_notifications')
    
    notifications = Notification.objects.filter(destinataire=request.user).order_by('-date_creation')
    return render(request, 'mes_notifications.html', {'notifications': notifications})

# Vues pour les horaires
@staff_member_required
def gestion_horaires(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'ajouter':
            nom = request.POST.get('nom')
            jour = request.POST.get('jour')
            heure_debut = request.POST.get('heure_debut')
            heure_fin = request.POST.get('heure_fin')
            pause_debut = request.POST.get('pause_debut') or None
            pause_fin = request.POST.get('pause_fin') or None
            
            if nom and jour and heure_debut and heure_fin:
                Horaire.objects.create(
                    nom=nom,
                    jour=jour,
                    heure_debut=heure_debut,
                    heure_fin=heure_fin,
                    pause_debut=pause_debut,
                    pause_fin=pause_fin
                )
                messages.success(request, 'Horaire ajouté avec succès.')
                return redirect('gestion_horaires')
        
        elif action == 'modifier':
            horaire_id = request.POST.get('horaire_id')
            if horaire_id:
                horaire = get_object_or_404(Horaire, id=horaire_id)
                horaire.nom = request.POST.get('nom')
                horaire.jour = request.POST.get('jour')
                horaire.heure_debut = request.POST.get('heure_debut')
                horaire.heure_fin = request.POST.get('heure_fin')
                horaire.pause_debut = request.POST.get('pause_debut') or None
                horaire.pause_fin = request.POST.get('pause_fin') or None
                horaire.actif = request.POST.get('actif') == 'on'
                horaire.save()
                messages.success(request, 'Horaire modifié avec succès.')
                return redirect('gestion_horaires')
        
        elif action == 'supprimer':
            horaire_id = request.POST.get('horaire_id')
            if horaire_id:
                Horaire.objects.filter(id=horaire_id).delete()
                messages.success(request, 'Horaire supprimé.')
                return redirect('gestion_horaires')
    
    horaires = Horaire.objects.all().order_by('jour', 'heure_debut')
    context = {
        'horaires': horaires,
        'jours': Horaire.JOUR_CHOICES,
    }
    return render(request, 'admin/horaires.html', context)

@login_required
def voir_horaires(request):
    horaires = Horaire.objects.filter(actif=True).order_by('jour', 'heure_debut')
    return render(request, 'horaires.html', {'horaires': horaires})

# Vues pour l'emploi du temps amélioré
@login_required
def emploi_du_temps_avance(request):
    profile = Profile.objects.get(user=request.user)
    
    if profile.role == 'admin':
        # Admin voit tous les emplois du temps
        cours_par_jour = {}
        for jour, nom_jour in Cours.JOUR_CHOICES:
            cours_par_jour[jour] = Cours.objects.filter(jour=jour).order_by('heure_debut')
    
    elif profile.role == 'enseignant':
        # Enseignant voit ses cours
        enseignant = Enseignant.objects.get(user=request.user)
        cours_par_jour = {}
        for jour, nom_jour in Cours.JOUR_CHOICES:
            cours_par_jour[jour] = Cours.objects.filter(jour=jour, enseignant=enseignant).order_by('heure_debut')
    
    elif profile.role == 'eleve':
        # Élève voit les cours de sa classe
        eleve = Eleve.objects.get(user=request.user)
        inscription = Inscription.objects.filter(eleve=eleve, accepte=True).first()
        
        if inscription:
            cours_par_jour = {}
            for jour, nom_jour in Cours.JOUR_CHOICES:
                cours_par_jour[jour] = Cours.objects.filter(jour=jour, classe=inscription.classe).order_by('heure_debut')
        else:
            cours_par_jour = {}
    
    else:
        cours_par_jour = {}
    
    context = {
        'cours_par_jour': cours_par_jour,
        'jours': Cours.JOUR_CHOICES,
    }
    return render(request, 'emploi_du_temps_avance.html', context)

# Vues pour la sauvegarde
@staff_member_required
def gestion_sauvegarde(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'creer_sauvegarde':
            nom = request.POST.get('nom')
            type_sauvegarde = request.POST.get('type_sauvegarde')
            description = request.POST.get('description')
            
            if nom and type_sauvegarde:
                # Simulation de création de sauvegarde
                # En production, vous utiliseriez django-backup ou une solution similaire
                import os
                from django.conf import settings
                
                # Créer le dossier de sauvegarde s'il n'existe pas
                backup_dir = os.path.join(settings.MEDIA_ROOT, 'sauvegardes')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Nom du fichier de sauvegarde
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                filename = f"sauvegarde_{type_sauvegarde}_{timestamp}.json"
                filepath = os.path.join(backup_dir, filename)
                
                try:
                    # Exporter les données (simplifié)
                    from django.core import serializers
                    from django.db import connection
                    
                    # Obtenir la liste des tables
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in cursor.fetchall()]
                    
                    # Créer un fichier de sauvegarde simple
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Sauvegarde {nom} - {timestamp}\n")
                        f.write(f"Type: {type_sauvegarde}\n")
                        f.write(f"Description: {description}\n")
                        f.write(f"Tables: {', '.join(tables)}\n")
                    
                    # Enregistrer dans la base de données
                    taille_fichier = os.path.getsize(filepath)
                    Sauvegarde.objects.create(
                        nom=nom,
                        type_sauvegarde=type_sauvegarde,
                        fichier=f'sauvegardes/{filename}',
                        taille_fichier=taille_fichier,
                        description=description,
                        reussi=True
                    )
                    
                    messages.success(request, f'Sauvegarde "{nom}" créée avec succès.')
                    
                except Exception as e:
                    messages.error(request, f'Erreur lors de la création de la sauvegarde: {str(e)}')
                
                return redirect('gestion_sauvegarde')
        
        elif action == 'restaurer':
            sauvegarde_id = request.POST.get('sauvegarde_id')
            if sauvegarde_id:
                sauvegarde = get_object_or_404(Sauvegarde, id=sauvegarde_id)
                # Logique de restauration (à implémenter selon vos besoins)
                messages.warning(request, 'Fonctionnalité de restauration à implémenter.')
                return redirect('gestion_sauvegarde')
        
        elif action == 'supprimer':
            sauvegarde_id = request.POST.get('sauvegarde_id')
            if sauvegarde_id:
                sauvegarde = get_object_or_404(Sauvegarde, id=sauvegarde_id)
                # Supprimer le fichier physique
                if sauvegarde.fichier:
                    try:
                        os.remove(sauvegarde.fichier.path)
                    except:
                        pass
                sauvegarde.delete()
                messages.success(request, 'Sauvegarde supprimée.')
                return redirect('gestion_sauvegarde')
    
    sauvegardes = Sauvegarde.objects.all().order_by('-date_creation')
    context = {
        'sauvegardes': sauvegardes,
        'types_sauvegarde': Sauvegarde.TYPE_CHOICES,
    }
    return render(request, 'admin/sauvegarde.html', context)

# Fonction utilitaire pour créer des notifications
def creer_notification(destinataire, titre, message, type_notification='info', lien=''):
    return Notification.objects.create(
        destinataire=destinataire,
        titre=titre,
        message=message,
        type_notification=type_notification,
        lien=lien
    )
