# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:15:46 2026

@author: pedro
"""
#so rodar uma vez por pessoa
import pandas as pd
import sqlite3
import os
from classes.gclass import Gclass
from classes.hospital import Hospital
from classes.department import Department
from classes.device import Device
from classes.utilization import Utilization

db_path = "HospitalData.db"
Gclass.path = db_path

#se esteve a dar erro, entao temos de dar delete à bd
if os.path.exists(db_path):
    os.remove(db_path)

# precisamos das tabelas para organizar os dados
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("CREATE TABLE Hospital (id INTEGER PRIMARY KEY, name TEXT, creation_date TEXT)")
cur.execute("CREATE TABLE Department (id INTEGER PRIMARY KEY, title TEXT, extra_info TEXT, hospital_id INTEGER)")
cur.execute("CREATE TABLE Device (id INTEGER PRIMARY KEY, category TEXT)")
cur.execute("CREATE TABLE Utilization (id INTEGER PRIMARY KEY, department_id INTEGER, device_id INTEGER, utilization_date TEXT, amount INTEGER)")
con.commit()
con.close()

#agora vamos ler os dados do csv e passar para as tabelas do sqlite
def init_database():
    df = pd.read_csv('base_dados_hospitalar_4classes_corrigida.csv', sep=';')
    print("A carregar dados para o SQLite...")

    for _, row in df.iterrows():
        # --- Criar HOSPITAL ---
        h_id = int(row['hospital_id'])
        if h_id not in Hospital.obj:
            h = Hospital(h_id, row['name'], row['creation_date'])
            Hospital.insert(h.id) # Correto: Passa o ID

        # --- Criar DEVICE ---
        dev_id = int(row['device_id'])
        if dev_id not in Device.obj:
            d = Device(dev_id, row['category'])
            Device.insert(d.id)   # Correto: Passa o ID

        # --- Criar DEPARTMENT ---
        dept_id = int(row['department_id'])
        if dept_id not in Department.obj:
            dep = Department(dept_id, row['title'], row['extra_info'], h_id)
            Department.insert(dep.id) # Correto: Passa o ID

        # --- Criar UTILIZATION ---
        u = Utilization(0, dept_id, dev_id, row['utilization_date'], row['amount'])
        Utilization.insert(u.id) # CORRIGIDO: Agora passa o ID gerado e não o objeto 'u'
#quando o processo é concluido, entao é suposto dar print a isto tudo
    print("Sucesso! Foram carregados e inseridos:")
    print(f"- {len(Hospital.obj)} Hospitais")
    print(f"- {len(Department.obj)} Departamentos")
    print(f"- {len(Device.obj)} Dispositivos")
    print(f"- {len(Utilization.obj)} Utilizações")

if __name__ == "__main__":
    init_database()