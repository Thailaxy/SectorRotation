let appData = null;
let currentSort = 'm1';
let sortDesc = true;
let rrgFilter = 'theme';
let rrgChart = null;

// ─── User personalization state (localStorage-persisted) ───
// Period selector: user picks exactly 4 of the 7 available periods to display.
const ALL_PERIODS = ['d1', 'w1', 'm1', 'm3', 'm6', 'y1', 'y5'];
const PERIOD_LABELS = { d1: '1D', w1: '1W', m1: '1M', m3: '3M', m6: '6M', y1: '1Y', y5: '5Y' };
const DEFAULT_PERIODS = ['d1', 'w1', 'm1', 'm3'];
const DEFAULT_VS_PERIOD = 'm1';

// The 20 ETFs that map to the current theme batch — used as the default
// selection the first time a user enters ETF mode. Picked to mirror what the
// theme heatmap already shows.
const DEFAULT_ETF_SELECTION = [
    'SPY', 'QQQ', 'IWM', 'XLF', 'XLV', 'XLU', 'XLP', 'XLY', 'XLC',
    'XLE', 'XLK', 'XLI', 'SMH', 'GDX', 'EEM', 'HYG', 'TLT', 'VNQ', 'XBI', 'IBB'
];

let selectedPeriods = JSON.parse(localStorage.getItem('selectedPeriods')) || DEFAULT_PERIODS;
let vsPeriod = localStorage.getItem('vsPeriod') || DEFAULT_VS_PERIOD;
let selectedEtfs = JSON.parse(localStorage.getItem('selectedEtfs')) || null;  // null = theme mode
let etfMode = localStorage.getItem('etfMode') === 'true';

async function loadData() {
    try {
        const res = await fetch('data.json');
        appData = await res.json();
        document.getElementById('asOfDate').innerText = appData.as_of_date;
        const updateSpy = (id, val) => {
            const el = document.getElementById(id);
            if (!el) return;
            el.innerText = val !== null ? `${val.toFixed(2)}%` : 'N/A';
            el.className = '';
            if (val > 0) el.classList.add('pos-val');
            else if (val < 0) el.classList.add('neg-val');
        };
        updateSpy('spy1D', appData.benchmark_return_1D);
        updateSpy('spy1M', appData.benchmark_return_1M);
        updateSpy('spy3M', appData.benchmark_return_3M);
        
        initUI();
    } catch (e) {
        console.error("Error loading data.json", e);
    }
}

function initUI() {
    renderHeatmap();
    renderPlaybook();
    renderBreadth();
    renderAppendix();
    initRRG();

    // Wire the new state-driven controls (re-bound on every initUI because
    // some elements are re-rendered on lang change).
    initPeriodSelector();
    initVsSpyDropdown();
    initViewToggle();
    initEtfPanel();
    initResetButton();
    // NOTE: initFeedbackButton() is NOT called here. It binds a submit handler
    // to the form, and re-binding on every lang toggle / mode switch would
    // stack multiple handlers and break the form. It's bound once at page load
    // instead (see bottom of file).

    // The "Select ETFs" button is always visible (clicking it auto-enters ETF mode
    // + opens the modal in one action — more discoverable than hiding it).
    const etfBtn = document.getElementById('etfSelectBtn');
    if (etfBtn) etfBtn.style.display = '';
}

function getThemeName(theme) {
    return currentLang === 'th' ? (theme.name_th || theme.name_en) : theme.name_en;
}

// Best-to-worst zone order used elsewhere in the UI (matches the Momentum
// Playbook's card order). Themes with no quadrant (incomplete data) sort last.
const ZONE_SORT_ORDER = { leading: 0, improving: 1, weakening: 2, lagging: 3 };

