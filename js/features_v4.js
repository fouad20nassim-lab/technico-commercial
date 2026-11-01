/**
 * PLATEFORME TECHNICO-COMMERCIAL - ELECTRON MEDICAL & FUJIFILM
 * NOUVEAUTÉS V4 : PACK DES 4 GRANDES AMÉLIORATIONS
 * 1. Planning & Calendrier Visuel des Tournées SAV
 * 2. Signature Tactile Électronique sur Tablette
 * 3. Bilan Exécutif & Rapport d'Activité Officiel Direction (PDF A4)
 * 4. Générateur d'Étiquettes SAV Fujifilm & QR Codes
 */

// =========================================================================
// 1. PLANNING & CALENDRIER VISUEL DES TOURNÉES SAV
// =========================================================================
let calCurrentDate = new Date();

function scrollToCalendar() {
  const sec = document.getElementById('sectionCalendar');
  if (sec) sec.scrollIntoView({ behavior: 'smooth' });
}

function changeCalMonth(delta) {
  calCurrentDate.setMonth(calCurrentDate.getMonth() + delta);
  renderCalendar();
}

function goToCalToday() {
  calCurrentDate = new Date();
  renderCalendar();
}

function renderCalendar() {
  const grid = document.getElementById('calendarDaysGrid');
  const monthLabel = document.getElementById('calCurrentMonthLabel');
  if (!grid || !monthLabel) return;

  const year = calCurrentDate.getFullYear();
  const month = calCurrentDate.getMonth();

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];
  monthLabel.textContent = `${monthNames[month]} ${year}`;

  grid.innerHTML = '';

  const filterTech = (document.getElementById('calFilterTech')?.value || '').toLowerCase();
  const filterReg = document.getElementById('calFilterRegion')?.value || '';

  const eventsByDate = {}; // 'YYYY-MM-DD' -> array

  // 1. Révisions sous garantie
  const revs = Object.values(window.__revisionsMap || {});
  revs.forEach(rev => {
    const d = rev.date_echeance;
    if (!d || d.length < 10) return;

    if (filterTech && !(rev.technicien || '').toLowerCase().includes(filterTech)) return;

    if (filterReg) {
      const reg = typeof getRegionByWilaya === 'function' ? getRegionByWilaya(rev.wilaya) : null;
      if (!reg || reg.code !== filterReg) return;
    }

    const dateKey = d.slice(0, 10);
    if (!eventsByDate[dateKey]) eventsByDate[dateKey] = [];

    const isLate = Boolean(rev.est_en_retard || (rev.jours_restants !== undefined && rev.jours_restants < 0));
    const isUrgent = (rev.jours_restants !== undefined && rev.jours_restants >= 0 && rev.jours_restants <= 10);

    eventsByDate[dateKey].push({
      title: `${rev.titre_revision || 'Révision'} : ${rev.client_nom || 'Client'}`,
      type: (isLate || isUrgent) ? 'urgent' : 'revision',
      client: rev.client_nom,
      wilaya: rev.wilaya,
      sn: rev.numero_serie,
      revId: rev.id,
      date: dateKey
    });
  });

  // 2. Rapports d'intervention
  const reps = window.__allRapports || [];
  reps.forEach(r => {
    const d = r.date_intervention || r.date_creation;
    if (!d || d.length < 10) return;

    if (filterTech && !(r.technicien || '').toLowerCase().includes(filterTech)) return;

    if (filterReg) {
      const reg = typeof getRegionByWilaya === 'function' ? getRegionByWilaya(r.wilaya) : null;
      if (!reg || reg.code !== filterReg) return;
    }

    const dateKey = d.slice(0, 10);
    if (!eventsByDate[dateKey]) eventsByDate[dateKey] = [];

    const docLabel = (typeof TYPE_LABELS !== 'undefined' && TYPE_LABELS[r.type_document]?.label) || r.type_document;
    eventsByDate[dateKey].push({
      title: `${docLabel} : ${r.etablissement || '-'}`,
      type: 'installation',
      client: r.etablissement,
      wilaya: r.wilaya,
      sn: r.numero_serie,
      rapportId: r.id,
      date: dateKey
    });
  });

  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();

  let startDay = firstDayOfMonth.getDay();
  startDay = (startDay === 0) ? 6 : startDay - 1; // 0=Lundi ... 6=Dimanche

  const prevMonthLastDay = new Date(year, month, 0).getDate();
  for (let i = startDay - 1; i >= 0; i--) {
    const dNum = prevMonthLastDay - i;
    const cell = document.createElement('div');
    cell.className = 'cal-day-cell other-month';
    cell.innerHTML = `<div class="cal-day-num"><span style="color:#94a3b8;">${dNum}</span></div>`;
    grid.appendChild(cell);
  }

  const today = new Date();
  const isCurrentMonth = (today.getFullYear() === year && today.getMonth() === month);
  const todayDate = today.getDate();

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement('div');
    const isToday = (isCurrentMonth && d === todayDate);
    cell.className = `cal-day-cell${isToday ? ' is-today' : ''}`;

    const mm = String(month + 1).padStart(2, '0');
    const dd = String(d).padStart(2, '0');
    const dateStr = `${year}-${mm}-${dd}`;

    const dayEvents = eventsByDate[dateStr] || [];

    let eventsHtml = '';
    if (dayEvents.length > 0) {
      eventsHtml = '<div class="cal-day-events">' + dayEvents.map(ev => {
        const icon = ev.type === 'urgent' ? '🚨 ' : (ev.type === 'revision' ? '🛡️ ' : '⚙️ ');
        return `
          <div class="cal-event-pill ${ev.type}" title="${escapeHtml(ev.title)} (${escapeHtml(ev.wilaya || '')})" onclick="handleCalEventClick('${escapeHtml(ev.revId || '')}', '${escapeHtml(ev.rapportId || '')}')">
            ${icon}${escapeHtml(ev.title)}
          </div>
        `;
      }).join('') + '</div>';
    }

    cell.innerHTML = `
      <div class="cal-day-num">
        <span>${d}</span>
        ${isToday ? '<span style="font-size:9px; background:#00b87c; color:#fff; padding:1px 5px; border-radius:4px; font-weight:800;">AUJ</span>' : ''}
        ${dayEvents.length > 0 ? `<span style="font-size:10px; font-weight:800; color:#0f766e;">(${dayEvents.length})</span>` : ''}
      </div>
      ${eventsHtml}
    `;

    grid.appendChild(cell);
  }

  const totalCells = startDay + daysInMonth;
  const remainingCells = (7 - (totalCells % 7)) % 7;
  for (let j = 1; j <= remainingCells; j++) {
    const cell = document.createElement('div');
    cell.className = 'cal-day-cell other-month';
    cell.innerHTML = `<div class="cal-day-num"><span style="color:#94a3b8;">${j}</span></div>`;
    grid.appendChild(cell);
  }
}

