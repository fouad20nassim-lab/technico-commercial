/**
 * ELECTRON MEDICAL ALGÉRIE · DISTRIBUTEUR OFFICIEL FUJIFILM MEDICAL SYSTEMS
 * FEATURE V6 : OPTIMISEUR DE TOURNÉES SAV & ITINÉRAIRES GPS MULTI-ARRÊTS
 * - Coordonnées GPS des 58 Wilayas d'Algérie
 * - Calcul des distances réelles et ordre de passage optimal
 * - Export vers Google Maps & Waze en 1 clic
 * - Feuille de route / Ordre de mission officiel imprimable A4
 * - Envoi direct sur WhatsApp du technicien en mission
 */

// 1. Coordonnées GPS des Wilayas d'Algérie (Centres urbains & CHU)
const WILAYA_GPS = {
  "01": { lat: 27.8767, lng: -0.2939, nom: "Adrar", region: "Sud" },
  "02": { lat: 36.1653, lng: 1.3345, nom: "Chlef", region: "Centre" },
  "03": { lat: 33.8000, lng: 2.8651, nom: "Laghouat", region: "Sud" },
  "04": { lat: 35.8756, lng: 7.1136, nom: "Oum El Bouaghi", region: "Est" },
  "05": { lat: 35.5559, lng: 6.1741, nom: "Batna", region: "Est" },
  "06": { lat: 36.7509, lng: 5.0567, nom: "Béjaïa", region: "Est" },
  "07": { lat: 34.8504, lng: 5.7281, nom: "Biskra", region: "Sud" },
  "08": { lat: 31.6167, lng: -2.2167, nom: "Béchar", region: "Sud" },
  "09": { lat: 36.4700, lng: 2.8300, nom: "Blida", region: "Centre" },
  "10": { lat: 36.3749, lng: 3.9020, nom: "Bouira", region: "Centre" },
  "11": { lat: 22.7850, lng: 5.5228, nom: "Tamanrasset", region: "Sud" },
  "12": { lat: 35.4042, lng: 8.1242, nom: "Tébessa", region: "Est" },
  "13": { lat: 34.8783, lng: -1.3150, nom: "Tlemcen", region: "Ouest" },
  "14": { lat: 35.3710, lng: 1.3170, nom: "Tiaret", region: "Ouest" },
  "15": { lat: 36.7119, lng: 4.0458, nom: "Tizi Ouzou", region: "Centre" },
  "16": { lat: 36.7538, lng: 3.0588, nom: "Alger", region: "Centre" },
  "17": { lat: 34.6728, lng: 3.2630, nom: "Djelfa", region: "Centre" },
  "18": { lat: 36.8206, lng: 5.7667, nom: "Jijel", region: "Est" },
  "19": { lat: 36.1911, lng: 5.4137, nom: "Sétif", region: "Est" },
  "20": { lat: 34.8303, lng: 0.1517, nom: "Saïda", region: "Ouest" },
  "21": { lat: 36.8787, lng: 6.9063, nom: "Skikda", region: "Est" },
  "22": { lat: 35.1899, lng: -0.6308, nom: "Sidi Bel Abbès", region: "Ouest" },
  "23": { lat: 36.9000, lng: 7.7667, nom: "Annaba", region: "Est" },
  "24": { lat: 36.4621, lng: 7.4261, nom: "Guelma", region: "Est" },
  "25": { lat: 36.3650, lng: 6.6147, nom: "Constantine", region: "Est" },
  "26": { lat: 36.2642, lng: 2.7539, nom: "Médéa", region: "Centre" },
  "27": { lat: 35.9312, lng: 0.0892, nom: "Mostaganem", region: "Ouest" },
  "28": { lat: 35.7058, lng: 4.5419, nom: "M'Sila", region: "Centre" },
  "29": { lat: 35.3967, lng: 0.1403, nom: "Mascara", region: "Ouest" },
  "30": { lat: 31.9530, lng: 5.3280, nom: "Ouargla", region: "Sud" },
  "31": { lat: 35.6987, lng: -0.6349, nom: "Oran", region: "Ouest" },
  "32": { lat: 33.6833, lng: 1.0167, nom: "El Bayadh", region: "Sud" },
  "33": { lat: 24.5500, lng: 9.4833, nom: "Illizi", region: "Sud" },
  "34": { lat: 36.0667, lng: 4.7667, nom: "Bordj Bou Arreridj", region: "Est" },
  "35": { lat: 36.7667, lng: 3.4775, nom: "Boumerdès", region: "Centre" },
  "36": { lat: 36.7667, lng: 8.3167, nom: "El Tarf", region: "Est" },
  "37": { lat: 27.6667, lng: -8.1667, nom: "Tindouf", region: "Sud" },
  "38": { lat: 35.6667, lng: 1.6333, nom: "Tissemsilt", region: "Ouest" },
  "39": { lat: 33.3667, lng: 6.8667, nom: "El Oued", region: "Sud" },
  "40": { lat: 35.5000, lng: 7.0833, nom: "Khenchela", region: "Est" },
  "41": { lat: 36.2833, lng: 7.9500, nom: "Souk Ahras", region: "Est" },
  "42": { lat: 36.5928, lng: 2.4475, nom: "Tipaza", region: "Centre" },
  "43": { lat: 36.4500, lng: 6.2667, nom: "Mila", region: "Est" },
  "44": { lat: 36.2639, lng: 1.9678, nom: "Aïn Defla", region: "Centre" },
  "45": { lat: 33.2333, lng: -0.3167, nom: "Naâma", region: "Sud" },
  "46": { lat: 35.3000, lng: -1.1333, nom: "Aïn Témouchent", region: "Ouest" },
  "47": { lat: 32.4909, lng: 3.6735, nom: "Ghardaïa", region: "Sud" },
  "48": { lat: 35.7333, lng: 0.5500, nom: "Relizane", region: "Ouest" },
  "49": { lat: 26.3333, lng: 0.1667, nom: "Timimoun", region: "Sud" },
  "50": { lat: 30.2000, lng: -2.3333, nom: "Béni Abbès", region: "Sud" },
  "51": { lat: 34.4667, lng: 4.8333, nom: "Ouled Djellal", region: "Sud" },
  "52": { lat: 21.3333, lng: 0.9500, nom: "In Salah", region: "Sud" },
  "53": { lat: 19.5667, lng: 5.7667, nom: "In Guezzam", region: "Sud" },
  "54": { lat: 32.9333, lng: 6.0667, nom: "Touggourt", region: "Sud" },
  "55": { lat: 26.5000, lng: 8.4667, nom: "Djanet", region: "Sud" },
  "56": { lat: 33.9167, lng: 6.9167, nom: "El M'Ghair", region: "Sud" },
  "57": { lat: 30.5833, lng: 2.8833, nom: "El Meniaa", region: "Sud" },
  "58": { lat: 30.0000, lng: -2.0000, nom: "Béni Ounif", region: "Sud" }
};

