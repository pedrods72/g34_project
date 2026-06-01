# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:18:54 2026

@author: pedro
"""
# interface do site onde há display dos nossos dados

from flask import Flask, render_template, request, session, flash, redirect, url_for, jsonify
import sqlite3
import os
from classes.hospital import Hospital
from classes.department import Department
from classes.device import Device
from classes.utilization import Utilization
from classes.userlogin import Userlogin
import pandas as pd

appy = Flask(__name__)
appy.config["TEMPLATES_AUTO_RELOAD"] = True          # reload automático de templates
appy.secret_key = 'CHAVE_SECRETA_HOSPITAL'
appy.jinja_env.globals['getattr'] = getattr          # getattr disponível nos templates Jinja

# Caminho para a base de dados
db_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'HospitalData.db')

# Inicializar leitura dos dados originais do projeto
Userlogin.read(db_name)
Hospital.read(db_name)
Department.read(db_name)
Device.read(db_name)
Utilization.read(db_name)

prev_option = ""

classes_map = {
    "Hospital":    Hospital,
    "Department":  Department,
    "Device":      Device,
    "Utilization": Utilization,
    "Userlogin":   Userlogin
}

# --- FUNÇÕES ANALÍTICAS UNIFICADAS (DADOS REAIS DA BD) ---

def tendencias_mensais():
    con = sqlite3.connect(db_name)
    df = pd.read_sql_query('''
        SELECT strftime('%Y-%m', utilization_date) as period, SUM(amount) as total
        FROM Utilization GROUP BY period ORDER BY period
    ''', con)
    con.close()
    return df.to_dict(orient='records')

def gastos_dispositivos():
    if not Utilization.lst:
        return []
    dados = []
    for u in Utilization.obj.values():
        dev_id = getattr(u, 'device_id', getattr(u, '_device_id', None))
        categoria = Device.obj[dev_id].category if dev_id in Device.obj else "Desconhecido"
        dados.append({'category': categoria, 'amount': float(getattr(u, 'amount', getattr(u, '_amount', 0.0)))})
    df = pd.DataFrame(dados)
    df_cat = df.groupby('category')['amount'].sum().reset_index().rename(columns={'amount': 'cost'}).sort_values(by='cost', ascending=False)
    total_global = df_cat['cost'].sum()
    df_cat['cumsum'] = df_cat['cost'].cumsum()
    df_cat['perc_accum'] = (df_cat['cumsum'] / total_global) * 100
    df_cat['is_critical'] = df_cat['perc_accum'] <= 80
    return df_cat.to_dict(orient='records')

def eficiencia_hospitais():
    if not Department.lst:
        return []
    df_depts = pd.DataFrame([{'hospital_id': getattr(d, 'hospital_id', getattr(d, '_hospital_id', 0)), 'dept_id': d.id} for d in Department.obj.values()])
    contagem_depts = df_depts.groupby('hospital_id').size().reset_index(name='depts')

    gastos_lista = []
    for u in Utilization.obj.values():
        u_dept = getattr(u, 'department_id', getattr(u, '_department_id', None))
        if u_dept in Department.obj:
            h_id = getattr(Department.obj[u_dept], 'hospital_id', getattr(Department.obj[u_dept], '_hospital_id', 0))
            gastos_lista.append({'hospital_id': h_id, 'amount': float(getattr(u, 'amount', getattr(u, '_amount', 0.0)))})
    if not gastos_lista:
        return []
    df_gastos = pd.DataFrame(gastos_lista)
    soma_gastos = df_gastos.groupby('hospital_id')['amount'].sum().reset_index(name='total_spend')

    df_hospitais = pd.DataFrame([{'hospital_id': h.id, 'name': h.name} for h in Hospital.obj.values()])
    df_final = df_hospitais.merge(contagem_depts, on='hospital_id', how='left').merge(soma_gastos, on='hospital_id', how='left')
    df_final['depts'] = df_final['depts'].fillna(0).astype(int)
    df_final['total_spend'] = df_final['total_spend'].fillna(0)
    df_final['avg_per_dept'] = df_final.apply(lambda r: round(r['total_spend'] / r['depts'], 2) if r['depts'] > 0 else 0, axis=1)
    return df_final.sort_values(by='avg_per_dept', ascending=False)[['name', 'depts', 'total_spend', 'avg_per_dept']].to_dict(orient='records')

def analise_custo_volume_hospitais():
    # Código original do Stockler unificado com segurança
    if not Utilization.lst or not Department.lst or not Hospital.lst:
        return []
    dados_utilizacao = []
    for u in Utilization.obj.values():
        u_dept = getattr(u, 'department_id', getattr(u, '_department_id', None))
        if u_dept in Department.obj:
            h_id = getattr(Department.obj[u_dept], 'hospital_id', getattr(Department.obj[u_dept], '_hospital_id', 0))
            dados_utilizacao.append({'hospital_id': h_id, 'amount': float(getattr(u, 'amount', getattr(u, '_amount', 0.0)))})
    if not dados_utilizacao:
        return []
    df_utils = pd.DataFrame(dados_utilizacao)
    df_analise = df_utils.groupby('hospital_id').agg(custo_total=('amount', 'sum'), num_utilizacoes=('amount', 'size')).reset_index()
    df_hospitais = pd.DataFrame([{'hospital_id': h.id, 'hospital_name': h.name} for h in Hospital.obj.values()])
    return df_hospitais.merge(df_analise, on='hospital_id', how='inner').to_dict(orient='records')


# --- ROTAS DA APLICAÇÃO ---

@appy.route("/login")
def login():
    return render_template("login.html", id=0, user="", password="", ulogin=session.get("user"), resul="")

@appy.route("/logoff")
def logoff():
    session.pop("user", None)
    return render_template("login.html", ulogin=session.get("user"))

@appy.route("/chklogin", methods=["post", "get"])
def chklogin():
    user     = request.form["user"]
    password = request.form["password"]
    resul    = Userlogin.chk_password(user, password)
    if resul == "Valid":
        session["user"] = user
        return redirect(url_for('stats'))
    return render_template("login.html", user=user, password=password, ulogin=session.get("user"), resul=resul)


@appy.route("/stats")
def stats():
    if not session.get("user"):
        return redirect(url_for('login'))

    # KPIs Principais do Tiago e do Pedro
    total_hospitais     = len(Hospital.lst)
    total_departamentos = len(Department.lst)
    total_devices       = len(Device.lst)
    total_utilizacoes   = len(Utilization.lst)
    total_amount        = sum(float(getattr(Utilization.obj[i], 'amount', getattr(Utilization.obj[i], '_amount', 0))) for i in Utilization.lst)
    avg_amount          = round(total_amount / total_utilizacoes, 2) if total_utilizacoes else 0
    total_amount_fmt    = f"{total_amount:,}€".replace(",", " ")

    con = sqlite3.connect(db_name)
    cur = con.cursor()
    cur.execute('''
        SELECT d.title, d.extra_info, h.name,
               (SELECT dev2.category FROM Utilization u2 JOIN Device dev2 ON u2.device_id = dev2.id WHERE u2.department_id = d.id GROUP BY dev2.category ORDER BY SUM(u2.amount) DESC LIMIT 1) AS top_cat,
               SUM(u.amount) AS total
        FROM Utilization u JOIN Department d ON u.department_id = d.id JOIN Hospital h ON d.hospital_id = h.id
        GROUP BY d.id ORDER BY total DESC LIMIT 10
    ''')
    dept_rows = cur.fetchall()
    top_depts_labels    = [r[0] for r in dept_rows]
    top_depts_hospitals = [r[2] for r in dept_rows]
    top_depts_values    = [r[4] for r in dept_rows]
    top_depts_table     = [{"dept_title": r[0], "extra_info": r[1], "hospital_name": r[2], "top_category": r[3] or "—", "total_amount": r[4]} for r in dept_rows]

    cur.execute("SELECT strftime('%Y', utilization_date), SUM(amount) FROM Utilization GROUP BY strftime('%Y', utilization_date) ORDER BY 1")
    anual_labels, anual_values = zip(*cur.fetchall()) if len(Utilization.lst) > 0 else ([], [])

    cur.execute("SELECT h.name, SUM(u.amount) AS total FROM Utilization u JOIN Department d ON u.department_id = d.id JOIN Hospital h ON d.hospital_id = h.id GROUP BY h.id ORDER BY total DESC LIMIT 15")
    hosp_labels, hosp_values = zip(*cur.fetchall()) if len(Hospital.lst) > 0 else ([], [])
    con.close()

    # Cálculo dos dados reais sem filtros simulados
    con = sqlite3.connect(db_name)
    df_macro = pd.read_sql_query('''
        WITH base AS (
            SELECT strftime('%Y-%m', utilization_date) as period,
                   department_id, device_id, amount
            FROM Utilization
        ),
        totais AS (
            SELECT period, SUM(amount) as total FROM base GROUP BY period
        ),
        dept_max AS (
            SELECT period, SUM(amount) as dept_leader
            FROM base GROUP BY period, department_id
        ),
        dept_leader AS (
            SELECT period, MAX(dept_leader) as dept_leader FROM dept_max GROUP BY period
        ),
        dev_max AS (
            SELECT period, SUM(amount) as device_leader
            FROM base GROUP BY period, device_id
        ),
        dev_leader AS (
            SELECT period, MAX(device_leader) as device_leader FROM dev_max GROUP BY period
        )
        SELECT t.period, t.total, d.dept_leader, dv.device_leader
        FROM totais t
        LEFT JOIN dept_leader d ON t.period = d.period
        LEFT JOIN dev_leader dv ON t.period = dv.period
        ORDER BY t.period
    ''', con)
    
    df_vol = pd.read_sql_query('''
        WITH hosp_monthly AS (
            SELECT strftime('%Y-%m', u.utilization_date) as period,
                   h.name as hospital_name,
                   SUM(u.amount) as total
            FROM Utilization u
            JOIN Department d ON u.department_id = d.id
            JOIN Hospital h ON d.hospital_id = h.id
            GROUP BY period, h.id
        )
        SELECT
            period,
            MIN(total) as min_val,
            MAX(total) as max_val,
            AVG(total) as avg,
            (SELECT hospital_name FROM hosp_monthly hm2 WHERE hm2.period = hm.period ORDER BY total ASC LIMIT 1) as min_name,
            (SELECT hospital_name FROM hosp_monthly hm2 WHERE hm2.period = hm.period ORDER BY total DESC LIMIT 1) as max_name
        FROM hosp_monthly hm
        GROUP BY period ORDER BY period
    ''', con)
    con.close()

    chart1_dados = df_macro.to_dict(orient='records') if not df_macro.empty else []
    chart2_dados = df_vol.to_dict(orient='records') if not df_vol.empty else []

    pareto = gastos_dispositivos()
    efficiency = eficiencia_hospitais()
    custo_volume_dados = analise_custo_volume_hospitais()

    return render_template("stats.html",
        ulogin=session.get('user'),
        total_hospitais=total_hospitais, total_departamentos=total_departamentos,
        total_devices=total_devices, total_utilizacoes=total_utilizacoes,
        total_amount_fmt=total_amount_fmt, avg_amount=avg_amount,
        chart1=chart1_dados, chart2=chart2_dados,
        top_dept_label=top_depts_labels[0] if top_depts_labels else "Nenhum",
        top_device_label="Dispositivos Críticos",
        pareto=pareto, efficiency=efficiency, custo_volume=custo_volume_dados,
        top_depts_labels=top_depts_labels, top_depts_hospitals=top_depts_hospitals, top_depts_values=top_depts_values,
        anual_labels=list(anual_labels), anual_values=list(anual_values),
        hosp_labels=list(hosp_labels), hosp_values=list(hosp_values),
        top_depts_table=top_depts_table
    )


@appy.route("/index", methods=["post", "get"])
def index():
    global prev_option
    if not session.get("user"): return redirect(url_for('login'))

    current_user_obj = Userlogin.find(session.get("user"), 'user')
    user_group = current_user_obj[0].usergroup if current_user_obj else ""
    current_class_name = request.args.get("class", session.get("current_class", "Hospital"))
    session["current_class"] = current_class_name
    cl = classes_map[current_class_name]

    butshow, butedit = "enabled", "disabled"
    show_list = False
    list_data = []
    option = request.args.get("option")

    if option == "edit": butshow, butedit = "disabled", "enabled"
    elif option == "delete":
        obj = cl.current()
        if obj:
            cl.remove(obj.id)
            if not cl.previous(): cl.first()
    elif option == "insert": butshow, butedit = "disabled", "enabled"
    elif option == 'cancel': pass
    elif prev_option == 'insert' and option == 'save':
        try:
            data = ["0"]
            for attribute in cl.att[1:]: data.append(request.form.get(attribute[1:], ""))
            strobj = ";".join(data)
            obj = cl.from_string(strobj)
            cl.insert(obj.id)
            cl.last()
            flash("Registo inserido com sucesso!", "success")
        except Exception as e: flash(f"Erro ao inserir: {e}", "error")
    elif prev_option == 'edit' and option == 'save':
        try:
            obj = cl.current()
            for attribute in cl.att[1:]:
                field_name = attribute[1:]
                if field_name in request.form: setattr(obj, attribute, request.form[field_name])
            cl.update(int(obj.id))
            flash("Registo atualizado com sucesso!", "success")
        except Exception as e: flash(f"Erro ao atualizar: {e}", "error")
    elif option == "list":
        show_list = True
        for id in cl.lst:
            row = {}
            for att in cl.att:
                key = att[1:]
                row[key] = '(Oculto)' if current_class_name == 'Userlogin' and key == 'password' else getattr(cl.obj[id], att)
            list_data.append(row)
    elif option == "first":    cl.first()
    elif option == "previous": cl.previous()
    elif option == "next":     cl.nextrec()
    elif option == "last":     cl.last()

    prev_option = option
    obj = cl.current()
    if option == 'insert' or len(cl.lst) == 0:
        obj_id = cl.get_id(0)
        fields = {att[1:]: "" for att in cl.att}
    else:
        obj_id = obj.id
        fields = {att[1:]: getattr(obj, att[1:]) for att in cl.att}

    return render_template("index.html",
                           hospitais_todos=Hospital.obj.values(), depts_todos=Department.obj.values(),
                           devices_todos=Device.obj.values(), utilizacoes_todos=Utilization.obj.values(),
                           Hospital=Hospital, Department=Department, Device=Device, Utilization=Utilization, Userlogin=Userlogin,
                           class_name=current_class_name, id=obj_id, fields=fields, header=cl.header, titles=cl.des,
                           butshow=butshow, butedit=butedit, show_list=show_list, list_data=list_data,
                           ulogin=session.get("user"), user_group=user_group)


@appy.route('/api/hospital/<int:hospital_id>/details')
def api_hospital_details(hospital_id):
    if not session.get("user"): return jsonify({"error": "Sessão expirada"}), 401
    if hospital_id not in Hospital.obj: return jsonify({"error": "Hospital não encontrado"}), 404

    hosp = Hospital.obj[hospital_id]
    depts_da_unidade = [d.id for d in Department.obj.values() if getattr(d, 'hospital_id', getattr(d, '_hospital_id', None)) == hospital_id]
    
    utils_da_unidade = []
    for u in Utilization.obj.values():
        if getattr(u, 'department_id', getattr(u, '_department_id', None)) in depts_da_unidade:
            utils_da_unidade.append(u)

    response_data = {
        "hospital_name": hosp.name, "has_data": False,
        "kpis": {"max": 0, "avg": 0, "min": 0},
        "sankey": {"labels": [], "sources": [], "targets": [], "values": []},
        "timeline": {"x": [], "y": []}
    }
    if not utils_da_unidade: return jsonify(response_data)

    dados_linhas = []
    for u in utils_da_unidade:
        dados_linhas.append({
            'dept_id': int(getattr(u, 'department_id', getattr(u, '_department_id', 0))),
            'device_id': int(getattr(u, 'device_id', getattr(u, '_device_id', 0))),
            'amount': float(getattr(u, 'amount', getattr(u, '_amount', 0.0))),
            'date': str(getattr(u, 'utilization_date', getattr(u, '_utilization_date', '2026-01-01')))
        })

    df = pd.DataFrame(dados_linhas)
    response_data["has_data"] = True
    response_data["kpis"] = {"max": float(df['amount'].max()), "avg": round(float(df['amount'].mean()), 2), "min": float(df['amount'].min())}

    labels = [hosp.name]
    dept_labels = [Department.obj[d_id].title for d_id in depts_da_unidade if d_id in Department.obj]
    dev_ids_presentes = df['device_id'].unique()
    dev_labels = [Device.obj[dv_id].category for dv_id in dev_ids_presentes if dv_id in Device.obj]
    labels.extend(dept_labels)
    labels.extend(dev_labels)
    
    label_to_index = {name: idx for idx, name in enumerate(labels)}
    sources, targets, values = [], [], []

    df_dept_summary = df.groupby('dept_id')['amount'].sum().reset_index()
    for _, row in df_dept_summary.iterrows():
        d_id = int(row['dept_id'])
        if d_id in Department.obj:
            sources.append(label_to_index[hosp.name])
            targets.append(label_to_index[Department.obj[d_id].title])
            values.append(float(row['amount']))

    df_dev_summary = df.groupby(['dept_id', 'device_id'])['amount'].sum().reset_index()
    for _, row in df_dev_summary.iterrows():
        d_id, dv_id = int(row['dept_id']), int(row['device_id'])
        if d_id in Department.obj and dv_id in Device.obj:
            sources.append(label_to_index[Department.obj[d_id].title])
            targets.append(label_to_index[Device.obj[dv_id].category])
            values.append(float(row['amount']))

    response_data["sankey"] = {"labels": labels, "sources": sources, "targets": targets, "values": values}
    df['month'] = pd.to_datetime(df['date']).dt.to_period('M').astype(str)
    df_time = df.groupby('month')['amount'].sum().reset_index().sort_values('month')
    response_data["timeline"] = {"x": df_time['month'].tolist(), "y": df_time['amount'].tolist()}

    return jsonify(response_data)


@appy.route("/")
def home():
    if not session.get("user"): return render_template("home.html")
    return redirect(url_for('stats'))

if __name__ == "__main__":
    appy.run(debug=True, use_reloader=False)