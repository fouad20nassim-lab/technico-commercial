// Liste officielle des 58 Wilayas d'Algérie
const WILAYAS_ALGERIE = [
  { code: "01", nom: "01 - Adrar", region: "Sud" },
  { code: "02", nom: "02 - Chlef", region: "Centre" },
  { code: "03", nom: "03 - Laghouat", region: "Sud" },
  { code: "04", nom: "04 - Oum El Bouaghi", region: "Est" },
  { code: "05", nom: "05 - Batna", region: "Est" },
  { code: "06", nom: "06 - Béjaïa", region: "Est" },
  { code: "07", nom: "07 - Biskra", region: "Sud" },
  { code: "08", nom: "08 - Béchar", region: "Sud" },
  { code: "09", nom: "09 - Blida", region: "Centre" },
  { code: "10", nom: "10 - Bouira", region: "Centre" },
  { code: "11", nom: "11 - Tamanrasset", region: "Sud" },
  { code: "12", nom: "12 - Tébessa", region: "Est" },
  { code: "13", nom: "13 - Tlemcen", region: "Ouest" },
  { code: "14", nom: "14 - Tiaret", region: "Ouest" },
  { code: "15", nom: "15 - Tizi Ouzou", region: "Centre" },
  { code: "16", nom: "16 - Alger", region: "Centre" },
  { code: "17", nom: "17 - Djelfa", region: "Centre" },
  { code: "18", nom: "18 - Jijel", region: "Est" },
  { code: "19", nom: "19 - Sétif", region: "Est" },
  { code: "20", nom: "20 - Saïda", region: "Ouest" },
  { code: "21", nom: "21 - Skikda", region: "Est" },
  { code: "22", nom: "22 - Sidi Bel Abbès", region: "Ouest" },
  { code: "23", nom: "23 - Annaba", region: "Est" },
  { code: "24", nom: "24 - Guelma", region: "Est" },
  { code: "25", nom: "25 - Constantine", region: "Est" },
  { code: "26", nom: "26 - Médéa", region: "Centre" },
  { code: "27", nom: "27 - Mostaganem", region: "Ouest" },
  { code: "28", nom: "28 - M'Sila", region: "Est" },
  { code: "29", nom: "29 - Mascara", region: "Ouest" },
  { code: "30", nom: "30 - Ouargla", region: "Sud" },
  { code: "31", nom: "31 - Oran", region: "Ouest" },
  { code: "32", nom: "32 - El Bayadh", region: "Ouest" },
  { code: "33", nom: "33 - Illizi", region: "Sud" },
  { code: "34", nom: "34 - Bordj Bou Arréridj", region: "Est" },
  { code: "35", nom: "35 - Boumerdès", region: "Centre" },
  { code: "36", nom: "36 - El Tarf", region: "Est" },
  { code: "37", nom: "37 - Tindouf", region: "Sud" },
  { code: "38", nom: "38 - Tissemsilt", region: "Centre" },
  { code: "39", nom: "39 - El Oued", region: "Sud" },
  { code: "40", nom: "40 - Khenchela", region: "Est" },
  { code: "41", nom: "41 - Souk Ahras", region: "Est" },
  { code: "42", nom: "42 - Tipaza", region: "Centre" },
  { code: "43", nom: "43 - Mila", region: "Est" },
  { code: "44", nom: "44 - Aïn Defla", region: "Centre" },
  { code: "45", nom: "45 - Naâma", region: "Ouest" },
  { code: "46", nom: "46 - Aïn Témouchent", region: "Ouest" },
  { code: "47", nom: "47 - Ghardaïa", region: "Sud" },
  { code: "48", nom: "48 - Relizane", region: "Ouest" },
  { code: "49", nom: "49 - Timimoun", region: "Sud" },
  { code: "50", nom: "50 - Bordj Badji Mokhtar", region: "Sud" },
  { code: "51", nom: "51 - Ouled Djellal", region: "Sud" },
  { code: "52", nom: "52 - Béni Abbès", region: "Sud" },
  { code: "53", nom: "53 - In Salah", region: "Sud" },
  { code: "54", nom: "54 - In Guezzam", region: "Sud" },
  { code: "55", nom: "55 - Touggourt", region: "Sud" },
  { code: "56", nom: "56 - Djanet", region: "Sud" },
  { code: "57", nom: "57 - El M'Ghair", region: "Sud" },
  { code: "58", nom: "58 - El Meniaa", region: "Sud" }
];

function populateWilayaSelect(selectElement, defaultVal = "") {
  if (!selectElement) return;
  const currentVal = defaultVal || selectElement.value;
  selectElement.innerHTML = '<option value="">-- Sélectionner la Wilaya (58) --</option>';
  WILAYAS_ALGERIE.forEach(w => {
    const opt = document.createElement("option");
    opt.value = w.nom;
    opt.textContent = `${w.nom} (${w.region})`;
    if (currentVal && (currentVal === w.nom || currentVal.includes(w.code))) {
      opt.selected = true;
    }
    selectElement.appendChild(opt);
  });
}

// 4 Grandes Régions Officielles (Centre, Est, Ouest, Sud)
const REGIONS_ALGERIE = {
  Centre: { code: 'Centre', nom: 'Région Centre', color: '#10b981', class: 'centre', dot: '🟢' },
  Est:    { code: 'Est',    nom: 'Région Est',    color: '#2563eb', class: 'est',    dot: '🔵' },
  Ouest:  { code: 'Ouest',  nom: 'Région Ouest',  color: '#f97316', class: 'ouest',  dot: '🟠' },
  Sud:    { code: 'Sud',    nom: 'Région Sud',    color: '#8b5cf6', class: 'sud',    dot: '🟣' }
};

function getRegionByWilaya(wilayaStr) {
  if (!wilayaStr) return null;
  const str = wilayaStr.trim().toLowerCase();
  const w = WILAYAS_ALGERIE.find(x => {
    const xNom = x.nom.toLowerCase();
    const xRaw = xNom.replace(/^[0-9]+\s*-\s*/, '').trim();
    return str.includes(xRaw) || xNom.includes(str) || str.startsWith(x.code);
  });
  if (w && REGIONS_ALGERIE[w.region]) {
    return REGIONS_ALGERIE[w.region];
  }
  return null;
}

function getRegionBadgeHtml(wilayaStr) {
  const reg = getRegionByWilaya(wilayaStr);
  if (!reg) return '';
  return `<span class="badge-region badge-region-${reg.class}" title="${reg.nom}"><span class="region-orb ${reg.class}" style="width:10px;height:10px;"></span> ${reg.nom}</span>`;
}

function getRegionPillHtml(regionKey) {
  if (!regionKey || regionKey === 'National' || regionKey === 'national') {
    return `<span class="badge-region badge-region-national" style="background:rgba(15,118,110,0.12); color:#0f766e; border:1px solid #0f766e; padding:3px 8px; border-radius:12px; font-size:11px; font-weight:800; display:inline-flex; align-items:center; gap:5px;" title="Toute l'Algérie (National)"><span style="font-size:12px;">🇩🇿</span> National</span>`;
  }
  const reg = REGIONS_ALGERIE[regionKey] || (Object.values(REGIONS_ALGERIE).find(r => r.nom.toLowerCase().includes(String(regionKey).toLowerCase()))) || REGIONS_ALGERIE.Centre;
  return `<span class="badge-region badge-region-${reg.class}" style="display:inline-flex; align-items:center; gap:5px;" title="${reg.nom}"><span class="region-orb ${reg.class}" style="width:10px;height:10px;"></span> ${reg.nom}</span>`;
}
