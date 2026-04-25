# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 15:33:26 2026

@author: User
"""

# @author: Stockler (baseado no template da class Person do prof. António Brito), revisto por: Pedro
# objetivo: class Hospital derivada da Gclass

from classes.gclass import Gclass
import datetime

class Hospital(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    
    att = ['_id', '_name', '_creation_date']
    
    header = 'Hospitais'
    
    des = ['Id', 'Nome do Hospital', 'Data de Criação']
    
    def __init__(self, id, name, creation_date):
        super().__init__()
        
        id = Hospital.get_id(id)
        self._id = id
        self._name = name
        
        if isinstance(creation_date, str):
            self._creation_date = datetime.date.fromisoformat(creation_date)
        else:
            self._creation_date = creation_date
        
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

 # Getter e Setter para a Data de Criação
    @property
    def creation_date(self):
        return self._creation_date

    @creation_date.setter
    def creation_date(self, creation_date):
        self._creation_date = creation_date

