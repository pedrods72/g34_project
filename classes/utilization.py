"""
Created on Sat Apr 25 16:19:29 2026

@author: tiago
"""
#Revisto por: Pedro

from classes.gclass import Gclass
import datetime

class Utilization(Gclass):
    obj = dict()
    lst = list()
    pos = 0
    sortkey = ''
    

    att = ['_id', '_department_id', '_device_id', '_utilization_date', '_amount']
    header = 'Utilizations'
    # Alterei o 'Id' do departamento e dispositivo para o nome legível
    des = ['Id', 'Department Name', 'Device Name', 'Utilization Date', 'Amount']
    

    def __init__(self, id, department_id, device_id, utilization_date, amount):
        super().__init__()
        
        id = Utilization.get_id(id)
        self._id = id
        

        self._department_id = int(department_id) if department_id else None
        
        self._device_id = int(device_id)
        
        # Proteção para o formato da data (lida tanto com DD/MM/YYYY como YYYY-MM-DD)
        if isinstance(utilization_date, str) and '/' in utilization_date:
            self._utilization_date = datetime.datetime.strptime(utilization_date, '%d/%m/%Y').date()
        else:
            self._utilization_date = datetime.date.fromisoformat(str(utilization_date))
            

        self._amount = int(amount)
        
        Utilization.obj[id] = self
        Utilization.lst.append(id)

    # --- PROPERTIES ---

    @property
    def id(self):
        return self._id
    @id.setter
    def id(self, id):
        self._id = id

    @property
    def department_id(self):
        return self._department_id
    @department_id.setter
    def department_id(self, department_id):
        self._department_id = department_id

    @property
    def device_id(self):
        return self._device_id
    @device_id.setter
    def device_id(self, device_id):
        self._device_id = device_id

    @property
    def utilization_date(self):
        return self._utilization_date
    @utilization_date.setter
    def utilization_date(self, utilization_date):
        self._utilization_date = utilization_date

    @property
    def amount(self):
        return self._amount
    @amount.setter
    def amount(self, amount):
        self._amount = amount
    @property
    def department_name(self):
        dept = Department.obj.get(self._department_id)
        return dept.title if dept else "N/A"

    @property
    def device_name(self):
        dev = Device.obj.get(self._device_id)
        return dev.category if dev else "N/A"

    @property
    def hospital_name(self):
        dept = Department.obj.get(self._department_id)
        if dept:
            hosp = Hospital.obj.get(dept.hospital_id)
            return hosp.name if hosp else "N/A"
        return "N/A"