function renderHeatmap() {
    const table = document.getElementById('heatmapTable');
    const thead = table.querySelector('thead tr');
    const tbody = table.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    // Build dynamic header from selectedPeriods + vs SPY column.
    // The vs SPY column reflects the current vsPeriod (e.g. "3M vs SPY").
    const t = dict[currentLang] || dict.en;
    const vsLabel = `${PERIOD_LABELS[vsPeriod]} ${t.vs_spy_suffix}`;

    const nameTh = document.createElement('th');
    nameTh.className = 'sortable';
    nameTh.setAttribute('data-sort', 'name');
    nameTh.setAttribute('data-i18n', etfMode ? 'etf_name_label' : 'col_theme');
    nameTh.innerText = etfMode ? t.etf_name_label : t.col_theme;
    thead.appendChild(nameTh);

    const zoneTh = document.createElement('th');
    zoneTh.className = 'sortable';
    zoneTh.setAttribute('data-sort', 'zone');
    zoneTh.setAttribute('data-i18n', 'col_zone');
    zoneTh.innerText = t.col_zone;
    thead.appendChild(zoneTh);

    selectedPeriods.forEach(p => {
        const th = document.createElement('th');
        th.className = 'sortable' + (currentSort === p ? ' active' : '');
        th.setAttribute('data-sort', p);
        th.innerText = PERIOD_LABELS[p];
        thead.appendChild(th);
    });

    const vsTh = document.createElement('th');
    vsTh.className = 'sortable' + (currentSort === 'vs_spy' ? ' active' : '');
    vsTh.setAttribute('data-sort', 'vs_spy');
    vsTh.innerText = vsLabel;
    thead.appendChild(vsTh);

    // Pick the row source: themes vs ETFs.
    let rows;
    if (etfMode) {
        const sel = selectedEtfs || DEFAULT_ETF_SELECTION;
        rows = (appData.etfs || []).filter(e => sel.includes(e.ticker));
    } else {
        rows = [...(appData.themes || [])];
    }

    // Sorting (works for both theme rows and ETF rows).
    rows.sort((a, b) => {
        // Name column
        if (currentSort === 'name') {
            const na = etfMode ? a.ticker : getThemeName(a);
            const nb = etfMode ? b.ticker : getThemeName(b);
            const res = String(na).localeCompare(String(nb));
            return sortDesc ? res : -res;
        }
        if (currentSort === 'zone') {
            const rankA = ZONE_SORT_ORDER[a.quadrant] ?? 99;
            const rankB = ZONE_SORT_ORDER[b.quadrant] ?? 99;
            return sortDesc ? rankA - rankB : rankB - rankA;
        }
        // Period columns or vs_spy.
        let valA, valB;
        if (currentSort === 'vs_spy') {
            valA = (a.returns.vs_spy || {})[vsPeriod];
            valB = (b.returns.vs_spy || {})[vsPeriod];
        } else {
            valA = a.returns[currentSort];
            valB = b.returns[currentSort];
        }
        valA = valA !== null && valA !== undefined ? valA : -999;
        valB = valB !== null && valB !== undefined ? valB : -999;
        return sortDesc ? valB - valA : valA - valB;
    });

    rows.forEach(row => {
        const tr = document.createElement('tr');

        // Zone badge — same logic for themes and ETFs.
        let qBadge = '';
        if (!row.data_ok) {
            qBadge = `<span class="badge incomplete" data-i18n="data_incomplete">${t.data_incomplete}</span>`;
        } else if (row.quadrant) {
            const label = row.quadrant.charAt(0).toUpperCase() + row.quadrant.slice(1);
            qBadge = `<span class="badge ${row.quadrant}">${label}</span>`;
        }

        // Name cell — ETF mode shows ticker; theme mode shows localized name + 📍.
        let nameHtml;
        if (etfMode) {
            nameHtml = `<strong>${row.ticker}</strong><br><span style="font-size:0.75rem;color:var(--text-secondary)">${row.name || ''}</span>`;
        } else {
            nameHtml = getThemeName(row);
            if (appData.user_holdings.includes(row.id)) nameHtml += ' 📍';
        }

        const cellsHtml = selectedPeriods.map(p => renderReturnCell(row.returns[p])).join('');
        const vsVal = (row.returns.vs_spy || {})[vsPeriod];
        const vsCell = renderReturnCell(vsVal);

        tr.innerHTML = `
            <td>${nameHtml}</td>
            <td class="zone-cell">${qBadge}</td>
            ${cellsHtml}
            ${vsCell}
        `;
        tbody.appendChild(tr);
    });

    // Re-bind sort handlers for the freshly rendered header cells.
    thead.querySelectorAll('th.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const clickedSort = th.getAttribute('data-sort');
            if (currentSort === clickedSort) {
                sortDesc = !sortDesc;
            } else {
                currentSort = clickedSort;
                sortDesc = true;
            }
            renderHeatmap();
        });
    });
}