// Siège d'Electron Medical Algérie (Base de départ par défaut)
const ELECTRON_MEDICAL_HQ = {
  nom: "Siège Electron Medical (Alger)",
  lat: 36.7538,
  lng: 3.0588,
  wilaya: "16 - Alger"
};

let currentTournee = {
  region: "",
  technicien: "Mustapha B.",
  dateTournee: new Date().toISOString().slice(0, 10),
  depart: ELECTRON_MEDICAL_HQ,
  selectedStops: [], // Liste des arrêts choisis
  optimizedStops: [],
  totalKm: 0,
  dureeEstimeeH: 0
};

// =========================================================================
// CALCUL DE DISTANCES & OPTIMISATION D'ITINÉRAIRE (ALGORITHME DU PLUS PROCHE)
// =========================================================================
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Rayon de la Terre en km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  // Facteur 1.25 pour tenir compte des sinuosités des routes réelles en Algérie
  return Math.round(R * c * 1.25);
}

function getWilayaCoords(wilayaStr) {
  if (!wilayaStr) return ELECTRON_MEDICAL_HQ;
  const clean = String(wilayaStr).trim();
  // Extraire le numéro (ex: "16 - Alger" -> "16")
  const match = clean.match(/^(\d{1,2})/);
  if (match) {
    const code = match[1].padStart(2, '0');
    if (WILAYA_GPS[code]) return WILAYA_GPS[code];
  }
  // Recherche par nom
  for (const k in WILAYA_GPS) {
    if (clean.toLowerCase().includes(WILAYA_GPS[k].nom.toLowerCase())) {
      return WILAYA_GPS[k];
    }
  }
  return ELECTRON_MEDICAL_HQ;
}

