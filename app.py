# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:18:54 2026

@author: pedro
"""
#interface do site onde há display dos nossos dados

from flask import Flask, render_template, request, session
import os
from classes.hospital import Hospital
from classes.department import Department
from classes.device import Device
from classes.utilization import Utilization

appy = Flask(__name__)
appy.secret_key = 'CHAVE_SECRETA_HOSPITAL'


#isto garante que o Flask procura a base de dados exatamente na mesma pasta onde o ficheiro app.py está guardado, independentemente do terminal.
db_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', 'HospitalData.db')

# Lê os dados
Hospital.read(db_name)
Department.read(db_name)
Device.read(db_name)
Utilization.read(db_name)

prev_option = ""



@appy.route("/", methods=["post","get"])
def index():
    global prev_option
    
    # que classe estamos a ver agora?
    # podemos mudar isto no menu
    current_class_name = request.args.get("class", session.get("current_class", "Hospital"))
    session["current_class"] = current_class_name
    
    #mapear o nome da string para a sua class correspondente
    classes_map = {
        "Hospital": Hospital,
        "Department": Department,
        "Device": Device,
        "Utilization": Utilization
    }
    cl = classes_map[current_class_name]
    
#instruções para o site funcionar
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
        # Gerar a string para o from_string baseada nos campos do formulário
        # O primeiro campo é sempre o ID (0 para auto-incremento)
        data = ["0"] 
        for attribute in cl.att[0:]: # Ignora o _id
            # Busca o valor no formulário (o nome do input no HTML deve ser o nome do atributo sem _)
            field_name = attribute[0:] 
            data.append(request.form[field_name])
        
        strobj = ";".join(data)
        obj = cl.from_string(strobj)
        cl.insert(obj.id)
        cl.last()
    elif prev_option == 'edit' and option == 'save':
        obj = cl.current()
        for attribute in cl.att[0:]:
            field_name = attribute[0:]
            setattr(obj, field_name, request.form[field_name])
        cl.update(obj.id)
    elif option == "list":
        show_list = True
        list_data = [
            {att[1:]: getattr(cl.obj[id], att[1:]) for att in cl.att}
            for id in cl.lst]
    elif option == "first":
        cl.first()
    elif option == "previous":
        cl.previous()
    elif option == "next":
        cl.nextrec()
    elif option == "last":
        cl.last()
    elif option == 'exit':
        return "<h1>Base de Dados Hospitalar Fechada.</h1>"

    prev_option = option
    obj = cl.current()
    
    # se a lista estiver vazia ou for um insert novo
    if option == 'insert' or len(cl.lst) == 0:
        obj_id = cl.get_id(0)
        # criamos um dicionário vazio para o template não dar erro ao ler campos
        fields = {att[0:]: "" for att in cl.att[0:]}
    else:
        obj_id = obj.id
        # criamos um dicionário com os valores atuais do objeto
        fields = {att[0:]: getattr(obj, att[0:]) for att in cl.att[0:]}

    return render_template("index.html",
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
    # use_reloader=False impede o flask de reiniciar e esconder o erro real (para detetar melhor os erros)
    appy.run(debug=True, use_reloader=False)
    
    
#acrescentar funcionalidades ao site (mexer com amounts, datas, melhorar a informação apresentada, se calhar graficos)