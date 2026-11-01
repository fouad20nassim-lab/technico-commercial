# 📋 Guide Officiel — Plateforme Technico-Commercial & Base de Données Solide
### S.A.R.L Electron Medical Algérie — Distributeur Officiel FUJIFILM Medical Systems

---

## 🚀 1. Lancement en 1 Clic

Double-cliquez simplement sur le fichier :
👉 **`DEMARRER_PLATEFORME.bat`** (dans votre dossier `D:\TECHNICO-COMMERCIAL`)

Ce script :
1. Détecte automatiquement l'environnement Python installé.
2. Démarre le serveur local et connecte la **base de données SQLite solide** (`technico_commercial.db`).
3. Ouvre immédiatement votre navigateur à l'adresse : **`http://localhost:8085`**.

---

## 🌐 2. Accès Multi-Appareils (Tablettes & Smartphones en Wi-Fi)

La plateforme est entièrement accessible par le réseau local :
- Cliquez sur le bouton **`📱 Accès Wi-Fi`** sur le tableau de bord pour afficher l'adresse IP locale (Exemple : `http://192.168.1.9:8085`).
- Les techniciens et ingénieurs peuvent remplir et faire signer les formulaires directement sur tablette ou smartphone tactile en salle d'intervention.

---

## 📑 3. Les 6 Modules Techniques Intégrés

