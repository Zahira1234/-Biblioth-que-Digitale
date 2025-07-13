import tkinter as tk
from tkinter import messagebox, simpledialog
import json
from datetime import datetime, timedelta
import customtkinter as ctk
import os
from PIL import Image, ImageTk

# ===================================================
# CLASSES MÉTIER
# ===================================================

class Livre:
    def __init__(self, titre, auteur, isbn):
        self.titre = titre
        self.auteur = auteur
        self.isbn = isbn
        self.disponible = True
        self.emprunteur = None
        self.date_emprunt = None
        self.date_retour_prevue = None
        self.nombre_emprunts = 0

    def to_dict(self):
        return {
            "titre": self.titre,
            "auteur": self.auteur,
            "isbn": self.isbn,
            "disponible": self.disponible,
            "emprunteur": self.emprunteur,
            "date_emprunt": self.date_emprunt.isoformat() if self.date_emprunt else None,
            "date_retour_prevue": self.date_retour_prevue.isoformat() if self.date_retour_prevue else None,
            "nombre_emprunts": self.nombre_emprunts
        }

class Utilisateur:
    def __init__(self, nom, id_utilisateur):
        self.nom = nom
        self.id_utilisateur = id_utilisateur
        self.livres_empruntes = []
        self.historique_emprunts = []
        self.penalites = 0.0

    def to_dict(self):
        return {
            "nom": self.nom,
            "id_utilisateur": self.id_utilisateur,
            "livres_empruntes": self.livres_empruntes,
            "historique_emprunts": self.historique_emprunts,
            "penalites": self.penalites
        }

