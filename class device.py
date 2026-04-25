# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 16:28:47 2026

@author: couto
"""

#Revisto por: Pedro
from classes.gclass import Gclass

class Device(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''

    att = ['_id', '_category']

    header = 'Devices'

    des = ['Id', 'Category']


    def __init__(self, id, category):
        super().__init__()

        id = Device.get_id(id)
        self._id = id
        
        self._category = str(category)

        # Guardar objeto
        Device.obj[id] = self
        Device.lst.append(id)

    # --- PROPERTIES ---

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category):
        self._category = category