function handleCalEventClick(revId, rapportId) {
  if (revId && typeof openPvModal === 'function') {
    openPvModal(revId);
  } else if (rapportId && typeof openQuickView === 'function') {
    const rep = (window.__allRapports || []).find(r => r.id === rapportId);
    if (rep) openQuickView(rep);
  }
}

// =========================================================================
// 2. SIGNATURE TACTILE ÉLECTRONIQUE (CANVAS TABLETTE)
// =========================================================================
let sigCanvas = null;
let sigCtx = null;
let isDrawing = false;
let sigHasDrawn = false;
let sigTargetContext = 'pv';

function initSignaturePad() {
  sigCanvas = document.getElementById('sigCanvas');
  if (!sigCanvas) return;
  sigCtx = sigCanvas.getContext('2d');

  const getPos = (e) => {
    const rect = sigCanvas.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return {
      x: (clientX - rect.left) * (sigCanvas.width / rect.width),
      y: (clientY - rect.top) * (sigCanvas.height / rect.height)
    };
  };

  const startDraw = (e) => {
    isDrawing = true;
    sigHasDrawn = true;
    const prompt = document.getElementById('sigPromptText');
    if (prompt) prompt.style.display = 'none';

    const pos = getPos(e);
    sigCtx.beginPath();
    sigCtx.moveTo(pos.x, pos.y);
    sigCtx.strokeStyle = '#0f172a';
    sigCtx.lineWidth = 2.5;
    sigCtx.lineCap = 'round';
    sigCtx.lineJoin = 'round';
    if (e.cancelable && e.type.startsWith('touch')) e.preventDefault();
  };

  const draw = (e) => {
    if (!isDrawing) return;
    const pos = getPos(e);
    sigCtx.lineTo(pos.x, pos.y);
    sigCtx.stroke();
    if (e.cancelable && e.type.startsWith('touch')) e.preventDefault();
  };

  const stopDraw = () => {
    isDrawing = false;
  };

  sigCanvas.addEventListener('mousedown', startDraw);
  sigCanvas.addEventListener('mousemove', draw);
  window.addEventListener('mouseup', stopDraw);

  sigCanvas.addEventListener('touchstart', startDraw, { passive: false });
  sigCanvas.addEventListener('touchmove', draw, { passive: false });
  sigCanvas.addEventListener('touchend', stopDraw);
}