// Algorithme d'optimisation de l'ordre de passage (Nearest Neighbor)
function optimizeStopsOrder(startPoint, stopsList) {
  if (stopsList.length <= 1) return [...stopsList];

  const unvisited = [...stopsList];
  const ordered = [];
  let currentLat = startPoint.lat;
  let currentLng = startPoint.lng;

  while (unvisited.length > 0) {
    let nearestIdx = 0;
    let minDist = Infinity;

    for (let i = 0; i < unvisited.length; i++) {
      const coords = getWilayaCoords(unvisited[i].wilaya);
      const dist = calculateDistanceKm(currentLat, currentLng, coords.lat, coords.lng);
      if (dist < minDist) {
        minDist = dist;
        nearestIdx = i;
      }
    }

    const nextStop = unvisited.splice(nearestIdx, 1)[0];
    const coords = getWilayaCoords(nextStop.wilaya);
    currentLat = coords.lat;
    currentLng = coords.lng;
    ordered.push(nextStop);
  }

  return ordered;
}

// =========================================================================
// INTERFACE UTILISATEUR & MODAL TOURNÉES
// =========================================================================
function openTourneeModal() {
  const modal = document.getElementById('tourneeGpsModal');
  if (!modal) return;
  modal.classList.add('active');

  const dateInp = document.getElementById('tourDateInput');
  if (dateInp && !dateInp.value) {
    dateInp.value = new Date().toISOString().slice(0, 10);
  }

  loadTourneeCandidates();
}

function closeTourneeModal() {
  const modal = document.getElementById('tourneeGpsModal');
  if (modal) modal.classList.remove('active');
}

function loadTourneeCandidates() {
  const filterReg = (document.getElementById('tourRegionSelect')?.value || '').toLowerCase();
  const filterTech = (document.getElementById('tourTechSelect')?.value || '').toLowerCase();
  const container = document.getElementById('tourCandidatesList');
  if (!container) return;

  const revisions = Object.values(window.__revisionsMap || {});
  const candidates = [];

  revisions.forEach(r => {
    // Filtrage par région
    if (filterReg) {
      const reg = typeof getRegionByWilaya === 'function' ? getRegionByWilaya(r.wilaya) : null;
      if (!reg || !reg.nom.toLowerCase().includes(filterReg)) return;
    }
    // Filtrage par technicien
    if (filterTech && !(r.technicien || '').toLowerCase().includes(filterTech)) return;

    // Prioriser les urgents et planifiés
    candidates.push({
      id: r.id,
      client_nom: r.client_nom || 'Établissement',
      wilaya: r.wilaya || 'Alger',
      materiel: r.materiel || 'FUJIFILM EP-8000',
      sn: r.numero_serie || '',
      titre: r.titre_revision || 'Révision Semestrielle',
      date_echeance: r.date_echeance || '',
      jours_restants: r.jours_restants,
      est_en_retard: r.est_en_retard,
      telephone: r.telephone || '',
      statut: r.statut
    });
  });

  if (candidates.length === 0) {
    // Si aucun résultat filtré, proposer les révisions générales ou exemples
    container.innerHTML = `
      <div style="text-align:center; padding:24px; color:var(--text-muted); font-size:13px;">
        Aucune intervention urgente trouvée pour ces filtres.<br>
        <button type="button" class="btn btn-secondary" style="margin-top:10px; font-size:11px;" onclick="document.getElementById('tourRegionSelect').value=''; loadTourneeCandidates();">
          Afficher tous les établissements d'Algérie
        </button>
      </div>
    `;
    updateTourneeStats([]);
    return;
  }

  container.innerHTML = candidates.map((c, idx) => {
    let badgeClass = 'badge-planifie';
    let badgeText = `${c.jours_restants}j restants`;
    if (c.est_en_retard) {
      badgeClass = 'badge-retard';
      badgeText = `⚠️ En retard (${Math.abs(c.jours_restants)}j)`;
    } else if (c.jours_restants !== undefined && c.jours_restants <= 10) {
      badgeClass = 'badge-rappel10j';
      badgeText = `🚨 Urgent J-${c.jours_restants}`;
    }

    return `
      <div class="tour-candidate-card" id="tourCard_${c.id}">
        <label style="display:flex; align-items:flex-start; gap:10px; cursor:pointer; width:100%;">
          <input type="checkbox" class="tour-stop-checkbox" value="${escapeHtmlAttr(c.id)}" checked onchange="onTourStopToggle()" style="margin-top:4px; transform:scale(1.2);">
          <div style="flex:1;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
              <strong style="color:var(--text-main); font-size:13px;">${escapeHtmlAttr(c.client_nom)}</strong>
              <span class="${badgeClass}" style="font-size:10px;">${badgeText}</span>
            </div>
            <div style="font-size:12px; color:var(--text-muted); display:flex; flex-wrap:wrap; gap:8px;">
              <span>📍 <b>${escapeHtmlAttr(c.wilaya)}</b></span>
              <span>🔬 ${escapeHtmlAttr(c.materiel)} ${c.sn ? `(SN: ${escapeHtmlAttr(c.sn)})` : ''}</span>
              ${c.telephone ? `<span>📞 <a href="tel:${escapeHtmlAttr(c.telephone)}" style="color:#00b87c; text-decoration:none;">${escapeHtmlAttr(c.telephone)}</a></span>` : ''}
            </div>
          </div>
        </label>
      </div>
    `;
  }).join('');

  onTourStopToggle();
}

