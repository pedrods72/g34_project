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

appy = Flask(__name__)
appy.config["TEMPLATES_AUTO_RELOAD"] = True          # reload automático de templates
appy.secret_key = 'CHAVE_SECRETA_HOSPITAL'
appy.jinja_env.globals['getattr'] = getattr          # getattr disponível nos templates Jinja

# assim o Flask procura a base de dados exatamente na mesma pasta onde
# o ficheiro app.py está guardado, independentemente do terminal.
db_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'HospitalData.db')

# Lê os dados
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
    return render_template("login.html", ulogin=session.get("user"))

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

    # --- Consultas SQL com chaves estrangeiras resolvidas ---
    con = sqlite3.connect(db_name)
    cur = con.cursor()



    # Barras: Top 10 departamentos com nome do hospital resolvido
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

    # Linha: evolução anual
    cur.execute('''
        SELECT strftime('%Y', utilization_date), SUM(amount)
        FROM Utilization
        GROUP BY strftime('%Y', utilization_date)
        ORDER BY 1
    ''')
    anual_rows   = cur.fetchall()
    anual_labels = [r[0] for r in anual_rows]
    anual_values = [r[1] for r in anual_rows]

    # Barras horizontais: Top 15 hospitais
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
        # gráficos
        top_depts_labels=top_depts_labels,
        top_depts_hospitals=top_depts_hospitals,
        top_depts_values=top_depts_values,
        anual_labels=anual_labels,
        anual_values=anual_values,
        hosp_labels=hosp_labels,
        hosp_values=hosp_values,
        # tabelas
        top_depts_table=top_depts_table,
    )



@appy.route("/search")
def search():
    class_name = request.args.get('class', 'Hospital')
    cls        = classes_map.get(class_name)
    if cls is None:
        return redirect('/')

    attributes = [a[1:] for a in cls.att[1:]]

    atts   = request.args.getlist('att[]')
    ops    = request.args.getlist('op[]')
    values = request.args.getlist('value[]')

    sort_by  = request.args.get('sort_by', '')
    sort_dir = request.args.get('sort_dir', 'asc')
    per_page = int(request.args.get('per_page', 10))

    # compatibilidade com formulário antigo
    if not atts and request.args.get('att'):
        atts   = [request.args.get('att')]
        ops    = ['contains']
        values = [request.args.get('value', '')]

    results = [cls.obj[id] for id in cls.lst]

    for att, op, value in zip(atts, ops, values):
        if not value or att not in attributes:
            continue
        filtered = []
        for obj in results:
            obj_val = getattr(obj, '_' + att, None)
            if obj_val is None:
                continue
            obj_str = str(obj_val).lower()
            val_str = value.strip().lower()
            match op:
                case 'contains': ok = val_str in obj_str
                case 'equals':   ok = obj_str == val_str
                case 'starts':   ok = obj_str.startswith(val_str)
                case 'ends':     ok = obj_str.endswith(val_str)
                case 'gt':
                    try:    ok = float(obj_val) > float(value)
                    except: ok = obj_str > val_str
                case 'lt':
                    try:    ok = float(obj_val) < float(value)
                    except: ok = obj_str < val_str
                case _: ok = val_str in obj_str
            if ok:
                filtered.append(obj)
        results = filtered

    if sort_by and sort_by in attributes:
        reverse = (sort_dir == 'desc')
        results.sort(
            key=lambda obj: (
                float(getattr(obj, '_' + sort_by))
                if str(getattr(obj, '_' + sort_by, '')).replace('.', '', 1).isdigit()
                else str(getattr(obj, '_' + sort_by, '')).lower()
            ),
            reverse=reverse
        )

    results = results[:per_page]

    return render_template('search.html',
        class_name=class_name,
        attributes=attributes,
        results=results,
        att=atts[0]    if atts   else '',
        op=ops[0]      if ops    else 'contains',
        value=values[0] if values else '',
        sort_by=sort_by,
        sort_dir=sort_dir,
        per_page=per_page,
    )
    match att:
        case 'department_name':
            obj_val = obj.department_name
        case 'device_name':
            obj_val = obj.device_name
        case 'hospital_name':
            obj_val = obj.hospital_name
        case _:
            obj_val = getattr(obj, '_' + att, None)



@appy.route("/dashboard", methods=["post", "get"])
def index():
    global prev_option

    if not session.get("user"):
        return redirect(url_for('login'))

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
@appy.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    appy.run(debug=True, use_reloader=False)

# TODO: dashboard com valores essenciais, melhorar gráficos, linhas com médias/medianas
# TODO: usar pandas, plotly, matplotlib
# TODO: interface de pesquisa no index em vez do search
# TODO: ecrã inicial mais apelativo
# TODO: continuar a melhorar a experiência do utilizador
# TODO: finalizar interface do Userlogin
