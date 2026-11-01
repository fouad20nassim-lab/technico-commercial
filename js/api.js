// Client API et Synchronisation Base de Données SQLite — Electron Medical Algérie
const API_BASE = (typeof window !== 'undefined' && window.location && window.location.origin.startsWith('http')) ? '' : 'http://localhost:8085';

const DB_STORAGE_KEY = 'electron_medical_technico_commercial_cache_v2';
const REVISIONS_STORAGE_KEY = 'electron_medical_revisions_cache_v2';

const API = {
  isOnline: false,
  _checkPromise: null,

  async checkConnection() {
    try {
      const res = await fetch(`${API_BASE}/api/status`, { method: 'GET', cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        this.isOnline = true;
        this.updateConnectionIndicator(true, data);
        return data;
      }
    } catch (e) {
      this.isOnline = false;
      this.updateConnectionIndicator(false);
    }
    return null;
  },

  async ensureConnection() {
    if (this.isOnline) return true;
    if (!this._checkPromise) {
      this._checkPromise = this.checkConnection().finally(() => {
        this._checkPromise = null;
      });
    }
    await this._checkPromise;
    return this.isOnline;
  },

  updateConnectionIndicator(online, serverInfo = null) {
    const badge = document.getElementById('connectionBadge');
    if (!badge) return;

    // Déterminer si l'utilisateur connecté est Administrateur
    let isAdmin = false;
    try {
      if (typeof Auth !== 'undefined' && Auth.getUser) {
        const u = Auth.getUser();
        isAdmin = u && (u.role === 'admin' || (u.permissions && u.permissions.includes('all')));
      }
    } catch (e) {}

    const isLocalHost = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || !window.location.hostname);

    // Masquer totalement l'indicateur pour les autres appareils et les comptes non-administrateurs
    if (!isAdmin || !isLocalHost) {
      badge.style.display = 'none';
      return;
    }

    if (online) {
      badge.className = 'status-pill online';
      badge.style.display = 'inline-flex';
      badge.innerHTML = `<span class="dot"></span> <b>Base SQLite Connectée</b>`;
      badge.title = `Base de données SQLite active sur ${serverInfo?.db_file || 'technico_commercial.db'} (${serverInfo?.local_ip || '127.0.0.1'}:8085)`;
    } else {
      badge.className = 'status-pill offline';
      badge.style.display = 'inline-flex';
      badge.innerHTML = `<span class="dot"></span> <b>Mode Local</b>`;
      badge.title = 'Serveur non détecté. Les données sont sauvegardées en cache local.';
    }
  },

  async getStats() {
    await this.ensureConnection();
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/stats`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('API Stats offline, fallback local', e);
      }
    }
    // Fallback local
    const local = this.getLocalCache();
    const byType = {};
    const byWilaya = {};
    local.forEach(r => {
      byType[r.type] = (byType[r.type] || 0) + 1;
      if (r.wilaya) byWilaya[r.wilaya] = (byWilaya[r.wilaya] || 0) + 1;
    });
    return {
      success: true,
      total_rapports: local.length,
      total_clients: new Set(local.map(r => r.client_nom)).size,
      by_type: byType,
      by_wilaya: byWilaya,
      recent: local.slice(0, 5),
      revisions_stats: { total_actives: 0, alertes_10j: 0 }
    };
  },

  async getRapports(filters = {}) {
    await this.ensureConnection();
    if (this.isOnline) {
      try {
        const params = new URLSearchParams();
        if (filters.type) params.set('type', filters.type);
        if (filters.q) params.set('q', filters.q);
        if (filters.wilaya) params.set('wilaya', filters.wilaya);
        if (filters.status) params.set('status', filters.status);
        if (filters.limit) params.set('limit', filters.limit);

        const res = await fetch(`${API_BASE}/api/rapports?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          if (data.rapports && !filters.type && !filters.q && !filters.wilaya) {
            localStorage.setItem(DB_STORAGE_KEY, JSON.stringify(data.rapports));
          }
          return data.rapports || [];
        }
      } catch (e) {
        console.warn('API getRapports offline, fallback local', e);
      }
    }
    let list = this.getLocalCache();
    if (filters.type) list = list.filter(r => r.type === filters.type);
    if (filters.wilaya) list = list.filter(r => (r.wilaya || '').toLowerCase().includes(filters.wilaya.toLowerCase()));
    if (filters.q) {
      const q = filters.q.toLowerCase();
      list = list.filter(r => [r.client_nom, r.ref_number, r.technicien, r.wilaya].join(' ').toLowerCase().includes(q));
    }
    return list;
  },

  async getRapportById(id) {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/rapports/${encodeURIComponent(id)}`);
        if (res.ok) {
          const data = await res.json();
          return data.rapport || null;
        }
      } catch (e) {
        console.warn('API getRapportById offline', e);
      }
    }
    const local = this.getLocalCache();
    const found = local.find(r => r.id === id);
    if (found && found.data) return found;
    return found ? { ...found, data: found } : null;
  },

  async saveRapport(doc) {
    const payload = {
      ...doc,
      updated_at: new Date().toISOString()
    };
    if (!payload.created_at) payload.created_at = new Date().toISOString();

    const local = this.getLocalCache();
    const idx = local.findIndex(r => r.id === payload.id);
    if (idx >= 0) local[idx] = payload;
    else local.unshift(payload);
    localStorage.setItem(DB_STORAGE_KEY, JSON.stringify(local));

    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/rapports`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const resData = await res.json();
          this.toast('Rapport synchronisé avec succès dans la base SQLite !', 'success');
          return resData;
        }
      } catch (e) {
        console.warn('Erreur envoi serveur, sauvegardé localement', e);
      }
    }
    this.toast('Rapport enregistré en local (Serveur hors ligne)', 'info');
    return { success: true, id: payload.id };
  },

  async deleteRapport(id) {
    let local = this.getLocalCache();
    local = local.filter(r => r.id !== id);
    localStorage.setItem(DB_STORAGE_KEY, JSON.stringify(local));

    if (this.isOnline) {
      try {
        await fetch(`${API_BASE}/api/rapports/${encodeURIComponent(id)}`, { method: 'DELETE' });
      } catch (e) {
        console.warn('Erreur delete serveur', e);
      }
    }
    this.toast('Rapport supprimé', 'info');
    return { success: true };
  },

  // --- NOUVEAU : GESTION GARANTIES 2 ANS & RÉVISIONS 6 MOIS (RAPPEL J-10) ---

  async getRevisions(filters = {}) {
    await this.ensureConnection();
    if (this.isOnline) {
      try {
        const params = new URLSearchParams();
        if (filters.statut) params.set('statut', filters.statut);
        if (filters.q) params.set('q', filters.q);
        if (filters.wilaya) params.set('wilaya', filters.wilaya);

        const res = await fetch(`${API_BASE}/api/revisions?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem(REVISIONS_STORAGE_KEY, JSON.stringify(data.revisions || []));
          return data.revisions || [];
        }
      } catch (e) {
        console.warn('API getRevisions offline, fallback local', e);
      }
    }
    try {
      return JSON.parse(localStorage.getItem(REVISIONS_STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  },

  async getAlertes10Jours() {
    await this.ensureConnection();
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/revisions/alertes-10j`);
        if (res.ok) {
          const data = await res.json();
          return data.alertes || [];
        }
      } catch (e) {
        console.warn('API getAlertes10Jours offline', e);
      }
    }
    const all = await this.getRevisions();
    return all.filter(r => r.statut === 'RAPPEL_10J' || r.statut === 'EN_RETARD');
  },

  async createRevisionSchedule(data) {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/revisions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (res.ok) {
          const json = await res.json();
          this.toast(json.message || 'Échéancier créé avec succès !', 'success');
          return json;
        }
      } catch (e) {
        console.warn('Erreur createRevisionSchedule', e);
      }
    }
    this.toast('Création enregistrée (mode local)', 'info');
    return { success: true };
  },

  async validerRevision(id, payload = {}) {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/revisions/${encodeURIComponent(id)}/valider`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const json = await res.json();
          this.toast(json.message || 'Révision marquée comme effectuée !', 'success');
          return json;
        }
      } catch (e) {
        console.warn('Erreur validerRevision', e);
      }
    }
    this.toast('Révision validée (mode local)', 'success');
    return { success: true };
  },

  downloadIcal(id = null) {
    const url = id ? `${API_BASE}/api/revisions/export-ical?id=${encodeURIComponent(id)}` : `${API_BASE}/api/revisions/export-ical`;
    window.location.href = url;
  },

  getLocalCache() {
    try {
      return JSON.parse(localStorage.getItem(DB_STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  },

  exportExcel() {
    window.location.href = `${API_BASE}/api/export/excel`;
  },

  async exportBackup() {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/backup`);
        if (res.ok) {
          const data = await res.json();
          this.downloadJson(data.backup || data, `Sauvegarde_Technico_Commercial_${new Date().toISOString().slice(0, 10)}.json`);
          return;
        }
      } catch (e) {
        console.warn('Export backup error, using local', e);
      }
    }
    const local = this.getLocalCache();
    this.downloadJson({ version: "2.1", export_date: new Date().toISOString(), rapports: local }, `Sauvegarde_Technico_Commercial_Locale_${new Date().toISOString().slice(0, 10)}.json`);
  },

  downloadSqliteBackup() {
    window.location.href = `${API_BASE}/api/backup/sqlite`;
  },

  async createBackupSnapshot(destDir = null) {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/backup/create-snapshot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ destination_dir: destDir })
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.error('Error creating snapshot', e);
      }
    }
    return { success: false, error: 'Serveur hors-ligne' };
  },

  async getBackupList() {
    if (this.isOnline) {
      try {
        const res = await fetch(`${API_BASE}/api/backup/list`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.error('Error fetching backup list', e);
      }
    }
    return { success: false, backups: [] };
  },

  async getClients360(filters = {}) {
    await this.ensureConnection();
    if (this.isOnline) {
      try {
        const params = new URLSearchParams();
        if (filters.client) params.set('client', filters.client);
        if (filters.wilaya) params.set('wilaya', filters.wilaya);
        const res = await fetch(`${API_BASE}/api/clients/360?${params.toString()}`);
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('API getClients360 offline, fallback', e);
      }
    }
    return { success: false, clients: [] };
  },

  formatAlgerianPhone(phone) {
    if (!phone) return '';
    let clean = phone.replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) {
      clean = '213' + clean.slice(1);
    } else if (!clean.startsWith('213') && clean.length === 9) {
      clean = '213' + clean;
    }
    return clean;
  },

  getRevisionWhatsAppMessage(rev) {
    const echDate = rev.date_echeance || '';
    const delai = rev.jours_restants !== undefined 
      ? (rev.jours_restants < 0 ? `⚠️ EN RETARD de ${Math.abs(rev.jours_restants)} jour(s)` : (rev.jours_restants <= 10 ? `⏳ Dans ${rev.jours_restants} jour(s)` : `Prévue le ${echDate}`))
      : `Prévue le ${echDate}`;
      
    return `🏥 *ELECTRON MEDICAL ALGÉRIE*
Distributeur Officiel FUJIFILM Medical Systems
Service Après-Vente & Maintenance Biomédicale
---------------------------------------
Bonjour,

Nous vous informons de la programmation de la révision périodique semestrielle sous *Garantie 2 Ans* pour votre équipement :

• *Établissement :* ${rev.client_nom || 'Votre Établissement'}
• *Wilaya :* ${rev.wilaya || ''}
• *Matériel :* ${rev.materiel || 'Endoscope Fujifilm'}
• *N° de Série :* ${rev.numero_serie || 'N/A'}
• *Type de Révision :* ${rev.titre_revision || 'Révision Semestrielle'}
• *Date Échéance :* ${echDate} (${delai})
• *Technicien Référent :* ${rev.technicien || 'Équipe Technique'}

Merci de bien vouloir nous confirmer vos disponibilités pour l'intervention de maintenance préventive de notre équipe technique.

📞 *Contact SAV :* 0550 12 34 56 / 023 45 67 89
📧 *Email :* sav@electronmedical-dz.com
🌐 *Site :* www.electronmedical-dz.com`;
  },

  openWhatsApp(phone, messageText) {
    const cleanPhone = this.formatAlgerianPhone(phone);
    const encoded = encodeURIComponent(messageText);
    const url = cleanPhone ? `https://wa.me/${cleanPhone}?text=${encoded}` : `https://wa.me/?text=${encoded}`;
    window.open(url, '_blank');
  },

  copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        this.toast('Message copié dans le presse-papier !', 'success');
      }).catch(() => {
        this.fallbackCopy(text);
      });
    } else {
      this.fallbackCopy(text);
    }
  },

  fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    this.toast('Message copié dans le presse-papier !', 'success');
  },

  downloadJson(obj, filename) {
    const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  toast(msg, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const colors = {
      success: '#078d78',
      info: '#1675d1',
      warning: '#d97706',
      error: '#dc2626'
    };
    toast.style.cssText = `background:${colors[type] || '#06353d'};color:#fff;padding:12px 20px;border-radius:10px;font-size:13px;font-weight:700;box-shadow:0 8px 24px rgba(0,0,0,0.25);animation:slideIn 0.3s ease;pointer-events:auto;max-width:380px;display:flex;align-items:center;gap:10px;`;
    const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
    toast.innerHTML = `<span style="font-size:16px;">${icon}</span> <span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  API.checkConnection();
});