function onTourStopToggle() {
  const checkedBoxes = document.querySelectorAll('.tour-stop-checkbox:checked');
  const revisions = window.__revisionsMap || {};
  const selected = [];

  checkedBoxes.forEach(cb => {
    const rev = revisions[cb.value];
    if (rev) {
      selected.push({
        id: rev.id,
        client_nom: rev.client_nom,
        wilaya: rev.wilaya,
        materiel: rev.materiel,
        sn: rev.numero_serie,
        telephone: rev.telephone,
        titre: rev.titre_revision,
        date_echeance: rev.date_echeance
      });
    }
  });

  // Calcul du parcours optimal
  const optimized = optimizeStopsOrder(ELECTRON_MEDICAL_HQ, selected);
  currentTournee.optimizedStops = optimized;

  updateTourneeStats(optimized);
  renderTourRoadmap(optimized);
}

function updateTourneeStats(stops) {
  let totalKm = 0;
  let curLat = ELECTRON_MEDICAL_HQ.lat;
  let curLng = ELECTRON_MEDICAL_HQ.lng;

  stops.forEach(s => {
    const coords = getWilayaCoords(s.wilaya);
    totalKm += calculateDistanceKm(curLat, curLng, coords.lat, coords.lng);
    curLat = coords.lat;
    curLng = coords.lng;
  });

  // Retour au siège
  if (stops.length > 0) {
    totalKm += calculateDistanceKm(curLat, curLng, ELECTRON_MEDICAL_HQ.lat, ELECTRON_MEDICAL_HQ.lng);
  }

  currentTournee.totalKm = totalKm;
  // Estimation temps de route : vitesse moyenne 75 km/h en Algérie + 45 min par visite
  const drivingHours = (totalKm / 75);
  const interventionHours = (stops.length * 0.75);
  currentTournee.dureeEstimeeH = (drivingHours + interventionHours).toFixed(1);

  const kmEl = document.getElementById('tourTotalKm');
  const timeEl = document.getElementById('tourEstTime');
  const countEl = document.getElementById('tourStopsCount');

  if (kmEl) kmEl.textContent = `${totalKm} km`;
  if (timeEl) timeEl.textContent = `~${currentTournee.dureeEstimeeH}h (Route + SAV)`;
  if (countEl) countEl.textContent = stops.length;
}

