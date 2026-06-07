// inicializações
document.addEventListener("DOMContentLoaded", function() {
    if (document.getElementById("tabela-dados")) {
        paginarTabela();
    }
    if (document.getElementById("select-hospital") || document.getElementById("select-hospital-filtro")) {
        filtrarDepartamentos();
    }
});

// filtro de departamentos baseado no hospital selecionado
function filtrarDepartamentos() {
    const selectHospital = document.getElementById('select-hospital') || document.getElementById('select-hospital-filtro');
    const selectDept = document.getElementById('select-department');
    if (!selectHospital || !selectDept) return; 
    
    const hospitalEscolhido = selectHospital.value;
    const deptSelecionadoAtualmente = selectDept.querySelector('option:checked');
    
    if (deptSelecionadoAtualmente && deptSelecionadoAtualmente.value !== "") {
        const hospitalDoDeptAtual = deptSelecionadoAtualmente.getAttribute('data-hospital');
        if (hospitalEscolhido !== "" && hospitalDoDeptAtual !== hospitalEscolhido) { 
            selectDept.value = ""; 
        }
    }
    
    const options = selectDept.getElementsByTagName('option');
    for (let i = 0; i < options.length; i++) {
        const opt = options[i];
        if (opt.value === "") continue; 
        const deptHospital = opt.getAttribute('data-hospital');
        
        // compatibilidade com mobile, o que parece estupido porque isto e um localhost
        if (hospitalEscolhido === "" || deptHospital === hospitalEscolhido) {
            opt.disabled = false;
            opt.style.display = '';
        } else {
            opt.disabled = true;
            opt.style.display = 'none';
        }
    }
}

// debounce (evita lag enquanto escreves)
let debounceTimeout;
function buscaRapidaTabela() {
    clearTimeout(debounceTimeout);
    
    // Aguarda 300ms após o utilizador parar de escrever para filtrar (evita travamentos)
    debounceTimeout = setTimeout(function() {
        const input = document.getElementById("input-busca-rapida");
        let filter = input.value.trim().toUpperCase();
        const table = document.getElementById("tabela-dados");
        if (!table) return;
        
        const tr = table.getElementsByTagName("tbody")[0].getElementsByTagName("tr");
        const procurarPorID = filter.startsWith("#");
        if (procurarPorID) filter = filter.substring(1);
        
        for (let i = 0; i < tr.length; i++) {
            if (tr[i].classList.contains('linha-raio-x-container')) continue;
            
            if (procurarPorID) {
                let idTd = tr[i].getElementsByTagName("td")[0];
                let idValue = idTd ? (idTd.textContent || idTd.innerText).replace("#", "").trim() : "";
                if (idValue === filter || idValue.startsWith(filter)) { 
                    tr[i].classList.remove("filtrado-escondido"); 
                } else { 
                    tr[i].classList.add("filtrado-escondido"); 
                }
            } else {
                let txtValue = tr[i].textContent || tr[i].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) { 
                    tr[i].classList.remove("filtrado-escondido"); 
                } else { 
                    tr[i].classList.add("filtrado-escondido"); 
                }
            }
        }
        paginarTabela();
    }, 300);
}

// paginations
let paginaAtual = 1;