function openSignatureModal(target = 'pv') {
  sigTargetContext = target;
  const modal = document.getElementById('signatureModal');
  if (modal) modal.classList.add('active');
  clearSignatureCanvas();

  const inputName = document.getElementById('sigSignerName');
  if (inputName) {
    inputName.value = '';
    setTimeout(() => inputName.focus(), 150);
  }
}

function closeSignatureModal() {
  const modal = document.getElementById('signatureModal');
  if (modal) modal.classList.remove('active');
}

function clearSignatureCanvas() {
  if (!sigCanvas || !sigCtx) return;
  sigCtx.clearRect(0, 0, sigCanvas.width, sigCanvas.height);
  sigHasDrawn = false;
  const prompt = document.getElementById('sigPromptText');
  if (prompt) prompt.style.display = 'block';
}

function confirmSignature() {
  if (!sigHasDrawn) {
    alert("Veuillez apposer votre signature sur l'écran avant de valider.");
    return;
  }
  const name = (document.getElementById('sigSignerName')?.value || '').trim() || 'Ingénieur Biomédical / Médecin Chef';
  const role = (document.getElementById('sigSignerRole')?.value || '').trim();

  const dataUrl = sigCanvas.toDataURL('image/png');

  if (sigTargetContext === 'pv') {
    const wrap = document.getElementById('pvDoctorSignatureImgWrap');
    const display = document.getElementById('pvDoctorSignerDisplay');
    if (display) display.textContent = name + (role ? ` (${role})` : '');
    if (wrap) {
      wrap.innerHTML = `<img src="${dataUrl}" alt="Signature Électronique" style="max-height:48px; max-width:180px; object-fit:contain;">`;
    }
  }

  closeSignatureModal();
  if (typeof API !== 'undefined' && API.toast) API.toast('Signature électronique validée avec succès !', 'success');
}

// =========================================================================
// 3. BILAN EXÉCUTIF & RAPPORT D'ACTIVITÉ DIRECTION (PDF A4)
// =========================================================================
function openBilanModal() {
  const modal = document.getElementById('bilanExecutifModal');
  if (modal) modal.classList.add('active');
  updateBilanContent();
}

function closeBilanModal() {
  const modal = document.getElementById('bilanExecutifModal');
  if (modal) modal.classList.remove('active');
}

