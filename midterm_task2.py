# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 16:21:42 2019

@author: timpa
"""

import midterm_task1

# please install from pip plox
import keyboard

import csv
from datetime import date
import re
import sys
import _thread as thread

def dob_valid(record):
    try:
        dob = record['DoB']
        dob_d = date.fromisoformat(dob)
    except ValueError as e:
        return False
    return (date.today() - dob_d) >= midterm_task1.imma_adult

def msd_valid(record):
    try:
        dob = record['DoB']
        dob_d = date.fromisoformat(dob)
    except ValueError as e:
        return False
    
    try:
        msd = record['msd']
        msd_d = date.fromisoformat(msd)
    except ValueError as e:
        return False

    return ((msd_d - dob_d) >= midterm_task1.imma_adult) and (msd_d >= midterm_task1.min_m_date)

def med_valid(record):
    if not record.get('med', ''):
        return True
    
    try:
        msd = record['msd']
        msd_d = date.fromisoformat(msd)
    except ValueError as e:
        return False

    try:
        med = record['med']
        med_d = date.fromisoformat(med)
    except ValueError as e:
        return False
    
    return med_d > msd_d

def rdate_valid(record):
    try:
        msd = record['msd']
        msd_d = date.fromisoformat(msd)
    except ValueError as e:
        return False

    try:
        rdate = record['rdate']
        rdate_d = date.fromisoformat(rdate)
    except ValueError as e:
        return False
    
    return (rdate_d - msd_d) <= midterm_task1.renewal_span

MEMBER_FORMAT = {
    # 'Mno': re.compile(r'\d{6}'),
    'First name': re.compile(r'[A-Za-z]+'),
    'MI': re.compile(r'[A-Z]'),
    'Last name': re.compile(r'[A-Za-z]+'),
    'DoB': dob_valid,
    'Address': re.compile(r'\d+ [A-Za-z]+ (St|Ave|Rd|Blvd|Dr)'),
    'Status': re.compile(r'(Basic|Silver|Gold|Platinum|None)'),
    'msd': msd_valid,
    'med': med_valid,
    'rdate': rdate_valid,
    'Phone': re.compile(r'\d{10}'),
    'Email': re.compile(r'([^@]+@[a-z]+\.(com|org|net)|^$)'),
}

def init_blank_search_db():
    db = {}
    for k in midterm_task1.fieldnames:
        db[k] = {}
    return db

def init_search_db(members, keys=midterm_task1.fieldnames):
    # Extract here later
    
    # In-memory view of membership database
    db = {}

    # For every member...
    for m in members:
        # and every member data field...
        for k in keys:
            # Create a dictionary listing all values of field
            if k not in db.keys():
                db[k] = {}
            # With a list with pointers to objects possessing said value
            if m[k] not in db[k].keys():
                db[k][m[k]] = []

            # Then insert a pointer to the member object into the search DB
            db[k][m[k]].append(m)
            
    # To search this DB for Mno:123090, use code...
    # db['Mno']['123090'] <- results are the stuff inside

    return db

def read_db(filename: str='memberdata.csv'):
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=midterm_task1.fieldnames)
        next(reader) # skip header row
        return init_search_db(row for row in reader)

def write_db(filename: str='memberdata.csv'):
    with open(filename, 'a', newline='') as csvfile:
        writer=csv.DictWriter(csvfile, restval='', fieldnames=midterm_task1.fieldnames)
        writer.writeheader()
        

def search_member(db, key, criterion):
    matching_values = []
    
    for db_key_val in db[key]:
        if criterion in db_key_val:
            matching_values.extend(db[key][db_key_val])   
    
    return matching_values

def validate_member(record):
    fix_these_fields = []

    for field in midterm_task1.fieldnames:
        validator = MEMBER_FORMAT.get(field, None)
        field_valid = True

        if type(validator) is re.Pattern:
            field_valid = validator.fullmatch(record.get(field, ''))
        elif callable(validator):
            field_valid = validator(record)
                
        if not field_valid:
            fix_these_fields.append(field)

    return fix_these_fields

def add_member(db, writer=None):
    """
    
    db = midterm_task2.read_db()
    with open('memberdata.csv', 'a', newline='') as csvfile:
        writer=csv.DictWriter(csvfile, restval='', fieldnames=midterm_task1.fieldnames)
        midterm_task2.add_member(db, writer=writer)
    
    """
    record = {}
    for field in midterm_task1.fieldnames[1:]:
        field_valid = False
        validator = MEMBER_FORMAT.get(field, None)
        
        while not field_valid:
            data = input('{0}:: '.format(field))
            field_valid = True
            
            if not data:
                # remember you can skip med when initializing
                if field == 'msd':
                    data = date.today().isoformat()
                elif field == 'rdate':
                    data = (date.fromisoformat(record['msd']) + midterm_task1.year).isoformat()
                print("Setting", field, "to", data, "...")

            record[field] = data
            
            if type(validator) is re.Pattern:
                field_valid = validator.fullmatch(data)
            elif callable(validator):
                field_valid = validator(record)

    record['Mno'] = str(max(int(s.lstrip('0')) for s in (db['Mno'].keys() or ["-1"])) + 1).zfill(6)
#    record['Mno'] = prev_mno + 1
#    record['Mno'] = max(int(s) for s in search_db['Mno'].keys()) + 1
    for field in midterm_task1.fieldnames:
        if record[field] not in db[field]:
            db[field][record[field]] = []
        db[field][record[field]].append(record)
    
    if writer:
        writer.writerow(record)
    
    # assuming you do this in the UI
    # update_normal_db(record)
    # update_search_db(record)
    
    return record

def remove_member():
    pass

def mod_status_member(record, up=True):
    # upgrades member status and adjusts renewal date in place
    status_idx = midterm_task1.statuses.index(record.get('Status', 'None'))
#    print("To upgrade, type: record['Status'] = mod_status_member(record, up=True)\n"
#          "To downgrade, type: record['Status'] = mod_status_member(record, up=False)")
    if up:
        record['Status'] = midterm_task1.statuses[min(status_idx + 1, 4)]
    else:
        record['Status'] = midterm_task1.statuses[max(status_idx - 1, 0)]

    record['rdate'] = (date.today() + midterm_task1.year).isoformat()

def mod_member_data():
    pass

# Handle key checks in separate thread:: https://stackoverflow.com/a/55822238
# Escape key detect:: https://stackoverflow.com/questions/21653072/exiting-a-loop-by-pressing-a-escape-key
def readch():
    """ Get a single character on Windows.
    see http://msdn.microsoft.com/en-us/library/078sfkak
    """
    ch = msvcrt.getch()
    if ch in b'\x00\xe0':  # arrow or function key prefix?
        ch = msvcrt.getch()  # second call returns the actual key code
    return ch


def check_keys():
    while True:  # making a loop
        try:  # used try so that if user pressed other than the given key error will not be shown
            if keyboard.is_pressed('esc'):  # if key 'q' is pressed 
                print('You Pressed A Key!')
                break  # finishing the loop
            else:
                pass
        except:
            break

def ui_loop(filename: str='memberdata.csv'):
    # remember to store reference to CSV writer at the beginning of the program
    #thread.start_new_thread(check_keys, ())
    running = True
    db = read_db(filename=filename)

    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, restval='', fieldnames=midterm_task1.fieldnames)

        while running:
            print("a. Add a new member\n"
                  "b. Remove member\n"
                  "c. Upgrade/Downgrade membership\n"
                  "d. Modify member data\n"
                  "e. Import members (csv or a text file)\n"
                  "f. Search a member\n"
                  "g. Bulk operation\n")
            choice = input("What to do? ")
            
            if choice == 'q':
                running = False
            elif choice == 'a':
                add_member(db, writer=writer)
            elif choice == 'e':
                pass
            elif choice in 'bcdfg':
                searching = True
                while searching:
                    key = input("Field name? ")
                    criterion = input("Criterion? ")
                    records = search_member(db, key, criterion)
                    
                    if len(records) > 10:
                        pchoice = input("More than 10 members matching the criteria, print? (Y/N)")
                        
                        if pchoice in 'Yy':
                            print(records)
                        elif pchoice in 'Nn':
                            pass
                            # go back up to search

                if choice == 'b':
                    pass
                elif choice == 'c':
                    pass
                    # then choose an item
                    
                    mod_status_member(record, up=up)
                    writer.writerow(record)
                elif choice == 'd':
                    pass
                
                elif choice == 'f':
                    # member search only
                    pass

                elif choice == 'g':
                    pass

if __name__ == "__main__":
    ui_loop()