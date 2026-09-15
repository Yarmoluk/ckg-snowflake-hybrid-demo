// Snowflake × CKG Hybrid Explorer
// CANVAS_HEIGHT: 660
// Loads the checked-in CKG artifact; this page never sends a warehouse query.

const csvUrl = '../ckg/ecommerce-tpch.csv';
const palette = {
  ROOT: ['#4dd8d0', '#b7fffb'], REGION: ['#65a9ff', '#c7e0ff'],
  SEGMENT: ['#ad8cff', '#e1d7ff'], SUPPLIER_NATION: ['#ff9b7f', '#ffded4'],
  PRIORITY: ['#f6cd70', '#fff1b7']
};
const positions = {
  ROOT: [[0, 0]], REGION: [[-350, -225], [-160, -280], [45, -290], [250, -245], [410, -150]],
  SEGMENT: [[-380, 215], [-190, 265], [0, 280], [185, 245], [360, 185]],
  SUPPLIER_NATION: [[-500, -10], [-450, 75], [-380, 0], [-315, 80], [-250, 0], [-185, 80], [-120, 0], [-55, 80], [15, 0], [85, 80], [155, 0], [225, 80], [295, 0], [365, 80], [435, 0], [500, 70], [-505, 145], [-400, 145], [-290, 145], [-180, 145], [-70, 145], [40, 145], [150, 145], [260, 145], [370, 145]],
  PRIORITY: [[-320, 375], [-160, 400], [0, 420], [160, 400], [320, 375]]
};
let graphRows = [], network, nodes, edges, currentTaxonomy = 'ALL';