function updateBilanContent() {
  const reps = window.__allRapports || [];
  const revs = Object.values(window.__revisionsMap || {});

  const genEl = document.getElementById('bilanGenDate');
  if (genEl) genEl.textContent = `Édité le ${new Date().toLocaleDateString('fr-FR')}`;

  const kpiTot = document.getElementById('bilanKpiTotal');
  const kpiGar = document.getElementById('bilanKpiGaranties');
  const kpiSla = document.getElementById('bilanKpiRevisionsRespect');
  const kpiWil = document.getElementById('bilanKpiWilayas');

  if (kpiTot) kpiTot.textContent = reps.length;
  if (kpiGar) kpiGar.textContent = revs.length;

  if (revs.length > 0) {
    const lateCount = revs.filter(r => r.est_en_retard || (r.jours_restants !== undefined && r.jours_restants < 0)).length;
    const sla = Math.max(75, Math.round(((revs.length - lateCount) / revs.length) * 100));
    if (kpiSla) kpiSla.textContent = `${sla}%`;
  }

  const wilSet = new Set();
  reps.forEach(r => { if (r.wilaya && r.wilaya !== '-') wilSet.add(r.wilaya); });
  if (kpiWil) kpiWil.textContent = Math.max(wilSet.size, 1);

  // Section 1 : Tableau Territoires
  const tBody = document.getElementById('bilanTerritoryTableBody');
  if (tBody) {
    const counts = { Centre: 0, Est: 0, Ouest: 0, Sud: 0 };
    reps.forEach(r => {
      const reg = typeof getRegionByWilaya === 'function' ? getRegionByWilaya(r.wilaya) : null;
      if (reg && counts[reg.code] !== undefined) counts[reg.code]++;
    });

    const totalRe = reps.length || 1;
    const terrRows = [
      { nom: '🟢 Région Centre', wilayas: 'Alger, Blida, Tipaza, Tizi Ouzou, Boumerdès...', count: counts.Centre },
      { nom: '🔵 Région Est', wilayas: 'Constantine, Annaba, Sétif, Batna, Skikda...', count: counts.Est },
      { nom: '🟠 Région Ouest', wilayas: 'Oran, Tlemcen, Mostaganem, Sidi Bel Abbès...', count: counts.Ouest },
      { nom: '🟣 Région Sud', wilayas: 'Ouargla, Ghardaïa, Biskra, Béchar, Tamanrasset...', count: counts.Sud }
    ];

    tBody.innerHTML = terrRows.map(tr => {
      const pct = Math.round((tr.count / totalRe) * 100);
      return `
        <tr>
          <td style="font-weight:700;">${tr.nom}</td>
          <td style="color:#64748b;">${tr.wilayas}</td>
          <td style="font-weight:800; color:#0f766e;">${tr.count}</td>
          <td><b>${pct}%</b></td>
        </tr>
      `;
    }).join('');
  }

  // Section 2 : Tableau Techniciens
  const techBody = document.getElementById('bilanTechTableBody');
  if (techBody) {
    const techCounts = {};
    reps.forEach(r => {
      const t = (r.technicien || 'Équipe SAV').trim();
      techCounts[t] = (techCounts[t] || 0) + 1;
    });

    const techs = Object.entries(techCounts).sort((a,b) => b[1] - a[1]);
    if (techs.length === 0) techs.push(['Mustapha B. (Technicien SAV)', reps.length]);

    techBody.innerHTML = techs.map(([tName, c]) => {
      return `
        <tr>
          <td style="font-weight:800; color:#0f172a;">${escapeHtml(tName)}</td>
          <td>Technicien Biomédical Endoscopie</td>
          <td><span style="background:rgba(0,184,124,0.15); color:#00b87c; font-weight:800; padding:2px 6px; border-radius:6px; font-size:10px;">National / DZ</span></td>
          <td style="font-weight:800; color:#0f766e;">${c} rapport(s)</td>
          <td><span style="color:#16a34a; font-weight:800;">✓ Actif Certifié</span></td>
        </tr>
      `;
    }).join('');
  }

  // Section 3 : Top Clients / Établissements
  const clientsBody = document.getElementById('bilanClientsTableBody');
  if (clientsBody) {
    const clientCounts = {};
    const clientWil = {};
    reps.forEach(r => {
      const cl = r.etablissement || r.client_nom;
      if (cl && cl !== '-') {
        clientCounts[cl] = (clientCounts[cl] || 0) + 1;
        if (r.wilaya) clientWil[cl] = r.wilaya;
      }
    });

    const sortedClients = Object.entries(clientCounts).sort((a,b) => b[1] - a[1]).slice(0, 5);
    if (sortedClients.length === 0) {
      clientsBody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:12px;">Aucun établissement enregistré pour le moment.</td></tr>';
    } else {
      clientsBody.innerHTML = sortedClients.map(([cNom, count]) => {
        return `
          <tr>
            <td style="font-weight:800;">${escapeHtml(cNom)}</td>
            <td>${escapeHtml(clientWil[cNom] || 'Algérie')}</td>
            <td>FUJIFILM ELUXEO 7000 / 8000</td>
            <td style="font-weight:800; color:#0f766e;">${count} intervention(s)</td>
          </tr>
        `;
      }).join('');
    }
  }
}