function renderReturnCell(val) {
    if (val === null) return `<td>-</td>`;

    let absVal = Math.min(Math.abs(val), 20); // Cap at 20% for scale
    let opacity = 0.1 + (absVal / 20) * 0.7; // From 0.1 to 0.8 opacity
    let rgb = val > 0 ? getCssVar('--pos-rgb') : getCssVar('--neg-rgb');
    let bgCol = `rgba(${rgb}, ${opacity})`;

    // Text stays in neutral ink rather than pos/neg accent color: at high
    // opacity the cell background is already strongly tinted, and same-hue
    // text on a same-hue fill drops below readable contrast (validated with
    // the dataviz skill's WCAG contrast checker). The background color and
    // the +/- sign already carry the direction; the text doesn't need to too.
    return `<td style="background-color: ${bgCol}; border-bottom: 1px solid var(--border); color: var(--text); font-weight: 600;">${val > 0 ? '+' : ''}${val.toFixed(2)}%</td>`;
}

function getBreadthColor(pct) {
    if (pct >= 50) return 'bb-green';
    if (pct >= 30) return 'bb-yellow';
    return 'bb-red';
}

// Same green/yellow/red breadth thresholds as getBreadthColor(), mapped to
// the existing .badge.leading/weakening/lagging classes so this badge picks
// up the same theme-aware background + contrast-checked text color as the
// quadrant badges, instead of duplicating hardcoded colors inline.
function getBreadthBadgeClass(pct) {
    if (pct >= 50) return 'leading';
    if (pct >= 30) return 'weakening';
    return 'lagging';
}

function renderPlaybook() {
    ['leading', 'improving', 'weakening', 'lagging'].forEach(q => {
        const listDiv = document.querySelector(`#pb-${q} .pb-list`);
        listDiv.innerHTML = '';
        
        let themesInQ = appData.themes.filter(t => t.quadrant === q);
        themesInQ.sort((a, b) => {
            let va = a.returns.m1_vs_spy !== null ? a.returns.m1_vs_spy : -999;
            let vb = b.returns.m1_vs_spy !== null ? b.returns.m1_vs_spy : -999;
            return vb - va;
        });
        
        themesInQ.forEach(t => {
            let badge = '';
            if (t.type === 'sector_etf') {
                badge = `<span class="badge incomplete">ETF</span>`;
            } else if (t.breadth_pct !== null) {
                let badgeClass = getBreadthBadgeClass(t.breadth_pct);
                badge = `<span class="badge ${badgeClass}">B ${t.breadth_pct.toFixed(0)}%</span>`;
            }
            
            let val = t.returns.m1_vs_spy !== null ? `${t.returns.m1_vs_spy>0?'+':''}${t.returns.m1_vs_spy.toFixed(1)}%` : '-';
            
            listDiv.innerHTML += `
                <div class="pb-item">
                    <span>${getThemeName(t)} ${val}</span>
                    <span>${badge}</span>
                </div>
            `;
        });
    });
}