class Bibliotheque:
    def __init__(self):
        self.livres = {}
        self.utilisateurs = {}
        self.duree_emprunt = 14
        self.taux_penalite = 0.5

    def sauvegarder(self, fichier="bibliotheque.json"):
        with open(fichier, "w", encoding="utf-8") as f:
            json.dump({
                "livres": {isbn: livre.to_dict() for isbn, livre in self.livres.items()},
                "utilisateurs": {id_user: user.to_dict() for id_user, user in self.utilisateurs.items()},
                "duree_emprunt": self.duree_emprunt,
                "taux_penalite": self.taux_penalite
            }, f, indent=4)

    def charger_donnees(self, fichier="bibliotheque.json"):
        try:
            with open(fichier, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            self.livres = {}
            for isbn, d in data["livres"].items():
                livre = Livre(d["titre"], d["auteur"], d["isbn"])
                livre.disponible = d["disponible"]
                livre.emprunteur = d["emprunteur"]
                livre.date_emprunt = datetime.fromisoformat(d["date_emprunt"]) if d["date_emprunt"] else None
                livre.date_retour_prevue = datetime.fromisoformat(d["date_retour_prevue"]) if d["date_retour_prevue"] else None
                livre.nombre_emprunts = d["nombre_emprunts"]
                self.livres[isbn] = livre
                
            self.utilisateurs = {}
            for id_user, u in data["utilisateurs"].items():
                user = Utilisateur(u["nom"], u["id_utilisateur"])
                user.livres_empruntes = u["livres_empruntes"]
                user.historique_emprunts = u["historique_emprunts"]
                user.penalites = u["penalites"]
                self.utilisateurs[id_user] = user
                
            self.duree_emprunt = data["duree_emprunt"]
            self.taux_penalite = data["taux_penalite"]
        except FileNotFoundError:
            self.sauvegarder()

    def ajouter_livre(self, livre):
        if livre.isbn in self.livres:
            return False
        self.livres[livre.isbn] = livre
        return True

    def supprimer_livre(self, isbn):
        if isbn in self.livres:
            if not self.livres[isbn].disponible:
                return False
            del self.livres[isbn]
            return True
        return False

    def ajouter_utilisateur(self, utilisateur):
        if utilisateur.id_utilisateur in self.utilisateurs:
            return False
        self.utilisateurs[utilisateur.id_utilisateur] = utilisateur
        return True

    def emprunter_livre(self, isbn, id_user):
        if isbn not in self.livres or id_user not in self.utilisateurs:
            return False
        
        livre = self.livres[isbn]
        user = self.utilisateurs[id_user]
        
        if not livre.disponible:
            return False
        
        livre.disponible = False
        livre.emprunteur = id_user
        livre.date_emprunt = datetime.now()
        livre.date_retour_prevue = livre.date_emprunt + timedelta(days=self.duree_emprunt)
        livre.nombre_emprunts += 1
        
        user.livres_empruntes.append(isbn)
        user.historique_emprunts.append(isbn)
        return True

    def retourner_livre(self, isbn):
        if isbn not in self.livres or self.livres[isbn].disponible:
            return False
        
        livre = self.livres[isbn]
        user = self.utilisateurs[livre.emprunteur]
        
        if datetime.now() > livre.date_retour_prevue:
            jours_retard = (datetime.now() - livre.date_retour_prevue).days
            user.penalites += jours_retard * self.taux_penalite
        
        livre.disponible = True
        livre.emprunteur = None
        livre.date_emprunt = None
        livre.date_retour_prevue = None
        user.livres_empruntes.remove(isbn)
        return True

    def rechercher_livre(self, critere, valeur):
        """Recherche des livres selon un critère et une valeur"""
        resultats = []
        
        for isbn, livre in self.livres.items():
            if critere == "titre" and valeur.lower() in livre.titre.lower():
                resultats.append(livre)
            elif critere == "auteur" and valeur.lower() in livre.auteur.lower():
                resultats.append(livre)
            elif critere == "isbn" and valeur == isbn:
                resultats.append(livre)
                
        return resultats

    def afficher_livres_disponibles(self):
        """Retourne la liste des livres disponibles"""
        return [livre for livre in self.livres.values() if livre.disponible]

    def verifier_retards(self):
        """Identifie les livres qui sont en retard"""
        livres_en_retard = []
        
        for isbn, livre in self.livres.items():
            if not livre.disponible and datetime.now() > livre.date_retour_prevue:
                livres_en_retard.append(livre)
        
        return livres_en_retard
    def supprimer_livre(self, isbn):
        if isbn in self.livres:
            del self.livres[isbn]
            return f"Livre avec ISBN '{isbn}' supprimé avec succès"
        return "Livre non trouvé"

    def get_statistiques(self):
        stats = {
            "total_livres": len(self.livres),
            "livres_disponibles": sum(1 for l in self.livres.values() if l.disponible),
            "livres_empruntes": sum(1 for l in self.livres.values() if not l.disponible),
            "total_utilisateurs": len(self.utilisateurs),
            "penalites_total": sum(u.penalites for u in self.utilisateurs.values()),
            "livre_plus_emprunte": None,
            "max_emprunts": 0,
            "utilisateur_plus_actif": None,
            "max_livres_empruntes": 0
        }
        
        # Trouver le livre le plus emprunté
        for livre in self.livres.values():
            if livre.nombre_emprunts > stats["max_emprunts"]:
                stats["max_emprunts"] = livre.nombre_emprunts
                stats["livre_plus_emprunte"] = livre
        
        # Trouver l'utilisateur le plus actif
        for user in self.utilisateurs.values():
            if len(user.historique_emprunts) > stats["max_livres_empruntes"]:
                stats["max_livres_empruntes"] = len(user.historique_emprunts)
                stats["utilisateur_plus_actif"] = user
        
        return stats

# ===================================================
# INTERFACE GRAPHIQUE
# ===================================================

class ApplicationTk:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.biblio = Bibliotheque()
        self.biblio.charger_donnees()
        self.setup_ui()

    def setup_window(self):
        self.root.title("Bibliothèque Digitale")
        self.root.geometry("1300x700")
        self.root.attributes("-transparentcolor", "#f0f4f8")
        self.root.configure(bg="#f0f4f8")
        self.root.attributes("-alpha", 0.97)
        self.root.overrideredirect(True)

    def setup_ui(self):
        self.setup_background()
        self.create_sidebar()
        self.create_main_content()
        self.show_welcome()

    def setup_background(self):
        """Configurer l'arrière-plan initial"""
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_color = "#f0f4f8"  # Couleur par défaut si pas d'image
        
        try:
            # Nom fixe de l'image d'arrière-plan (cherche d'abord image.png, sinon bg.jpg)
            image_name = "j.png" if os.path.exists("j.png") else "bg.jpg"
            
            # Si aucune image n'existe, on crée un arrière-plan de couleur unie
            if not os.path.exists(image_name):
                self.bg_image = None
                self.canvas.configure(bg=self.bg_color)
                print(f"Image d'arrière-plan non trouvée: {image_name}")
                print("Utilisation d'une couleur d'arrière-plan unie.")
            else:
                # Obtenir les dimensions actuelles de la fenêtre
                window_width = 1300  # Dimensions initiales
                window_height = 700
                
                # Charger l'image et la redimensionner à la taille de la fenêtre
                original_image = Image.open(image_name)
                self.background_image = ImageTk.PhotoImage(original_image.resize((window_width, window_height), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS))
                
                # Placer l'image sur le Canvas
                self.bg_image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.background_image)
        except Exception as e:
            print(f"Erreur lors du chargement de l'image: {e}")
            self.bg_image_id = None
            self.canvas.configure(bg=self.bg_color)
        
        try:
            img = Image.open("bg.jpg") if os.path.exists("bg.jpg") else None
            if img:
                self.bg_image = ImageTk.PhotoImage(img.resize((1200, 800)))
                self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        except Exception as e:
            print(f"Erreur background: {e}")

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.canvas, width=250, corner_radius=15, fg_color="white")
        self.sidebar.pack(side="left", fill="y", padx=15, pady=15)

        menu_items = [
            ("🏠 Accueil", self.show_welcome),
            ("📚 Livres", self.show_livres),
            ("🔍 Rechercher Livre", self.recherche_livre),
             ("🗑 Supprimer Livre", self.supprimer_livre),
            ("👥 Utilisateurs", self.show_utilisateurs),
            ("📤 Retourner", self.show_retour),
            ("📊 Statistiques", self.show_stats),
            ("📦 Livres Disponibles", self.afficher_livres_disponibles),
            ("⏰ Vérifier Retards", self.verifier_retards),
            ("Sauvegarder", self.sauvegarder_donnees),
            ("⚙️ Paramètres", self.show_parametres),
            ("❌ Quitter", self.exit_app)
        ]

        ctk.CTkLabel(self.sidebar, 
                    text="Menu Principal",
                    font=("Arial", 18, "bold"),
                    text_color="#1e293b").pack(pady=20)

        for text, command in menu_items:
            btn = ctk.CTkButton(self.sidebar,
                               text=text,
                               command=command,
                               font=("Arial", 14),
                               corner_radius=8,
                               fg_color="#3b82f6",
                               hover_color="#2563eb")
            btn.pack(pady=5, padx=10, fill="x")

    def create_main_content(self):
        self.main_content = ctk.CTkFrame(self.canvas, corner_radius=15, fg_color="white")
        self.main_content.pack(expand=True, fill="both", padx=15, pady=15)

    # =============== METHODES D'AFFICHAGE ===============

    def clear_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()
    def show_parametres(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("Durée emprunt (jours)", 100), ("Taux pénalité (€/jour)", 100)]
        
        for field, width in fields:
            frame = ctk.CTkFrame(form, fg_color="transparent")
            frame.pack(pady=10)
            ctk.CTkLabel(frame, text=field, width=150).pack(side="left")
            entries[field] = ctk.CTkEntry(frame, width=width)
            entries[field].insert(0, str(getattr(self.biblio, field.split()[0].lower())))
            entries[field].pack(side="right")

        def valider():
            try:
                self.biblio.duree_emprunt = int(entries["Durée emprunt (jours)"].get())
                self.biblio.taux_penalite = float(entries["Taux pénalité (€/jour)"].get())
                self.biblio.sauvegarder()
                messagebox.showinfo("Succès", "Paramètres mis à jour!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Valeurs invalides: {str(e)}")

        ctk.CTkButton(form, 
                      text="Enregistrer les modifications", 
                      command=valider,
                      fg_color="#3b82f6",
                      hover_color="#2563eb").pack(pady=20)


    def show_welcome(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(content, 
                    text="Bienvenue dans votre Bibliothèque Digitale",
                    font=("Arial", 24, "bold"),
                    text_color="#1e293b").pack(pady=50)

        stats = self.biblio.get_statistiques()
        stats_text = (
            f"📚 Livres total: {stats['total_livres']}\n"
            f"📖 Disponibles: {stats['livres_disponibles']}\n"
            f"👥 Utilisateurs: {stats['total_utilisateurs']}\n"
            f"💰 Pénalités totales: {stats['penalites_total']}€"
        )
        
        ctk.CTkLabel(content, 
                    text=stats_text,
                    font=("Arial", 18),
                    text_color="#475569").pack()
    def show_welcome(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        # Frame principale avec ombre et bordure arrondie
        welcome_frame = ctk.CTkFrame(content, 
                                   corner_radius=20,
                                   fg_color="#ffffff",
                                   border_width=2,
                                   border_color="#e2e8f0")
        welcome_frame.pack(expand=True, fill="both", padx=50, pady=50)

        # Titre avec icône et effet de dégradé
        title_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        title_frame.pack(pady=(40, 20))
        
        # Icône de livre
        book_icon = ctk.CTkLabel(title_frame, 
                                text="📚", 
                                font=("Arial", 60),
                                text_color="#3b82f6")
        book_icon.pack(side="left", padx=10)
        
        # Titre principal avec dégradé
        title_label = ctk.CTkLabel(title_frame,
                                 text="Bibliothèque Digitale",
                                 font=("Arial", 32, "bold"),
                                 text_color="#1e293b")
        title_label.pack(side="left", padx=10)

        # Sous-titre
        subtitle_label = ctk.CTkLabel(welcome_frame,
                                    text="Gestion complète de votre collection de livres",
                                    font=("Arial", 16),
                                    text_color="#64748b")
        subtitle_label.pack(pady=(0, 40))

        # Statistiques dans des cartes modernes
        stats = self.biblio.get_statistiques()
        stats_data = [
            {"icon": "📚", "title": "Livres", "value": stats['total_livres'], "color": "#3b82f6"},
            {"icon": "📖", "title": "Disponibles", "value": stats['livres_disponibles'], "color": "#10b981"},
            {"icon": "👥", "title": "Utilisateurs", "value": stats['total_utilisateurs'], "color": "#8b5cf6"},
            {"icon": "💰", "title": "Pénalités", "value": f"{stats['penalites_total']}€", "color": "#ef4444"}
        ]

        stats_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        stats_frame.pack(pady=(0, 40))

        for i, stat in enumerate(stats_data):
            card = ctk.CTkFrame(stats_frame,
                              width=180,
                              height=120,
                              corner_radius=15,
                              fg_color=stat["color"])
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            
            # Contenu de la carte
            icon = ctk.CTkLabel(card, 
                               text=stat["icon"], 
                               font=("Arial", 24),
                               text_color="white")
            icon.pack(pady=(15, 5))
            
            value = ctk.CTkLabel(card,
                                text=str(stat["value"]),
                                font=("Arial", 24, "bold"),
                                text_color="white")
            value.pack()
            
            title = ctk.CTkLabel(card,
                               text=stat["title"],
                               font=("Arial", 14),
                               text_color="white")
            title.pack(pady=(0, 15))

        # Message d'accueil personnalisé
        welcome_msg = ctk.CTkLabel(welcome_frame,
                                  text="Bienvenue dans votre système de gestion de bibliothèque.\n"
                                       "Commencez par explorer les différentes fonctionnalités disponibles.",
                                  font=("Arial", 14),
                                  text_color="#475569",
                                  justify="center")
        welcome_msg.pack(pady=(0, 40))

        # Bouton de démarrage rapide
        quick_actions_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        quick_actions_frame.pack(pady=(0, 30))

        quick_actions = [
            ("Ajouter un livre", self.show_ajouter_livre, "#10b981"),
            ("Emprunter un livre", self.show_emprunt, "#3b82f6"),
            ("Voir les statistiques", self.show_stats, "#8b5cf6")
        ]

        for text, command, color in quick_actions:
            btn = ctk.CTkButton(quick_actions_frame,
                               text=text,
                               command=command,
                               font=("Arial", 14),
                               fg_color=color,
                               hover_color=f"{color}90",
                               width=180,
                               height=40,
                               corner_radius=8)
            btn.pack(side="left", padx=10, pady=5)

        # Pied de page avec version et copyright
        footer = ctk.CTkLabel(welcome_frame,
                             text="© 2023 Bibliothèque Digitale - Version 1.0",
                             font=("Arial", 12),
                             text_color="#94a3b8")
        footer.pack(side="bottom", pady=20)

    def show_livres(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, 
                     text="Gestion des Livres", 
                     font=("Arial", 20, "bold")).pack(anchor="center")


        # Liste
        scroll_frame = ctk.CTkScrollableFrame(content, height=500)
        scroll_frame.pack(fill="both", expand=True)

        for isbn, livre in self.biblio.livres.items():
            frame = ctk.CTkFrame(scroll_frame, corner_radius=8)
            frame.pack(fill="x", pady=2, padx=5)
            
            status = "🟢" if livre.disponible else "🔴"
            text = f"{status} {livre.titre} - {livre.auteur} ({isbn})"
            ctk.CTkLabel(frame, 
                         text=text,
                         font=("Arial", 14)).pack(side="left", padx=10)
            
            if not livre.disponible:
                user = self.biblio.utilisateurs[livre.emprunteur]
                ctk.CTkLabel(frame, 
                            text=f"Emprunté par: {user.nom}",
                            text_color="#64748b").pack(side="right", padx=10)

    def show_ajouter_livre(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("Titre", 300), ("Auteur", 300), ("ISBN", 200)]
        
        for field, width in fields:
            frame = ctk.CTkFrame(form, fg_color="transparent")
            frame.pack(pady=10)
            ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
            entries[field] = ctk.CTkEntry(frame, width=width)
            entries[field].pack(side="right")

        def valider():
            try:
                livre = Livre(
                    titre=entries["Titre"].get(),
                    auteur=entries["Auteur"].get(),
                    isbn=entries["ISBN"].get()
                )
                if self.biblio.ajouter_livre(livre):
                    self.biblio.sauvegarder()
                    messagebox.showinfo("Succès", "Livre ajouté avec succès!")
                    self.show_livres()
                else:
                    messagebox.showerror("Erreur", "ISBN déjà existant!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Données invalides: {str(e)}")

        ctk.CTkButton(form, 
                      text="Valider l'ajout", 
                      command=valider,
                      fg_color="#10b981",
                      hover_color="#059669").pack(pady=20,anchor="e",padx=80)

    def show_utilisateurs(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, 
                     text="Gestion des Utilisateurs", 
                     font=("Arial", 20, "bold")).pack(side="left")

        ctk.CTkButton(header, 
                      text="➕ Ajouter Utilisateur", 
                      command=self.show_ajouter_utilisateur,
                      width=120).pack(side="right", padx=10)

        # Liste
        scroll_frame = ctk.CTkScrollableFrame(content, height=500)
        scroll_frame.pack(fill="both", expand=True)

        for user_id, user in self.biblio.utilisateurs.items():
            frame = ctk.CTkFrame(scroll_frame, corner_radius=8)
            frame.pack(fill="x", pady=2, padx=5)
            
            ctk.CTkLabel(frame, 
                         text=f"👤 {user.nom} ({user_id})",
                         font=("Arial", 14)).pack(side="left", padx=10)
            
            ctk.CTkLabel(frame, 
                         text=f"📚 {len(user.livres_empruntes)} emprunts | 💰 {user.penalites}€",
                         text_color="#64748b").pack(side="right", padx=10)

    def show_ajouter_utilisateur(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("Nom complet", 300), ("ID Utilisateur", 200)]
        
        for field, width in fields:
            frame = ctk.CTkFrame(form, fg_color="transparent")
            frame.pack(pady=10)
            ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
            entries[field] = ctk.CTkEntry(frame, width=width)
            entries[field].pack(side="right")

        def valider():
            try:
                user = Utilisateur(
                    nom=entries["Nom complet"].get(),
                    id_utilisateur=entries["ID Utilisateur"].get()
                )
                if self.biblio.ajouter_utilisateur(user):
                    self.biblio.sauvegarder()
                    messagebox.showinfo("Succès", "Utilisateur ajouté avec succès!")
                    self.show_utilisateurs()
                else:
                    messagebox.showerror("Erreur", "ID déjà existant!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Données invalides: {str(e)}")

        ctk.CTkButton(form, 
                      text="Valider l'ajout", 
                      command=valider,
                      fg_color="#10b981",
                      hover_color="#059669").pack(pady=20,anchor="e",padx=80)

    def recherche_livre(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        label = ctk.CTkLabel(content, text="Recherche de Livre", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        # Choix du critère
        critere_label = ctk.CTkLabel(content, text="Critère de recherche:")
        critere_label.pack()
        critere_var = tk.StringVar(value="titre")
        critere_menu = ctk.CTkOptionMenu(content, variable=critere_var, values=["titre", "auteur", "isbn"])
        critere_menu.pack(pady=5)

        # Champ de recherche
        recherche_entry = ctk.CTkEntry(content, placeholder_text="Entrez votre recherche ici")
        recherche_entry.pack(pady=5)

        # Zone d'affichage des résultats
        resultats_frame = ctk.CTkFrame(content)
        resultats_frame.pack(pady=10, fill="both", expand=True)

        def lancer_recherche():
            for widget in resultats_frame.winfo_children():
                widget.destroy()

            critere = critere_var.get()
            valeur = recherche_entry.get()
            resultats = self.biblio.rechercher_livre(critere, valeur)

            if not resultats:
                ctk.CTkLabel(resultats_frame, text="Aucun résultat trouvé.").pack()
            else:
                for livre in resultats:
                    dispo = "✅ Disponible" if livre.disponible else "❌ Emprunté"
                    texte = f"{livre.titre} - {livre.auteur} (ISBN: {livre.isbn}) - {dispo}"
                    ctk.CTkLabel(resultats_frame, text=texte, anchor="w").pack(fill="x", padx=10, pady=2)

        bouton_recherche = ctk.CTkButton(content, text="Rechercher", command=lancer_recherche)
        bouton_recherche.pack(pady=5)

    def afficher_livres_disponibles(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        label = ctk.CTkLabel(content, text="Liste des livres disponibles", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        # Table pour afficher les livres
        table_frame = ctk.CTkFrame(content)
        table_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # En-têtes de colonnes
        ctk.CTkLabel(table_frame, text="ISBN", font=("Arial", 14, "bold"), width=150).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(table_frame, text="Titre", font=("Arial", 14, "bold"), width=300).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(table_frame, text="Auteur", font=("Arial", 14, "bold"), width=200).grid(row=0, column=2, padx=5, pady=5)

        # Récupérer et afficher les livres disponibles
        livres_disponibles = self.biblio.afficher_livres_disponibles()

        if not livres_disponibles:
            ctk.CTkLabel(table_frame, text="Aucun livre disponible actuellement", font=("Arial", 14), width=650).grid(row=1, column=0, columnspan=3, padx=5, pady=10)
        else:
            for i, livre in enumerate(livres_disponibles, 1):
                ctk.CTkLabel(table_frame, text=livre.isbn).grid(row=i, column=0, padx=5, pady=2)
                ctk.CTkLabel(table_frame, text=livre.titre).grid(row=i, column=1, padx=5, pady=2)
                ctk.CTkLabel(table_frame, text=livre.auteur).grid(row=i, column=2, padx=5, pady=2)

    def verifier_retards(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        label = ctk.CTkLabel(content, text="Livres en retard", font=("Arial", 18, "bold"))
        label.pack(pady=10)

        # Table pour afficher les livres en retard
        table_frame = ctk.CTkFrame(content)
        table_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # En-têtes de colonnes
        ctk.CTkLabel(table_frame, text="ISBN", font=("Arial", 14, "bold"), width=150).grid(row=0, column=0, padx=5, pady=5)
        ctk.CTkLabel(table_frame, text="Titre", font=("Arial", 14, "bold"), width=250).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkLabel(table_frame, text="Emprunteur", font=("Arial", 14, "bold"), width=150).grid(row=0, column=2, padx=5, pady=5)
        ctk.CTkLabel(table_frame, text="Date de retour prévue", font=("Arial", 14, "bold"), width=200).grid(row=0, column=3, padx=5, pady=5)

        # Récupérer et afficher les livres en retard
        livres_en_retard = self.biblio.verifier_retards()

        if not livres_en_retard:
            ctk.CTkLabel(table_frame, text="Aucun livre en retard actuellement", font=("Arial", 14), width=750).grid(row=1, column=0, columnspan=4, padx=5, pady=10)
        else:
            for i, livre in enumerate(livres_en_retard, 1):
                emprunteur = self.biblio.utilisateurs[livre.emprunteur].nom if livre.emprunteur in self.biblio.utilisateurs else "Inconnu"
                date_retour = livre.date_retour_prevue.strftime("%d/%m/%Y") if livre.date_retour_prevue else "Inconnue"

                ctk.CTkLabel(table_frame, text=livre.isbn).grid(row=i, column=0, padx=5, pady=2)
                ctk.CTkLabel(table_frame, text=livre.titre).grid(row=i, column=1, padx=5, pady=2)
                ctk.CTkLabel(table_frame, text=emprunteur).grid(row=i, column=2, padx=5, pady=2)
                ctk.CTkLabel(table_frame, text=date_retour).grid(row=i, column=3, padx=5, pady=2)

    def show_emprunt(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("ID Utilisateur", 200), ("ISBN Livre", 200)]
        
        for field, width in fields:
            frame = ctk.CTkFrame(form, fg_color="transparent")
            frame.pack(pady=10)
            ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
            entries[field] = ctk.CTkEntry(frame, width=width)
            entries[field].pack(side="right")

        def valider():
            try:
                id_user = entries["ID Utilisateur"].get()
                isbn = entries["ISBN Livre"].get()
                
                if self.biblio.emprunter_livre(isbn, id_user):
                    self.biblio.sauvegarder()
                    messagebox.showinfo("Succès", "Emprunt enregistré!")
                    self.show_emprunt()
                else:
                    messagebox.showerror("Erreur", "Emprunt impossible!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Données invalides: {str(e)}")

        ctk.CTkButton(form, 
                      text="Valider l'emprunt", 
                      command=valider,
                      fg_color="#3b82f6",
                      hover_color="#2563eb").pack(pady=20,anchor="e",padx=30)

    def show_retour(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("ISBN Livre", 200)]
        
        for field, width in fields:
            frame = ctk.CTkFrame(form, fg_color="transparent")
            frame.pack(pady=10)
            ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
            entries[field] = ctk.CTkEntry(frame, width=width)
            entries[field].pack(side="right")

        def valider():
            try:
                isbn = entries["ISBN Livre"].get()
                
                if self.biblio.retourner_livre(isbn):
                    self.biblio.sauvegarder()
                    messagebox.showinfo("Succès", "Retour enregistré!")
                    self.show_retour()
                else:
                    messagebox.showerror("Erreur", "Retour impossible!")
            except Exception as e:
                messagebox.showerror("Erreur", f"Données invalides: {str(e)}")

        ctk.CTkButton(form, 
                      text="Valider le retour", 
                      command=valider,
                      fg_color="#3b82f6",
                      hover_color="#2563eb").pack(pady=20,anchor="e",padx=30)

    def show_stats(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)
        stats = self.biblio.get_statistiques()
        
        cards = [
            ("📚 Livres total", stats['total_livres'], "#3b82f6"),
            ("📖 Disponibles", stats['livres_disponibles'], "#10b981"),
            ("👥 Utilisateurs", stats['total_utilisateurs'], "#8b5cf6"),
            ("💰 Pénalités", f"{stats['penalites_total']}€", "#ef4444")
        ]

        grid_frame = ctk.CTkFrame(content, fg_color="transparent")
        grid_frame.pack()

        for i, (title, value, color) in enumerate(cards):
            frame = ctk.CTkFrame(grid_frame, 
                                width=250, 
                                height=150,
                                corner_radius=15,
                                fg_color=color)
            frame.grid(row=i//2, column=i%2, padx=10, pady=10)
            
            ctk.CTkLabel(frame, 
                        text=title,
                        font=("Arial", 16, "bold"),
                        text_color="white").pack(pady=10)
            
            ctk.CTkLabel(frame, 
                        text=str(value),
                        font=("Arial", 24, "bold"),
                        text_color="white").pack(expand=True)

        # Afficher le livre le plus emprunté
        if stats["livre_plus_emprunte"]:
            livre_frame = ctk.CTkFrame(content, fg_color="transparent")
            livre_frame.pack(pady=20)
            
            ctk.CTkLabel(livre_frame, 
                        text="Livre le plus emprunté:",
                        font=("Arial", 16, "bold")).pack()
            
            livre = stats["livre_plus_emprunte"]
            ctk.CTkLabel(livre_frame, 
                        text=f"{livre.titre} - {livre.auteur}",
                        font=("Arial", 14)).pack()
            ctk.CTkLabel(livre_frame, 
                        text=f"Nombre d'emprunts: {stats['max_emprunts']}").pack()

        # Afficher l'utilisateur le plus actif
        if stats["utilisateur_plus_actif"]:
            user_frame = ctk.CTkFrame(content, fg_color="transparent")
            user_frame.pack(pady=20)
            
            ctk.CTkLabel(user_frame, 
                        text="Utilisateur le plus actif:",
                        font=("Arial", 16, "bold")).pack()
            
            user = stats["utilisateur_plus_actif"]
            ctk.CTkLabel(user_frame, 
                        text=f"{user.nom} (ID: {user.id_utilisateur})",
                        font=("Arial", 14)).pack()
            ctk.CTkLabel(user_frame, 
                        text=f"Nombre d'emprunts: {stats['max_livres_empruntes']}").pack()

    # =============== GESTION FENETRE ===============

    def start_move(self, event):
        self.x = event.x
        self.y = event.y
    def exit_app(self):
       if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter l'application ?"):
        self.root.destroy()

    def sauvegarder_donnees(self):
        """Sauvegarde les données de la bibliothèque"""
        self.biblio.sauvegarder()
        messagebox.showinfo("Sauvegarde", "Les données ont été sauvegardées avec succès!")

    def move_window(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    def supprimer_livre(self):
        self.clear_content()
        content = ctk.CTkFrame(self.main_content, fg_color="transparent")
        content.pack(expand=True, fill="both", padx=20, pady=20)

        form = ctk.CTkFrame(content, fg_color="transparent")
        form.pack(expand=True)

        entries = {}
        fields = [("ISBN du livre à supprimer", 300)]
    
        for field, width in fields:
           frame = ctk.CTkFrame(form, fg_color="transparent")
           frame.pack(pady=10)
           ctk.CTkLabel(frame, text=field, width=100).pack(side="left")
           entries[field] = ctk.CTkEntry(frame, width=width)
           entries[field].pack(side="right")

        def valider():
            try:
                isbn = entries["ISBN du livre à supprimer"].get()
            
                if not isbn:
                    messagebox.showerror("Erreur", "Le champ ISBN est obligatoire!")
                    return
                
            # Vérifier si le livre est actuellement emprunté
                if isbn in self.biblio.livres and not self.biblio.livres[isbn].disponible:
                    messagebox.showerror("Erreur", "Impossible de supprimer un livre actuellement emprunté!")
                    return
                
                message = self.biblio.supprimer_livre(isbn)
                if "succès" in message:
                    messagebox.showinfo("Succès", message)
                    self.supprimer_livre()  # Réinitialiser le formulaire
                else:
                    messagebox.showerror("Erreur", message)
            except Exception as e:
                messagebox.showerror("Erreur", f"Données invalides: {str(e)}")

        ctk.CTkButton(form, 
                 text="Supprimer le livre", 
                 command=valider,
                 fg_color="#3b82f6",
                 hover_color="#2563eb").pack(pady=20, anchor="e", padx=30)

if __name__ == "__main__":
    root = tk.Tk()
    app = ApplicationTk(root)
    root.mainloop()