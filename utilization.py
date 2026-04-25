"""
Created on Sat Apr 25 16:19:29 2026

@author: tiago
"""

# Class Utilization - generic version with inheritance
from classes.gclass import Gclass
import datetime

class Utilization(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    # Attribute names list, identifier attribute must be the first one and called 'id'
    att = ['_id', '_department_id', '_device_id', '_utilization_date', '_amount']
    # Class header title
    header = 'Utilizations'
    # field description for use in, for example, input form
    des = ['Id', 'Department Id', 'Device Id', 'Utilization Date', 'Amount']
    # Constructor: Called when an object is instantiated
    def __init__(self, id, department_id, device_id, utilization_date, amount):
        super().__init__()
        # Object attributes
        id = Utilization.get_id(id)
        self._id = id
        self._department_id = int(department_id)
        self._device_id = int(device_id)
        self._utilization_date = datetime.date.fromisoformat(utilization_date)
        self._amount = int(amount)
        # Add the new object to the dictionary of objects
        Utilization.obj[id] = self
        # Add the id to the list of object ids
        Utilization.lst.append(id)

    # id property getter method
    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, id):
        self._id = id

    # department_id property getter method
    @property
    def department_id(self):
        return self._department_id
    @department_id.setter
    def department_id(self, department_id):
        self._department_id = department_id

    # device_id property getter method
    @property
    def device_id(self):
        return self._device_id
    @device_id.setter
    def device_id(self, device_id):
        self._device_id = device_id

    # utilization_date property getter method
    @property
    def utilization_date(self):
        return self._utilization_date
    @utilization_date.setter
    def utilization_date(self, utilization_date):
        self._utilization_date = utilization_date

    # amount property getter method
    @property
    def amount(self):
        return self._amount
    @amount.setter
    def amount(self, amount):
        self._amount = amount