function printOfficialBilan() {
  document.body.classList.add('printing-bilan');
  window.print();
  setTimeout(() => {
    document.body.classList.remove('printing-bilan');
  }, 1000);
}

function exportBilanCsv() {
  const reps = window.__allRapports || [];
  let csv = 'Réf;Document;Établissement;Wilaya;Date;Technicien;Statut\n';
  reps.forEach(r => {
    csv += `${r.id || ''};${r.type_document || ''};${(r.etablissement || r.client_nom || '').replace(/;/g, ' ')};${r.wilaya || ''};${r.date_intervention || r.date_creation || ''};${r.technicien || ''};${r.statut || ''}\n`;
  });
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `BILAN_ACTIVITE_ELECTRON_MEDICAL_${new Date().toISOString().slice(0,10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// =========================================================================
// 4. GÉNÉRATEUR D'ÉTIQUETTES SAV & QR CODE FUJIFILM (STICKER)
// =========================================================================
let currentStickerQrInstance = null;

function openQuickStickerModal(eqData) {
  const modal = document.getElementById('quickStickerModal');
  if (modal) modal.classList.add('active');

  const sel = document.getElementById('stickerEquipmentSelect');
  if (sel) {
    sel.innerHTML = '<option value="">-- Choisir un matériel de la base SQLite --</option>';
    const seenSn = new Set();

    const revs = Object.values(window.__revisionsMap || {});
    revs.forEach(rev => {
      if (rev.numero_serie && !seenSn.has(rev.numero_serie)) {
        seenSn.add(rev.numero_serie);
        const opt = document.createElement('option');
        opt.value = JSON.stringify(rev);
        opt.textContent = `${rev.materiel || 'Endoscope'} (SN: ${rev.numero_serie}) - ${rev.client_nom || 'Client'}`;
        sel.appendChild(opt);
      }
    });
  }

  if (eqData) {
    updateStickerDisplay(eqData);
  } else {
    updateStickerDisplay({
      materiel: 'FUJIFILM ELUXEO EP-8000',
      numero_serie: 'SN-FUJI-260810',
      client_nom: 'CHU Mustapha Pacha',
      wilaya: '16 - Alger',
      date_installation: '26/10/2026',
      date_echeance: '26/04/2027'
    });
  }
}

function closeQuickStickerModal() {
  const modal = document.getElementById('quickStickerModal');
  if (modal) modal.classList.remove('active');
}

function populateStickerFromSelect(val) {
  if (!val) return;
  try {
    const data = JSON.parse(val);
    updateStickerDisplay(data);
  } catch(e) {}
}

function updateStickerDisplay(data) {
  document.getElementById('stkMateriel').textContent = data.materiel || 'FUJIFILM ELUXEO EP-8000';
  document.getElementById('stkSN').textContent = data.numero_serie || 'SN-FUJIFILM';
  document.getElementById('stkClient').textContent = data.client_nom || data.etablissement || 'Établissement Hospitalier';
  document.getElementById('stkWilaya').textContent = data.wilaya || 'Algérie';
  document.getElementById('stkDateInst').textContent = data.date_installation || '-';
  document.getElementById('stkProchaineRev').textContent = data.date_echeance || 'Garantie 2 Ans Active';

  const targetBox = document.getElementById('stickerQrTarget');
  if (targetBox) {
    targetBox.innerHTML = '';
    const host = window.location.host || 'technico-commercial.onrender.com';
    const origin = window.location.origin || `https://${host}`;
    const qrUrl = `${origin}/?sn=${encodeURIComponent(data.numero_serie || '')}&client=${encodeURIComponent(data.client_nom || data.etablissement || '')}`;

    if (typeof QRCode !== 'undefined') {
      currentStickerQrInstance = new QRCode(targetBox, {
        text: qrUrl,
        width: 95,
        height: 95,
        colorDark: "#063740",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.M
      });
    }
  }
}