function paginarTabela() {
    const table = document.getElementById("tabela-dados");
    if (!table) return;
    const tbody = table.getElementsByTagName("tbody")[0];
    const todasAsLinhas = tbody.querySelectorAll("tr:not(.linha-raio-x-container)");
    const linhasValidas = Array.from(todasAsLinhas).filter(tr => !tr.classList.contains("filtrado-escondido"));
    
    // CORREÇÃO: Respeita a escolha do utilizador na Pesquisa Avançada ou usa o padrão 25
    const limiteLinhas = window.LINHAS_POR_PAGINA || 25;
    const totalPaginas = Math.ceil(linhasValidas.length / limiteLinhas);
    const container = document.getElementById("paginacao-container");
    if (!container) return;
    
    container.innerHTML = "";
    
    for (let i = 0; i < todasAsLinhas.length; i++) { 
        if (todasAsLinhas[i].classList.contains("filtrado-escondido")) { 
            todasAsLinhas[i].style.display = "none"; 
        } 
    }
    
    if (totalPaginas <= 1) { 
        linhasValidas.forEach(tr => tr.style.display = ""); 
        return; 
    }
    
    function renderizarNavegacao(numPagina) {
        paginaAtual = numPagina;
        const inicio = (numPagina - 1) * limiteLinhas;
        const fim = inicio + limiteLinhas;
        
        linhasValidas.forEach((tr, index) => { 
            tr.style.display = (index >= inicio && index < fim) ? "" : "none"; 
        });
        
        container.innerHTML = "";
        
        function criarBotao(texto, destino, desativado = false, ativo = false) {
            const btn = document.createElement("button");
            btn.type = "button"; // Garante que não submete formulários por engano
            btn.innerText = texto; 
            btn.className = "btn"; 
            btn.style.padding = "6px 12px"; 
            btn.style.margin = "0 2px";
            btn.style.cursor = desativado ? "default" : "pointer"; 
            btn.disabled = desativado;
            
            if (ativo) { 
                btn.style.background = "#3b82f6"; 
                btn.style.color = "white"; 
            } else if (desativado) { 
                btn.style.background = "#f8fafc"; 
                btn.style.color = "#cbd5e1"; 
            } else { 
                btn.style.background = "#f1f5f9"; 
                btn.style.color = "#334155"; 
            }
            
            if (!desativado && !ativo) { 
                btn.onclick = function(e) { 
                    if(e) e.preventDefault();
                    renderizarNavegacao(destino); 
                }; 
            }
            container.appendChild(btn);
        }
        
        criarBotao("|<<", 1, paginaAtual === 1);
        criarBotao("<", paginaAtual - 1, paginaAtual === 1);
        let inicioJanela = Math.max(1, paginaAtual - 2);
        let fimJanela = Math.min(totalPaginas, paginaAtual + 2);
        for (let i = inicioJanela; i <= fimJanela; i++) { criarBotao(i, i, false, i === paginaAtual); }
        criarBotao(">", paginaAtual + 1, paginaAtual === totalPaginas);
        criarBotao(">>|", totalPaginas, paginaAtual === totalPaginas);
    }
    renderizarNavegacao(1);
}

function confirmarEliminacao() { 
    return confirm("Tem a certeza absoluta que deseja eliminar este registo? Esta ação não pode ser revertida."); 
}

// graficos no index
let linhaContainerAtiva = null;
let idHospitalAtivo = null;

function fecharRaioXInline() {
    if (linhaContainerAtiva) { linhaContainerAtiva.remove(); linhaContainerAtiva = null; idHospitalAtivo = null; }
}

