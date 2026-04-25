# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 16:28:47 2026

@author: couto
"""
# Class Device - generic version with inheritance
from classes.gclass import Gclass

class Device(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''

    # Attribute names list (id primeiro e com _)
    att = ['_id','_category','_name']

    # Class header title
    header = 'Devices'

    # Field descriptions
    des = ['Id','Category','Name']

    # Constructor
    def __init__(self, id, category, name):
        super().__init__()

        id = Device.get_id(id)
        self._id = id
        self._category = category
        self._name = name

        # Guardar objeto
        Device.obj[id] = self
        Device.lst.append(id)

    # id property
    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, id):
        self._id = id

    # category property
    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, category):
        self._category = category

    # name property
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name