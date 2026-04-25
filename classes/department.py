# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:11:49 2026

@author: pedro(provisorio)
"""
from classes.gclass import Gclass

class Department(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''


    att = ['_id', '_title', '_extra_info', '_hospital_id']
    header = 'Departments'
    des = ['Id', 'Title', 'Extra Info', 'Hospital Id']

    def __init__(self, id, title, extra_info, hospital_id):
        super().__init__()
        id = Department.get_id(id)
        self._id = id
        self._title = title
        self._extra_info = extra_info
        self._hospital_id = int(hospital_id)

        Department.obj[id] = self
        Department.lst.append(id)

    @property
    def id(self): return self._id
    @id.setter
    def id(self, id): self._id = id

    @property
    def title(self): return self._title
    @title.setter
    def title(self, title): self._title = title

    @property
    def extra_info(self): return self._extra_info
    @extra_info.setter
    def extra_info(self, extra_info): self._extra_info = extra_info

    @property
    def hospital_id(self): return self._hospital_id
    @hospital_id.setter
    def hospital_id(self, hospital_id): self._hospital_id = hospital_id