function carregarRaioXHospital(hospitalId, elementoTr) {  
    if (idHospitalAtivo === hospitalId) { fecharRaioXInline(); return; }
    fecharRaioXInline();
    const numeroColunas = elementoTr.cells.length;

    fetch(`/api/hospital/${hospitalId}/details`)
        .then(response => response.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            linhaContainerAtiva = document.createElement('tr');
            linhaContainerAtiva.className = 'linha-raio-x-container';
            linhaContainerAtiva.onclick = (e) => e.stopPropagation(); 
            
            const tdGigante = document.createElement('td');
            tdGigante.colSpan = numeroColunas;
            tdGigante.style.padding = "0"; 
            tdGigante.style.background = "#f8fafc";

            let template = document.getElementById('template_raio_x');
            if (!template) {
                template = document.createElement('template');
                template.id = 'template_raio_x';
                template.innerHTML = `
                    <div id="painel_raio_x" style="background:#f8fafc;border-radius:20px;padding:28px;border:1px solid #e2e8f0;margin:15px 10px;box-shadow:inset 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;">
                            <div>
                                <span style="background:#e0f2fe;color:#0369a1;padding:5px 12px;border-radius:6px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Filtro de Unidade Ativo</span>
                                <h2 id="rx_hospital_title" style="margin:6px 0 0 0;color:#0f172a;font-size:1.4rem;font-weight:800;">Nome do Hospital</h2>
                            </div>
                            <button onclick="fecharRaioXInline()" style="background:white;border:1px solid #cbd5e1;padding:6px 12px;border-radius:8px;font-size:0.78rem;font-weight:600;color:#64748b;cursor:pointer;">Fechar Raio-X</button>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:25px;">
                            <div style="background:white;padding:18px;border-radius:12px;border:1px solid #f1f5f9;"><p style="margin:0;font-size:0.78rem;color:#64748b;font-weight:600;">Custo Máximo p/ Intervenção</p><h4 id="kpi_rx_max" style="margin:6px 0 0 0;font-size:1.25rem;color:#ef4444;font-weight:800;">0.00 €</h4></div>
                            <div style="background:white;padding:18px;border-radius:12px;border:1px solid #f1f5f9;"><p style="margin:0;font-size:0.78rem;color:#64748b;font-weight:600;">Custo Médio p/ Operação</p><h4 id="kpi_rx_avg" style="margin:6px 0 0 0;font-size:1.25rem;color:#3b82f6;font-weight:800;">0.00 €</h4></div>
                            <div style="background:white;padding:18px;border-radius:12px;border:1px solid #f1f5f9;"><p style="margin:0;font-size:0.78rem;color:#64748b;font-weight:600;">Custo Mínimo de Registo</p><h4 id="kpi_rx_min" style="margin:6px 0 0 0;font-size:1.25rem;color:#10b981;font-weight:800;">0.00 €</h4></div>
                        </div>
                        <div style="display:grid;grid-template-columns:1.3fr 1fr;gap:25px;">
                            <div style="background:white;padding:22px;border-radius:14px;border:1px solid #f1f5f9;"><h4 style="margin:0 0 4px 0;font-size:0.95rem;color:#0f172a;font-weight:700;">Rastreabilidade de Fluxo Financeiro (Sankey)</h4><div id="chart_rx_sankey" style="width:100%;height:320px;"></div></div>
                            <div style="background:white;padding:22px;border-radius:14px;border:1px solid #f1f5f9;"><h4 style="margin:0 0 4px 0;font-size:0.95rem;color:#0f172a;font-weight:700;">Curva de Consumo Mensal Histórico</h4><div id="chart_rx_timeline" style="width:100%;height:320px;"></div></div>
                        </div>
                    </div>`;
                document.body.appendChild(template);
            }
            const clone = template.content.cloneNode(true);
            tdGigante.appendChild(clone);
            linhaContainerAtiva.appendChild(tdGigante);
            elementoTr.parentNode.insertBefore(linhaContainerAtiva, elementoTr.nextSibling);
            idHospitalAtivo = hospitalId;

            document.getElementById('rx_hospital_title').innerText = `Raio-X Orçamental: ${data.hospital_name}`;
            document.getElementById('kpi_rx_max').innerText = data.kpis.max.toLocaleString('pt-PT', { style: 'currency', currency: 'EUR' });
            document.getElementById('kpi_rx_avg').innerText = data.kpis.avg.toLocaleString('pt-PT', { style: 'currency', currency: 'EUR' });
            document.getElementById('kpi_rx_min').innerText = data.kpis.min.toLocaleString('pt-PT', { style: 'currency', currency: 'EUR' });

            linhaContainerAtiva.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            if (!data.has_data) {
                document.getElementById('chart_rx_sankey').innerHTML = "<p style='text-align:center; padding-top:100px; color:#94a3b8;'>Sem registos de utilização nesta unidade.</p>";
                return;
            }

            const dataSankey = [{
                type: "sankey",
                orientation: "h",
                node: {
                    pad: 15, thickness: 18,
                    line: { color: "rgba(15, 23, 42, 0.08)", width: 0.5 },
                    label: data.sankey.labels,
                    color: data.sankey.labels.map((_, i) => i === 0 ? "#0f172a" : i < 5 ? "rgba(59, 130, 246, 0.8)" : "rgba(16, 185, 129, 0.7)")
                },
                link: { source: data.sankey.sources, target: data.sankey.targets, value: data.sankey.values, color: "rgba(226, 232, 240, 0.4)" }
            }];
            Plotly.newPlot('chart_rx_sankey', dataSankey, { font: { family: "'Inter', sans-serif", size: 10 }, margin: { t: 10, b: 10, l: 10, r: 10 } }, { responsive: true, displayModeBar: false });

            const dataTimeline = [{ x: data.timeline.x, y: data.timeline.y, type: 'scatter', mode: 'lines+markers', line: { color: '#4f46e5', width: 2.5 } }];
            Plotly.newPlot('chart_rx_timeline', dataTimeline, { font: { family: "'Inter', sans-serif" }, margin: { t: 15, b: 40, l: 55, r: 15 }, xaxis: { type: 'category' } }, { responsive: true, displayModeBar: false });
        });
}

window.linhaSatAtiva = null;
window.idDeptAtivo = null;

