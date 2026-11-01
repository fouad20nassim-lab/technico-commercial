/**
 * ELECTRON MEDICAL ALGÉRIE — Distributeur Officiel Fujifilm Medical Systems
 * MODULE DE SÉCURITÉ, AUTHENTIFICATION ET GESTION DES SESSIONS
 * Version: 2.0 (Optimisé PC et Tablette Tactile)
 */

(function(window) {
  'use strict';

  var TOKEN_KEY = 'technico_auth_token_v1';
  var USER_KEY = 'technico_auth_user_v1';
  var INACTIVITY_LIMIT_MS = 25 * 60 * 1000; // 25 minutes d'inactivité avant verrouillage automatique
  var lastActivityTimestamp = Date.now();
  var inactivityTimer = null;

  var API_BASE = (typeof window !== 'undefined' && window.location && window.location.origin && window.location.origin.startsWith('http')) ? '' : 'http://localhost:8085';

  var USERS_STORAGE_KEY = 'technico_users_v2';

  // Comptes par défaut de secours
  var DEFAULT_USERS = [
    { id: 1, username: 'admin', nom_complet: 'Administrateur Principal', role: 'admin', pin_code: '1234', password: 'admin', email: 'admin@electron-medical.dz', telephone: '+213 (0) 23 85 00 01', statut: 'actif', permissions: ['all', 'settings', 'sqlite', 'users', 'reports_delete', 'export', 'validate'] },
    { id: 2, username: 'mustapha.b', nom_complet: 'Mustapha B. (Technicien SAV)', role: 'technicien', pin_code: '1111', password: 'tech123', email: 'm.b@electron-medical.dz', telephone: '+213 (0) 550 11 22 33', statut: 'actif', permissions: ['reports_write', 'inspection', 'validate_revisions'] },
    { id: 3, username: 'karim.t', nom_complet: 'Karim T. (Commercial / ADV)', role: 'commercial', pin_code: '2222', password: 'comm123', email: 'k.t@electron-medical.dz', telephone: '+213 (0) 550 44 55 66', statut: 'actif', permissions: ['clients_read', 'clients_write', 'revisions_read', 'export'] },
    { id: 4, username: 'dr.benali', nom_complet: 'Dr. Benali (Responsable Qualité)', role: 'qualite', pin_code: '3333', password: 'qualite123', email: 'benali@electron-medical.dz', telephone: '+213 (0) 550 77 88 99', statut: 'actif', permissions: ['reports_read', 'quality_approve', 'audit_read'] }
  ];

  function getStoredUsersList() {
    try {
      var raw = localStorage.getItem(USERS_STORAGE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch(e) {}
    try {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(DEFAULT_USERS));
    } catch(e) {}
    return DEFAULT_USERS.slice();
  }

  function saveStoredUsersList(list) {
    try {
      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(list));
    } catch(e) {}
  }

  var OFFLINE_USERS = getStoredUsersList();

  var Auth = {
    getToken: function() {
      try {
        return localStorage.getItem('technico_auth_token') || sessionStorage.getItem('technico_auth_token') ||
               localStorage.getItem('technico_auth_token_v1') || sessionStorage.getItem('technico_auth_token_v1') || null;
      } catch (e) {
        return null;
      }
    },

    setToken: function(token, remember) {
      try {
        localStorage.setItem('technico_auth_token', token);
        localStorage.setItem('technico_auth_token_v1', token);
        sessionStorage.setItem('technico_auth_token', token);
        sessionStorage.setItem('technico_auth_token_v1', token);
        localStorage.setItem('technico_session_active', 'true');
        sessionStorage.setItem('technico_session_active', 'true');
      } catch (e) {}
    },

    getUser: function() {
      try {
        var raw = localStorage.getItem('technico_auth_user') || sessionStorage.getItem('technico_auth_user') ||
                  localStorage.getItem('technico_auth_user_v1') || sessionStorage.getItem('technico_auth_user_v1');
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },

    setUser: function(user) {
      try {
        var str = JSON.stringify(user);
        localStorage.setItem('technico_auth_user', str);
        localStorage.setItem('technico_auth_user_v1', str);
        sessionStorage.setItem('technico_auth_user', str);
        sessionStorage.setItem('technico_auth_user_v1', str);
        localStorage.setItem('technico_session_active', 'true');
        sessionStorage.setItem('technico_session_active', 'true');
      } catch (e) {}
    },

    clearAuth: function() {
      try {
        localStorage.removeItem('technico_auth_token');
        localStorage.removeItem('technico_auth_token_v1');
        localStorage.removeItem('technico_auth_user');
        localStorage.removeItem('technico_auth_user_v1');
        localStorage.removeItem('technico_session_active');
        sessionStorage.removeItem('technico_auth_token');
        sessionStorage.removeItem('technico_auth_token_v1');
        sessionStorage.removeItem('technico_auth_user');
        sessionStorage.removeItem('technico_auth_user_v1');
        sessionStorage.removeItem('technico_session_active');
      } catch (e) {}
    },

    isLoggedIn: function() {
      return !!this.getToken() && !!this.getUser();
    },

    isAdmin: function() {
      var u = this.getUser();
      return u && (u.role === 'admin' || (u.permissions && u.permissions.indexOf('all') !== -1));
    },

    hasPermission: function(perm) {
      var u = this.getUser();
      if (!u) return false;
      if (u.role === 'admin' || (u.permissions && u.permissions.indexOf('all') !== -1)) return true;
      return u.permissions && u.permissions.indexOf(perm) !== -1;
    },

    // --- REQUETES SERVEUR ---

    login: function(username, password, callback) {
      var self = this;
      var u = (username || '').trim().toLowerCase();
      var p = (password || '').trim();

      // Secours immédiat sans attente pour Admin (mot de passe 'admin' ou PIN '1234')
      if (u === 'admin' && (p === 'admin' || p === '1234')) {
        var currentList = getStoredUsersList();
        var adminUser = currentList.find(function(x) { return x.role === 'admin'; }) || DEFAULT_USERS[0];
        var token = 'token_admin_' + Date.now();
        self.setToken(token, true);
        self.setUser(adminUser);
        self.resetActivityTimer();
        if (callback) callback(null, adminUser);
        return;
      }

      fetch(API_BASE + '/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, password: password })
      })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.success && data.token) {
          self.setToken(data.token, true);
          self.setUser(data.user);
          self.resetActivityTimer();
          if (callback) callback(null, data.user);
        } else {
          // Fallback local si échec serveur
          var currentList = getStoredUsersList();
          var found = currentList.find(function(x) {
            return (x.username && x.username.toLowerCase() === u) && (x.password === p || x.pin_code === p || x.pin === p);
          });
          if (found) {
            var fakeToken = 'offline_token_' + found.id + '_' + Date.now();
            self.setToken(fakeToken, true);
            self.setUser(found);
            self.resetActivityTimer();
            if (callback) callback(null, found);
          } else {
            if (callback) callback(data.error || 'Identifiants invalides');
          }
        }
      })
      .catch(function(err) {
        // Fallback de sécurité Offline-First si le serveur local n'est pas encore démarré
        var currentList = getStoredUsersList();
        var found = currentList.find(function(x) {
          return (x.username && x.username.toLowerCase() === u) && (x.password === p || x.pin_code === p || x.pin === p);
        });
        if (found) {
          var fakeToken = 'offline_token_' + found.id + '_' + Date.now();
          self.setToken(fakeToken, true);
          self.setUser(found);
          self.resetActivityTimer();
          if (callback) callback(null, found);
        } else {
          if (callback) callback('Identifiants incorrects (Mode local : admin / 1234 ou admin / admin).');
        }
      });
    },

    loginWithPin: function(pin, username, callback) {
      var self = this;
      var payload = { pin: pin };
      if (username) payload.username = username;

      // Recherche locale préalable
      var currentList = getStoredUsersList();
      var foundLocal = currentList.find(function(x) {
        if (username) {
          return x.username.toLowerCase() === username.toLowerCase() && x.pin_code === pin;
        }
        return x.pin_code === pin;
      });
      if (!foundLocal && pin === '1234') {
        foundLocal = currentList.find(function(x) { return x.role === 'admin'; }) || DEFAULT_USERS[0];
      }

      fetch(API_BASE + '/api/auth/pin-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.success && data.token) {
          self.setToken(data.token, true);
          self.setUser(data.user);
          self.resetActivityTimer();
          if (callback) callback(null, data.user);
        } else {
          if (foundLocal) {
            var fakeToken = 'offline_token_' + foundLocal.id + '_' + Date.now();
            self.setToken(fakeToken, true);
            self.setUser(foundLocal);
            self.resetActivityTimer();
            if (callback) callback(null, foundLocal);
          } else {
            if (callback) callback(data.error || 'Code PIN incorrect (PIN Admin : 1234)');
          }
        }
      })
      .catch(function(err) {
        // Fallback de sécurité Offline-First garanti
        if (foundLocal) {
          var fakeToken = 'offline_token_' + foundLocal.id + '_' + Date.now();
          self.setToken(fakeToken, true);
          self.setUser(foundLocal);
          self.resetActivityTimer();
          if (callback) callback(null, foundLocal);
        } else {
          if (callback) callback('Code PIN incorrect (PIN Admin par défaut = 1234).');
        }
      });
    },

    checkSession: function(callback) {
      var self = this;
      var token = this.getToken();
      if (!token) {
        if (callback) callback(null, null);
        return;
      }

      fetch(API_BASE + '/api/auth/me', {
        headers: { 'Authorization': 'Bearer ' + token }
      })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.success && data.authenticated && data.user) {
          self.setUser(data.user);
          self.resetActivityTimer();
          if (callback) callback(null, data.user);
        } else {
          // Si le token est local/offline, conserver
          var local = self.getUser();
          if (local) {
            if (callback) callback(null, local);
          } else {
            self.clearAuth();
            if (callback) callback(null, null);
          }
        }
      })
      .catch(function(err) {
        var local = self.getUser();
        if (callback) callback(null, local);
      });
    },

    logout: function(callback) {
      var self = this;
      var token = this.getToken();
      fetch(API_BASE + '/api/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + (token || '')
        }
      }).finally(function() {
        self.clearAuth();
        if (callback) callback();
        else window.location.reload();
      });
    },

    changePasswordOrPin: function(newPassword, newPin, callback) {
      var token = this.getToken();
      var u = this.getUser();
      if (!u) {
        if (callback) callback('Non connecté');
        return;
      }

      fetch(API_BASE + '/api/users/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + (token || '')
        },
        body: JSON.stringify({
          id: u.id,
          new_password: newPassword || undefined,
          new_pin: newPin || undefined
        })
      })
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.success) {
          if (callback) callback(null, data);
        } else {
          if (callback) callback(data.error || 'Échec de la modification');
        }
      })
      .catch(function(err) {
        // En mode offline, mettre à jour localement
        if (newPin) u.pin_code = newPin;
        self.setUser(u);
        if (callback) callback(null, { success: true, offline: true });
      });
    },

    // --- GESTION DE L'INACTIVITÉ (SÉCURITÉ SUR TABLETTE & POSTE PARTAGÉ) ---

    resetActivityTimer: function() {
      lastActivityTimestamp = Date.now();
      if (!inactivityTimer) {
        inactivityTimer = setInterval(function() {
          if (Auth.isLoggedIn() && (Date.now() - lastActivityTimestamp > INACTIVITY_LIMIT_MS)) {
            console.warn('[SECURITE] Session verrouillée suite à inactivité prolongée.');
            Auth.logout(function() {
              alert('Pour votre sécurité, votre session a été verrouillée après une période d\'inactivité.');
              window.location.reload();
            });
          }
        }, 30000);
      }
    },

    registerActivityListeners: function() {
      var update = function() { lastActivityTimestamp = Date.now(); };
      window.addEventListener('mousemove', update, { passive: true });
      window.addEventListener('mousedown', update, { passive: true });
      window.addEventListener('touchstart', update, { passive: true });
      window.addEventListener('keydown', update, { passive: true });
      this.resetActivityTimer();
    },

    // --- UTILITAIRES D'AFFICHAGE ET PAVÉ TACTILE PIN POUR TABLETTES ---

    getRoleLabel: function(role) {
      switch (role) {
        case 'admin': return 'Administrateur Principal';
        case 'technicien': return 'Technicien SAV / Ingénieur';
        case 'commercial': return 'Commercial / ADV';
        case 'qualite': return 'Responsable Qualité';
        default: return role || 'Utilisateur';
      }
    },

    getRoleBadgeClass: function(role) {
      switch (role) {
        case 'admin': return 'badge-role-admin';
        case 'technicien': return 'badge-role-tech';
        case 'commercial': return 'badge-role-comm';
        case 'qualite': return 'badge-role-qualite';
        default: return 'badge-role-default';
      }
    },

    getStoredUsers: function() {
      return getStoredUsersList();
    },

    saveStoredUsers: function(list) {
      saveStoredUsersList(list);
      OFFLINE_USERS = list;
    },

    upsertStoredUser: function(user) {
      var list = getStoredUsersList();
      var idx = list.findIndex(function(x) { return (user.id && x.id === user.id) || (x.username && user.username && x.username.toLowerCase() === user.username.toLowerCase()); });
      if (idx >= 0) {
        list[idx] = Object.assign({}, list[idx], user);
      } else {
        if (!user.id) user.id = Date.now();
        list.push(user);
      }
      saveStoredUsersList(list);
      OFFLINE_USERS = list;
      return list;
    },

    deleteStoredUser: function(userId) {
      var list = getStoredUsersList().filter(function(x) { return x.id !== userId; });
      saveStoredUsersList(list);
      OFFLINE_USERS = list;
      return list;
    }
  };

  // Initialisation automatique des écouteurs d'activité
  Auth.registerActivityListeners();

  window.Auth = Auth;
})(window);