| Module | Fichier | Rôle & Contenu |
| :--- | :--- | :--- |
| **01. Visite de Contrôle** | [`visite_controle.html`](file:///d:/TECHNICO-COMMERCIAL/visite_controle.html) | Maintenance préventive, contrôle technique endoscope (étanchéité, béquillage ±5%, switches, canaux), conclusion, photos et signatures. |
| **02. Rapport d'Installation Client** | [`rapport_installation.html`](file:///d:/TECHNICO-COMMERCIAL/rapport_installation.html) | Réception, inventaire des 12 équipements constructeur, gestion des consommables, réserves et double signature. |
| **03. Rapport de Formation** | [`rapport_formation.html`](file:///d:/TECHNICO-COMMERCIAL/rapport_formation.html) | Équipe formée, validation du programme des 8 points officiels FUJIFILM, émargement et attestation. |
| **04. Rapport de Mise en Service** | [`rapport_mise_en_service.html`](file:///d:/TECHNICO-COMMERCIAL/rapport_mise_en_service.html) | Mise en service officielle, formation, contrôle des documents remis et vérifications fonctionnelles. |
| **05. Procédure d'Installation** | [`procedure_installation.html`](file:///d:/TECHNICO-COMMERCIAL/procedure_installation.html) | Checklist interactive en 6 étapes : préparation, montage de la colonne, réseau, désinfection et clôture ADV. |
| **06. Feuille d’Inspection** | [`feuille_inspection.html`](file:///d:/TECHNICO-COMMERCIAL/feuille_inspection.html) | Contrôle d'entrée & après réparation, 264 modèles FUJIFILM avec tolérances d'usine, gestion dynamique des techniciens et points de contrôle. |

---

## 🗄️ 4. Base de Données Solide SQLite (`technico_commercial.db`)

- **Stockage permanent & Fiable :** Fini les pertes de données ! Tous les rapports sont enregistrés dans la base relationnelle SQLite locale.
- **Double protection Offline-First :** Si le serveur est temporairement éteint, les formulaires continuent de fonctionner en cache local et se synchronisent dès la reconnexion.
- **Sauvegarde automatique :** Chaque modification déclenche une copie miroir de sécurité dans `technico_commercial.db.bak`.

---

## 📊 5. Exportations & Sauvegardes

1. **Export Excel / CSV en 1 clic :** Cliquez sur **`📊 Export Excel`** sur le tableau de bord pour télécharger instantanément l'intégralité du registre avec accents préservés (BOM UTF-8).
2. **Sauvegarde JSON complète :** Cliquez sur **`💾 Sauvegarde JSON`** pour exporter l'ensemble des données.
3. **Restauration :** Cliquez sur **`📥 Restaurer`** pour réimporter une sauvegarde en cas de changement d'ordinateur.
4. **Impression & Export PDF :** Chaque formulaire dispose d'un bouton **`🖨️ Imprimer / PDF`** générant une mise en page officielle A4 sans boutons ni éléments parasites.

---

## 🔐 6. Administration Sécurisée, Gestion des Comptes & Base SQLite

Accessible en cliquant sur **`🔐 Administration Sécurisée`** ou [`parametres_admin.html`](file:///d:/TECHNICO-COMMERCIAL/parametres_admin.html) :

### A. Administration Sécurisée & Authentification
- **Double mode de déverrouillage :**
  - **Sur PC :** Identifiant & Mot de passe avec clavier.
  - **Sur Tablette & Écran Tactile :** Pavé numérique grand format pour saisie immédiate du **Code PIN**.
- **Comptes par défaut configurés :**
  - **Administrateur Principal :** `admin` / Mot de passe : `admin` / Code PIN : `1234`
  - **Technicien SAV :** `mustapha.b` / PIN : `1111`
  - **Commercial ADV :** `karim.t` / PIN : `2222`
  - **Responsable Qualité :** `dr.benali` / PIN : `3333`
- **Sécurité active :** Hachage salé PBKDF2-HMAC-SHA256 (100 000 itérations), sessions avec jeton token, verrouillage automatique en cas d'inactivité prolongée (protection tablettes de salle).

### B. Contrôle Global des Paramètres
- **9 modules administratifs centralisés :**
  1. `👥 Comptes & Permissions` (Création, modification, rôles et codes PIN)
  2. `💾 Conservation & Base SQLite` (Diagnostic intégrité, VACUUM, snapshots et sauvegardes)
  3. `👨‍🔧 Techniciens & Équipe` (Roster des techniciens d'inspection, réparation et qualité)
  4. `🔬 Modèles FUJIFILM (264+)` (Spécifications usine, angles béquillage, débits eau/air/aspi)
  5. `📋 Grilles de Contrôle` (Points de contrôle technique personnalisables)
  6. `🎨 Dessins & Schémas` (Schémas anatomiques d'endoscopes modifiables)
  7. `🔘 Options & Réponses` (Listes de résultats, types de réparations, services)
  8. `🏢 Entreprise & Documents` (Identité Electron Medical Algérie, coordonnées, en-têtes)
  9. `🛡️ Journal d'Audit` (Traçabilité exhaustive et horodatée de tous les événements)

### C. Conservation et Supervision de la Base SQLite
- **Diagnostics en direct :**
  - Statut d'intégrité live via `PRAGMA integrity_check`.
  - Mode Journal **WAL (Write-Ahead Logging)** pour prévenir toute corruption en cas de coupure de courant.
  - Décompte instantané des enregistrements par table (rapports, clients, garanties, comptes, audit).
- **Opérations en 1 clic :**
  - **Télécharger la Base (.db) :** Export direct du fichier réel SQLite sur clé USB ou disque de secours.
  - **Instantané Horodaté (Snapshot) :** Copie miroir automatique créée dans `backups/`.
  - **Optimiser (VACUUM & Checkpoint) :** Défragmentation et reconstruction des index.
  - **Restaurer une Sauvegarde :** Remplacement sécurisé avec pré-sauvegarde automatique de sécurité.
  - **Importer un fichier (.db) :** Téléversement direct avec contrôle d'en-tête SQLite.

### D. Gestion des Comptes et Permissions
- **Rôles RBAC (Role-Based Access Control) :**
  - **Administrateur :** Contrôle intégral, paramètres, maintenance SQLite et gestion des comptes.
  - **Technicien SAV :** Remplissage des rapports, visites de contrôle, feuilles d'inspection et validation des révisions.
  - **Commercial / ADV :** Gestion du fichier client, suivi des garanties 2 ans et export des registres.
  - **Responsable Qualité :** Validation technique et consultation du journal d'audit.
- **Protection anti-suppression :** Impossible de supprimer votre propre compte ou le compte Administrateur Principal.
- **Création instantanée (+ Nouvel Utilisateur) :** Formulaire tactile avec nom, identifiant, rôle, PIN rapide 4 chiffres et mot de passe, synchronisé en direct avec la base SQLite et sauvegardé en local (Local-First).
- **Verrouillage Sécurisé Immédiat :**
  - La page `Paramètres & Configuration Globale` est **verrouillée par défaut** à l'ouverture.
  - Déverrouillage tactile rapide via **Code PIN Tablette (1234)** ou **Mot de passe PC (admin / admin)**.
  - Bouton rouge **"🔒 Verrouiller la Page"** accessible en permanence pour reverrouiller instantanément en 1 clic.
  - Reverrouillage automatique en cas d'inactivité prolongée (15 minutes).

### E. Interface Optimisée PC & Tablette, Mode Clair / Mode Sombre
- **Bouton Pill [☀️ Mode] :** Un bouton élégant en forme de pilule `☀️ Mode` / `🌙 Mode` est disponible en haut de chaque page de l'application.
- **Basculement instantané :** Permet de basculer en 1 clic entre le **Mode Clair** (idéal de jour et pour les bureaux) et le **Mode Sombre** (confort visuel en salle d'endoscopie sombre et sur tablettes).
- **Mémorisation automatique :** Le mode sélectionné est conservé dans le navigateur (`localStorage`) et s'applique sans scintillement sur toutes les pages et lors de chaque nouvelle visite.
- **Ergonomie tactile certifiée :** Boutons d'au moins 48px, typographie lisible en salle d'intervention, pavé tactile PIN, navigation fluide par onglets horizontaux.

---
*Plateforme développée pour S.A.R.L Electron Medical Algérie · Excellence in Endoscopy Care.*
