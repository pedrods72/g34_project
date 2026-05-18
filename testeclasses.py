# -*- coding: utf-8 -*-
"""
@author: António Brito / Carlos Bragança
(2021)
#objective: Test classes based on generic class Gclass

"""""
# -*- coding: utf-8 -*-
"""
@author: António Brito / Carlos Bragança
(2021)
#objective: Test classes based on generic class Gclass

"""""
db = 'HospitalData.db'

# from classes.hospital import Hospital
# test_class = Hospital
# ob = '600;Xavier;1958-03-20;5000.0'

#Uncomment to test class Product
# from classes.department import Department
# test_class = Department
# ob='Product1;10.9;100'

#Uncomment to test class Customer_login
# from classes.device import Device
# test_class = Device

#Uncomment to test class Order
from classes.utilization import Utilization
test_class = Utilization

import datetime

# Reads the test_class db file
test_class.read('data/' + db)

op = ''
while op != 'q':
    print('')
    print('Choose one letter for select the option')
    print('---------------')
    print('l - list')
    print('b - beginning')
    print('n - next')
    print('p - previous')
    print('e - end')
    print('---------------')
    print('i - insert')
    print('m - modify')
    print('r - remove')
    print('---------------')
    print('s - sort by attribute')
    print('f - find by attribute')
    print('---------------')
    print('q - quit')
    print('---------------')

    # FIX: guard current() when the list is empty
    if len(test_class.lst) == 0:
        p = None
        print('(no records)')
    else:
        p = test_class.current()
        print(f'\n{p}')

    op = input('?')

    if op == 'b':
        test_class.first()

    elif op == 'n':
        test_class.nextrec()

    elif op == 'p':
        test_class.previous()

    elif op == 'e':
        test_class.last()

    elif op == 'i':
        # FIX: always get a prototype object to inspect attributes,
        # even when the list is empty — use from_string() for that.
        p1 = None
        if len(test_class.lst) == 0:
            proto = test_class.from_string(ob)
            p1 = proto        # marks that this temp object must be removed
        else:
            proto = test_class.current()

        str_list = list(proto.__dict__.keys())
        attrib = str_list[0]
        atype = type(getattr(proto, attrib))

        print('leave blank to auto-increment')
        id_input = input(f'{attrib[1:]} = ')
        if id_input == "":
            id_val = 0          # 0 signals auto-increment to the class
        else:
            id_val = int(id_input)

        strarg = f'test_class({id_val}'
        for i in range(1, len(str_list)):
            attrib = str_list[i]
            atype = type(getattr(proto, attrib))
            if atype in (datetime.date, str):
                value = input(f'{attrib[1:]} = ')
                strarg += f',"{value}"'
            else:
                value = atype(input(f'{attrib[1:]} = '))
                strarg += f',{value}'
        strarg += ')'

        # FIX: remove the temporary prototype BEFORE inserting the real one
        if p1 is not None:
            first_attr = list(proto.__dict__.keys())[0]
            temp_id = getattr(p1, first_attr)
            if temp_id in test_class.lst:
                test_class.remove(temp_id)

        print(strarg)
        pobj = eval(strarg)
        first_attr = list(pobj.__dict__.keys())[0]
        code = getattr(pobj, first_attr)
        test_class.current(code)
        test_class.insert(code)

    elif op == 'm':
        if p is None:
            print('No records to modify.')
            continue

        str_list = list(p.__dict__.keys())
        attrib = str_list[0]
        id_input = input(f'Record {attrib[1:]} = ')

        # FIX: only proceed (and call update) when user provided an id
        if id_input != "":
            id_val = int(id_input)
            obj = test_class.current(id_val)
            if obj is None:
                print(f'Record {id_val} not found.')
                continue
            print('Leave blank to keep current value, or enter new value')
            for attrib in str_list[1:]:
                value = input(f'{attrib[1:]} = ')
                if value != "":
                    atype = type(getattr(obj, attrib))
                    if atype == datetime.date:
                        setattr(obj, attrib, datetime.date.fromisoformat(value))
                    else:
                        setattr(obj, attrib, atype(value))
            test_class.update(id_val)  # FIX: only called when id_val is valid

    elif op == 'r':
        if p is None:
            print('No records to remove.')
            continue

        str_list = list(p.__dict__.keys())
        attrib = str_list[0]
        atype = type(getattr(p, attrib))
        cod = atype(input(f'{attrib[1:]} = '))
        if cod in test_class.lst:
            print(test_class.obj[cod])
            print('Confirm that you want to delete the record (y/n)?', end='')
            if input().upper() == 'Y':
                test_class.remove(cod)
        else:
            print(f'Record {cod} not found.')

    elif op == 'l':
        # FIX: guard empty list and handle missing keys gracefully
        if len(test_class.lst) == 0:
            print('(no records)')
        else:
            for code in test_class.lst:
                try:
                    print(test_class.obj[code])
                except KeyError:
                    print(f'(record {code} missing from obj dict)')

    elif op == 's':
        if p is None:
            print('No records to sort.')
            continue
        attrib = input('sort by attribute name: ')
        # FIX: use p.__dict__ safely with underscore prefix check
        if '_' + attrib in list(p.__dict__.keys()):
            reverse_input = input('Reverse? (y/N): ')
            reverse = reverse_input.strip().lower() == 'y'
            # FIX: use the private attribute name to get the current id
            first_attr = list(p.__dict__.keys())[0]
            codep = getattr(p, first_attr)
            test_class.sort(attrib, reverse)
            for code in test_class.lst:
                print(test_class.obj[code])
            test_class.current(codep)
        else:
            print(f'Attribute "{attrib}" not found.')

    elif op == 'f':
        if p is None:
            print('No records to search.')
            continue
        attrib = input('Attribute name: ')
        if '_' + attrib in list(p.__dict__.keys()):
            atype = type(getattr(p, '_' + attrib))
            value = atype(input('Value: '))
            fobjs = test_class.find(value, attrib)
            if fobjs and len(fobjs) > 0:
                # FIX: gets the id via the first private attribute, not .id
                first_attr = list(fobjs[0].__dict__.keys())[0]
                test_class.current(getattr(fobjs[0], first_attr))
                for obj in fobjs:
                    print(obj)
            else:
                print('No records found.')
        else:
            print(f'Attribute "{attrib}" not found.')

    else:
        if op != 'q':
            print(f'Unknown option: "{op}"')