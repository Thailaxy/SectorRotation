let appData = null;
let currentSort = 'm1';
let sortDesc = true;
let rrgFilter = 'theme';
let rrgChart = null;

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
}

function getThemeName(theme) {
    return currentLang === 'th' ? (theme.name_th || theme.name_en) : theme.name_en;
}

// Best-to-worst zone order used elsewhere in the UI (matches the Momentum
// Playbook's card order). Themes with no quadrant (incomplete data) sort last.
const ZONE_SORT_ORDER = { leading: 0, improving: 1, weakening: 2, lagging: 3 };

function renderHeatmap() {
    const tbody = document.querySelector('#heatmapTable tbody');
    tbody.innerHTML = '';

    let themes = [...appData.themes];
    themes.sort((a, b) => {
        if (currentSort === 'theme') {
            let res = getThemeName(a).localeCompare(getThemeName(b));
            return sortDesc ? res : -res;
        }
        if (currentSort === 'zone') {
            let rankA = ZONE_SORT_ORDER[a.quadrant] ?? 99;
            let rankB = ZONE_SORT_ORDER[b.quadrant] ?? 99;
            return sortDesc ? rankA - rankB : rankB - rankA;
        }
        let valA, valB;
        if (currentSort === 'm1_vs_spy') {
            valA = a.returns.m1_vs_spy; valB = b.returns.m1_vs_spy;
        } else {
            valA = a.returns[currentSort]; valB = b.returns[currentSort];
        }
        valA = valA !== null ? valA : -999;
        valB = valB !== null ? valB : -999;
        return sortDesc ? valB - valA : valA - valB;
    });

    themes.forEach(theme => {
        const tr = document.createElement('tr');

        let qBadge = '';
        if (!theme.data_ok) {
            let badgeText = dict[currentLang] && dict[currentLang]['data_incomplete'] ? dict[currentLang]['data_incomplete'] : 'Incomplete Data';
            qBadge = `<span class="badge incomplete" data-i18n="data_incomplete">${badgeText}</span>`;
        } else if (theme.quadrant) {
            let label = theme.quadrant.charAt(0).toUpperCase() + theme.quadrant.slice(1);
            qBadge = `<span class="badge ${theme.quadrant}">${label}</span>`;
        }

        let nameHtml = getThemeName(theme);
        if (appData.user_holdings.includes(theme.id)) {
            nameHtml += ' 📍';
        }

        tr.innerHTML = `
            <td>${nameHtml}</td>
            <td class="zone-cell">${qBadge}</td>
            ${renderReturnCell(theme.returns.d1)}
            ${renderReturnCell(theme.returns.w1)}
            ${renderReturnCell(theme.returns.m1)}
            ${renderReturnCell(theme.returns.m3)}
            ${renderReturnCell(theme.returns.m1_vs_spy)}
        `;
        tbody.appendChild(tr);
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
    
    let themes = appData.themes.filter(t => t.type === 'theme');
    themes.sort((a, b) => {
        let va = a.breadth_pct !== null ? a.breadth_pct : -1;
        let vb = b.breadth_pct !== null ? b.breadth_pct : -1;
        return vb - va;
    });
    
    themes.forEach(t => {
        const tr = document.createElement('tr');
        let pct = t.breadth_pct;
        let vol = t.dollar_vol_ratio;
        
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
            <td>${getThemeName(t)}</td>
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

document.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
        let clickedSort = th.getAttribute('data-sort');
        if (currentSort === clickedSort) {
            sortDesc = !sortDesc;
        } else {
            currentSort = clickedSort;
            sortDesc = true;
        }
        document.querySelectorAll('th.sortable').forEach(el => el.classList.remove('active'));
        th.classList.add('active');
        renderHeatmap();
    });
});

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

loadData();