function renderBreadth() {
    const tbody = document.querySelector('#breadthTable tbody');
    tbody.innerHTML = '';

    // In ETF mode, show selected ETFs instead of themes. Same columns,
    // same rendering — just a different row source. Group C ETFs (bonds,
    // commodities, vol, crypto) have breadth_pct=null and show '-'.
    let rows;
    if (etfMode) {
        const sel = selectedEtfs || DEFAULT_ETF_SELECTION;
        rows = (appData.etfs || []).filter(e => sel.includes(e.ticker));
    } else {
        rows = appData.themes.filter(t => t.type === 'theme');
    }

    rows.sort((a, b) => {
        let va = a.breadth_pct !== null ? a.breadth_pct : -1;
        let vb = b.breadth_pct !== null ? b.breadth_pct : -1;
        return vb - va;
    });

    rows.forEach(row => {
        const tr = document.createElement('tr');
        let pct = row.breadth_pct;
        let vol = row.dollar_vol_ratio;

        // Name cell: ETF mode shows ticker + name, theme mode shows localized name.
        let nameHtml;
        if (etfMode) {
            nameHtml = `<strong>${row.ticker}</strong><br><span style="font-size:0.75rem;color:var(--text-secondary)">${row.name || ''}</span>`;
        } else {
            nameHtml = getThemeName(row);
        }

        let pctHtml = '-';
        if (pct !== null) {
            let color = getBreadthColor(pct);
            pctHtml = `
                <div>${pct.toFixed(1)}%</div>
                <div class="breadth-bar-container"><div class="breadth-bar ${color}" style="width:${pct}%"></div></div>
            `;
        }

        let volHtml = '-';
        if (vol !== null) {
            let col = vol > 1 ? 'pos-val' : (vol < 1 ? 'neg-val' : '');
            volHtml = `<span class="${col}">${vol.toFixed(2)}x</span>`;
        }

        tr.innerHTML = `
            <td>${nameHtml}</td>
            <td>${pctHtml}</td>
            <td>${volHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAppendix() {
    const grid = document.getElementById('appendixGrid');
    grid.innerHTML = '';
    
    appData.themes.forEach(t => {
        const div = document.createElement('div');
        div.className = 'appendix-card';
        
        let etfsHtml = t.ref_etfs.map(e => {
            let l = currentLang === 'th' ? e.label_th : e.label_en;
            return `<span class="etf-pill"><strong>${e.ticker}</strong> ${l}</span>`;
        }).join('');
        
        let constLabel = dict[currentLang] && dict[currentLang]['col_constituents'] ? dict[currentLang]['col_constituents'] : 'Constituents: ';
        let constsHtml = t.type === 'theme' ? `<p><span data-i18n="col_constituents">${constLabel}</span>${t.constituents.join(', ')}</p>` : '';
        
        div.innerHTML = `
            <h3>${getThemeName(t)}</h3>
            <div>${etfsHtml}</div>
            ${constsHtml}
        `;
        grid.appendChild(div);
    });
}

function getCssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function getColorMap() {
    return {
        leading: getCssVar('--leading'),
        improving: getCssVar('--improving'),
        weakening: getCssVar('--weakening'),
        lagging: getCssVar('--lagging')
    };
}

let selectedTheme = null;

function initRRG() {
    if (rrgChart) rrgChart.dispose();
    rrgChart = echarts.init(document.getElementById('rrgChart'));
    
    rrgChart.on('click', function(params) {
        if (params.seriesType === 'line') {
            selectedTheme = params.seriesName;
            renderRRG();
        }
    });
    
    rrgChart.getZr().on('click', function(e) {
        if (!e.target) {
            selectedTheme = null;
            renderRRG();
        }
    });

    renderRRG();
}

function renderRRG() {
    let filtered = appData.themes.filter(t => t.rrg !== null);
    if (rrgFilter !== 'all') {
        filtered = filtered.filter(t => t.type === rrgFilter);
    }

    const colorMap = getColorMap();
    const axisColor = getCssVar('--muted') || '#8b949e';
    const gridColor = getCssVar('--border') || '#30363d';

    let series = [];
    filtered.forEach(t => {
        if (!t.rrg) return;
        let c = colorMap[t.quadrant] || getCssVar('--text');
        let dataPts = t.rrg.tail.map(pt => [pt.ratio, pt.momentum]);
        
        let opacity = selectedTheme ? (selectedTheme === getThemeName(t) ? 1 : 0.1) : 0.5;
        let width = selectedTheme && selectedTheme === getThemeName(t) ? 2 : 1;
        series.push({
            name: getThemeName(t),
            type: 'line',
            data: dataPts,
            smooth: true,
            symbol: 'circle',
            symbolSize: (val, params) => params.dataIndex === dataPts.length - 1 ? 10 : 4,
            lineStyle: { width: width, color: c, opacity: opacity },
            itemStyle: { color: c, opacity: opacity },
            emphasis: {
                focus: 'series',
                lineStyle: { width: 2, opacity: 1 }
            }
        });
    });
    
    let option = {
        grid: { top: 20, right: 20, bottom: 20, left: 30, containLabel: true },
        tooltip: {
            formatter: (params) => {
                let p = params[0] || params;
                let t = filtered.find(th => getThemeName(th) === p.seriesName);
                if (!t) return p.seriesName;
                return `<strong>${p.seriesName}</strong><br/>
                Ratio: ${p.value[0]}<br/>
                Momentum: ${p.value[1]}<br/>
                Zone: ${t.quadrant}`;
            }
        },
        xAxis: { type: 'value', min: 70, max: 150, splitLine: { show: false }, axisLabel: { color: axisColor } },
        yAxis: { type: 'value', min: 70, max: 150, splitLine: { show: false }, axisLabel: { color: axisColor } },
        series: series,
        graphic: [
            { type: 'text', z: -1, left: 'right', top: 'top', style: { text: 'LEADING', fill: colorMap.leading, font: 'bold 12px Inter', opacity: 0.7 } },
            { type: 'text', z: -1, left: 'left', top: 'top', style: { text: 'IMPROVING', fill: colorMap.improving, font: 'bold 12px Inter', opacity: 0.7 } },
            { type: 'text', z: -1, left: 'right', bottom: 'bottom', style: { text: 'WEAKENING', fill: colorMap.weakening, font: 'bold 12px Inter', opacity: 0.7 } },
            { type: 'text', z: -1, left: 'left', bottom: 'bottom', style: { text: 'LAGGING', fill: colorMap.lagging, font: 'bold 12px Inter', opacity: 0.7 } }
        ]
    };
    
    rrgChart.setOption(option);
    
    // Background quadrants and markLine
    option.series.push({
        type: 'scatter',
        data: [],
        markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: gridColor, width: 1, type: 'solid' },
            data: [
                { xAxis: 100 },
                { yAxis: 100 }
            ]
        },
        markArea: {
            silent: true,
            data: [
                [{ xAxis: 100, yAxis: 100 }, { xAxis: 200, yAxis: 200, itemStyle: { color: colorMap.leading, opacity: 0.05 } }], // Leading
                [{ xAxis: 0, yAxis: 100 }, { xAxis: 100, yAxis: 200, itemStyle: { color: colorMap.improving, opacity: 0.05 } }], // Improving
                [{ xAxis: 100, yAxis: 0 }, { xAxis: 200, yAxis: 100, itemStyle: { color: colorMap.weakening, opacity: 0.05 } }], // Weakening
                [{ xAxis: 0, yAxis: 0 }, { xAxis: 100, yAxis: 100, itemStyle: { color: colorMap.lagging, opacity: 0.05 } }]  // Lagging
            ]
        }
    });
    rrgChart.setOption(option, true);
}

// ─── Period selector / vs SPY dropdown / ETF mode — all dynamic UI ───
// Re-rendered by initUI() so handlers bind on every render.

document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
        rrgFilter = btn.getAttribute('data-filter');
        renderRRG();
    });
});

document.addEventListener('langChanged', () => {
    if (appData) {
        initUI();
        renderFeedbackTable();
    }
});

document.addEventListener('themeChanged', () => {
    if (appData) {
        renderRRG();
    }
});

window.addEventListener('resize', () => {
    if (rrgChart) rrgChart.resize();
});

// ─── New: period selector + vs SPY dropdown + ETF mode wiring ───
function initPeriodSelector() {
    const container = document.getElementById('periodSelector');
    if (!container) return;
    container.innerHTML = '';

    ALL_PERIODS.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'period-btn' + (selectedPeriods.includes(p) ? ' active' : '');
        btn.setAttribute('data-period', p);
        btn.innerText = PERIOD_LABELS[p];
        btn.addEventListener('click', () => togglePeriod(p));
        container.appendChild(btn);
    });
}

function togglePeriod(p) {
    const t = dict[currentLang] || dict.en;
    if (selectedPeriods.includes(p)) {
        // Deselect is always allowed — no minimum. Users may want fewer columns.
        selectedPeriods = selectedPeriods.filter(x => x !== p);
    } else {
        // Block selecting past 4 active.
        if (selectedPeriods.length >= 4) {
            alert(t.periods_max);
            return;
        }
        selectedPeriods.push(p);
    }
    localStorage.setItem('selectedPeriods', JSON.stringify(selectedPeriods));
    initPeriodSelector();
    renderHeatmap();
}

function initVsSpyDropdown() {
    const sel = document.getElementById('vsPeriodSelect');
    if (!sel) return;
    sel.innerHTML = '';
    ALL_PERIODS.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p;
        opt.innerText = PERIOD_LABELS[p];
        if (p === vsPeriod) opt.selected = true;
        sel.appendChild(opt);
    });
    sel.addEventListener('change', () => {
        vsPeriod = sel.value;
        localStorage.setItem('vsPeriod', vsPeriod);
        renderHeatmap();
    });
}

function initViewToggle() {
    const btn = document.getElementById('viewToggle');
    if (!btn) return;
    const t = dict[currentLang] || dict.en;
    btn.innerText = etfMode ? t.view_themes : t.view_etfs;
    btn.addEventListener('click', () => {
        etfMode = !etfMode;
        localStorage.setItem('etfMode', etfMode ? 'true' : 'false');
        // First entry to ETF mode with no saved selection → use the default 20.
        if (etfMode && !selectedEtfs) {
            selectedEtfs = [...DEFAULT_ETF_SELECTION];
            localStorage.setItem('selectedEtfs', JSON.stringify(selectedEtfs));
        }
        currentSort = 'm1';
        sortDesc = true;
        initUI();
    });
}

function initEtfPanel() {
    const openBtn = document.getElementById('etfSelectBtn');
    const modal = document.getElementById('etfModal');
    const closeBtn = document.getElementById('etfModalClose');
    const resetBtn = document.getElementById('etfResetBtn');
    const clearBtn = document.getElementById('etfClearBtn');
    const searchInput = document.getElementById('etfSearchInput');
    if (!openBtn || !modal) return;

    // Open/close toggle. Clicking the gear also auto-enters ETF mode so users
    // don't have to click "View: ETFs" first — one click to see the selector.
    openBtn.addEventListener('click', () => {
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
            return;
        }
        // Auto-switch to ETF mode (no-op if already in it).
        if (!etfMode) {
            etfMode = true;
            localStorage.setItem('etfMode', 'true');
            if (!selectedEtfs) {
                selectedEtfs = [...DEFAULT_ETF_SELECTION];
                localStorage.setItem('selectedEtfs', JSON.stringify(selectedEtfs));
            }
            currentSort = 'm1';
            sortDesc = true;
            initUI();
        }
        renderEtfChecklist();
        modal.style.display = 'block';
        // Focus the search input for instant typing.
        if (searchInput) {
            searchInput.value = '';
            setTimeout(() => searchInput.focus(), 50);
        }
    });
    if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.style.display = 'none');
    }
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            selectedEtfs = [...DEFAULT_ETF_SELECTION];
            localStorage.setItem('selectedEtfs', JSON.stringify(selectedEtfs));
            renderEtfChecklist();
            renderHeatmap();
            renderBreadth();
        });
    }
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            // Clear all but enforce minimum 1 — pick SPY as the canonical default.
            selectedEtfs = ['SPY'];
            localStorage.setItem('selectedEtfs', JSON.stringify(selectedEtfs));
            renderEtfChecklist();
            renderHeatmap();
            renderBreadth();
        });
    }
    // Live search filter — re-renders the checklist as the user types.
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const term = searchInput.value.toLowerCase().trim();
            const clearX = document.getElementById('etfSearchClear');
            if (clearX) clearX.style.display = term ? '' : 'none';
            renderEtfChecklist(term);
        });
        // Click the ✕ inside the search field to clear it.
        const searchClear = document.getElementById('etfSearchClear');
        if (searchClear) {
            searchClear.addEventListener('click', () => {
                searchInput.value = '';
                searchClear.style.display = 'none';
                renderEtfChecklist();
                searchInput.focus();
            });
        }
    }
    // Click outside modal closes it.
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
}

function renderEtfChecklist(filterTerm = '') {
    const list = document.getElementById('etfChecklist');
    const counter = document.getElementById('etfCounter');
    if (!list || !counter) return;
    const t = dict[currentLang] || dict.en;
    list.innerHTML = '';

    const term = (filterTerm || '').toLowerCase().trim();

    // Group ETFs by theme_label for easier scanning.
    const groups = {};
    (appData.etfs || []).forEach(e => {
        // When a search term is active, filter by ticker or name match.
        if (term) {
            const hay = `${e.ticker} ${e.name || ''} ${e.theme_label || ''}`.toLowerCase();
            if (!hay.includes(term)) return;
        }
        const g = e.theme_label || 'Other';
        (groups[g] = groups[g] || []).push(e);
    });

    // If the search matched nothing, show a friendly empty state.
    if (Object.keys(groups).length === 0) {
        const empty = document.createElement('div');
        empty.className = 'etf-search-empty';
        empty.innerText = `No ETFs match "${filterTerm}"`;
        list.appendChild(empty);
        counter.innerText = t.etfs_selected((selectedEtfs || []).length);
        return;
    }

    const sel = selectedEtfs || [];
    Object.keys(groups).sort().forEach(g => {
        const groupDiv = document.createElement('div');
        groupDiv.className = 'etf-group';
        const title = document.createElement('div');
        title.className = 'etf-group-title';
        title.innerText = g;
        groupDiv.appendChild(title);

        groups[g].sort((a, b) => (a.rank || 999) - (b.rank || 999)).forEach(e => {
            const label = document.createElement('label');
            label.className = 'etf-check';
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = e.ticker;
            cb.checked = sel.includes(e.ticker);
            cb.addEventListener('change', () => {
                if (cb.checked) {
                    if ((selectedEtfs || []).length >= 20) {
                        cb.checked = false;
                        alert(t.etfs_max);
                        return;
                    }
                    selectedEtfs = [...(selectedEtfs || []), e.ticker];
                } else {
                    // Enforce minimum 1 selection.
                    if ((selectedEtfs || []).length <= 1) {
                        cb.checked = true;
                        alert(t.etf_min_one);
                        return;
                    }
                    selectedEtfs = (selectedEtfs || []).filter(x => x !== e.ticker);
                }
                localStorage.setItem('selectedEtfs', JSON.stringify(selectedEtfs));
                counter.innerText = t.etfs_selected((selectedEtfs || []).length);
                renderHeatmap();
                renderBreadth();
            });
            label.appendChild(cb);
            label.appendChild(document.createTextNode(` ${e.ticker} — ${e.name || ''}`));
            groupDiv.appendChild(label);
        });
        list.appendChild(groupDiv);
    });
    counter.innerText = t.etfs_selected((selectedEtfs || []).length);
}

function initResetButton() {
    const btn = document.getElementById('resetBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        localStorage.removeItem('selectedPeriods');
        localStorage.removeItem('vsPeriod');
        localStorage.removeItem('selectedEtfs');
        localStorage.removeItem('etfMode');
        selectedPeriods = [...DEFAULT_PERIODS];
        vsPeriod = DEFAULT_VS_PERIOD;
        selectedEtfs = null;
        etfMode = false;
        currentSort = 'm1';
        sortDesc = true;
        initUI();
    });
}

// ─── Feedback feature ───
// Submissions go to Formspree (formId xjgqjnen) — emails the admin the full
// payload including the optional reply-to email. Admin curates which entries
// appear publicly by editing web/public/feedback.json and committing.
// EMAIL NEVER ENTERS feedback.json.

const FORMSPREE_ENDPOINT = 'https://formspree.io/f/xjgqjnen';
let feedbackData = null;

function initFeedbackButton() {
    const openBtn = document.getElementById('feedbackBtn');
    const modal = document.getElementById('feedbackModal');
    const closeBtn = document.getElementById('feedbackModalClose');
    const form = document.getElementById('feedbackForm');
    if (!openBtn || !modal || !form) return;

    // Guard against double-binding — if this ever runs twice (e.g. called from
    // multiple places), don't stack submit handlers. The data-bound flag is
    // more robust than a module-level boolean.
    if (form.dataset.bound === 'true') return;
    form.dataset.bound = 'true';

    openBtn.addEventListener('click', () => {
        modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
    });
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const t = dict[currentLang] || dict.en;
        const submitBtn = document.getElementById('feedbackSubmit');
        const status = document.getElementById('feedbackStatus');
        submitBtn.disabled = true;
        submitBtn.innerText = t.feedback_sending;
        status.className = 'feedback-status';
        status.innerText = '';

        try {
            const formData = new FormData(form);
            const res = await fetch(FORMSPREE_ENDPOINT, {
                method: 'POST',
                body: formData,
                headers: { Accept: 'application/json' }
            });
            if (res.ok) {
                status.classList.add('success');
                status.innerText = t.feedback_success;
                form.reset();
                setTimeout(() => { modal.style.display = 'none'; status.innerText = ''; }, 3000);
            } else {
                const data = await res.json().catch(() => ({}));
                status.classList.add('error');
                status.innerText = data?.errors?.[0]?.message || t.feedback_error;
            }
        } catch (err) {
            status.classList.add('error');
            status.innerText = t.feedback_error;
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerText = t.feedback_submit;
        }
    });
}

async function loadFeedback() {
    try {
        const res = await fetch('feedback.json');
        feedbackData = await res.json();
        renderFeedbackTable();
    } catch (e) {
        console.error('Error loading feedback.json', e);
    }
}

function renderFeedbackTable() {
    const tbody = document.querySelector('#feedbackTable tbody');
    if (!tbody || !feedbackData) return;
    tbody.innerHTML = '';
    const t = dict[currentLang] || dict.en;
    const entries = feedbackData.feedback || [];

    if (entries.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td colspan="3" style="text-align:center;color:var(--muted);padding:24px">${t.feedback_empty}</td>`;
        tbody.appendChild(tr);
        return;
    }

    entries.forEach(entry => {
        const tr = document.createElement('tr');
        const statusKey = `feedback_status_${(entry.status || 'open').replace('-', '_')}`;
        const statusLabel = t[statusKey] || entry.status || '';
        const photoHtml = entry.photo
            ? `<a href="${entry.photo}" target="_blank" rel="noopener"><img src="${entry.photo}" alt="feedback photo" class="feedback-thumb"></a>`
            : '-';

        tr.innerHTML = `
            <td>
                <strong>${escapeHtml(entry.requestor || 'Anonymous')}</strong>
                <div style="font-size:0.75rem;color:var(--muted);margin-top:2px">${escapeHtml(entry.date || '')}</div>
                <span class="badge ${statusBadgeClass(entry.status)}" style="margin-top:4px;display:inline-block">${statusLabel}</span>
            </td>
            <td>${escapeHtml(entry.details || '')}</td>
            <td>${photoHtml}</td>
        `;
        tbody.appendChild(tr);
    });
}

function statusBadgeClass(status) {
    if (status === 'done') return 'leading';
    if (status === 'in-progress' || status === 'progress') return 'weakening';
    return 'incomplete';
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

loadData();
loadFeedback();
// Bind feedback button ONCE on initial page load. Re-binding inside initUI()
// stacked multiple submit handlers and broke the form on lang toggle.
initFeedbackButton();