function fecharSaturacaoInline() {
    if (window.linhaSatAtiva) { window.linhaSatAtiva.remove(); window.linhaSatAtiva = null; window.idDeptAtivo = null; }
}

function carregarSaturacaoDepartamento(elementoTr) {
    const deptId = parseInt(elementoTr.getAttribute('data-id'));
    const deptTitle = elementoTr.getAttribute('data-title');
    if (window.idDeptAtivo === deptId) { fecharSaturacaoInline(); return; }
    fecharSaturacaoInline();

    fetch(`/api/department/${deptId}/saturation`)
        .then(response => response.json())
        .then(data => {
            if (data.error) { alert(data.error); return; }
            window.linhaSatAtiva = document.createElement('tr');
            window.linhaSatAtiva.className = 'linha-raio-x-container';
            const tdGigante = document.createElement('td');
            tdGigante.colSpan = elementoTr.cells.length;
            tdGigante.style.padding = "0";

            let template = document.getElementById('template_saturacao_dept');
            if (!template) {
                template = document.createElement('template');
                template.id = 'template_saturacao_dept';
                template.innerHTML = `
                    <div id="painel_saturacao_dept" style="background:#fff7ed;border-radius:20px;padding:28px;border:1px solid #ffedd5;margin:15px 10px;box-shadow:inset 0 2px 4px rgba(0,0,0,0.01);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                            <div>
                                <span style="background:#ffedd5;color:#ea580c;padding:5px 12px;border-radius:6px;font-size:0.75rem;font-weight:700;text-transform:uppercase;">Benchmark de Carga</span>
                                <h2 id="sat_dept_title" style="margin:6px 0 0 0;color:#0f172a;font-size:1.35rem;font-weight:800;"></h2>
                            </div>
                            <button onclick="fecharSaturacaoInline()" style="background:white;border:1px solid #f97316;padding:6px 12px;border-radius:8px;font-size:0.78rem;font-weight:600;color:#ea580c;cursor:pointer;">Fechar Análise</button>
                        </div>
                        <div style="background:white;padding:24px;border-radius:14px;border:1px solid #f1f5f9;"><div id="chart_sat_dept_plotly" style="width:100%;height:180px;"></div></div>
                    </div>`;
                document.body.appendChild(template);
            }
            tdGigante.appendChild(template.content.cloneNode(true));
            window.linhaSatAtiva.appendChild(tdGigante);
            elementoTr.parentNode.insertBefore(window.linhaSatAtiva, elementoTr.nextSibling);
            window.idDeptAtivo = deptId;

            document.getElementById('sat_dept_title').innerText = `Análise de Desvio: ${deptTitle}`;
            window.linhaSatAtiva.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            if (!data.has_data) {
                document.getElementById('chart_sat_dept_plotly').innerHTML = "<div style='text-align:center; padding:40px; color:#64748b;'>✔️ Departamento estável.</div>";
                return;
            }

            Plotly.newPlot('chart_sat_dept_plotly', [{
                x: [data.desvio_perc], y: [data.hospital_name], type: 'bar', orientation: 'h', marker: { color: '#ea580c' }
            }], { margin: { t: 15, b: 35, l: 140, r: 60 } }, { responsive: true, displayModeBar: false });
        });
}

