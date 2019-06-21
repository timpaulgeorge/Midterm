# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 16:21:42 2019

@author: timpa
"""

import midterm_task1

# please install from pip plox
from dateutil.relativedelta import relativedelta
import keyboard

import csv
from datetime import date
import functools
import os
import re
import sys

def dob_valid(record):
    try:
        dob = record['DoB']
        dob_d = date.fromisoformat(dob)
        when_18 = dob_d + midterm_task1.imma_adult # Needed to avoid comparing relativedeltas
    except ValueError as e:
        return False
    return date.today() >= when_18

def msd_valid(record):
    try:
        dob = record['DoB']
        dob_d = date.fromisoformat(dob)
        when_18 = dob_d + midterm_task1.imma_adult # Needed to avoid comparing relativedeltas
    except ValueError as e:
        return False
    
    try:
        msd = record['msd']
        msd_d = date.fromisoformat(msd)
    except ValueError as e:
        return False

    return (msd_d >= when_18) and (msd_d >= midterm_task1.min_m_date)

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
        max_rdate = msd_d + midterm_task1.renewal_span
    except ValueError as e:
        return False

    try:
        rdate = record['rdate']
        rdate_d = date.fromisoformat(rdate)
    except ValueError as e:
        return False
    
    return rdate_d <= max_rdate

def date_filter(key, min_years, max_years, record):
    d = date.fromisoformat(record[key])
    min_year_d = relativedelta(years=min_years) + d
    max_year_d = relativedelta(years=max_years) + d
    today = date.today()

    if max_years is None:
        return today >= min_year_d
    else:
        return today >= min_year_d and today <= max_year_d

def status_filter(min_status, max_status, record):
    sts = midterm_task1.statuses.index(record['Status'])
    sts_idx_0 = midterm_task1.statuses.index(min_status)
    if max_status:
        sts_idx_1 = midterm_task1.statuses.index(max_status)
        return sts >= min_status and sts <= max_status
    else:
        return sts >= min_status

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

def merge_db(filename, db, writer):
    dob_dups = {}

    def handle_record(record):
        is_missing = bool(record.keys() - midterm_task1.essential_fields)
        is_invalid = validate_member(record)
        if is_invalid:
            # flag as not okay
            return False, 'invalid'


        is_duplicate = False
        if record['Mno'] in db['Mno']:
            is_duplicate = True
        if record['DoB'] in db['DoB']:
            dob_dups[record] = [
                r for r in db['DoB'].get(record['DoB'], []) if
                r['First name'] == record['First name'] and
                r['Last name'] == record['Last name']
            ]
            is_duplicate = any(dob_dups[record])

        if is_duplicate:
            return False, 'duplicate'

        if is_missing:
            return False, 'missing'

        return True, None

    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=midterm_task1.fieldnames)
        next(reader) # skip header row

        ok_records = []
        invalid_count = 0
        missing_records = []
        dup_records = []


        for row in reader:
            ok, reason = handle_record(row)
            if ok:
                ok_records.append(row)
            else:
                if reason == 'invalid':
                    invalid_count += 1
                elif reason == 'missing':
                    missing_records.append(row)
                elif reason == 'duplicate':
                    dup_records.append(row)

        rows = ok_records
        prompt = "Add {} members with missing attributes? ".format(len(missing_records))
        if input(prompt) in 'Yy':
            rows = chain(rows, missing_records)
            for r in rows:
                for field in midterm_task1.fieldnames:
                    if r[field] not in db[field]:
                        db[field][r[field]] = []
                    db[field][r[field]].append(r)
                writer.writerow(r)

        prompt = "Overwrite {} duplicate members? ".format(len(dup_records))
        if input(prompt) in 'Yy':
            for r in dup_records:
                dups_by_mno = db['Mno'][r['Mno']][:]
                del db['Mno'][r['Mno']][:]

                # remove all pointers to overwritten objects in memory (Mno dups)
                for dr in dups_by_mno:
                    for f in midterm_task1.fieldnames:
                        db[f][dr[f]].remove(dr)

                # remove all pointers to overwritten objects in memory (DoB dups)
                for dr in dob_dups[r]:
                    for f in midterm_task1.fieldnames:
                        db[f][dr[f]].remove(dr)

                for field in midterm_task1.fieldnames:
                    if r[field] not in db[field]:
                        db[field][r[field]] = []
                    db[field][r[field]].append(r)
                writer.writerow(r)

def read_db(filename: str='memberdata.csv', db=None):
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

def validate_member(record, keys=midterm_task1.fieldnames):
    fix_these_fields = []

    for field in keys:
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
        
        while not field_valid:
            data = input('{0}:: '.format(field))
            
            if not data:
                if field == 'msd':
                    data = date.today().isoformat()
                elif field == 'rdate':
                    data = (date.fromisoformat(record['msd']) + midterm_task1.year).isoformat()
                print("Setting", field, "to", data, "...")

            record[field] = data
            field_valid = bool(not validate_member(record, keys=[field]))

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

def remove_member(record, db, writer=None):
    old_member_level = record['Status']
    record['Status'] = 'None'
    record['med'] = date.today().isoformat()

    db['Status'][old_member_level].remove(record)
    db['Status'][record['Status']].append(record)
    if writer:
        writer.writerow(record)

def mod_status_member(record, db, up=True, writer=None):
    # upgrades member status and adjusts renewal date in place
    old_member_level = record['Status']
    status_idx = midterm_task1.statuses.index(record.get('Status', 'None'))
#    print("To upgrade, type: record['Status'] = mod_status_member(record, up=True)\n"
#          "To downgrade, type: record['Status'] = mod_status_member(record, up=False)")
    if up:
        record['Status'] = midterm_task1.statuses[min(status_idx + 1, 4)]
    else:
        record['Status'] = midterm_task1.statuses[max(status_idx - 1, 0)]

    record['rdate'] = (date.today() + midterm_task1.year).isoformat()
    db['Status'][old_member_level].remove(record)
    db['Status'][record['Status']].append(record)

    if writer:
        writer.writerow(record)

def mod_member_data(record, field, db, writer=None):
    field_valid = False
    field = input("Field to change? ")
    old_value = record[field]

    while not field_valid:
        new_value = input("Please insert new value. ")
        record[field] = new_value
        fix_fields = validate_member(record, keys=[field])
        field_valid = bool(not fix_fields)

    db[field][old_value].remove(record)
    db[field][new_value].append(record)

    if writer:
        writer.writerow(record)

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
    """ Currently not used. """
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

        def hotkey_handler():
            print("I am amazing... or something.")
        # keyboard.add_hotkey('esc', hotkey_handler, args=tuple())

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
                # import text file
                # it's always appending
                while True:
                    fpath = input('Filename? ')
                    if os.path.exists(fpath): break

                merge_db(fpath, db, writer)
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
                            break
                        elif pchoice in 'Nn':
                            continue
                            # go back up to search
                    else:
                        print(records)
                        break

                member_edited = 0
                record = None
                if choice in 'bcd':
                    while True:
                        try:
                            member_edited = int(input("Choose a member (1-{0}). ".format(len(records))))
                            break
                        except ValueError as e:
                            continue
                    if member_edited <= 0: continue
                    record = records[member_edited - 1]

                searching = False

                if choice == 'b':
                    # remove member
                    subchoice = input("Sure you wanna delete them? (Y/N) ")

                    if subchoice not in "Yy": continue
                    remove_member(record, db, writer=writer)

                elif choice == 'c':
                    # upgrade/downgrade chosen member
                    subchoice = input("Upgrade, downgrade, or do nothing? (Y/N/*) ")

                    if subchoice not in "YyNn": continue
                    up = subchoice in "Yy"

                    mod_status_member(record, db, up=up, writer=writer)

                elif choice == 'd':
                    # modify member data
                    field_valid = False
                    subchoice = input("Field to change? ")

                    mod_member_data(record, subchoice, db, writer=writer)

                elif choice == 'f':
                    # member search only
                    print("Heading back to menu...")

                elif choice == 'g':
                    # bulk operation
                    print((
                        "a. Push renewal date.\n"
                        "b. Change membership status.\n"
                        "c. Delete members.\n"
                    ))
                    bulk_choice = input("Which bulk op? ")

                    ## Restrict to the following
                    print((
                        "(age). Members for a given age range.\n"
                        "(member). Members who have been members for more than a certain period.\n"
                        "(status). Members with certain membership status.\n"
                        "(age) X Y, (member) X Y, (status) X Y\n"
                        "(age) X+, (member) X+, (status) X\n"
                    ))

                    filter_syntax = input('Filter? ')
                    age_filter = re.compile(r'age (\d+)( \d+)?', flags=re.I)
                    mem_filter = re.compile(r'member (\d+)( \d+)?', flags=re.I)
                    sts_filter = re.compile(r'status (none|basic|silver|gold|platinum)( none|basic|silver|gold|platinum)?')

                    filter_parts = filter_syntax.split(', ')
                    criterion = []
                    for f in filter_parts:
                        age_f = age_filter.fullmatch(f)
                        mem_f = mem_filter.fullmatch(f)
                        sts_f = sts_filter.fullmatch(f)

                        if age_f:
                            min_years = int(age_f.groups()[0])
                            max_years = int(age_f.groups()[1]) if age_f.groups()[1] else None
                            criterion.append(functools.partial(date_filter, 'DoB', min_years, max_years))
                        elif mem_f:
                            min_years = int(mem_f.groups()[0])
                            max_years = int(mem_f.groups()[1]) if mem_f.groups()[1] else None
                            criterion.append(functools.partial(date_filter, 'msd', min_years, max_years))
                        elif sts_f:
                            min_status = sts_f.groups()[0].strip().title()
                            max_status = sts_f.groups()[1].strip().title() if sts_f.groups()[1] else None
                            criterion.append(functools.partial(status_filter, min_status, max_status))

                    records = [ r for r in records if all(map(lambda x: x(r), criterion)) ]

                    if bulk_choice == 'a':
                        ## push renewal date
                        old_values = [ (r['rdate'], r) for r in records ]

                        while True:
                            try:
                                bump_months = int(input('Bump membership by how many months? '))
                                break
                            except ValueError as e:
                                continue

                        for r in records:
                            r['rdate'] = (date.fromisoformat(r['rdate']) + relativedelta(months=bump_months)).isoformat()
                        for ov in old_values:
                            db['rdate'][ov[0]].remove(ov[1])
                            if ov[1]['rdate'] not in db['rdate']:
                                db['rdate'][ov[1]['rdate']] = []
                            db['rdate'][ov[1]['rdate']].append(ov[1])
                            writer.writerow(ov[1])

                    elif bulk_choice == 'b':
                        ## change membership status
                        subchoice = input("Upgrade, downgrade, or do nothing? (Y/N/*) ")

                        if subchoice not in "YyNn": continue
                        up = subchoice in "Yy"

                        for r in records:
                            mod_status_member(r, db, up=up, writer=writer)

                    elif bulk_choice == 'c':
                        ## delete members
                        for r in records:
                            remove_member(r, db, writer=writer)

if __name__ == "__main__":
    ui_loop()
