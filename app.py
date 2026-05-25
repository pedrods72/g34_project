# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:18:54 2026

@author: pedro
"""
# interface do site onde há display dos nossos dados

from flask import Flask, render_template, request, session, flash
import sqlite3
import os
from classes.hospital import Hospital
from classes.department import Department
from classes.device import Device
from classes.utilization import Utilization

appy = Flask(__name__)
appy.secret_key = 'CHAVE_SECRETA_HOSPITAL'

# assim o Flask procura a base de dados exatamente na mesma pasta onde
# o ficheiro app.py está guardado, independentemente do terminal.
db_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'HospitalData.db')

# Lê os dados
Hospital.read(db_name)
Department.read(db_name)
Device.read(db_name)
Utilization.read(db_name)

prev_option = ""

# mapear os nomes da string 
classes_map = {
    "Hospital": Hospital,
    "Department": Department,
    "Device": Device,
    "Utilization": Utilization
}



def tendencias_mensais():
    # dicionário para acumular gastos por mês ou ano
    historico = {}
    for obj_id in Utilization.lst:
        u = Utilization.obj[obj_id]
        # assume-se que a u.utilization_date está como "YYYY-MM-DD"
        mes_ano = u.utilization_date.strftime('%Y-%m')
        historico[mes_ano] = historico.get(mes_ano, 0) + u.amount
    
    # ordenar por data para calcular a variação
    meses_sorted = sorted(historico.keys())
    trends = []
    for i in range(len(meses_sorted)):
        atual = meses_sorted[i]
        val = historico[atual]
        mudanca = 0
        if i > 0:
            prev_val = historico[meses_sorted[i-1]]
            mudanca = ((val - prev_val) / prev_val) * 100
        trends.append({"period": atual, "total": val, "growth": round(mudanca, 2)})
    
    return trends

def gastos_dispositivos():
    # calcular o gasto total por dispositivo
    gastos_devices = {}
    for u_id in Utilization.lst:
        u = Utilization.obj[u_id]
        categoria = Device.obj[u.device_id].category
        gastos_devices[categoria] = gastos_devices.get(categoria, 0) + u.amount
    
    # Ordenar do mais caro para o mais barato
    sorted_devs = sorted(gastos_devices.items(), key=lambda x: x[1], reverse=True)
    total_global = sum(gastos_devices.values())
    
    pareto_data = []
    acumulado = 0
    for cat, custo in sorted_devs:
        acumulado += custo
        perc_accum = (acumulado/ total_global) * 100
        pareto_data.append({
            "category": cat,
            "cost": custo,
            "is_critical": perc_accum <= 80  # Os 20% de tipos que causam 80% do gasto
        })
    return pareto_data

def eficiencia_hospitais():
    stats = {}
    # first, contar departamentos por hospital
    for d_id in Department.lst:
        h_id = Department.obj[d_id].hospital_id
        if h_id not in stats:
            stats[h_id] = {"name": Hospital.obj[h_id].name, "depts": 0, "total_spend": 0}
        stats[h_id]["depts"] += 1

    # then os gastos das utilizações
    for u_id in Utilization.lst:
        u = Utilization.obj[u_id]
        # after that precisamos de chegar ao hospital através do departamento
        dept = Department.obj[u.department_id]
        h_id = dept.hospital_id
        if h_id in stats:
            stats[h_id]["total_spend"] += u.amount

    # finally calcular média por departamento
    for h_id in stats:
        h = stats[h_id]
        h["avg_per_dept"] = round(h["total_spend"] / h["depts"], 2) if h["depts"] > 0 else 0
        
    return sorted(stats.values(), key=lambda x: x["avg_per_dept"], reverse=True)

@appy.route("/stats")
def stats():
    # --- KPIs ---
    total_hospitais    = len(Hospital.lst)
    total_departamentos = len(Department.lst)
    total_devices      = len(Device.lst)
    total_utilizacoes  = len(Utilization.lst)
    total_amount       = sum(Utilization.obj[i].amount for i in Utilization.lst)
    avg_amount         = round(total_amount / total_utilizacoes, 2) if total_utilizacoes else 0
    total_amount_fmt   = f"{total_amount:,}"

    # --- Consultas SQL com chaves estrangeiras resolvidas ---
    con = sqlite3.connect(db_name)
    cur = con.cursor()

    # Gráfico circular: amount por categoria de dispositivo
    cur.execute('''
        SELECT dev.category, SUM(u.amount)
        FROM Utilization u
        JOIN Device dev ON u.device_id = dev.id
        GROUP BY dev.category
        ORDER BY SUM(u.amount) DESC
    ''')
    device_rows   = cur.fetchall()
    device_labels = [r[0] for r in device_rows]
    device_values = [r[1] for r in device_rows]

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
    dept_rows          = cur.fetchall()
    top_depts_labels   = [r[0] for r in dept_rows]           # nome do departamento
    top_depts_hospitals = [r[2] for r in dept_rows]          # nome do hospital (FK resolvida)
    top_depts_values   = [r[4] for r in dept_rows]
    top_depts_table    = [
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

    # Barras horizontais: Top 15 hospitais (FK Departamento → Hospital resolvida)
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

    trends = tendencias_mensais()
    
    pareto = gastos_dispositivos()
    
    efficiency = eficiencia_hospitais()
    
    return render_template("stats.html",
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
        device_labels=device_labels,
        device_values=device_values,
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
    cl_name = request.args.get("class", "Hospital")
    att     = request.args.get("att", "")
    value   = request.args.get("value", "")
    cl      = classes_map[cl_name]

    results = []
    if att and value:
        proto = cl.obj[cl.lst[0]] if cl.lst else None
        if proto and '_' + att in proto.__dict__:
            atype = type(getattr(proto, '_' + att))
            try:
                typed_value = atype(value)
            except Exception:
                typed_value = value
            results = cl.find(typed_value, att)

    return render_template("search.html",
        class_name=cl_name,
        att=att,
        value=value,
        results=results,
        Hospital=Hospital,
        Department=Department,
        Device=Device,
        attributes=[a[1:] for a in cl.att[1:]])


@appy.route("/", methods=["post", "get"])
def index():
    global prev_option

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
                # no HTML os names são sem underscore
                # attribute[1:] para isto bater com o name do input
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
            # saltar ID 
            for attribute in cl.att[1:]:
                field_name = attribute[1:]
                if field_name in request.form:
                    setattr(obj, attribute, request.form[field_name])
            
            # converter para int para evitar o KeyError: '2' no gclass.py.
            cl.update(int(obj.id))
            flash("Registo atualizado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao atualizar: {e}", "error")

    elif option == "list":
        show_list = True
        # usar 'att' (com underscore) para ler do objeto.
        list_data = [
            {att[1:]: getattr(cl.obj[id], att) for att in cl.att}
            for id in cl.lst
        ]

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
        # usar getattr(obj, att) para ir buscar o valor do atributo real (_name)
        fields = {att[1:]: getattr(obj, att) for att in cl.att}

    return render_template("index.html",
                           hospitais_todos = Hospital.obj.values(),
                           depts_todos = Department.obj.values(),
                           devices_todos = Device.obj.values(),
                           utilizacoes_todos = Utilization.obj.values(),
                           Hospital=Hospital,
                           Department=Department,
                           Device=Device,
                           Utilization=Utilization,
                           class_name=current_class_name,
                           id=obj_id,
                           fields=fields,
                           header=cl.header,
                           titles=cl.des,
                           butshow=butshow,
                           butedit=butedit,
                           show_list=show_list,
                           list_data=list_data)


if __name__ == "__main__":
    appy.run(debug=True, use_reloader=False)