function renderTourRoadmap(stops) {
  const container = document.getElementById('tourRoadmapContainer');
  if (!container) return;

  if (stops.length === 0) {
    container.innerHTML = `<div style="text-align:center; padding:20px; color:var(--text-muted); font-size:12px;">Cochez au moins un hôpital pour générer l'ordre de mission.</div>`;
    return;
  }

  let html = `
    <div class="roadmap-timeline">
      <div class="roadmap-step step-depart">
        <div class="step-marker">🏁</div>
        <div class="step-content">
          <div style="font-weight:800; font-size:12px; color:#0f766e;">DÉPART : Siège Electron Medical (Alger)</div>
          <div style="font-size:11px; color:var(--text-muted);">Prise en charge du véhicule de service & pièces SAV</div>
        </div>
      </div>
  `;

  stops.forEach((s, idx) => {
    const coords = getWilayaCoords(s.wilaya);
    const googleMapsSingleUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.client_nom + ' ' + s.wilaya + ' Algérie')}`;
    const wazeUrl = `https://waze.com/ul?ll=${coords.lat},${coords.lng}&navigate=yes`;

    html += `
      <div class="roadmap-step">
        <div class="step-marker">${idx + 1}</div>
        <div class="step-content">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:6px;">
            <div>
              <div style="font-weight:800; font-size:13px; color:var(--text-main);">${escapeHtmlAttr(s.client_nom)}</div>
              <div style="font-size:11px; color:var(--text-muted);">📍 Wilaya : <b>${escapeHtmlAttr(s.wilaya)}</b> | 🔬 ${escapeHtmlAttr(s.materiel)}</div>
              ${s.telephone ? `<div style="font-size:11px; margin-top:2px;">📞 Contact : <a href="tel:${escapeHtmlAttr(s.telephone)}" style="color:#00b87c; font-weight:700;">${escapeHtmlAttr(s.telephone)}</a></div>` : ''}
            </div>
            <div style="display:flex; gap:6px; align-items:center;" class="no-print">
              <a href="${googleMapsSingleUrl}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px; display:inline-flex; align-items:center; gap:4px;" title="Itinéraire Google Maps">
                <span>📍 Maps</span>
              </a>
              <a href="${wazeUrl}" target="_blank" class="btn btn-secondary" style="padding:4px 8px; font-size:11px; display:inline-flex; align-items:center; gap:4px; color:#0284c7;" title="Itinéraire Waze">
                <span>🚗 Waze</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  html += `
      <div class="roadmap-step step-retour">
        <div class="step-marker">🏁</div>
        <div class="step-content">
          <div style="font-weight:800; font-size:12px; color:#0f766e;">RETOUR : Siège Electron Medical (Alger)</div>
          <div style="font-size:11px; color:var(--text-muted);">Fin de mission, dépôt des PV de révision signés</div>
        </div>
      </div>
    </div>
  `;

  container.innerHTML = html;
}

// =========================================================================
// ACTIONS GPS & WHATSAPP
// =========================================================================
function launchFullGoogleMapsRoute() {
  const stops = currentTournee.optimizedStops;
  if (!stops || stops.length === 0) {
    alert("Veuillez sélectionner au moins un arrêt pour la tournée.");
    return;
  }

  const origin = encodeURIComponent("Siège Electron Medical Alger Algérie");
  const destination = encodeURIComponent("Siège Electron Medical Alger Algérie");

  const waypoints = stops.map(s => encodeURIComponent(`${s.client_nom}, ${s.wilaya}, Algérie`)).join('|');

  const gmapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&waypoints=${waypoints}&travelmode=driving`;
  window.open(gmapsUrl, '_blank');
}

function sendTourneeWhatsApp() {
  const stops = currentTournee.optimizedStops;
  if (!stops || stops.length === 0) {
    alert("Veuillez sélectionner au moins un arrêt pour la tournée.");
    return;
  }

  const tech = document.getElementById('tourTechSelect')?.value || 'Technicien SAV';
  const date = document.getElementById('tourDateInput')?.value || new Date().toISOString().slice(0, 10);

  let msg = `🇩🇿 *ELECTRON MEDICAL ALGÉRIE — ORDRE DE MISSION SAV*\n`;
  msg += `🚗 *Tournée Technique du :* ${date}\n`;
  msg += `👤 *Technicien en charge :* ${tech}\n`;
  msg += `📊 *Distance estimée :* ${currentTournee.totalKm} km (${stops.length} étapes)\n\n`;
  msg += `📍 *ORDRE DE PASSAGE OPTIMAL :*\n`;

  stops.forEach((s, idx) => {
    msg += `\n*${idx + 1}. ${s.client_nom}* (${s.wilaya})\n`;
    msg += `   • Matériel : ${s.materiel} ${s.sn ? `(SN: ${s.sn})` : ''}\n`;
    if (s.telephone) msg += `   • Contact CHU : ${s.telephone}\n`;
    const mapsLink = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(s.client_nom + ' ' + s.wilaya + ' Algerie')}`;
    msg += `   • GPS Maps : ${mapsLink}\n`;
  });

  msg += `\nBonne route et bon courage pour les révisions ! 🛠️`;

  const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`;
  window.open(waUrl, '_blank');
}

function printTourneeMission() {
  document.body.classList.add('printing-tournee');
  window.print();
  setTimeout(() => {
    document.body.classList.remove('printing-tournee');
  }, 1000);
}