// graficos /stats
function inicializarGraficosStats(c1Data, c2Data, pareto, custoVolume, paretoAvg, paretoMedian) {
    const baseLayoutStyles = {
        font: { family: "'Inter', sans-serif", color: '#64748b', size: 11 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 40, b: 60, l: 65, r: 65 },
        hovermode: 'x unified',
        xaxis: { 
            gridcolor: '#f8fafc', 
            zeroline: false, 
            type: 'category', 
            linecolor: '#e2e8f0', 
            tickangle: -45, 
            tickfont: { size: 10, color: '#94a3b8' } 
        }
    };

    if (c1Data && c1Data.length > 0) {
        const xLabels = c1Data.map(d => d.period);
        Plotly.newPlot('chart_macro_dual', [
            { x: xLabels, y: c1Data.map(d => d.total), type: 'scatter', mode: 'lines+markers', name: 'Gasto Global Sistema', line: { color: '#0f172a', width: 2.5 }, marker: { size: 4 }, yaxis: 'y1', hovertemplate: '%{y:,.2f} €<extra></extra>' },
            { x: xLabels, y: c1Data.map(d => d.cost_per_use), type: 'scatter', mode: 'lines', name: 'Custo por Utilização Individual', line: { color: '#3b82f6', width: 2, dash: 'dash' }, yaxis: 'y2', hovertemplate: '%{y:,.2f} €/registo<extra></extra>' }
        ], {
            ...baseLayoutStyles,
            showlegend: false,
            margin: { t: 20, b: 40, l: 70, r: 70 },
            yaxis: { title: { text: 'Encargos Globais (€)', font: { size: 10, weight: 600 } }, gridcolor: '#f1f5f9', zeroline: true, rangemode: 'tozero' },
            yaxis2: { title: { text: 'Custo Unitário Clínica (€)', font: { size: 10, weight: 600 } }, overlaying: 'y', side: 'right', zeroline: false, rangemode: 'tozero', gridcolor: 'rgba(0,0,0,0)', tickfont: { color: '#3b82f6' } }
        }, { responsive: true, displayModeBar: false });
    }

    if (c2Data && c2Data.length > 0) {
        const xLabels = c2Data.map(d => d.period);
        Plotly.newPlot('chart_volatilidade_bandas', [
            { x: xLabels, y: c2Data.map(d => d.min_val), type: 'scatter', mode: 'lines', name: 'Mínimo Operacional', line: { width: 0 }, text: c2Data.map(d => d.min_name), hovertemplate: 'Chão: %{text} (%{y:,.2f} €)', showlegend: false },
            { x: xLabels, y: c2Data.map(d => d.max_val), type: 'scatter', mode: 'lines', name: 'Janela de Dispersão da Rede', fill: 'tonexty', fillcolor: 'rgba(59, 130, 246, 0.05)', line: { width: 0 }, text: c2Data.map(d => d.max_name), hovertemplate: 'Teto: %{text} (%{y:,.2f} €)' },
            { x: xLabels, y: c2Data.map(d => d.avg), type: 'scatter', mode: 'lines+markers', name: 'Média por Unidade Hospitalar', line: { color: '#4f46e5', width: 2 }, marker: { size: 4 }, hovertemplate: 'Média: %{y:,.2f} €' }
        ], {
            ...baseLayoutStyles,
            showlegend: false,
            margin: { t: 20, b: 40, l: 70, r: 25 },
            yaxis: { gridcolor: '#f1f5f9', zeroline: true, rangemode: 'tozero' }
        }, { responsive: true, displayModeBar: false });
    }

    if (pareto && pareto.length > 0) {
        const devLabels = pareto.map(d => d.category);
        const devValues = pareto.map(d => d.cost);

        Plotly.newPlot('chart_devices_clean', [
            { 
                type: 'bar', 
                orientation: 'h', 
                x: devValues, 
                y: devLabels, 
                marker: { color: '#2563eb', line: { color: '#1d4ed8', width: 1 } }, 
                texttemplate: '  %{y} - Total: %{x:,.2f} €',
                textposition: 'inside', 
                insidetextanchor: 'start', 
                font: { color: '#ffffff', size: 11, weight: 600 }, 
                hoverinfo: 'none'
            }
        ], {
            ...baseLayoutStyles,
            showlegend: false,
            hovermode: false, 
            margin: { t: 40, b: 40, l: 20, r: 40 }, 
            xaxis: { type: 'linear', gridcolor: '#f8fafc', zeroline: false, rangemode: 'tozero', tickfont: { size: 10 }, tickangle: 0 },
            yaxis: { type: 'category', autorange: 'reversed', gridcolor: 'rgba(0,0,0,0)', showticklabels: false },
            shapes: [
                { type: 'line', xref: 'x', yref: 'paper', x0: paretoAvg, x1: paretoAvg, y0: 0, y1: 1, line: { color: '#ef4444', width: 1.5, dash: 'dash' } },
                { type: 'line', xref: 'x', yref: 'paper', x0: paretoMedian, x1: paretoMedian, y0: 0, y1: 1, line: { color: '#10b981', width: 1.5, dash: 'dot' } }
            ],
            annotations: [
                { x: paretoAvg, y: 1.05, yref: 'paper', xref: 'x', text: `Média: ${(paretoAvg/1000000).toFixed(2)}M €`, showarrow: false, font: { color: '#ef4444', size: 10, weight: 600 }, xanchor: 'center', yanchor: 'bottom' },
                { x: paretoMedian, y: -0.08, yref: 'paper', xref: 'x', text: `Mediana: ${(paretoMedian/1000000).toFixed(2)}M €`, showarrow: false, font: { color: '#10b981', size: 10, weight: 600 }, xanchor: 'center', yanchor: 'top' }
            ]
        }, { responsive: true, displayModeBar: false });
    }

    if (custoVolume && custoVolume.length > 0) {
        Plotly.newPlot('chart_scatter_clean', [{
            x: custoVolume.map(v => parseInt(v.num_utilizacoes) || 0),
            y: custoVolume.map(v => parseFloat(v.custo_total) || 0),
            mode: 'markers',
            type: 'scatter',
            text: custoVolume.map(v => v.hospital_name),
            marker: { size: 8, color: 'rgba(139, 92, 246, 0.15)', line: { color: '#8b5cf6', width: 1.2 } },
            hovertemplate: '<b>%{text}</b><br>Utilizações: %{x}<br>Custos: %{y:,.2f} €<extra></extra>'
        }], {
            ...baseLayoutStyles,
            margin: { t: 20, b: 40, l: 70, r: 20 },
            xaxis: { type: 'linear', tickangle: 0, title: { text: 'Volume de Intervenções (Registos)', font: { size: 10 } }, rangemode: 'tozero' },
            yaxis: { type: 'linear', gridcolor: '#f1f5f9', rangemode: 'tozero' }
        }, { responsive: true, displayModeBar: false });
    }
}

