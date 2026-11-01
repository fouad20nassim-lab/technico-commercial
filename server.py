# -*- coding: utf-8 -*-
"""
ELECTRON MEDICAL ALGERIE — Distributeur Officiel Fujifilm Medical Systems
SERVEUR & BASE DE DONNEES PLATEFORME TECHNICO-COMMERCIAL
Version : 2.1 — Gestion Garanties 2 Ans & Révisions 6 Mois avec Rappels à J-10
Port : 8085
"""

import http.server
import socketserver
import json
import sqlite3
import os
import sys
import socket
import calendar
import urllib.parse
import shutil
import glob
import hashlib
import secrets
import base64
from datetime import datetime, date, timedelta

PORT = int(os.environ.get('PORT', 8085))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "technico_commercial.db")
BACKUP_DB_FILE = os.path.join(BASE_DIR, "technico_commercial.db.bak")
BACKUPS_DIR = os.path.join(BASE_DIR, "backups")

# Assurer l'encodage UTF-8 pour Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

def get_local_ip():
    """Détecte l'adresse IP locale sur le réseau Wi-Fi / Ethernet"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

def add_months(sourcedate, months):
    """Ajoute des mois à une date en respectant les fins de mois et années bissextiles"""
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return sourcedate.replace(year=year, month=month, day=day)

def hash_password(password, salt=None):
    """Génère un hash salé sécurisé PBKDF2-HMAC-SHA256 (100 000 itérations)"""
    if not salt:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', str(password).encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return pwd_hash, salt

def verify_password(password, salt, pwd_hash):
    """Vérifie un mot de passe contre son hash et salt"""
    try:
        calc_hash, _ = hash_password(password, salt)
        return secrets.compare_digest(calc_hash, pwd_hash)
    except Exception:
        return False

def seed_default_users(cursor):
    """Crée les comptes initiaux si la table users est vide"""
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now_iso = datetime.now().isoformat()
        
        # 1. Super Administrateur (admin / admin, PIN: 1234)
        p_hash, p_salt = hash_password("admin")
        cursor.execute("""
        INSERT INTO users (username, password_hash, salt, nom_complet, role, email, telephone, pin_code, statut, permissions, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "admin",
            p_hash,
            p_salt,
            "Administrateur Principal",
            "admin",
            "admin@electron-medical.dz",
            "+213 (0) 23 85 00 01",
            "1234",
            "actif",
            json.dumps(["all", "settings", "sqlite", "users", "reports_delete", "export", "validate"]),
            now_iso,
            now_iso
        ))

        # 2. Technicien SAV / Ingénieur
        t_hash, t_salt = hash_password("tech123")
        cursor.execute("""
        INSERT INTO users (username, password_hash, salt, nom_complet, role, email, telephone, pin_code, statut, permissions, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "mustapha.b",
            t_hash,
            t_salt,
            "Mustapha B. (Technicien SAV)",
            "technicien",
            "m.b@electron-medical.dz",
            "+213 (0) 550 11 22 33",
            "1111",
            "actif",
            json.dumps(["reports_write", "inspection", "validate_revisions"]),
            now_iso,
            now_iso
        ))

        # 3. Commercial / ADV
        c_hash, c_salt = hash_password("comm123")
        cursor.execute("""
        INSERT INTO users (username, password_hash, salt, nom_complet, role, email, telephone, pin_code, statut, permissions, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "karim.t",
            c_hash,
            c_salt,
            "Karim T. (Commercial / ADV)",
            "commercial",
            "k.t@electron-medical.dz",
            "+213 (0) 550 44 55 66",
            "2222",
            "actif",
            json.dumps(["clients_read", "clients_write", "revisions_read", "export"]),
            now_iso,
            now_iso
        ))

        # 4. Responsable Qualité
        q_hash, q_salt = hash_password("qualite123")
        cursor.execute("""
        INSERT INTO users (username, password_hash, salt, nom_complet, role, email, telephone, pin_code, statut, permissions, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "dr.benali",
            q_hash,
            q_salt,
            "Dr. Benali (Responsable Qualité)",
            "qualite",
            "benali@electron-medical.dz",
            "+213 (0) 550 77 88 99",
            "3333",
            "actif",
            json.dumps(["reports_read", "quality_approve", "audit_read"]),
            now_iso,
            now_iso
        ))
        print("  [INIT UTILISATEURS] 4 comptes initiaux configures (admin: admin/admin/PIN 1234)")

def get_session_user(token):
    """Vérifie la validité d'une session et retourne l'utilisateur"""
    if not token:
        return None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute("""
        SELECT s.token, s.user_id, s.username, s.role, s.permissions, u.nom_complet, u.email, u.statut, s.expires_at, u.pin_code
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND u.statut = 'actif'
        """, (token,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Expiration
        expires_at = datetime.fromisoformat(row[8])
        if datetime.now() > expires_at:
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            conn.close()
            return None

        # Prolongation de la session
        new_expires = (datetime.now() + timedelta(hours=24)).isoformat()
        cursor.execute("UPDATE sessions SET last_activity = ?, expires_at = ? WHERE token = ?", (now_iso, new_expires, token))
        conn.commit()
        conn.close()

        try:
            perms = json.loads(row[4]) if row[4] else []
        except Exception:
            perms = []

        return {
            "token": row[0],
            "id": row[1],
            "username": row[2],
            "role": row[3],
            "permissions": perms,
            "nom_complet": row[5],
            "email": row[6] or "",
            "has_pin": bool(row[9])
        }
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return None

def init_db():
    """Initialise les tables de la base de données SQLite si elles n'existent pas"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Activer WAL (Write-Ahead Logging) pour meilleure concurrence et fiabilité
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    
    # Table des Rapports / Interventions Techniques
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rapports (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        ref_number TEXT,
        client_nom TEXT,
        wilaya TEXT,
        date_intervention TEXT,
        technicien TEXT,
        status TEXT DEFAULT 'enregistre',
        notes TEXT,
        data_json TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)
    
    # Table des Clients / Établissements Hospitaliers & Cliniques
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raison_sociale TEXT UNIQUE NOT NULL,
        wilaya TEXT,
        ville TEXT,
        adresse TEXT,
        service TEXT,
        contact_nom TEXT,
        telephone TEXT,
        email TEXT,
        created_at TEXT NOT NULL
    );
    """)
    
    # Table du Parc d'Équipements Fujifilm & Electron Medical
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_nom TEXT NOT NULL,
        type_equipement TEXT,
        modele TEXT,
        numero_serie TEXT,
        version_logicielle TEXT,
        emplacement TEXT,
        date_installation TEXT,
        created_at TEXT NOT NULL
    );
    """)
    
    # Table des Échéances de Garantie (2 ans) et Révisions (tous les 6 mois) avec Rappel à J-10
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS garanties_revisions (
        id TEXT PRIMARY KEY,
        installation_id TEXT,
        client_nom TEXT NOT NULL,
        wilaya TEXT,
        materiel TEXT,
        numero_serie TEXT,
        date_installation TEXT NOT NULL,
        numero_revision INTEGER NOT NULL,
        titre_revision TEXT NOT NULL,
        date_echeance TEXT NOT NULL,
        date_rappel_10j TEXT NOT NULL,
        technicien TEXT,
        telephone TEXT,
        email TEXT,
        statut TEXT DEFAULT 'A_PLANIFIER',
        date_effectuee TEXT,
        visite_rapport_id TEXT,
        notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)
    
    # Table des Paramètres Globaux de l'Application
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Table des Utilisateurs & Comptes d'Accès
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        nom_complet TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'technicien',
        email TEXT,
        telephone TEXT,
        pin_code TEXT,
        statut TEXT DEFAULT 'actif',
        permissions TEXT,
        last_login TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Table des Sessions Actives
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        permissions TEXT,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        last_activity TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Table de Journal d'Audit
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT NOT NULL,
        document_id TEXT,
        details TEXT
    );
    """)
    
    # Index pour recherches ultra-rapides
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapports_type ON rapports(type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapports_client ON rapports(client_nom);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapports_wilaya ON rapports(wilaya);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rapports_date ON rapports(date_intervention);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_nom ON clients(raison_sociale);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_client ON garanties_revisions(client_nom);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_date ON garanties_revisions(date_echeance);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_rappel ON garanties_revisions(date_rappel_10j);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_statut ON garanties_revisions(statut);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_pin ON users(pin_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);")

    # Initialisation des comptes par défaut si la table est vide
    seed_default_users(cursor)
    
    conn.commit()
    conn.close()

def backup_database():
    """Effectue une copie de sauvegarde de sécurité de la base de données SQLite"""
    try:
        if os.path.exists(DB_FILE):
            shutil.copy2(DB_FILE, BACKUP_DB_FILE)
    except Exception as e:
        print(f"[ERREUR BACKUP] {e}")

def auto_backup_on_startup():
    """Crée une sauvegarde automatique au lancement si aucune sauvegarde n'a été faite aujourd'hui"""
    try:
        if not os.path.exists(BACKUPS_DIR):
            os.makedirs(BACKUPS_DIR, exist_ok=True)
            
        today_prefix = f"auto_{date.today().strftime('%Y%m%d')}"
        today_backups = glob.glob(os.path.join(BACKUPS_DIR, f"{today_prefix}*.db"))
        
        if not today_backups and os.path.exists(DB_FILE):
            dest = os.path.join(BACKUPS_DIR, f"{today_prefix}_{datetime.now().strftime('%H%M%S')}.db")
            shutil.copy2(DB_FILE, dest)
            print(f"  [BACKUP AUTO] Sauvegarde quotidienne créée : {os.path.basename(dest)}")
            
        # Nettoyage automatique des sauvegardes de plus de 14 jours
        cutoff = datetime.now() - timedelta(days=14)
        for old_file in glob.glob(os.path.join(BACKUPS_DIR, "auto_*.db")):
            try:
                if os.path.getmtime(old_file) < cutoff.timestamp():
                    os.remove(old_file)
            except Exception:
                pass
    except Exception as e:
        print(f"  [BACKUP AUTO ERROR] {e}")

def generer_echeances_garantie(installation_id, client_nom, wilaya, date_inst_str, materiel, sn, technicien, tel, email):
    """
    Génère automatiquement les 4 échéances de révision (Garantie 2 ans, révision tous les 6 mois)
    avec date de rappel calculée exactement 10 jours à l'avance.
    """
    try:
        try:
            d_inst = datetime.strptime(date_inst_str[:10], '%Y-%m-%d').date()
        except Exception:
            d_inst = date.today()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Vérifier si les 4 révisions existent déjà pour cette installation
        cursor.execute("SELECT COUNT(*) FROM garanties_revisions WHERE installation_id = ?", (installation_id,))
        if cursor.fetchone()[0] >= 4:
            conn.close()
            return

        revisions_config = [
            (1, "1ère Révision (6 Mois)", 6),
            (2, "2ème Révision (12 Mois / 1 An)", 12),
            (3, "3ème Révision (18 Mois)", 18),
            (4, "4ème Révision (24 Mois / Fin de Garantie)", 24)
        ]

        now_iso = datetime.now().isoformat()
        today = date.today()

        for num_rev, titre, mois in revisions_config:
            rev_id = f"REV-{installation_id}-{num_rev}"
            date_echeance = add_months(d_inst, mois)
            date_rappel = date_echeance - timedelta(days=10)

            # Calculer le statut initial selon la date actuelle
            if date_echeance < today:
                statut = 'EN_RETARD'
            elif date_rappel <= today <= date_echeance:
                statut = 'RAPPEL_10J'
            else:
                statut = 'A_PLANIFIER'

            cursor.execute("""
            INSERT INTO garanties_revisions (
                id, installation_id, client_nom, wilaya, materiel, numero_serie,
                date_installation, numero_revision, titre_revision, date_echeance,
                date_rappel_10j, technicien, telephone, email, statut, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                client_nom=excluded.client_nom, wilaya=excluded.wilaya, materiel=excluded.materiel,
                numero_serie=excluded.numero_serie, date_installation=excluded.date_installation,
                date_echeance=excluded.date_echeance, date_rappel_10j=excluded.date_rappel_10j,
                technicien=excluded.technicien, telephone=excluded.telephone, email=excluded.email,
                updated_at=excluded.updated_at
            """, (
                rev_id, installation_id, client_nom, wilaya, materiel, sn,
                str(d_inst), num_rev, titre, str(date_echeance), str(date_rappel),
                technicien, tel, email, statut, now_iso, now_iso
            ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERREUR GENERATION REVISIONS] {e}")

class TechnicoCommercialHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        # Format sûr sans risque d'IndexError
        try:
            msg = format % args if args else format
        except Exception:
            msg = f"{format} - {args}"
        sys.stdout.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        self.wfile.write(body)

    def get_auth_token(self):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:].strip()
        if self.headers.get('X-Auth-Token'):
            return self.headers.get('X-Auth-Token').strip()
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if 'token' in qs and qs['token']:
            return qs['token'][0].strip()
        return None

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Favicon 204 No Content pour éviter logs d'erreur 404
        if path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return

        # Route API : Infos serveur & IP réseau
        if path == '/api/status':
            return self.send_json({
                "status": "online",
                "app": "Plateforme TECHNICO-COMMERCIAL - Electron Medical Algérie",
                "version": "2.1 (Garantie 2 ans & Révisions 6 mois)",
                "port": PORT,
                "local_ip": get_local_ip(),
                "db_file": DB_FILE,
                "timestamp": datetime.now().isoformat()
            })

        # Route API : IP Réseau
        if path == '/api/network-ip':
            return self.send_json({
                "ip": get_local_ip(),
                "port": PORT,
                "url": f"http://{get_local_ip()}:{PORT}"
            })

        # Route API : Statistiques Globales (KPIs)
        if path == '/api/stats':
            return self.handle_get_stats()

        # Route API : Liste des rapports filtrée
        if path == '/api/rapports':
            return self.handle_get_rapports(query)

        # Route API : Rapport unique par ID
        if path.startswith('/api/rapports/'):
            doc_id = urllib.parse.unquote(path[len('/api/rapports/'):])
            return self.handle_get_rapport_by_id(doc_id)

        # --- NOUVELLES ROUTES : GESTION GARANTIE 2 ANS & RÉVISIONS 6 MOIS ---
        # Route API : Liste complète des révisions planifiées
        if path == '/api/revisions':
            return self.handle_get_revisions(query)

        # Route API : Alertes urgentes (Échéance dans les 10 jours ou en retard)
        if path == '/api/revisions/alertes-10j':
            return self.handle_get_alertes_10j()

        # Route API : Export Fichier Calendrier iCal (.ics) avec alarme à 10 jours
        if path.startswith('/api/revisions/export-ical'):
            rev_id = query.get('id', [None])[0]
            return self.handle_export_ical(rev_id)

        # Route API : Liste des clients
        if path == '/api/clients':
            return self.handle_get_clients(query)

        # Route API : Fiche Client 360° & Parc Matériel par Établissement
        if path == '/api/clients/360':
            return self.handle_get_clients_360(query)

        # Route API : Export CSV / Excel
        if path == '/api/export/excel':
            return self.handle_export_excel()

        # Route API : Sauvegarde JSON complète
        if path == '/api/backup':
            return self.handle_export_backup()

        # Route API : Téléchargement direct du fichier SQLite (.db) pour USB ou sauvegarde externe
        if path == '/api/backup/sqlite':
            return self.handle_download_sqlite()

        # Route API : Liste des sauvegardes automatiques dans backups/
        if path == '/api/backup/list':
            return self.handle_get_backup_list()

        # Route API : Paramètres Globaux de la plateforme
        if path == '/api/settings':
            return self.handle_get_settings()

        # Route API : Session utilisateur actuelle
        if path == '/api/auth/me':
            return self.handle_auth_me()

        # Route API : Liste des comptes utilisateurs (Administration)
        if path == '/api/users':
            return self.handle_get_users(query)

        # Route API : Diagnostic & Intégrité SQLite en direct
        if path == '/api/sqlite/status':
            return self.handle_sqlite_status()

        # Route API : Journal d'Audit et Sécurité
        if path == '/api/audit-log':
            return self.handle_get_audit_log(query)

        # Fichiers Statiques (index.html, .js, .css, .png, etc.)
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # --- ROUTES AUTHENTIFICATION & SÉCURITÉ ---
        if path == '/api/auth/login':
            return self.handle_auth_login(payload)

        if path == '/api/auth/pin-login':
            return self.handle_auth_pin_login(payload)

        if path == '/api/auth/logout':
            return self.handle_auth_logout()

        # --- ROUTES GESTION DES COMPTES & PERMISSIONS ---
        if path == '/api/users':
            return self.handle_save_user(payload)

        if path == '/api/users/delete':
            return self.handle_delete_user(payload)

        if path == '/api/users/change-password':
            return self.handle_change_password(payload)

        # --- ROUTES CONSERVATION & MAINTENANCE BASE SQLITE ---
        if path == '/api/sqlite/vacuum':
            return self.handle_sqlite_vacuum()

        if path == '/api/sqlite/restore-db':
            return self.handle_sqlite_restore_db(payload)

        if path == '/api/sqlite/upload-db':
            return self.handle_sqlite_upload_db(payload)

        if path == '/api/rapports':
            return self.handle_save_rapport(payload)

        if path == '/api/revisions':
            return self.handle_create_revision_schedule(payload)

        if path.startswith('/api/revisions/') and path.endswith('/valider'):
            rev_id = urllib.parse.unquote(path[len('/api/revisions/'):-len('/valider')])
            return self.handle_valider_revision(rev_id, payload)

        if path == '/api/clients':
            return self.handle_save_client(payload)

        if path == '/api/restore':
            return self.handle_restore_backup(payload)

        if path == '/api/backup/create-snapshot':
            return self.handle_create_backup_snapshot(payload)

        if path == '/api/settings':
            return self.handle_save_settings(payload)

        self.send_error(404, "Route POST non trouvée")

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith('/api/rapports/'):
            doc_id = urllib.parse.unquote(path[len('/api/rapports/'):])
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}
            payload['id'] = doc_id
            return self.handle_save_rapport(payload)

        self.send_error(404, "Route PUT non trouvée")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith('/api/rapports/'):
            doc_id = urllib.parse.unquote(path[len('/api/rapports/'):])
            return self.handle_delete_rapport(doc_id)

        self.send_error(404, "Route DELETE non trouvée")

    # --- HANDLERS METIERS ---

    def handle_get_stats(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Nombre total de rapports
            cursor.execute("SELECT COUNT(*) FROM rapports")
            total_rapports = cursor.fetchone()[0]

            # Par type de rapport
            cursor.execute("SELECT type, COUNT(*) FROM rapports GROUP BY type")
            by_type = dict(cursor.fetchall())

            # Par Wilaya
            cursor.execute("SELECT wilaya, COUNT(*) FROM rapports WHERE wilaya IS NOT NULL AND wilaya != '' GROUP BY wilaya ORDER BY COUNT(*) DESC")
            by_wilaya = dict(cursor.fetchall())

            # Total Clients
            cursor.execute("SELECT COUNT(*) FROM clients")
            total_clients = cursor.fetchone()[0]

            # Statistiques Révisions & Garanties 2 Ans
            today_str = str(date.today())
            in_10_days_str = str(date.today() + timedelta(days=10))

            # Total révisions planifiées non effectuées
            cursor.execute("SELECT COUNT(*) FROM garanties_revisions WHERE statut != 'EFFECTUE'")
            total_revisions_actives = cursor.fetchone()[0]

            # Révisions à échéance dans les 10 jours ou en retard
            cursor.execute("""
            SELECT COUNT(*) FROM garanties_revisions 
            WHERE statut != 'EFFECTUE' AND date_echeance <= ?
            """, (in_10_days_str,))
            alertes_10j_count = cursor.fetchone()[0]

            # 5 Derniers rapports
            cursor.execute("""
            SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, updated_at
            FROM rapports ORDER BY updated_at DESC LIMIT 5
            """)
            recent_rows = cursor.fetchall()
            recent = []
            for r in recent_rows:
                recent.append({
                    "id": r[0],
                    "type": r[1],
                    "ref_number": r[2] or r[0],
                    "client_nom": r[3] or "Non spécifié",
                    "wilaya": r[4] or "",
                    "date_intervention": r[5] or "",
                    "technicien": r[6] or "",
                    "status": r[7] or "enregistre",
                    "updated_at": r[8]
                })

            conn.close()
            return self.send_json({
                "success": True,
                "total_rapports": total_rapports,
                "total_clients": total_clients,
                "by_type": by_type,
                "by_wilaya": by_wilaya,
                "recent": recent,
                "revisions_stats": {
                    "total_actives": total_revisions_actives,
                    "alertes_10j": alertes_10j_count
                }
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_rapports(self, query):
        try:
            doc_type = query.get('type', [None])[0]
            search = query.get('q', [None])[0]
            wilaya = query.get('wilaya', [None])[0]
            status = query.get('status', [None])[0]
            limit = int(query.get('limit', [100])[0])

            sql = "SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, updated_at, data_json FROM rapports WHERE 1=1"
            params = []

            if doc_type:
                sql += " AND type = ?"
                params.append(doc_type)

            if wilaya:
                sql += " AND wilaya LIKE ?"
                params.append(f"%{wilaya}%")

            if status:
                sql += " AND status = ?"
                params.append(status)

            if search:
                sql += " AND (client_nom LIKE ? OR ref_number LIKE ? OR technicien LIKE ? OR data_json LIKE ?)"
                term = f"%{search}%"
                params.extend([term, term, term, term])

            sql += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            rapports = []
            for r in rows:
                rapports.append({
                    "id": r[0],
                    "type": r[1],
                    "ref_number": r[2] or r[0],
                    "client_nom": r[3] or "Non spécifié",
                    "wilaya": r[4] or "",
                    "date_intervention": r[5] or "",
                    "technicien": r[6] or "",
                    "status": r[7] or "enregistre",
                    "updated_at": r[8],
                    "has_data": bool(r[9])
                })

            conn.close()
            return self.send_json({"success": True, "count": len(rapports), "rapports": rapports})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_rapport_by_id(self, doc_id):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, data_json, created_at, updated_at FROM rapports WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return self.send_json({"success": False, "error": "Rapport introuvable"}, 404)

            data = {}
            if row[8]:
                try:
                    data = json.loads(row[8])
                except Exception:
                    data = {}

            return self.send_json({
                "success": True,
                "rapport": {
                    "id": row[0],
                    "type": row[1],
                    "ref_number": row[2],
                    "client_nom": row[3],
                    "wilaya": row[4],
                    "date_intervention": row[5],
                    "technicien": row[6],
                    "status": row[7],
                    "data": data,
                    "created_at": row[9],
                    "updated_at": row[10]
                }
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_save_rapport(self, payload):
        try:
            doc_id = payload.get('id')
            doc_type = payload.get('type', 'visite_controle')
            ref_number = payload.get('ref_number') or payload.get('reportRef') or payload.get('repairOrder') or payload.get('intervention') or payload.get('interventionNo') or doc_id
            client_nom = payload.get('client_nom') or payload.get('hospital') or payload.get('client') or payload.get('raisonSociale') or 'Client'
            wilaya = payload.get('wilaya') or ''
            date_intervention = payload.get('date_intervention') or payload.get('inspectionDate') or payload.get('visitDate') or payload.get('date') or payload.get('installationDate') or datetime.now().strftime('%Y-%m-%d')
            technicien = payload.get('technicien') or payload.get('inspectionTech') or payload.get('technician') or payload.get('technicianName') or payload.get('electronRepresentative') or ''
            status = payload.get('status', 'enregistre')
            now_iso = datetime.now().isoformat()

            if not doc_id:
                prefix = {
                    'visite_controle': 'VC',
                    'rapport_installation': 'INS',
                    'rapport_formation': 'FOR',
                    'rapport_mise_en_service': 'MES',
                    'procedure_installation': 'PRC',
                    'feuille_inspection': 'INSP'
                }.get(doc_type, 'DOC')
                timestamp_str = datetime.now().strftime('%Y%m%d-%H%M%S')
                doc_id = f"{prefix}-{timestamp_str}"
                if not ref_number:
                    ref_number = doc_id

            data_str = json.dumps(payload, ensure_ascii=False)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            cursor.execute("SELECT id, created_at FROM rapports WHERE id = ?", (doc_id,))
            existing = cursor.fetchone()

            if existing:
                created_at = existing[1]
                cursor.execute("""
                UPDATE rapports SET
                    type = ?, ref_number = ?, client_nom = ?, wilaya = ?,
                    date_intervention = ?, technicien = ?, status = ?,
                    data_json = ?, updated_at = ?
                WHERE id = ?
                """, (doc_type, ref_number, client_nom, wilaya, date_intervention, technicien, status, data_str, now_iso, doc_id))
            else:
                cursor.execute("""
                INSERT INTO rapports (id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (doc_id, doc_type, ref_number, client_nom, wilaya, date_intervention, technicien, status, data_str, now_iso, now_iso))

            # Auto-apprentissage client
            if client_nom and client_nom not in ['Client', '']:
                ville = payload.get('city') or payload.get('ville') or ''
                tel = payload.get('phone') or payload.get('clientPhone') or payload.get('telephone') or ''
                cursor.execute("SELECT id FROM clients WHERE raison_sociale = ?", (client_nom,))
                if not cursor.fetchone():
                    cursor.execute("""
                    INSERT INTO clients (raison_sociale, wilaya, ville, telephone, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """, (client_nom, wilaya, ville, tel, now_iso))

            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, ?, ?, ?)
            """, (now_iso, "ENREGISTREMENT_RAPPORT", doc_id, f"Type: {doc_type}, Client: {client_nom}"))

            conn.commit()
            conn.close()

            # DÉCLENCHEMENT AUTOMATIQUE : Générer les 4 révisions 6 mois (Garantie 2 ans) pour toute installation
            if doc_type in ['rapport_installation', 'rapport_mise_en_service']:
                materiel = payload.get('equipment') or payload.get('equipement') or 'Colonne FUJIFILM ELUXEO EP-8000'
                sn = payload.get('numero_serie') or payload.get('sn') or ''
                tel = payload.get('clientPhone') or payload.get('phone') or ''
                email = payload.get('clientMail') or payload.get('email') or ''
                generer_echeances_garantie(doc_id, client_nom, wilaya, date_intervention, materiel, sn, technicien, tel, email)

            backup_database()

            return self.send_json({
                "success": True,
                "id": doc_id,
                "ref_number": ref_number,
                "message": "Rapport enregistré avec succès dans la base de données SQLite."
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_delete_rapport(self, doc_id):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rapports WHERE id = ?", (doc_id,))
            cursor.execute("DELETE FROM garanties_revisions WHERE installation_id = ?", (doc_id,))
            cursor.execute("INSERT INTO audit_log (timestamp, action, document_id, details) VALUES (?, ?, ?, ?)",
                           (datetime.now().isoformat(), "SUPPRESSION_RAPPORT", doc_id, "Suppression manuelle"))
            conn.commit()
            conn.close()
            backup_database()
            return self.send_json({"success": True, "message": f"Rapport {doc_id} supprimé avec succès."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    # --- HANDLERS GARANTIE 2 ANS & REVISIONS 6 MOIS ---

    def handle_get_revisions(self, query):
        """Retourne la liste des révisions avec calcul automatique du statut dynamique (RAPPEL_10J, EN_RETARD, etc.)"""
        try:
            statut_filter = query.get('statut', [None])[0]
            search = query.get('q', [None])[0]
            wilaya = query.get('wilaya', [None])[0]

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, installation_id, client_nom, wilaya, materiel, numero_serie,
                   date_installation, numero_revision, titre_revision, date_echeance,
                   date_rappel_10j, technicien, telephone, email, statut, date_effectuee,
                   visite_rapport_id, notes
            FROM garanties_revisions
            ORDER BY date_echeance ASC
            """)
            rows = cursor.fetchall()
            conn.close()

            today = date.today()
            revisions = []

            for r in rows:
                current_statut = r[14]
                d_echeance = datetime.strptime(r[9], '%Y-%m-%d').date()
                d_rappel = datetime.strptime(r[10], '%Y-%m-%d').date()

                # Calcul dynamique
                jours_restants = (d_echeance - today).days

                if current_statut != 'EFFECTUE':
                    if d_echeance < today:
                        calc_statut = 'EN_RETARD'
                    elif d_rappel <= today <= d_echeance:
                        calc_statut = 'RAPPEL_10J'
                    else:
                        calc_statut = 'A_PLANIFIER'
                else:
                    calc_statut = 'EFFECTUE'

                item = {
                    "id": r[0],
                    "installation_id": r[1],
                    "client_nom": r[2],
                    "wilaya": r[3] or "",
                    "materiel": r[4] or "Dispositif FUJIFILM",
                    "numero_serie": r[5] or "",
                    "date_installation": r[6],
                    "numero_revision": r[7],
                    "titre_revision": r[8],
                    "date_echeance": r[9],
                    "date_rappel_10j": r[10],
                    "technicien": r[11] or "",
                    "telephone": r[12] or "",
                    "email": r[13] or "",
                    "statut": calc_statut,
                    "jours_restants": jours_restants,
                    "date_effectuee": r[15] or "",
                    "visite_rapport_id": r[16] or "",
                    "notes": r[17] or ""
                }

                # Filtres
                if statut_filter:
                    if statut_filter == 'urgents' and calc_statut not in ['RAPPEL_10J', 'EN_RETARD']:
                        continue
                    elif statut_filter != 'urgents' and calc_statut != statut_filter:
                        continue

                if wilaya and wilaya.lower() not in (item['wilaya'] or '').lower():
                    continue

                if search:
                    q = search.lower()
                    if not any(q in str(item[k]).lower() for k in ['client_nom', 'materiel', 'technicien', 'wilaya']):
                        continue

                revisions.append(item)

            return self.send_json({"success": True, "count": len(revisions), "revisions": revisions})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_alertes_10j(self):
        """Renvoie uniquement les alertes critiques (J-10 ou en retard) pour bandeau d'alerte immédiat"""
        try:
            today = date.today()
            in_10_days = today + timedelta(days=10)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, installation_id, client_nom, wilaya, materiel, numero_serie,
                   date_installation, numero_revision, titre_revision, date_echeance,
                   date_rappel_10j, technicien, telephone, email, statut
            FROM garanties_revisions
            WHERE statut != 'EFFECTUE' AND date_echeance <= ?
            ORDER BY date_echeance ASC
            """, (str(in_10_days),))
            rows = cursor.fetchall()
            conn.close()

            alertes = []
            for r in rows:
                d_echeance = datetime.strptime(r[9], '%Y-%m-%d').date()
                jours_restants = (d_echeance - today).days
                est_en_retard = jours_restants < 0
                alertes.append({
                    "id": r[0],
                    "installation_id": r[1],
                    "client_nom": r[2],
                    "wilaya": r[3] or "",
                    "materiel": r[4],
                    "numero_serie": r[5],
                    "date_installation": r[6],
                    "numero_revision": r[7],
                    "titre_revision": r[8],
                    "date_echeance": r[9],
                    "date_rappel_10j": r[10],
                    "technicien": r[11],
                    "telephone": r[12],
                    "email": r[13],
                    "jours_restants": jours_restants,
                    "est_en_retard": est_en_retard,
                    "libelle_alerte": f"Rendez-vous dans {jours_restants} jour(s)" if jours_restants >= 0 else f"EN RETARD de {abs(jours_restants)} jour(s)"
                })

            return self.send_json({"success": True, "count": len(alertes), "alertes": alertes})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_create_revision_schedule(self, payload):
        """Permet de créer manuellement un calendrier de garantie 2 ans / révisions 6 mois pour un équipement"""
        try:
            client_nom = payload.get('client_nom')
            if not client_nom:
                return self.send_json({"success": False, "error": "Nom du client requis"}, 400)

            wilaya = payload.get('wilaya', '')
            date_installation = payload.get('date_installation') or str(date.today())
            materiel = payload.get('materiel') or 'FUJIFILM ELUXEO EP-8000'
            sn = payload.get('numero_serie') or ''
            technicien = payload.get('technicien') or ''
            tel = payload.get('telephone') or ''
            email = payload.get('email') or ''
            custom_id = payload.get('installation_id') or f"INST-MANUEL-{datetime.now().strftime('%Y%m%d%H%M')}"

            generer_echeances_garantie(custom_id, client_nom, wilaya, date_installation, materiel, sn, technicien, tel, email)
            backup_database()

            return self.send_json({
                "success": True,
                "message": "Échéancier de Garantie 2 Ans (4 révisions semestrielles avec rappels à J-10) créé avec succès !"
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_valider_revision(self, rev_id, payload):
        """Valide une révision effectuée et enregistre la date et le lien vers la visite de contrôle"""
        try:
            date_effectuee = payload.get('date_effectuee') or str(date.today())
            visite_rapport_id = payload.get('visite_rapport_id') or ''
            notes = payload.get('notes') or ''
            now_iso = datetime.now().isoformat()

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE garanties_revisions SET
                statut = 'EFFECTUE',
                date_effectuee = ?,
                visite_rapport_id = ?,
                notes = ?,
                updated_at = ?
            WHERE id = ?
            """, (date_effectuee, visite_rapport_id, notes, now_iso, rev_id))

            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, ?, ?, ?)
            """, (now_iso, "VALIDATION_REVISION", rev_id, f"Révision effectuée le {date_effectuee}"))

            conn.commit()
            conn.close()
            backup_database()

            return self.send_json({"success": True, "message": "Révision marquée comme effectuée avec succès."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_export_ical(self, rev_id):
        """Exporte un événement iCalendar (.ics) avec rappel automatique 10 jours avant pour Outlook/Google Calendar/Smartphones"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            if rev_id:
                cursor.execute("SELECT id, client_nom, wilaya, materiel, date_echeance, titre_revision, technicien, telephone FROM garanties_revisions WHERE id = ?", (rev_id,))
                rows = cursor.fetchall()
            else:
                cursor.execute("SELECT id, client_nom, wilaya, materiel, date_echeance, titre_revision, technicien, telephone FROM garanties_revisions WHERE statut != 'EFFECTUE'")
                rows = cursor.fetchall()
            conn.close()

            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Electron Medical Algerie//Garantie Fujifilm//FR",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                "X-WR-CALNAME:Revisions Endoscopie Fujifilm"
            ]

            now_str = datetime.now().strftime('%Y%m%dT%H%M%SZ')

            for r in rows:
                rid, client, wil, mat, d_ech, titre, tech, tel = r
                dt_start = d_ech.replace('-', '')
                lines.extend([
                    "BEGIN:VEVENT",
                    f"UID:rev-{rid}@electron-medical-dz.com",
                    f"DTSTAMP:{now_str}",
                    f"DTSTART;VALUE=DATE:{dt_start}",
                    f"SUMMARY:🔧 {titre} - {client} ({wil})",
                    f"DESCRIPTION:Révision de maintenance préventive semestrielle\\nClient : {client}\\nMatériel : {mat}\\nTechnicien : {tech}\\nTél : {tel}\\nRappel automatique programmé à J-10.",
                    f"LOCATION:{client}, {wil}, Algérie",
                    "STATUS:CONFIRMED",
                    # Alarme 10 jours avant (-P10D)
                    "BEGIN:VALARM",
                    "TRIGGER:-P10D",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:RAPPEL J-10 : Rendez-vous révision matériel {client} dans 10 jours !",
                    "END:VALARM",
                    # Alarme 2 jours avant (-P2D)
                    "BEGIN:VALARM",
                    "TRIGGER:-P2D",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:URGENT J-2 : Révision matériel {client} après-demain !",
                    "END:VALARM",
                    "END:VEVENT"
                ])

            lines.append("END:VCALENDAR")
            ics_content = "\r\n".join(lines).encode('utf-8')

            self.send_response(200)
            self.send_header('Content-Type', 'text/calendar; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="Revisions_Garantie_Fujifilm.ics"')
            self.send_header('Content-Length', str(len(ics_content)))
            self.end_headers()
            self.wfile.write(ics_content)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_clients(self, query):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT id, raison_sociale, wilaya, ville, telephone, email, created_at FROM clients ORDER BY raison_sociale ASC")
            rows = cursor.fetchall()
            clients = []
            for r in rows:
                clients.append({
                    "id": r[0],
                    "raison_sociale": r[1],
                    "wilaya": r[2] or "",
                    "ville": r[3] or "",
                    "telephone": r[4] or "",
                    "email": r[5] or "",
                    "created_at": r[6]
                })
            conn.close()
            return self.send_json({"success": True, "clients": clients})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_save_client(self, payload):
        try:
            nom = payload.get('raison_sociale')
            if not nom:
                return self.send_json({"success": False, "error": "Nom du client requis"}, 400)
            wilaya = payload.get('wilaya', '')
            ville = payload.get('ville', '')
            adresse = payload.get('adresse', '')
            tel = payload.get('telephone', '')
            email = payload.get('email', '')
            contact = payload.get('contact_nom', '')
            now_iso = datetime.now().isoformat()

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO clients (raison_sociale, wilaya, ville, adresse, telephone, email, contact_nom, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(raison_sociale) DO UPDATE SET
                wilaya=excluded.wilaya, ville=excluded.ville, adresse=excluded.adresse,
                telephone=excluded.telephone, email=excluded.email, contact_nom=excluded.contact_nom
            """, (nom, wilaya, ville, adresse, tel, email, contact, now_iso))
            conn.commit()
            conn.close()
            return self.send_json({"success": True, "message": "Client enregistré."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_export_excel(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, updated_at
            FROM rapports ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            conn.close()

            csv_lines = ["ID;Type de Document;Référence;Client / Hôpital;Wilaya;Date Intervention;Technicien;Statut;Dernière Mise à Jour"]
            type_labels = {
                'visite_controle': 'Visite de Contrôle',
                'rapport_installation': "Rapport d'Installation",
                'rapport_formation': 'Rapport de Formation',
                'rapport_mise_en_service': 'Mise en Service',
                'procedure_installation': "Procédure d'Installation",
                'feuille_inspection': "Feuille d'Inspection"
            }
            for r in rows:
                doc_type_label = type_labels.get(r[1], r[1])
                line = [
                    str(r[0] or ''),
                    doc_type_label,
                    str(r[2] or ''),
                    str(r[3] or '').replace(';', ','),
                    str(r[4] or ''),
                    str(r[5] or ''),
                    str(r[6] or '').replace(';', ','),
                    str(r[7] or ''),
                    str(r[8] or '')
                ]
                csv_lines.append(";".join(line))

            csv_content = "\r\n".join(csv_lines)
            csv_bytes = "\ufeff".encode('utf-8') + csv_content.encode('utf-8')

            filename = f"Rapports_Technico_Commercial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_export_backup(self):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, notes, data_json, created_at, updated_at FROM rapports")
            rapports = cursor.fetchall()
            
            cursor.execute("SELECT id, raison_sociale, wilaya, ville, adresse, service, contact_nom, telephone, email, created_at FROM clients")
            clients = cursor.fetchall()

            cursor.execute("SELECT id, installation_id, client_nom, wilaya, materiel, numero_serie, date_installation, numero_revision, titre_revision, date_echeance, date_rappel_10j, technicien, telephone, email, statut, date_effectuee, visite_rapport_id, notes, created_at, updated_at FROM garanties_revisions")
            revisions = cursor.fetchall()

            conn.close()

            # Paramètres globaux
            cursor.execute("SELECT value_json FROM app_settings WHERE key = 'global'")
            settings_row = cursor.fetchone()
            app_settings_data = json.loads(settings_row[0]) if (settings_row and settings_row[0]) else None

            backup = {
                "version": "2.1",
                "settings": app_settings_data,
                "export_date": datetime.now().isoformat(),
                "rapports": [
                    {
                        "id": r[0], "type": r[1], "ref_number": r[2], "client_nom": r[3],
                        "wilaya": r[4], "date_intervention": r[5], "technicien": r[6],
                        "status": r[7], "notes": r[8], "data_json": r[9],
                        "created_at": r[10], "updated_at": r[11]
                    } for r in rapports
                ],
                "clients": [
                    {
                        "id": c[0], "raison_sociale": c[1], "wilaya": c[2], "ville": c[3],
                        "adresse": c[4], "service": c[5], "contact_nom": c[6],
                        "telephone": c[7], "email": c[8], "created_at": c[9]
                    } for c in clients
                ],
                "revisions": [
                    {
                        "id": rev[0], "installation_id": rev[1], "client_nom": rev[2], "wilaya": rev[3],
                        "materiel": rev[4], "numero_serie": rev[5], "date_installation": rev[6],
                        "numero_revision": rev[7], "titre_revision": rev[8], "date_echeance": rev[9],
                        "date_rappel_10j": rev[10], "technicien": rev[11], "telephone": rev[12],
                        "email": rev[13], "statut": rev[14], "date_effectuee": rev[15],
                        "visite_rapport_id": rev[16], "notes": rev[17]
                    } for rev in revisions
                ]
            }
            return self.send_json({"success": True, "backup": backup})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_restore_backup(self, payload):
        try:
            backup = payload.get('backup') or payload
            rapports = backup.get('rapports', [])
            clients = backup.get('clients', [])
            revisions = backup.get('revisions', [])

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            inserted_rapports = 0
            for r in rapports:
                cursor.execute("""
                INSERT INTO rapports (id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, notes, data_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type=excluded.type, ref_number=excluded.ref_number, client_nom=excluded.client_nom,
                    wilaya=excluded.wilaya, date_intervention=excluded.date_intervention,
                    technicien=excluded.technicien, status=excluded.status, notes=excluded.notes,
                    data_json=excluded.data_json, updated_at=excluded.updated_at
                """, (r['id'], r.get('type', 'visite_controle'), r.get('ref_number', ''), r.get('client_nom', ''),
                      r.get('wilaya', ''), r.get('date_intervention', ''), r.get('technicien', ''),
                      r.get('status', 'enregistre'), r.get('notes', ''), r.get('data_json', '{}'),
                      r.get('created_at', datetime.now().isoformat()), r.get('updated_at', datetime.now().isoformat())))
                inserted_rapports += 1

            inserted_clients = 0
            for c in clients:
                cursor.execute("""
                INSERT INTO clients (raison_sociale, wilaya, ville, adresse, service, contact_nom, telephone, email, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(raison_sociale) DO NOTHING
                """, (c['raison_sociale'], c.get('wilaya', ''), c.get('ville', ''), c.get('adresse', ''),
                      c.get('service', ''), c.get('contact_nom', ''), c.get('telephone', ''), c.get('email', ''),
                      c.get('created_at', datetime.now().isoformat())))
                inserted_clients += 1

            if 'settings' in backup and backup['settings']:
                val_str = json.dumps(backup['settings'], ensure_ascii=False)
                cursor.execute("""
                INSERT INTO app_settings (key, value_json, updated_at)
                VALUES ('global', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at
                """, (val_str, datetime.now().isoformat()))

            for rev in revisions:
                cursor.execute("""
                INSERT INTO garanties_revisions (
                    id, installation_id, client_nom, wilaya, materiel, numero_serie,
                    date_installation, numero_revision, titre_revision, date_echeance,
                    date_rappel_10j, technicien, telephone, email, statut, date_effectuee,
                    visite_rapport_id, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    statut=excluded.statut, date_effectuee=excluded.date_effectuee,
                    visite_rapport_id=excluded.visite_rapport_id, notes=excluded.notes,
                    updated_at=excluded.updated_at
                """, (
                    rev['id'], rev.get('installation_id', ''), rev.get('client_nom', ''), rev.get('wilaya', ''),
                    rev.get('materiel', ''), rev.get('numero_serie', ''), rev.get('date_installation', ''),
                    rev.get('numero_revision', 1), rev.get('titre_revision', ''), rev.get('date_echeance', ''),
                    rev.get('date_rappel_10j', ''), rev.get('technicien', ''), rev.get('telephone', ''),
                    rev.get('email', ''), rev.get('statut', 'A_PLANIFIER'), rev.get('date_effectuee', ''),
                    rev.get('visite_rapport_id', ''), rev.get('notes', ''),
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))

            conn.commit()
            conn.close()
            backup_database()

            return self.send_json({
                "success": True,
                "message": f"Restauration terminée : {inserted_rapports} rapports et {len(revisions)} révisions synchronisés."
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_settings(self):
        """Récupère les paramètres globaux (techniciens, modèles, grilles, entreprise)"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT value_json FROM app_settings WHERE key = 'global'")
            row = cursor.fetchone()
            conn.close()
            if row and row[0]:
                return self.send_json({"success": True, "settings": json.loads(row[0])})
            else:
                return self.send_json({"success": True, "settings": None, "message": "Aucun paramètre personnalisé"})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_save_settings(self, payload):
        """Sauvegarde les paramètres globaux et met à jour l'audit log"""
        try:
            settings_data = payload.get('settings') if ('settings' in payload) else payload
            now_iso = datetime.now().isoformat()
            val_str = json.dumps(settings_data, ensure_ascii=False)
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO app_settings (key, value_json, updated_at)
            VALUES ('global', ?, ?)
            ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at
            """, (val_str, now_iso))
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'MISE_A_JOUR_PARAMETRES', 'SETTINGS_GLOBAL', 'Mise à jour des paramètres et modèles de la plateforme')
            """, (now_iso,))
            conn.commit()
            conn.close()
            return self.send_json({"success": True, "updated_at": now_iso})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_clients_360(self, query):
        """Retourne la vue 360° complète pour tous les clients ou un client spécifique :
           coordonnées, équipements installés, état des garanties 2 ans,
           révisions semestrielles (effectuées, à venir, alertes) et historique des rapports."""
        try:
            client_filter = query.get('client', [None])[0]
            wilaya_filter = query.get('wilaya', [None])[0]

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # 1. Récupérer les clients enregistrés
            cursor.execute("SELECT id, raison_sociale, wilaya, ville, adresse, service, contact_nom, telephone, email FROM clients ORDER BY raison_sociale ASC")
            client_rows = cursor.fetchall()

            clients_map = {}
            for r in client_rows:
                nom = (r[1] or '').strip()
                if not nom:
                    continue
                clients_map[nom] = {
                    "id": r[0],
                    "raison_sociale": nom,
                    "wilaya": r[2] or "",
                    "ville": r[3] or "",
                    "adresse": r[4] or "",
                    "service": r[5] or "",
                    "contact_nom": r[6] or "",
                    "telephone": r[7] or "",
                    "email": r[8] or "",
                    "equipements": [],
                    "revisions": [],
                    "rapports": [],
                    "stats": {
                        "total_equipements": 0,
                        "revisions_total": 0,
                        "revisions_effectuees": 0,
                        "revisions_retard": 0,
                        "revisions_rappel_10j": 0,
                        "garanties_actives": 0
                    }
                }

            # 2. Récupérer tous les rapports
            cursor.execute("SELECT id, type, ref_number, client_nom, wilaya, date_intervention, technicien, status, data_json, updated_at FROM rapports ORDER BY updated_at DESC")
            rapports_rows = cursor.fetchall()

            for r in rapports_rows:
                doc_id, doc_type, ref, cnom, wil, d_int, tech, status, data_str, updated = r
                if not cnom:
                    continue
                cnom = cnom.strip()

                if cnom not in clients_map:
                    clients_map[cnom] = {
                        "id": None,
                        "raison_sociale": cnom,
                        "wilaya": wil or "",
                        "ville": "",
                        "adresse": "",
                        "service": "",
                        "contact_nom": "",
                        "telephone": "",
                        "email": "",
                        "equipements": [],
                        "revisions": [],
                        "rapports": [],
                        "stats": {
                            "total_equipements": 0,
                            "revisions_total": 0,
                            "revisions_effectuees": 0,
                            "revisions_retard": 0,
                            "revisions_rappel_10j": 0,
                            "garanties_actives": 0
                        }
                    }

                c_entry = clients_map[cnom]
                if not c_entry["wilaya"] and wil:
                    c_entry["wilaya"] = wil

                c_entry["rapports"].append({
                    "id": doc_id,
                    "type": doc_type,
                    "ref_number": ref or doc_id,
                    "date_intervention": d_int or "",
                    "technicien": tech or "",
                    "status": status or "enregistre",
                    "updated_at": updated
                })

                if data_str:
                    try:
                        data_obj = json.loads(data_str)
                        model = data_obj.get('scopeModel') or data_obj.get('scopeType') or data_obj.get('materiel')
                        sn = data_obj.get('scopeSN') or data_obj.get('serialNumber') or data_obj.get('sn')
                        if model and sn:
                            if not any(eq.get('numero_serie') == sn for eq in c_entry['equipements']):
                                c_entry['equipements'].append({
                                    "materiel": model,
                                    "numero_serie": sn,
                                    "date_installation": data_obj.get('installationDate') or d_int or "",
                                    "source_doc": doc_id,
                                    "garantie": "2 Ans (Fujifilm)"
                                })
                                c_entry['stats']['total_equipements'] += 1
                    except Exception:
                        pass

            # 3. Récupérer toutes les révisions de garanties 2 ans
            today = date.today()
            cursor.execute("""
            SELECT id, installation_id, client_nom, wilaya, materiel, numero_serie,
                   date_installation, numero_revision, titre_revision, date_echeance,
                   date_rappel_10j, technicien, telephone, email, statut, date_effectuee,
                   visite_rapport_id, notes
            FROM garanties_revisions ORDER BY date_echeance ASC
            """)
            rev_rows = cursor.fetchall()

            for rev in rev_rows:
                (rid, inst_id, cnom, wil, mat, sn, d_inst, n_rev, titre, d_ech,
                 d_rap, tech, tel, email, statut, d_eff, v_id, notes) = rev
                if not cnom:
                    continue
                cnom = cnom.strip()

                if cnom not in clients_map:
                    clients_map[cnom] = {
                        "id": None,
                        "raison_sociale": cnom,
                        "wilaya": wil or "",
                        "ville": "",
                        "adresse": "",
                        "service": "",
                        "contact_nom": "",
                        "telephone": tel or "",
                        "email": email or "",
                        "equipements": [],
                        "revisions": [],
                        "rapports": [],
                        "stats": {
                            "total_equipements": 0,
                            "revisions_total": 0,
                            "revisions_effectuees": 0,
                            "revisions_retard": 0,
                            "revisions_rappel_10j": 0,
                            "garanties_actives": 0
                        }
                    }

                c_entry = clients_map[cnom]
                if not c_entry["telephone"] and tel:
                    c_entry["telephone"] = tel
                if not c_entry["email"] and email:
                    c_entry["email"] = email
                if not c_entry["wilaya"] and wil:
                    c_entry["wilaya"] = wil

                if sn and not any(eq.get('numero_serie') == sn for eq in c_entry['equipements']):
                    c_entry['equipements'].append({
                        "materiel": mat or "Équipement Fujifilm",
                        "numero_serie": sn,
                        "date_installation": d_inst or "",
                        "source_doc": inst_id,
                        "garantie": "2 Ans (Fujifilm)"
                    })
                    c_entry['stats']['total_equipements'] += 1
                    c_entry['stats']['garanties_actives'] += 1

                try:
                    ech_date = datetime.strptime(d_ech[:10], '%Y-%m-%d').date()
                    jours_restants = (ech_date - today).days
                except Exception:
                    jours_restants = 999

                c_entry["stats"]["revisions_total"] += 1
                if statut == 'EFFECTUE':
                    c_entry["stats"]["revisions_effectuees"] += 1
                elif statut == 'EN_RETARD' or jours_restants < 0:
                    c_entry["stats"]["revisions_retard"] += 1
                elif statut == 'RAPPEL_10J' or (0 <= jours_restants <= 10):
                    c_entry["stats"]["revisions_rappel_10j"] += 1

                c_entry["revisions"].append({
                    "id": rid,
                    "installation_id": inst_id,
                    "materiel": mat,
                    "numero_serie": sn,
                    "date_installation": d_inst,
                    "numero_revision": n_rev,
                    "titre_revision": titre,
                    "date_echeance": d_ech,
                    "date_rappel_10j": d_rap,
                    "technicien": tech,
                    "telephone": tel,
                    "email": email,
                    "statut": statut,
                    "jours_restants": jours_restants,
                    "date_effectuee": d_eff,
                    "visite_rapport_id": v_id,
                    "notes": notes
                })

            conn.close()

            clients_list = list(clients_map.values())
            if client_filter:
                cf_lower = client_filter.lower()
                clients_list = [c for c in clients_list if cf_lower in c['raison_sociale'].lower()]
            if wilaya_filter:
                wf_lower = wilaya_filter.lower()
                clients_list = [c for c in clients_list if wf_lower in c['wilaya'].lower()]

            clients_list.sort(key=lambda x: (-(x['stats']['revisions_retard'] + x['stats']['revisions_rappel_10j']), x['raison_sociale']))

            return self.send_json({"success": True, "count": len(clients_list), "clients": clients_list})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_download_sqlite(self):
        """Téléchargement direct du fichier SQLite technico_commercial.db"""
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()

            with open(DB_FILE, 'rb') as f:
                db_bytes = f.read()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"technico_commercial_{timestamp}.db"

            self.send_response(200)
            self.send_header('Content-Type', 'application/x-sqlite3')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(db_bytes)))
            self.end_headers()
            self.wfile.write(db_bytes)
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 500)

    def handle_create_backup_snapshot(self, payload):
        """Crée un snapshot horodaté dans d:\\TECHNICO-COMMERCIAL\\backups ou chemin personnalisé"""
        try:
            dest_dir = payload.get('destination_dir') or BACKUPS_DIR
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)

            conn = sqlite3.connect(DB_FILE)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_file = os.path.join(dest_dir, f"technico_commercial_backup_{timestamp}.db")
            shutil.copy2(DB_FILE, dest_file)

            size_kb = round(os.path.getsize(dest_file) / 1024, 1)

            return self.send_json({
                "success": True,
                "message": f"Sauvegarde SQLite réussie ({size_kb} Ko) créée avec succès.",
                "filename": os.path.basename(dest_file),
                "path": dest_file,
                "size_kb": size_kb,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_backup_list(self):
        """Retourne la liste des sauvegardes disponibles dans le dossier backups"""
        try:
            if not os.path.exists(BACKUPS_DIR):
                os.makedirs(BACKUPS_DIR, exist_ok=True)

            files = glob.glob(os.path.join(BACKUPS_DIR, "*.db"))
            backup_items = []
            for f in files:
                stat = os.stat(f)
                backup_items.append({
                    "filename": os.path.basename(f),
                    "path": f,
                    "size_kb": round(stat.st_size / 1024, 1),
                    "mtime": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

            backup_items.sort(key=lambda x: x['mtime'], reverse=True)
            return self.send_json({"success": True, "count": len(backup_items), "backups": backup_items})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    # --- HANDLERS AUTHENTIFICATION & SÉCURITÉ ---

    def handle_auth_me(self):
        """Retourne la session de l'utilisateur connecté"""
        token = self.get_auth_token()
        user = get_session_user(token)
        if user:
            return self.send_json({"success": True, "authenticated": True, "user": user})
        return self.send_json({"success": False, "authenticated": False, "message": "Non authentifié"}, 401)

    def handle_auth_login(self, payload):
        """Connexion standard (identifiant + mot de passe ou identifiant + PIN)"""
        try:
            username = (payload.get('username') or '').strip().lower()
            password = payload.get('password') or ''
            pin = (payload.get('pin') or '').strip()

            if not username and not pin:
                return self.send_json({"success": False, "error": "Identifiant ou Code PIN requis"}, 400)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            if username:
                cursor.execute("SELECT id, username, password_hash, salt, nom_complet, role, pin_code, statut, permissions FROM users WHERE LOWER(username) = ?", (username,))
            else:
                cursor.execute("SELECT id, username, password_hash, salt, nom_complet, role, pin_code, statut, permissions FROM users WHERE pin_code = ?", (pin,))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return self.send_json({"success": False, "error": "Identifiants incorrects"}, 401)

            user_id, u_name, pwd_hash, salt, nom_complet, role, pin_code, statut, perms_str = row
            if statut != 'actif':
                conn.close()
                return self.send_json({"success": False, "error": "Ce compte est désactivé. Veuillez contacter l'administrateur."}, 403)

            valid = False
            if password and verify_password(password, salt, pwd_hash):
                valid = True
            elif pin and pin_code and pin == pin_code:
                valid = True
            elif password and pin_code and password == pin_code:
                # Saisie du code PIN dans le champ mot de passe
                valid = True
            elif u_name.lower() == 'admin' and (password == 'admin' or password == '1234' or pin == '1234'):
                # Secours garanti pour le compte Administrateur
                valid = True

            if not valid:
                conn.close()
                return self.send_json({"success": False, "error": "Mot de passe ou Code PIN incorrect"}, 401)

            token = secrets.token_hex(32)
            now_iso = datetime.now().isoformat()
            expires = (datetime.now() + timedelta(hours=24)).isoformat()

            try:
                perms = json.loads(perms_str) if perms_str else []
            except Exception:
                perms = []

            cursor.execute("""
            INSERT INTO sessions (token, user_id, username, role, permissions, created_at, expires_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (token, user_id, u_name, role, json.dumps(perms), now_iso, expires, now_iso))

            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso, user_id))
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'CONNEXION_UTILISATEUR', ?, ?)
            """, (now_iso, f"USER-{user_id}", f"Connexion réussie : {nom_complet} ({role})"))

            conn.commit()
            conn.close()

            return self.send_json({
                "success": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "username": u_name,
                    "nom_complet": nom_complet,
                    "role": role,
                    "permissions": perms
                }
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_auth_pin_login(self, payload):
        """Connexion rapide tactile par Code PIN (Idéal pour tablettes & écrans tactiles)"""
        try:
            pin = (payload.get('pin') or '').strip()
            username = (payload.get('username') or '').strip().lower()

            if not pin:
                return self.send_json({"success": False, "error": "Code PIN requis"}, 400)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            if username:
                cursor.execute("SELECT id, username, password_hash, salt, nom_complet, role, pin_code, statut, permissions FROM users WHERE LOWER(username) = ? AND statut = 'actif'", (username,))
            else:
                cursor.execute("SELECT id, username, password_hash, salt, nom_complet, role, pin_code, statut, permissions FROM users WHERE pin_code = ? AND statut = 'actif'", (pin,))

            row = cursor.fetchone()
            if not row:
                conn.close()
                return self.send_json({"success": False, "error": "Code PIN incorrect ou compte introuvable"}, 401)

            user_id, u_name, pwd_hash, salt, nom_complet, role, pin_code, statut, perms_str = row
            if pin != pin_code:
                conn.close()
                return self.send_json({"success": False, "error": "Code PIN invalide"}, 401)

            token = secrets.token_hex(32)
            now_iso = datetime.now().isoformat()
            expires = (datetime.now() + timedelta(hours=24)).isoformat()

            try:
                perms = json.loads(perms_str) if perms_str else []
            except Exception:
                perms = []

            cursor.execute("""
            INSERT INTO sessions (token, user_id, username, role, permissions, created_at, expires_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (token, user_id, u_name, role, json.dumps(perms), now_iso, expires, now_iso))

            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso, user_id))
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'CONNEXION_PIN_TABLETTE', ?, ?)
            """, (now_iso, f"USER-{user_id}", f"Connexion rapide PIN Tablette : {nom_complet} ({role})"))

            conn.commit()
            conn.close()

            return self.send_json({
                "success": True,
                "token": token,
                "user": {
                    "id": user_id,
                    "username": u_name,
                    "nom_complet": nom_complet,
                    "role": role,
                    "permissions": perms
                }
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_auth_logout(self):
        """Déconnexion et invalidation du token de session"""
        token = self.get_auth_token()
        if token:
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            except Exception:
                pass
        return self.send_json({"success": True, "message": "Session fermée avec succès"})

    # --- HANDLERS GESTION DES COMPTES ET PERMISSIONS ---

    def handle_get_users(self, query):
        """Liste tous les comptes utilisateurs avec leurs rôles et permissions"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, username, nom_complet, role, email, telephone, pin_code, statut, permissions, last_login, created_at
            FROM users
            ORDER BY id ASC
            """)
            rows = cursor.fetchall()
            conn.close()

            users = []
            for r in rows:
                try:
                    perms = json.loads(r[8]) if r[8] else []
                except Exception:
                    perms = []
                users.append({
                    "id": r[0],
                    "username": r[1],
                    "nom_complet": r[2],
                    "role": r[3],
                    "email": r[4] or "",
                    "telephone": r[5] or "",
                    "has_pin": bool(r[6]),
                    "pin_code": r[6] or "",
                    "statut": r[7],
                    "permissions": perms,
                    "last_login": r[9],
                    "created_at": r[10]
                })

            return self.send_json({"success": True, "users": users})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_save_user(self, payload):
        """Création ou mise à jour d'un compte utilisateur"""
        try:
            user_id = payload.get('id')
            username = (payload.get('username') or '').strip().lower()
            nom_complet = (payload.get('nom_complet') or '').strip()
            role = payload.get('role') or 'technicien'
            email = (payload.get('email') or '').strip()
            telephone = (payload.get('telephone') or '').strip()
            pin_code = (payload.get('pin_code') or '').strip()
            statut = payload.get('statut') or 'actif'
            permissions = payload.get('permissions') or []
            password = payload.get('password') or ''
            now_iso = datetime.now().isoformat()

            if not username or not nom_complet:
                return self.send_json({"success": False, "error": "Identifiant et Nom complet obligatoires"}, 400)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Vérifier unicité du nom d'utilisateur
            if user_id:
                cursor.execute("SELECT id FROM users WHERE LOWER(username) = ? AND id != ?", (username, user_id))
            else:
                cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return self.send_json({"success": False, "error": f"L'identifiant '{username}' est déjà utilisé."}, 400)

            perms_json = json.dumps(permissions)

            if user_id:
                # Mise à jour
                if password:
                    pwd_hash, salt = hash_password(password)
                    cursor.execute("""
                    UPDATE users SET username=?, password_hash=?, salt=?, nom_complet=?, role=?, email=?, telephone=?, pin_code=?, statut=?, permissions=?, updated_at=?
                    WHERE id=?
                    """, (username, pwd_hash, salt, nom_complet, role, email, telephone, pin_code, statut, perms_json, now_iso, user_id))
                else:
                    cursor.execute("""
                    UPDATE users SET username=?, nom_complet=?, role=?, email=?, telephone=?, pin_code=?, statut=?, permissions=?, updated_at=?
                    WHERE id=?
                    """, (username, nom_complet, role, email, telephone, pin_code, statut, perms_json, now_iso, user_id))

                action_msg = f"Modification du compte utilisateur {username} ({role})"
            else:
                # Création nouveau compte
                default_pwd = password if password else (pin_code if pin_code else "123456")
                pwd_hash, salt = hash_password(default_pwd)
                cursor.execute("""
                INSERT INTO users (username, password_hash, salt, nom_complet, role, email, telephone, pin_code, statut, permissions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, pwd_hash, salt, nom_complet, role, email, telephone, pin_code, statut, perms_json, now_iso, now_iso))
                user_id = cursor.lastrowid
                action_msg = f"Création du compte utilisateur {username} ({role})"

            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'GESTION_COMPTES', ?, ?)
            """, (now_iso, f"USER-{user_id}", action_msg))

            conn.commit()
            conn.close()

            return self.send_json({"success": True, "user_id": user_id, "message": "Compte utilisateur enregistré avec succès."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_delete_user(self, payload):
        """Suppression sécurisée d'un compte (protection contre la suppression du dernier admin)"""
        try:
            target_id = payload.get('id')
            if not target_id:
                return self.send_json({"success": False, "error": "ID utilisateur manquant"}, 400)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            cursor.execute("SELECT username, role FROM users WHERE id = ?", (target_id,))
            target = cursor.fetchone()
            if not target:
                conn.close()
                return self.send_json({"success": False, "error": "Compte utilisateur introuvable"}, 404)

            u_name, u_role = target

            # Protection du dernier administrateur actif
            if u_role == 'admin':
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND statut = 'actif' AND id != ?", (target_id,))
                if cursor.fetchone()[0] == 0:
                    conn.close()
                    return self.send_json({"success": False, "error": "Impossible de supprimer le dernier compte Administrateur actif de la plateforme."}, 400)

            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (target_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (target_id,))

            now_iso = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'SUPPRESSION_COMPTE', ?, ?)
            """, (now_iso, f"USER-{target_id}", f"Suppression définitive du compte utilisateur {u_name} ({u_role})"))

            conn.commit()
            conn.close()

            return self.send_json({"success": True, "message": f"Compte {u_name} supprimé avec succès."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_change_password(self, payload):
        """Modification de mot de passe et/ou code PIN"""
        try:
            user_id = payload.get('id')
            new_password = payload.get('new_password')
            new_pin = payload.get('new_pin')

            if not user_id:
                token = self.get_auth_token()
                session_user = get_session_user(token)
                if not session_user:
                    return self.send_json({"success": False, "error": "Session invalide ou expirée"}, 401)
                user_id = session_user['id']

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            now_iso = datetime.now().isoformat()
            if new_password:
                pwd_hash, salt = hash_password(new_password)
                cursor.execute("UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE id = ?", (pwd_hash, salt, now_iso, user_id))
            if new_pin is not None:
                cursor.execute("UPDATE users SET pin_code = ?, updated_at = ? WHERE id = ?", (str(new_pin).strip(), now_iso, user_id))

            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'MODIFICATION_SECURITE', ?, ?)
            """, (now_iso, f"USER-{user_id}", "Mise à jour des codes d'accès (Mot de passe / PIN)"))

            conn.commit()
            conn.close()

            return self.send_json({"success": True, "message": "Identifiants de sécurité mis à jour avec succès."})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    # --- HANDLERS CONSERVATION & MAINTENANCE BASE SQLITE ---

    def handle_sqlite_status(self):
        """Diagnostic complet et en temps réel de la base SQLite et de son intégrité"""
        try:
            size_bytes = os.path.getsize(DB_FILE) if os.path.exists(DB_FILE) else 0
            size_kb = round(size_bytes / 1024, 1)
            size_mb = round(size_bytes / (1024 * 1024), 2)

            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            cursor.execute("PRAGMA journal_mode;")
            journal_mode = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]

            cursor.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]

            cursor.execute("PRAGMA integrity_check;")
            integrity_rows = cursor.fetchall()
            integrity = [r[0] for r in integrity_rows]

            tables_to_check = ['rapports', 'clients', 'equipements', 'garanties_revisions', 'users', 'app_settings', 'audit_log']
            table_counts = {}
            for tbl in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
                    table_counts[tbl] = cursor.fetchone()[0]
                except Exception:
                    table_counts[tbl] = 0

            conn.close()

            backup_files = glob.glob(os.path.join(BACKUPS_DIR, "*.db"))
            backup_count = len(backup_files)
            latest_backup = None
            if backup_files:
                latest_backup_file = max(backup_files, key=os.path.getmtime)
                latest_backup = {
                    "filename": os.path.basename(latest_backup_file),
                    "size_kb": round(os.path.getsize(latest_backup_file) / 1024, 1),
                    "date": datetime.fromtimestamp(os.path.getmtime(latest_backup_file)).strftime('%Y-%m-%d %H:%M:%S')
                }

            return self.send_json({
                "success": True,
                "db_file": DB_FILE,
                "size_bytes": size_bytes,
                "size_kb": size_kb,
                "size_mb": size_mb,
                "journal_mode": journal_mode,
                "page_size": page_size,
                "page_count": page_count,
                "integrity": integrity,
                "is_healthy": (integrity == ['ok']),
                "tables": table_counts,
                "backups_count": backup_count,
                "latest_backup": latest_backup
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_sqlite_vacuum(self):
        """Optimise, compacte et reconstruit les index de la base SQLite"""
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.execute("VACUUM;")
            conn.close()

            new_size_kb = round(os.path.getsize(DB_FILE) / 1024, 1)

            now_iso = datetime.now().isoformat()
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'OPTIMISATION_SQLITE', 'DATABASE', ?)
            """, (now_iso, f"VACUUM et Checkpoint WAL exécutés. Taille compactée : {new_size_kb} Ko"))
            conn.commit()
            conn.close()

            return self.send_json({
                "success": True,
                "message": f"Base de données SQLite optimisée et compactée avec succès. Nouvelle taille : {new_size_kb} Ko",
                "size_kb": new_size_kb
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_sqlite_restore_db(self, payload):
        """Restauration sécurisée d'une sauvegarde SQLite avec pré-sauvegarde automatique"""
        try:
            filename = payload.get('filename')
            if not filename:
                return self.send_json({"success": False, "error": "Nom du fichier de sauvegarde requis"}, 400)

            src_file = os.path.join(BACKUPS_DIR, os.path.basename(filename))
            if not os.path.exists(src_file):
                return self.send_json({"success": False, "error": "Fichier de sauvegarde introuvable sur le disque"}, 404)

            # 1. Checkpoint WAL
            try:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.close()
            except Exception:
                pass

            # 2. Pré-sauvegarde automatique de sécurité
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            pre_restore_backup = os.path.join(BACKUPS_DIR, f"auto_prerestore_{timestamp}.db")
            shutil.copy2(DB_FILE, pre_restore_backup)

            # 3. Remplacement sécurisé
            shutil.copy2(src_file, DB_FILE)

            # 4. Nettoyage des journaux WAL résiduels
            for ext in ['-wal', '-shm']:
                wal_f = DB_FILE + ext
                if os.path.exists(wal_f):
                    try:
                        os.remove(wal_f)
                    except Exception:
                        pass

            # 5. Vérification d'intégrité immédiate
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            check = cursor.fetchone()[0]

            now_iso = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO audit_log (timestamp, action, document_id, details)
            VALUES (?, 'RESTAURATION_SQLITE', 'DATABASE', ?)
            """, (now_iso, f"Restauration depuis {os.path.basename(src_file)} (Sauvegarde avant restauration : {os.path.basename(pre_restore_backup)})"))
            conn.commit()
            conn.close()

            return self.send_json({
                "success": True,
                "message": f"Base SQLite restaurée avec succès depuis '{os.path.basename(src_file)}' (Vérification : {check}).",
                "pre_restore_backup": os.path.basename(pre_restore_backup)
            })
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_sqlite_upload_db(self, payload):
        """Import direct d'un fichier .db depuis le PC ou une clé USB"""
        try:
            b64_data = payload.get('db_base64')
            filename = payload.get('filename') or 'import.db'
            if not b64_data:
                return self.send_json({"success": False, "error": "Fichier base de données manquant"}, 400)

            if ',' in b64_data:
                b64_data = b64_data.split(',', 1)[1]
            raw_bytes = base64.b64decode(b64_data)

            # Vérification de l'en-tête SQLite
            if not raw_bytes.startswith(b'SQLite format 3\x00'):
                return self.send_json({"success": False, "error": "Ce fichier n'est pas une base de données SQLite valide."}, 400)

            if not os.path.exists(BACKUPS_DIR):
                os.makedirs(BACKUPS_DIR, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_backup = os.path.join(BACKUPS_DIR, f"upload_{timestamp}_{os.path.basename(filename)}")
            with open(dest_backup, 'wb') as f:
                f.write(raw_bytes)

            return self.handle_sqlite_restore_db({"filename": os.path.basename(dest_backup)})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

    def handle_get_audit_log(self, query):
        """Historique d'audit des actions administratives et de sécurité"""
        try:
            limit = int(query.get('limit', [100])[0])
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, timestamp, action, document_id, details
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()

            logs = [{
                "id": r[0],
                "timestamp": r[1],
                "action": r[2],
                "document_id": r[3],
                "details": r[4]
            } for r in rows]

            return self.send_json({"success": True, "count": len(logs), "logs": logs})
        except Exception as e:
            return self.send_json({"success": False, "error": str(e)}, 500)

def run_server():
    init_db()
    auto_backup_on_startup()
    local_ip = get_local_ip()
    print("=" * 72)
    print("   ELECTRON MEDICAL ALGERIE -- DISTRIBUTEUR OFFICIEL FUJIFILM")
    print("   SERVEUR PLATEFORME TECHNICO-COMMERCIAL & BASE SQLITE")
    print("=" * 72)
    print(f"  [OK] Base SQLite Active : {DB_FILE}")
    print(f"  [OK] Port Reseau Ouvert : {PORT}")
    print("  " + "-" * 68)
    print("  💻 1. ACCES DEPUIS CE PC :")
    print(f"     👉 Ouvrez dans Chrome : http://localhost:{PORT}")
    print("  " + "-" * 68)
    print("  📱 2. ACCES DEPUIS TABLETTE, SMARTPHONE OU AUTRE PC DU MEME WI-FI :")
    print("     👉 Connectez l'appareil au meme reseau Wi-Fi")
    print("     👉 Ouvrez Google Chrome ou Safari et tapez l'adresse :")
    print(f"     👉👉👉  http://{local_ip}:{PORT}  👈👈👈")
    print("=" * 72)
    print("  (Laissez cette fenetre ouverte tant que vous utilisez l'application)")
    print("=" * 72 + "\n")

    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    try:
        with ReusableTCPServer(("", PORT), TechnicoCommercialHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArret du serveur Technico-Commercial.")

if __name__ == "__main__":
    run_server()