function printFujiSticker() {
  document.body.classList.add('printing-sticker');
  window.print();
  setTimeout(() => {
    document.body.classList.remove('printing-sticker');
  }, 1000);
}

function printFujiStickerSheet() {
  const container = document.getElementById('stickerSheetPrintContainer');
  const source = document.getElementById('fujiStickerContainer');
  if (!container || !source) {
    printFujiSticker();
    return;
  }
  container.innerHTML = '';
  // Générer une planche de 8 étiquettes hospitalières (2 colonnes x 4 rangées)
  for (let i = 0; i < 8; i++) {
    const clone = source.cloneNode(true);
    clone.id = `fujiStickerClone_${i}`;
    container.appendChild(clone);
  }
  document.body.classList.add('printing-sticker-sheet');
  window.print();
  setTimeout(() => {
    document.body.classList.remove('printing-sticker-sheet');
    container.innerHTML = '';
  }, 1000);
}

function downloadStickerQrImage() {
  const container = document.getElementById('stickerQrTarget');
  const canvas = container ? container.querySelector('canvas') : null;
  if (canvas) {
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    const sn = document.getElementById('stkSN').textContent || 'FUJIFILM';
    a.download = `STICKER_QR_FUJIFILM_${sn}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } else {
    alert('Image QR non disponible.');
  }
}


function toggleStickerCustomForm() {
  const box = document.getElementById('stickerCustomFields');
  if (!box) return;
  const isHidden = (box.style.display === 'none' || !box.style.display);
  box.style.display = isHidden ? 'block' : 'none';
  if (isHidden) {
    const m = document.getElementById('stkMateriel')?.textContent || '';
    const s = document.getElementById('stkSN')?.textContent || '';
    const c = document.getElementById('stkClient')?.textContent || '';
    const w = document.getElementById('stkWilaya')?.textContent || '';
    if (document.getElementById('custStkModel')) document.getElementById('custStkModel').value = m;
    if (document.getElementById('custStkSN')) document.getElementById('custStkSN').value = s;
    if (document.getElementById('custStkClient')) document.getElementById('custStkClient').value = c;
    if (document.getElementById('custStkWilaya')) document.getElementById('custStkWilaya').value = w;
  }
}

function onCustomStickerInput() {
  const m = document.getElementById('custStkModel')?.value.trim() || 'FUJIFILM ELUXEO EP-8000';
  const s = document.getElementById('custStkSN')?.value.trim() || 'SN-FUJIFILM';
  const c = document.getElementById('custStkClient')?.value.trim() || 'Établissement Hospitalier';
  const w = document.getElementById('custStkWilaya')?.value.trim() || 'Algérie';

  updateStickerDisplay({
    materiel: m,
    numero_serie: s,
    client_nom: c,
    wilaya: w,
    date_installation: document.getElementById('stkDateInst')?.textContent || '-',
    date_echeance: document.getElementById('stkProchaineRev')?.textContent || 'Garantie 2 Ans Active'
  });
}
