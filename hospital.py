# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 15:33:26 2026

@author: User
"""

# @author: Stockler (baseado no template de António Brito)
# objective: class Hospital derived from Gclass

from gclass import Gclass

class Hospital(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    
    # Lista de atributos: o id tem de ser o primeiro
    # No teu CSV tens hospital_id e name
    att = ['_id', '_name']
    
    # Título para as listagens
    header = 'Hospitais'
    
    # Descrição dos campos
    des = ['Id', 'Nome do Hospital']
    
    def __init__(self, id, name):
        super().__init__()
        # O get_id vem da Gclass que copiaste antes
        id = Hospital.get_id(id)
        self._id = id
        self._name = name
        
        # Guarda nas listas da classe para o motor funcionar
        Hospital.obj[id] = self
        Hospital.lst.append(id)

    # Getter e Setter para o ID
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    # Getter e Setter para o Nome
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name