function alterarMetaOrcamento(percentagem, elementoBotao) {
    const chartDiv = document.getElementById('chart_devices_clean');
    if (!chartDiv || !chartDiv.data) return;
    
    const devValues = chartDiv.data[0].x;
    const maxValue = Math.max(...devValues);
    const novaMeta = maxValue * percentagem;
    
    const novasCores = devValues.map(v => v > novaMeta ? 'rgba(239, 68, 68, 0.85)' : '#f1f5f9');
    
    Plotly.relayout('chart_devices_clean', { 'shapes[0].x0': novaMeta, 'shapes[0].x1': novaMeta });
    Plotly.restyle('chart_devices_clean', { 'marker.color': [novasCores] });

    const botoes = elementoBotao.parentElement.getElementsByClassName('threshold-btn');
    for (let btn of botoes) { btn.classList.remove('active'); }
    elementoBotao.classList.add('active');
}



function buildFilterRow() {
    const attributes = window.APP_ATTRIBUTES || [];
    const opts = attributes.map(a =>
        `<option value="${a}">${a.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</option>`
    ).join('');
    
    const ops = [
        ['contains','Contém'],['equals','Igual a'],['starts','Começa por'],
        ['ends','Termina em'],['gt','Maior que'],['lt','Menor que']
    ].map(([v,l])=>`<option value="${v}">${l}</option>`).join('');

    const row = document.createElement('div');
    row.className = 'filter-row';
    row.style = 'display:grid; grid-template-columns:1fr 160px 2fr auto; gap:10px; align-items:end; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; margin-bottom:10px;';
    row.innerHTML = `
        <div class="form-group" style="margin:0;">
            <label style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Atributo</label>
            <select name="att[]" style="padding:8px 10px;font-size:0.9rem;">${opts}</select>
        </div>
        <div class="form-group" style="margin:0;">
            <label style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Operador</label>
            <select name="op[]" style="padding:8px 10px;font-size:0.9rem;">${ops}</select>
        </div>
        <div class="form-group" style="margin:0;">
            <label style="font-size:0.72rem;color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Valor</label>
            <input type="text" name="value[]" placeholder="Escreve o que procuras..." style="padding:8px 10px;font-size:0.9rem;">
        </div>
        <button type="button" onclick="removeFilter(this)" style="background:none;border:1px solid #fca5a5;color:#ef4444;border-radius:7px;width:36px;height:36px;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;flex-shrink:0;align-self:flex-end;">✕</button>
    `;
    return row;
}

function addFilter() {
    const container = document.getElementById('filters-container');
    if (container) {
        container.appendChild(buildFilterRow());
        updateRemoveButtons();
    }
}

function removeFilter(btn) {
    btn.closest('.filter-row').remove();
    updateRemoveButtons();
}

function updateRemoveButtons() {
    const rows = document.querySelectorAll('.filter-row');
    rows.forEach(row => {
        row.querySelector('button').style.visibility = rows.length === 1 ? 'hidden' : 'visible';
    });
}