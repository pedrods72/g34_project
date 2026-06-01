# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:18:54 2026

@author: pedro
"""
# interface do site onde há display dos nossos dados

from flask import Flask, render_template, request, session, flash, redirect, url_for
import sqlite3
import os
from classes.hospital import Hospital
from classes.department import Department
from classes.device import Device
from classes.utilization import Utilization
from classes.userlogin import Userlogin
import pandas as pd
import plotly.express as px  # Adicionado para os gráficos interativos

appy = Flask(__name__)
appy.config["TEMPLATES_AUTO_RELOAD"] = True          # reload automático de templates
appy.secret_key = 'CHAVE_SECRETA_HOSPITAL'
appy.jinja_env.globals['getattr'] = getattr          # getattr disponível nos templates Jinja

# assim o Flask procura a base de dados exatamente na mesma pasta onde
# o ficheiro app.py está guardado, independentemente do terminal.
db_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'HospitalData.db')

# lê os dados
Userlogin.read(db_name)
Hospital.read(db_name)
Department.read(db_name)
Device.read(db_name)
Utilization.read(db_name)

prev_option = ""

# mapear os nomes da string
classes_map = {
    "Hospital":    Hospital,
    "Department":  Department,
    "Device":      Device,
    "Utilization": Utilization,
    "Userlogin":   Userlogin
}


@appy.route("/login")
def login():
    return render_template("login.html", id=0, user="", password="",
                           ulogin=session.get("user"), resul="")

@appy.route("/logoff")
def logoff():
    session.pop("user", None)
    return redirect(url_for('home'))

@appy.route("/chklogin", methods=["post", "get"])
def chklogin():
    user     = request.form["user"]
    password = request.form["password"]
    resul    = Userlogin.chk_password(user, password)
    if resul == "Valid":
        session["user"] = user
        return redirect(url_for('stats'))
    return render_template("login.html", user=user, password=password,
                           ulogin=session.get("user"), resul=resul)


# pandas

def tendencias_mensais():
    if not Utilization.lst:
        return []

    df_util = pd.DataFrame([{
        'date':   u.utilization_date,
        'amount': u.amount
    } for u in Utilization.obj.values()])

    df_util['period'] = pd.to_datetime(df_util['date']).dt.to_period('M').astype(str)

    df_monthly = (df_util
                  .groupby('period')['amount']
                  .sum()
                  .reset_index()
                  .sort_values('period'))

    df_monthly['growth'] = df_monthly['amount'].pct_change() * 100
    df_monthly['growth'] = df_monthly['growth'].fillna(0).round(2)
    df_monthly = df_monthly.rename(columns={'amount': 'total'})

    return df_monthly.to_dict(orient='records')


def gastos_dispositivos():
    if not Utilization.lst:
        return []

    dados = []
    for u in Utilization.obj.values():
        categoria = Device.obj[u.device_id].category if u.device_id in Device.obj else "Desconhecido"
        dados.append({'category': categoria, 'amount': u.amount})

    df = pd.DataFrame(dados)
    df_cat = (df.groupby('category')['amount']
                .sum()
                .reset_index()
                .rename(columns={'amount': 'cost'})
                .sort_values(by='cost', ascending=False))

    total_global = df_cat['cost'].sum()
    df_cat['cumsum']     = df_cat['cost'].cumsum()
    df_cat['perc_accum'] = (df_cat['cumsum'] / total_global) * 100
    df_cat['is_critical'] = df_cat['perc_accum'] <= 80

    return df_cat.to_dict(orient='records')


def eficiencia_hospitais():
    if not Department.lst:
        return []

    df_depts = pd.DataFrame([{
        'hospital_id': d.hospital_id,
        'dept_id':     d.id
    } for d in Department.obj.values()])

    contagem_depts = df_depts.groupby('hospital_id').size().reset_index(name='depts')

    gastos_lista = []
    for u in Utilization.obj.values():
        if u.department_id in Department.obj:
            h_id = Department.obj[u.department_id].hospital_id
            gastos_lista.append({'hospital_id': h_id, 'amount': u.amount})

    df_gastos   = pd.DataFrame(gastos_lista)
    soma_gastos = df_gastos.groupby('hospital_id')['amount'].sum().reset_index(name='total_spend')

    df_hospitais = pd.DataFrame([{
        'hospital_id': h.id,
        'name':        h.name
    } for h in Hospital.obj.values()])

    df_final = df_hospitais.merge(contagem_depts, on='hospital_id', how='left')
    df_final = df_final.merge(soma_gastos,        on='hospital_id', how='left')

    df_final['depts']       = df_final['depts'].fillna(0).astype(int)
    df_final['total_spend'] = df_final['total_spend'].fillna(0)
    df_final['avg_per_dept'] = df_final.apply(
        lambda r: round(r['total_spend'] / r['depts'], 2) if r['depts'] > 0 else 0, axis=1
    )
    df_final = df_final.sort_values(by='avg_per_dept', ascending=False)

    return df_final[['name', 'depts', 'total_spend', 'avg_per_dept']].to_dict(orient='records')


# antigo analise_hospitalar.py autoria: stockler

def criar_grafico_gastos_plotly(dados_gastos):
    if not dados_gastos:
        return "<p>Sem dados para gerar gráfico.</p>"
    df = pd.DataFrame(dados_gastos)
    fig = px.bar(df, x='category', y='cost',
                 title="Custos por Categoria de Dispositivo",
                 labels={'category': 'Categoria', 'cost': 'Custo Total (€)'},
                 color='cost', color_continuous_scale='Blues')
    return fig.to_html(full_html=False)


def criar_grafico_tendencias(dados_trends):
    if not dados_trends:
        return ""
    df = pd.DataFrame(dados_trends)
    fig = px.line(df, x='period', y='total', 
                  title="Evolução Mensal de Utilização",
                  markers=True)
    return fig.to_html(full_html=False)


def grafico_rentabilidade_dispositivos(utilization_cls, device_cls):
    if not utilization_cls.lst or not device_cls.lst:
        return "<p>Sem dados para gerar gráfico de rentabilidade.</p>"
    df_util = pd.DataFrame([{'dev_id': u.device_id, 'amt': u.amount} for u in utilization_cls.obj.values()])
    df_dev = pd.DataFrame([{'id': d.id, 'cat': d.category} for d in device_cls.obj.values()])
  
    df = pd.merge(df_util, df_dev, left_on='dev_id', right_on='id')
    resumo = df.groupby('cat').agg({'amt': 'sum', 'dev_id': 'count'}).reset_index()
    resumo.columns = ['Categoria', 'Custo_Total', 'Frequencia']
    
    fig = px.scatter(resumo, x="Frequencia", y="Custo_Total", size="Custo_Total", 
                     color="Categoria", hover_name="Categoria",
                     title="Análise de Rentabilidade: Uso vs Investimento")
    return fig.to_html(full_html=False)


def detetar_alertas_gastos(efficiency_data):
    if not efficiency_data:
        return []
    df = pd.DataFrame(efficiency_data)
    limite = df['total_spend'].mean() * 1.2
    alertas = df[df['total_spend'] > limite]
    return alertas[['name', 'total_spend']].to_dict(orient='records')


# atalhos

@appy.route("/stats")
def stats():
    if not session.get("user"):
        return redirect(url_for('login'))

    # --- KPIs ---
    total_hospitais     = len(Hospital.lst)
    total_departamentos = len(Department.lst)
    total_devices       = len(Device.lst)
    total_utilizacoes   = len(Utilization.lst)
    total_amount        = sum(Utilization.obj[i].amount for i in Utilization.lst)
    avg_amount          = round(total_amount / total_utilizacoes, 2) if total_utilizacoes else 0
    total_amount_fmt    = f"{total_amount:,}€".replace(",", " ")

   
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    
    cur.execute('''
        SELECT d.title, d.extra_info, h.name,
               (SELECT dev2.category
                FROM Utilization u2
                JOIN Device dev2 ON u2.device_id = dev2.id
                WHERE u2.department_id = d.id
                GROUP BY dev2.category
                ORDER BY SUM(u2.amount) DESC LIMIT 1) AS top_cat,
               SUM(u.amount) AS total
        FROM Utilization u
        JOIN Department d ON u.department_id = d.id
        JOIN Hospital  h ON d.hospital_id   = h.id
        GROUP BY d.id
        ORDER BY total DESC
        LIMIT 10
    ''')
    dept_rows           = cur.fetchall()
    top_depts_labels    = [r[0] for r in dept_rows]
    top_depts_hospitals = [r[2] for r in dept_rows]
    top_depts_values    = [r[4] for r in dept_rows]
    top_depts_table     = [
        {"dept_title":    r[0],
         "extra_info":    r[1],
         "hospital_name": r[2],
         "top_category":  r[3] or "—",
         "total_amount":  r[4]}
        for r in dept_rows
    ]

    
    cur.execute('''
        SELECT strftime('%Y', utilization_date), SUM(amount)
        FROM Utilization
        GROUP BY strftime('%Y', utilization_date)
        ORDER BY 1
    ''')
    anual_rows   = cur.fetchall()
    anual_labels = [r[0] for r in anual_rows]
    anual_values = [r[1] for r in anual_rows]

    
    cur.execute('''
        SELECT h.name, SUM(u.amount) AS total
        FROM Utilization u
        JOIN Department d ON u.department_id = d.id
        JOIN Hospital   h ON d.hospital_id   = h.id
        GROUP BY h.id
        ORDER BY total DESC
        LIMIT 15
    ''')
    hosp_rows   = cur.fetchall()
    hosp_labels = [r[0] for r in hosp_rows]
    hosp_values = [r[1] for r in hosp_rows]

    con.close()


    trends     = tendencias_mensais()
    pareto     = gastos_dispositivos()
    efficiency = eficiencia_hospitais()

    
    alertas               = detetar_alertas_gastos(efficiency)

    return render_template("stats.html",
        ulogin=session.get('user'),
        # números
        total_hospitais=total_hospitais,
        total_departamentos=total_departamentos,
        total_devices=total_devices,
        total_utilizacoes=total_utilizacoes,
        total_amount_fmt=total_amount_fmt,
        avg_amount=avg_amount,
        trends=trends,
        pareto=pareto,
        efficiency=efficiency,
        alertas=alertas,
        # gráficos estáticos antigos / dados raw
        top_depts_labels=top_depts_labels,
        top_depts_hospitals=top_depts_hospitals,
        top_depts_values=top_depts_values,
        anual_labels=anual_labels,
        anual_values=anual_values,
        hosp_labels=hosp_labels,
        hosp_values=hosp_values,
        # tabelas
        top_depts_table=top_depts_table
    )


@appy.route("/search") # autoria: couto
def search():
    appy.jinja_env.globals.update(hasattr=hasattr)
    current_user_obj = Userlogin.find(session.get("user"), 'user')
    user_group = current_user_obj[0].usergroup if current_user_obj else ""
    class_name = request.args.get('class', 'Hospital')
    cls = classes_map.get(class_name)
    if cls is None: return redirect('/')

    attributes = [a[1:] for a in cls.att[1:]]
    # Adicionamos os nomes virtuais para poder selecionar no formulário
    if class_name == 'Utilization':
        attributes.extend(['department_name', 'device_name', 'hospital_name'])

    atts = request.args.getlist('att[]')
    ops = request.args.getlist('op[]')
    values = request.args.getlist('value[]')

    sort_by = request.args.get('sort_by', '')
    sort_dir = request.args.get('sort_dir', 'asc')
    per_page = int(request.args.get('per_page', 10))

    results = [cls.obj[id] for id in cls.lst]

    for att, op, value in zip(atts, ops, values):
        if not value: continue
        filtered = []
        for obj in results:
            # Lógica para obter o valor correto (seja ID ou Nome)
            if att == 'department_name': obj_val = getattr(obj, 'department_name', "")
            elif att == 'device_name': obj_val = getattr(obj, 'device_name', "")
            elif att == 'hospital_name': obj_val = getattr(obj, 'hospital_name', "")
            else: obj_val = getattr(obj, '_' + att, None)
            
            if obj_val is None: continue
            
            obj_str = str(obj_val).lower()
            val_str = value.strip().lower()
            
            ok = False
            match op:
                case 'contains': ok = val_str in obj_str
                case 'equals': ok = obj_str == val_str
                case 'starts': ok = obj_str.startswith(val_str)
                case 'ends': ok = obj_str.endswith(val_str)
                case 'gt':
                    try: ok = float(obj_val) > float(value)
                    except: ok = obj_str > val_str
                case 'lt':
                    try: ok = float(obj_val) < float(value)
                    except: ok = obj_str < val_str
            if ok: filtered.append(obj)
        results = filtered

    return render_template('search.html', class_name=class_name, attributes=attributes, 
                           results=results, att=atts[0] if atts else '', 
                           op=ops[0] if ops else 'contains', value=values[0] if values else '',
        sort_by=sort_by,
        sort_dir=sort_dir,
        per_page=per_page,
        ulogin=session.get("user"),
        user_group=user_group
    )


@appy.route("/index", methods=["post", "get"]) # autoria: martim
def index():
    global prev_option

    if not session.get("user"):
        return redirect(url_for('home'))
    
    current_user_obj = Userlogin.find(session.get("user"), 'user')
    user_group = current_user_obj[0].usergroup if current_user_obj else ""

    current_class_name = request.args.get("class", session.get("current_class", "Hospital"))
    session["current_class"] = current_class_name
    cl = classes_map[current_class_name]

    butshow, butedit = "enabled", "disabled"
    show_list = False
    list_data = []
    option = request.args.get("option")

    if option == "edit":
        butshow, butedit = "disabled", "enabled"

    elif option == "delete":
        obj = cl.current()
        if obj:
            cl.remove(obj.id)
            if not cl.previous():
                cl.first()

    elif option == "insert":
        butshow, butedit = "disabled", "enabled"

    elif option == 'cancel':
        pass

    elif prev_option == 'insert' and option == 'save':
        try:
            data = ["0"]
            for attribute in cl.att[1:]:
                field_name = attribute[1:]
                data.append(request.form.get(field_name, ""))
            strobj = ";".join(data)
            obj = cl.from_string(strobj)
            cl.insert(obj.id)
            cl.last()
            flash("Registo inserido com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao inserir: {e}", "error")

    elif prev_option == 'edit' and option == 'save':
        try:
            obj = cl.current()
            for attribute in cl.att[1:]:
                field_name = attribute[1:]
                if field_name in request.form:
                    setattr(obj, attribute, request.form[field_name])
            cl.update(int(obj.id))
            flash("Registo atualizado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "error")

    elif option == "list":
        show_list = True
        list_data = []
        for id in cl.lst:
            row = {}
            for att in cl.att:
                key = att[1:]
                if current_class_name == 'Userlogin' and key == 'password':
                    row[key] = '(Oculto)'
                else:
                    row[key] = getattr(cl.obj[id], att)
            list_data.append(row)

    elif option == "first":    cl.first()
    elif option == "previous": cl.previous()
    elif option == "next":     cl.nextrec()
    elif option == "last":     cl.last()
    elif option == 'exit':
        return "<h1>Base de Dados Hospitalar Fechada.</h1>"

    prev_option = option
    obj = cl.current()

    if option == 'insert' or len(cl.lst) == 0:
        obj_id = cl.get_id(0)
        fields = {att[1:]: "" for att in cl.att}
    else:
        obj_id = obj.id
        fields = {att[1:]: getattr(obj, att[1:]) for att in cl.att}

    return render_template("index.html",
                           hospitais_todos=Hospital.obj.values(),
                           depts_todos=Department.obj.values(),
                           devices_todos=Device.obj.values(),
                           utilizacoes_todos=Utilization.obj.values(),
                           Hospital=Hospital,
                           Department=Department,
                           Device=Device,
                           Utilization=Utilization,
                           Userlogin=Userlogin,
                           class_name=current_class_name,
                           id=obj_id,
                           fields=fields,
                           header=cl.header,
                           titles=cl.des,
                           butshow=butshow,
                           butedit=butedit,
                           show_list=show_list,
                           list_data=list_data,
                           ulogin=session.get("user"),
                           user_group=user_group)
# autoria: tiago
@appy.route("/")
def home():
    if not session.get("user"):
        return render_template("home.html")
    else:
        return redirect(url_for('stats'))


@appy.route('/api/hospital/<int:hospital_id>/details')
def api_hospital_details(hospital_id):
    if not session.get("user"):
        from flask import jsonify
        return jsonify({"error": "Sessão expirada"}), 401

    if hospital_id not in Hospital.obj:
        from flask import jsonify
        return jsonify({"error": "Hospital não encontrado"}), 404

    hosp = Hospital.obj[hospital_id]
    
    # 1. Filtrar departamentos e utilizações desta unidade
    depts_da_unidade = [d.id for d in Department.obj.values() if d.hospital_id == hospital_id]
    utils_da_unidade = [u for u in Utilization.obj.values() if u.department_id in depts_da_unidade]

    from flask import jsonify
    response_data = {
        "hospital_name": hosp.name,
        "has_data": False,
        "kpis": {"max": 0, "avg": 0, "min": 0},
        "sankey": {"labels": [], "sources": [], "targets": [], "values": []},
        "timeline": {"x": [], "y": []}
    }

    if not utils_da_unidade:
        return jsonify(response_data)

    # Converter para DataFrame Pandas para análise avançada
    df = pd.DataFrame([{
        'dept_id': u.department_id,
        'device_id': u.device_id,
        'amount': u.amount,
        'date': u.utilization_date
    } for u in utils_da_unidade])

    response_data["has_data"] = True
    response_data["kpis"] = {
        "max": float(df['amount'].max()),
        "avg": round(float(df['amount'].mean()), 2),
        "min": float(df['amount'].min())
    }

    # --- PROCESSAR DIAGRAMA DE SANKEY INLINE ---
    labels = [hosp.name]
    dept_labels = [Department.obj[d_id].title for d_id in depts_da_unidade if d_id in Department.obj]
    dev_ids_presentes = df['device_id'].unique()
    dev_labels = [Device.obj[dv_id].category for dv_id in dev_ids_presentes if dv_id in Device.obj]
    
    labels.extend(dept_labels)
    labels.extend(dev_labels)
    
    label_to_index = {name: idx for idx, name in enumerate(labels)}
    
    sources, targets, values = [], [], []

    # Fluxo 1: Hospital -> Departamentos
    df_dept_summary = df.groupby('dept_id')['amount'].sum().reset_index()
    for _, row in df_dept_summary.iterrows():
        d_id = int(row['dept_id'])
        if d_id in Department.obj:
            d_name = Department.obj[d_id].title
            sources.append(label_to_index[hosp.name])
            targets.append(label_to_index[d_name])
            values.append(float(row['amount']))

    # Fluxo 2: Departamentos -> Categorias de Dispositivos
    df_dev_summary = df.groupby(['dept_id', 'device_id'])['amount'].sum().reset_index()
    for _, row in df_dev_summary.iterrows():
        d_id = int(row['dept_id'])
        dv_id = int(row['device_id'])
        if d_id in Department.obj and dv_id in Device.obj:
            d_name = Department.obj[d_id].title
            dv_name = Device.obj[dv_id].category
            sources.append(label_to_index[d_name])
            targets.append(label_to_index[dv_name])
            values.append(float(row['amount']))

    response_data["sankey"] = {
        "labels": labels,
        "sources": sources,
        "targets": targets,
        "values": values
    }

    # --- PROCESSAR EVOLUÇÃO CRONOLÓGICA MENSAL ---
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
    df_time = df.groupby('month')['amount'].sum().reset_index().sort_values('month')
    
    response_data["timeline"] = {
        "x": df_time['month'].tolist(),
        "y": df_time['amount'].tolist()
    }

    return jsonify(response_data)    

if __name__ == "__main__":
    appy.run(debug=True, use_reloader=False)