function parseCsv(text) {
  const [header, ...lines] = text.trim().split(/\r?\n/);
  const keys = header.split(',');
  return lines.map(line => {
    const values = line.split(',');
    return Object.fromEntries(keys.map((key, i) => [key, values[i] || '']));
  });
}
function embeddedGraphRows() {
  // Exact fallback snapshot of ckg/ecommerce-tpch.csv. It keeps this portfolio
  // artifact useful when opened directly from Finder, where browsers block fetch().
  const hashes = {
    Q1: 'sha256:e1bc798705e9090a7b100d65e1a342b925f61dd57cd8112730506f7abd1e9051',
    Q2: 'sha256:800e749a61633916072e87b58489f61f2b4127f19456de25b764c49b268848e6',
    Q3: 'sha256:07e4a05ef8c335a6ebfd4c6ffcb5013d1f62b7e8e230837639ae46375d1c6927',
    Q4: 'sha256:3964aa93b67c91e8dfc7f6a6ad5b2a6ca17c7a3d87a7817ae4810db22637d808'
  };
  const rows = [{ ConceptID: '1', ConceptLabel: 'TPC-H E-Commerce Dataset', Dependencies: '', TaxonomyID: 'ROOT', SourceURL: 'snowflake://SNOWFLAKE_SAMPLE_DATA/TPCH_SF1', source_content_hash: 'sha256:standard-benchmark-schema' }];
  const append = (labels, prefix, taxonomy, dependency, query, startId) => labels.forEach((label, index) => rows.push({
    ConceptID: String(startId + index), ConceptLabel: `${prefix}${label}`, Dependencies: dependency(label, index), TaxonomyID: taxonomy,
    SourceURL: `sql:02_sample_queries.sql#${query}`, source_content_hash: hashes[query]
  }));
  append(['EUROPE', 'ASIA', 'AMERICA', 'AFRICA', 'MIDDLE EAST'], 'Region: ', 'REGION', () => '1:IMPLEMENTS', 'Q1', 2);
  append(['BUILDING', 'HOUSEHOLD', 'FURNITURE', 'MACHINERY', 'AUTOMOBILE'], 'Segment: ', 'SEGMENT', () => '1:IMPLEMENTS', 'Q2', 7);
  const supplierRegions = [6, 4, 5, 4, 6, 3, 4, 6, 5, 3, 3, 2, 2, 3, 4, 2, 2, 6, 4, 2, 5, 3, 5, 5, 6];
  append(['IRAQ', 'PERU', 'ALGERIA', 'ARGENTINA', 'EGYPT', 'INDIA', 'CANADA', 'SAUDI ARABIA', 'MOZAMBIQUE', 'CHINA', 'INDONESIA', 'FRANCE', 'RUSSIA', 'VIETNAM', 'BRAZIL', 'ROMANIA', 'GERMANY', 'IRAN', 'UNITED STATES', 'UNITED KINGDOM', 'ETHIOPIA', 'JAPAN', 'KENYA', 'MOROCCO', 'JORDAN'], 'Supplier base: ', 'SUPPLIER_NATION', (_, index) => `${supplierRegions[index]}:REQUIRES`, 'Q3', 12);
  append(['5-LOW', '1-URGENT', '4-NOT SPECIFIED', '2-HIGH', '3-MEDIUM'], 'Fulfillment priority: ', 'PRIORITY', () => '1:IMPLEMENTS', 'Q4', 37);
  return rows;
}
function cleanLabel(label) {
  return label.replace('Supplier base: ', '').replace('Fulfillment priority: ', '').replace('Region: ', '').replace('Segment: ', '');
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}
function dependencies(row) {
  return row.Dependencies ? row.Dependencies.split('|').map(edge => {
    const [target, type = 'RELATES_TO'] = edge.split(':'); return { target, type };
  }) : [];
}
function buildGraph(rows) {
  const used = {};
  const visNodes = rows.map(row => {
    const type = row.TaxonomyID;
    const index = used[type] || 0;
    used[type] = index + 1;
    const [x, y] = (positions[type] || [[0, 0]])[index] || [index * 30, index * 25];
    const [background, border] = palette[type] || palette.ROOT;
    return {
      id: row.ConceptID, label: cleanLabel(row.ConceptLabel), group: type, x, y,
      title: row.ConceptLabel,
      color: { background, border, highlight: { background: border, border: '#ffffff' } },
      font: { color: '#06181d', face: 'Arial', size: type === 'SUPPLIER_NATION' ? 11 : 13, bold: type === 'ROOT' },
      shape: type === 'ROOT' ? 'hexagon' : type === 'SUPPLIER_NATION' ? 'dot' : 'box',
      size: type === 'SUPPLIER_NATION' ? 12 : 20, margin: type === 'SUPPLIER_NATION' ? 0 : 9,
      borderWidth: 2
    };
  });
  const visEdges = rows.flatMap(row => dependencies(row).map((dep, index) => ({
    id: `${row.ConceptID}-${index}`, from: row.ConceptID, to: dep.target,
    label: dep.type === 'IMPLEMENTS' ? '' : dep.type, arrows: 'to',
    color: { color: dep.type === 'IMPLEMENTS' ? 'rgba(110, 180, 189, .38)' : 'rgba(255, 190, 119, .52)', highlight: '#ffffff' },
    width: dep.type === 'IMPLEMENTS' ? 1.2 : 1.8, font: { color: '#d7f4f0', size: 9, strokeWidth: 0 }, smooth: { type: 'cubicBezier', roundness: .2 }
  })));
  nodes = new vis.DataSet(visNodes); edges = new vis.DataSet(visEdges);
  const standalone = window.self === window.top;
  network = new vis.Network(document.getElementById('network'), { nodes, edges }, {
    layout: { improvedLayout: false }, physics: false,
    interaction: { hover: true, selectConnectedEdges: false, dragView: standalone, zoomView: standalone, navigationButtons: true },
    nodes: { shadow: { enabled: true, color: 'rgba(0,0,0,.35)', size: 8, x: 0, y: 3 } },
    edges: { smooth: { type: 'cubicBezier' } }
  });
  network.once('afterDrawing', () => network.fit({ animation: false, padding: 88, maxZoomLevel: .9 }));
  network.on('selectNode', params => showDetails(params.nodes[0]));
  network.on('deselectNode', clearDetails);
}
function renderStats() {
  const count = type => graphRows.filter(row => row.TaxonomyID === type).length;
  document.getElementById('graph-stats').innerHTML = [
    ['nodes', graphRows.length], ['typed edges', edges.length], ['regions', count('REGION')], ['source queries', new Set(graphRows.map(r => r.SourceURL)).size - 1]
  ].map(([label, value]) => `<div class="stat"><b>${value}</b><span>${label}</span></div>`).join('');
}
function showDetails(id) {
  const row = graphRows.find(item => item.ConceptID === String(id)); if (!row) return;
  const upstream = dependencies(row).map(dep => graphRows.find(x => x.ConceptID === dep.target)?.ConceptLabel || dep.target).join(', ') || '—';
  const downstream = graphRows.filter(item => dependencies(item).some(dep => dep.target === row.ConceptID)).map(item => item.ConceptLabel).join(', ') || '—';
  document.getElementById('node-details').innerHTML = `<h2>${escapeHtml(row.ConceptLabel)}</h2><p>${escapeHtml(row.TaxonomyID.replace('_', ' '))} · structural graph fact</p><dl><dt>Relationship</dt><dd>Upstream: ${escapeHtml(upstream)}<br>Downstream: ${escapeHtml(downstream)}</dd><dt>Source query</dt><dd><code>${escapeHtml(row.SourceURL)}</code></dd><dt>Result-set provenance</dt><dd><code>${escapeHtml(row.source_content_hash)}</code></dd></dl>`;
}
function clearDetails() {
  document.getElementById('node-details').innerHTML = '<h2>Select a node</h2><p>Its type, graph relationships, query source, and result-set hash will appear here.</p>';
}
function applyFilter() {
  const needle = document.getElementById('node-search').value.trim().toLowerCase();
  const visibleIds = graphRows.filter(row => (currentTaxonomy === 'ALL' || row.TaxonomyID === currentTaxonomy) && row.ConceptLabel.toLowerCase().includes(needle)).map(row => row.ConceptID);
  const visible = new Set(visibleIds);
  nodes.update(graphRows.map(row => ({ id: row.ConceptID, hidden: !visible.has(row.ConceptID) })));
  edges.update(edges.get().map(edge => ({ id: edge.id, hidden: !visible.has(String(edge.from)) || !visible.has(String(edge.to)) })));
}
function createFilters() {
  const types = ['ALL', ...Object.keys(palette)];
  document.getElementById('taxonomy-filters').innerHTML = types.map(type => `<button type="button" class="filter ${type === 'ALL' ? 'active' : ''}" data-type="${type}">${type === 'ALL' ? 'All types' : type.replace('_', ' ').toLowerCase()}</button>`).join('');
  document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
    currentTaxonomy = button.dataset.type; document.querySelectorAll('.filter').forEach(item => item.classList.toggle('active', item === button)); applyFilter();
  }));
}
function routeQuestion() {
  const question = document.getElementById('question').value.trim();
  const output = document.getElementById('route-result');
  if (!question) { output.className = 'route-result'; output.textContent = 'Type a question first.'; return; }
  const text = question.toLowerCase();
  const live = /\b(revenue|count|counts|total|average|avg|most|least|latest|today|current|how many|how much|trend|sales|orders?)\b/.test(text);
  const structural = /\b(exist|exists|type|types|segment|segments|region|regions|supplier|suppliers|priority|priorities|relationship|relate|structure)\b/.test(text);
  let type = 'ckg', headline = 'CKG · structural answer', copy = 'This question is about categories or relationships. Search the compressed graph first; no warehouse query is needed.';
  if (live && structural) { type = 'hybrid'; headline = 'Both · structural context + live truth'; copy = 'Use the graph for the stable entities and relationships, then issue Snowflake SQL for the changing value. The agent should explain that split.'; }
  else if (live) { type = 'live'; headline = 'Live Snowflake · current metric'; copy = 'This asks for a value that can change. Issue a narrowly scoped live SQL query; do not pretend the static graph contains the answer.'; }
  output.className = `route-result ${type}`; output.innerHTML = `<strong>${headline}</strong><br>${copy}`;
}
async function init() {
  try {
    const response = await fetch(csvUrl);
    if (!response.ok) throw new Error(`Could not load CKG CSV (${response.status})`);
    graphRows = parseCsv(await response.text());
  } catch (_) {
    graphRows = embeddedGraphRows();
  }
  buildGraph(graphRows); renderStats(); createFilters();
  document.getElementById('node-search').addEventListener('input', applyFilter);
  document.getElementById('ask-button').addEventListener('click', routeQuestion);
  document.getElementById('question').addEventListener('keydown', event => { if (event.key === 'Enter') routeQuestion(); });
  document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => { document.getElementById('question').value = button.dataset.question; routeQuestion(); }));
  document.getElementById('reset-view').addEventListener('click', () => { currentTaxonomy = 'ALL'; document.getElementById('node-search').value = ''; document.querySelector('.filter').click(); network.fit({ animation: { duration: 300 }, padding: 88, maxZoomLevel: .9 }); clearDetails(); });
}
document.addEventListener('DOMContentLoaded', () => init().catch(error => { document.getElementById('node-details').innerHTML = `<h2>Unable to load graph</h2><p>${escapeHtml(error.message)}</p>`; }));
