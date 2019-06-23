# -*- coding: utf-8 -*-
"""
Created on Fri Jun 21 18:49:46 2019

@author: tim george
"run Manage_members.py" works perfectly for me in IPython console. The UI shows up.
This is a member management program. Use the prompts run through the UI 
and select the options which calls various functions and modifies the .csv file
generated in gen_member_data
"""
# https://gist.github.com/liuw/2407154
import ctypes # Calm down, this has become standard library since 2.5
import threading
import time
import shutil

NULL = 0

def ctype_async_raise(thread_obj, exception):
    found = False
    target_tid = 0
    for tid, tobj in threading._active.items():
        if tobj is thread_obj:
            found = True
            target_tid = tid
            break

    if not found:
        raise ValueError("Invalid thread object")

    ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(target_tid),
        ctypes.py_object(exception)
    )
    # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
    if ret == 0:
        raise ValueError("Invalid thread ID")
    elif ret > 1:
        # Huh? Why would we notify more than one threads?
        # Because we punch a hole into C level interpreter.
        # So it is better to clean up the mess.
        ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, NULL)
        raise SystemError("PyThreadState_SetAsyncExc failed")

import gen_member_data
 
# please install from pip plox
from dateutil.relativedelta import relativedelta
import keyboard
 
from argparse import ArgumentParser
import csv
from datetime import date, datetime
import functools
import os
import re
import sys
import threading
 
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.pyplot import figure
 
statuses = ["None", "Basic", "Silver", "Gold", "Platinum"]
sorted_statuses=sorted(statuses)
 
def sub_record(old_record, new_record, filename='memberdata.csv'):
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=gen_member_data.fieldnames)
        next(reader) # skip header row
        with open('tmp.csv', 'a', newline='') as tmpfile:
            writer=csv.DictWriter(tmpfile, restval='', fieldnames=gen_member_data.fieldnames)
            writer.writeheader()
            for row in reader:
                if row == old_record:
                    writer.writerow(new_record)
                else:
                    writer.writerow(row)
    shutil.move('tmp.csv', filename)
 
def d_from_mdy(s):
    return datetime.strptime(s, '%b %d %Y').date()
 
def dob_valid(record):
    try:
        dob = record['DoB']
        dob_d = d_from_mdy(dob)
        when_18 = dob_d + gen_member_data.imma_adult # Needed to avoid comparing relativedeltas
    except ValueError as e:
        return False
    return date.today() >= when_18
 
def msd_valid(record):
    try:
        dob = record['DoB']
        dob_d = d_from_mdy(dob)
        when_18 = dob_d + gen_member_data.imma_adult # Needed to avoid comparing relativedeltas
    except ValueError as e:
        return False
   
    try:
        msd = record['msd']
        msd_d = d_from_mdy(msd)
    except ValueError as e:
        return False
 
    return (msd_d >= when_18) and (msd_d >= gen_member_data.min_m_date)
 
def med_valid(record):
    if not record.get('med', ''):
        return True
   
    try:
        msd = record['msd']
        msd_d = d_from_mdy(msd)
    except ValueError as e:
        return False
 
    try:
        med = record['med']
        med_d = d_from_mdy(med)
    except ValueError as e:
        return False
   
    return med_d >= msd_d
 
def rdate_valid(record):
    try:
        msd = record['msd']
        msd_d = d_from_mdy(msd)
        max_rdate = msd_d + gen_member_data.renewal_span
    except ValueError as e:
        return False
 
    try:
        rdate = record['rdate']
        rdate_d = d_from_mdy(rdate)
    except ValueError as e:
        return False
   
    return rdate_d <= max_rdate
 
def date_filter(key, min_years, max_years, record):
    d = d_from_mdy(record[key])
    min_year_d = relativedelta(years=min_years) + d
    max_year_d = relativedelta(years=max_years) + d
    today = date.today()
 
    if max_years is None:
        return today >= min_year_d
    else:
        return today >= min_year_d and today <= max_year_d
 
def status_filter(min_status, max_status, record):
    sts = gen_member_data.statuses.index(record['Status'])
    sts_idx_0 = gen_member_data.statuses.index(min_status)
    if max_status:
        sts_idx_1 = gen_member_data.statuses.index(max_status)
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
 
HELP_TEXT = {
    'First name': 'Abcdefg',
    'MI': 'A',
    'Last name': 'Abcdefg',
    'DoB': 'mmm dd YYYY',
    'Address': '123456 Something St',
    'Status': 'None, Basic, Gold, Silver, Platinum',
    'msd': 'mmm dd YYYY (defaults to today)',
    'med': 'mmm dd YYYY (or blank)',
    'rdate': 'mmm dd YYYY (blank defaults to msd + 1 year)',
    'Phone': '0001112222',
    'Email': 'Nothing OR xxx@yyy.com',
    'Notes': 'Anything, really.'
}
 
def init_blank_search_db():
    db = {}
    for k in gen_member_data.fieldnames:
        db[k] = {}
    return db
 
def init_search_db(members, keys=gen_member_data.fieldnames):
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
 
def dob_dups(record, db):
    output = []
 
    if 'DoB' not in record:
        return output
 
    for r in db['DoB'].get(record['DoB'], []):
        fname_same = r['First name'] == record['First name']
        lname_same = r['Last name'] == record['Last name']
        if fname_same and lname_same:
            output.append(r)
    return output
 
def merge_db(filename, db, writer):
    dob_dups = {}
 
    def handle_record(record):
        is_missing = bool(record.keys() - gen_member_data.essential_fields)
        is_invalid = validate_member(record)
        if is_invalid:
            # flag as not okay
            # breaking on DoB, msd, and email
            print(is_invalid)
            return False, 'invalid'
 
 
        is_duplicate = False
        if record['Mno'] in db['Mno']:
            is_duplicate = True
        if record['DoB'] in db['DoB']:
            dob_dups[record['Mno']] = dob_dups(record, db)
            is_duplicate = any(dob_dups[record['Mno']])
 
        if is_duplicate:
            return False, 'duplicate'
 
        if is_missing:
            return False, 'missing'
 
        return True, None
 
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=gen_member_data.fieldnames)
        next(reader) # skip header row
 
        ok_records = []
        invalid_count = 0
        missing_records = []
        dup_records = []
 
 
        for row in reader:
            ok, reason = handle_record(row)
            print(">>", row, ok, reason)
            if ok:
                ok_records.append(row)
            else:
                if reason == 'invalid':
                    invalid_count += 1
                elif reason == 'missing':
                    missing_records.append(row)
                elif reason == 'duplicate':
                    dup_records.append(row)
 
        if invalid_count:
            print("Skipped {} entries".format(invalid_count))
        if ok_records:
            print("Adding {} entries to the DB".format(len(ok_records)))
            for r in ok_records:
                for field in gen_member_data.fieldnames:
                    if r[field] not in db[field]:
                        db[field][r[field]] = []
                    db[field][r[field]].append(r)
                writer.writerow(r)
        if missing_records:
            prompt = "Add {} members with missing attributes? ".format(len(missing_records))
            if input(prompt) in 'Yy':
                print("Adding...")
                for r in missing_records:
                    for field in gen_member_data.fieldnames:
                        if r[field] not in db[field]:
                            db[field][r[field]] = []
                        db[field][r[field]].append(r)
                    writer.writerow(r)
        if dup_records:
            # fix this to to overwrite all old records, including DoB dups
            # for now it just shoves them in
            prompt = "Overwrite {} duplicate members? ".format(len(dup_records))
            if input(prompt) in 'Yy':
                print("Adding...")
                for r in dup_records:
                    dups_by_mno = db['Mno'][r['Mno']][:]
                    del db['Mno'][r['Mno']][:]
 
                    # remove all pointers to overwritten objects in memory (Mno dups)
                    for dr in dups_by_mno:
                        for f in gen_member_data.fieldnames:
                            # Object not in cache anymore? Getting a ValueError for obj not in list
                            try:
                                db[f][dr[f]].remove(dr)
                            except ValueError as e:
                                continue
 
                    # remove all pointers to overwritten objects in memory (DoB dups)
                    for dr in dob_dups[r['Mno']]:
                        for f in gen_member_data.fieldnames:
                            # Object not in cache anymore? Getting a ValueError for obj not in list
                            try:
                                db[f][dr[f]].remove(dr)
                            except ValueError as e:
                                continue
 
                    for field in gen_member_data.fieldnames:
                        if r[field] not in db[field]:
                            db[field][r[field]] = []
                        db[field][r[field]].append(r)
                    writer.writerow(r)
 
def read_db(filename: str='memberdata.csv', db=None):
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=gen_member_data.fieldnames)
        next(reader) # skip header row
        return init_search_db(row for row in reader)
 
def write_db(filename: str='memberdata.csv'):
    with open(filename, 'a', newline='') as csvfile:
        writer=csv.DictWriter(csvfile, restval='', fieldnames=gen_member_data.fieldnames)
        writer.writeheader()
       
 
def search_member(db, kc_pairs):
    matching_values = []
    key_list = list(kc_pairs.keys())
    key, other_keys = key_list[0], key_list[1:]
   
    for db_key_val in db[key]:
        if kc_pairs[key] in db_key_val:
            matching_values.extend(
                r for r in db[key][db_key_val]
                if all(kc_pairs[o] in r[o] for o in other_keys)
            )
   
    return matching_values
 
def validate_member(record, keys=gen_member_data.fieldnames):
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
       writer=csv.DictWriter(csvfile, restval='', fieldnames=gen_member_data.fieldnames)
       midterm_task2.add_member(db, writer=writer)
   
   """
    record = {}
    for field in gen_member_data.fieldnames[1:]:
        field_valid = False
        dup_by_dob = [0]
       
        while (not field_valid) or (dup_by_dob):
            data = input('{0}:: {1}\n> '.format(field, HELP_TEXT.get(field, '')))
           
            if not data:
                if field == 'msd':
                    data = date.today().strftime('%b %d %Y')
                elif field == 'rdate':
                    data = (d_from_mdy(record['msd']) + gen_member_data.year).strftime('%b %d %Y')
                print("Setting", field, "to", data, "...")
 
            record[field] = data
            field_valid = bool(not validate_member(record, keys=[field]))
            # final comprehensive uniqueness check
            # make sure that there's no DoB-Fname-Lname combos same as this
            dup_by_dob = dob_dups(record, db)
 
    record['Mno'] = str(max(int(s.lstrip('0')) for s in (db['Mno'].keys() or ["-1"])) + 1).zfill(6)
 
 
#    record['Mno'] = prev_mno + 1
#    record['Mno'] = max(int(s) for s in search_db['Mno'].keys()) + 1
    for field in gen_member_data.fieldnames:
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
    orecord = record.copy()
    old_member_level = record['Status']
    record['Status'] = 'None'
    record['med'] = date.today().strftime('%b %d %Y')
 
    db['Status'][old_member_level].remove(record)
    db['Status'][record['Status']].append(record)
    sub_record(orecord, record)
 
def mod_status_member(record, db, up=True, writer=None):
    # upgrades member status and adjusts renewal date in place
    orecord = record.copy()
    old_member_level = record['Status']
    status_idx = gen_member_data.statuses.index(record.get('Status', 'None'))
#    print("To upgrade, type: record['Status'] = mod_status_member(record, up=True)\n"
#          "To downgrade, type: record['Status'] = mod_status_member(record, up=False)")
    if up:
        record['Status'] = gen_member_data.statuses[min(status_idx + 1, 4)]
    else:
        record['Status'] = gen_member_data.statuses[max(status_idx - 1, 0)]
 
    record['rdate'] = (date.today() + gen_member_data.year).strftime('%b %d %Y')
    db['Status'][old_member_level].remove(record)
    db['Status'][record['Status']].append(record)
 
    sub_record(orecord, record)
 
def mod_member_data(record, field, db, writer=None):
    orecord = record.copy()
    field_valid = False
    field = input("Field to change? ")
    old_value = record[field]
 
    while not field_valid:
        new_value = input("Please insert new value. ")
        record[field] = new_value
        fix_fields = validate_member(record, keys=[field])
        field_valid = bool(not fix_fields)
 
    if old_value in db[field]:
        db[field][old_value].remove(record)
    if new_value not in db[field]:
        db[field][new_value] = []
    db[field][new_value].append(record)
 
    sub_record(orecord, record)
 
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
 
class BackOutException(BaseException):
    pass
 
def ui_loop(filename: str='memberdata.csv'):
    # remember to store reference to CSV writer at the beginning of the program
    #thread.start_new_thread(check_keys, ())
    running = True
    db = read_db(filename=filename)
 
    # [ ] On-write de-duplication
    # [ ] Incremental import deduplication (allow import to be used for file reading?)
    # [ ] Refactor UI loop to call only functions for heavy backend lifting
 
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, restval='', fieldnames=gen_member_data.fieldnames)
 
        def hotkey_handler():
            ctype_async_raise(threading.main_thread(), BackOutException)
        keyboard.add_hotkey('esc', hotkey_handler, args=tuple())
 
        while running:
            in_screen = False
            try:
                print("> You can hit <Esc><Enter> at any time to go back to the main menu.")
                print("> Or exit the program, if you're at the menu.")
                print("a. Add a new member\n"
                      "b. Remove member\n"
                      "c. Upgrade/Downgrade membership\n"
                      "d. Modify member data\n"
                      "e. Import members (csv or a text file)\n"
                      "f. Search a member\n"
                      "g. Bulk operation\n")
                choice = input("What to do? ")
 
                in_screen = True
                if choice == 'q':
                    running = False
                elif choice == 'a':
                    add_member(db)
                elif choice == 'e':
                    # import text file
                    # it's always appending
                    while True:
                        fpath = input('Filename? ')
                        if os.path.exists(fpath): break
 
                    merge_db(fpath, db, writer)
                elif choice in 'bcdfg':
                    searching = True
                    search_pair = re.compile(r'([^:]+):([^:]+)')
                    while searching:
                        # TODO: Filter by multiple criteria
                        print("Search syntax:: Field name:Criterion[, Field name: Criterion, ...]")
                        kc_pairs = {}
                        query = input("Query? ")
                        for q in query.split(', '):
                            kc = search_pair.fullmatch(q)
                            if kc:
                                kc_pairs[kc.group(1)] = kc.group(2)
 
                        records = search_member(db, kc_pairs)
 
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
                        remove_member(record, db)
 
                    elif choice == 'c':
                        # upgrade/downgrade chosen member
                        subchoice = input("Upgrade, downgrade, or do nothing? (Y/N/*) ")
 
                        if subchoice not in "YyNn": continue
                        up = subchoice in "Yy"
 
                        mod_status_member(record, db, up=up)
 
                    elif choice == 'd':
                        # modify member data
                        field_valid = False
                        subchoice = input("Field to change? ")
                        mod_member_data(record, subchoice, db)
 
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
                            old_values = dict((r['rdate'], (r.copy(), r)) for r in records)
 
                            while True:
                                try:
                                    bump_months = int(input('Bump membership by how many months? '))
                                    break
                                except ValueError as e:
                                    continue
 
                            for r in records:
                                # old_r = r.copy()
                                r['rdate'] = (d_from_mdy(r['rdate']) + relativedelta(months=bump_months)).strftime('%b %d %Y')
 
                            for old_rd, rrs in old_values.items():
                                old_r, new_r = rrs
                                # removes from old rdate by mem pointer?
                                db['rdate'][old_rd].remove(new_r)
                                if new_r['rdate'] not in db['rdate']:
                                    db['rdate'][new_r['rdate']] = []
                                db['rdate'][new_r['rdate']].append(new_r)
                                sub_record(old_r, new_r)
 
                        elif bulk_choice == 'b':
                            ## change membership status
                            subchoice = input("Upgrade, downgrade, or do nothing? (Y/N/*) ")
 
                            if subchoice not in "YyNn": continue
                            up = subchoice in "Yy"
 
                            for r in records:
                                mod_status_member(r, db, up=up)
 
                        elif bulk_choice == 'c':
                            ## delete members
                            for r in records:
                                remove_member(r, db)
                else:
                    in_screen = False
            except BackOutException as e:
                print("Exception handler!", in_screen)
                if in_screen:
                    continue
                else:
                    sys.exit(0)
 
def Status():
    #load the data column we want
    membership_status=np.loadtxt('memberdata.csv', dtype=str, skiprows=1, usecols=[6], delimiter=',')
   
    sorted_status_db=sorted(membership_status)
#    print(sorted_status_db)
    #get a counter of how many statuses we have
    counted=Counter(sorted_status_db)
#    print(counted)
    #make our lists
    number_of_members=[]
    number_of_members_Basic=counted['Basic']
    number_of_members.append(number_of_members_Basic)
    number_of_members_Gold=counted['Gold']
    number_of_members.append(number_of_members_Gold)
    number_of_members_None=counted['None']
    number_of_members.append(number_of_members_None)
    number_of_members_Platinum=counted['Platinum']
    number_of_members.append(number_of_members_Platinum)
    number_of_members_Silver=counted['Silver']
    number_of_members.append(number_of_members_Silver)
    #get our upper limit for the graph
    max_number_of_members=max(number_of_members)
#    print(max_number_of_members)
    #Format our graph and spit it out
    figure(num=None, figsize=(25,15), dpi=80, facecolor='w', edgecolor='k')
    x=np.arange(len(counted))
    width=.3
    plt.bar(x, number_of_members, width=width)
    plt.xticks(x,sorted_statuses)
    plt.ylim(0,max_number_of_members)
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.title('Number of members in membership status', fontsize=30)
    plt.xlabel('Membership status', fontsize=30)
    plt.ylabel('Number of members', fontsize=30, )
    plt.show()
#            
def Age():
    #load our data
    members_age=np.loadtxt('memberdata.csv', dtype='str', skiprows=1, usecols=[4], delimiter=',')
    list_of_ages=[]
    #calculate age of each member
    for i in members_age:
#        print(i)
        # https://stackoverflow.com/a/18215499
        try:
            dt = datetime.strptime(i,'%m-%d-%Y')
            list_of_ages.append((np.datetime64('today')-np.datetime64(dt)).astype('timedelta64[Y]') / np.timedelta64(1, 'Y'))
        except ValueError as e:
            continue
        
 
    sorted_ages=sorted(list_of_ages)
    bin_18_25=[]
    bin_25_35=[]
    bin_35_50=[]
    bin_50_65=[]
    bin_greater_65=[]
    #sort the ages into their bins
    for i in sorted_ages:
        if 18 <= i and i < 25:
            bin_18_25.append(i)
        if 25 <= i and i < 35:
            bin_25_35.append(i)
        if 35 <= i and i < 50:
            bin_35_50.append(i)
        if 50 <= i and i < 65:
            bin_50_65.append(i)
        if 65 <= i:
            bin_greater_65.append(i)
   
    num_members_in_bins_list=[]
    num_18_25=len(bin_18_25)
    num_25_35=len(bin_25_35)
    num_35_50=len(bin_35_50)
    num_50_65=len(bin_50_65)
    num_greater_65=len(bin_greater_65)
    num_members_in_bins_list.append(num_18_25)
    num_members_in_bins_list.append(num_25_35)
    num_members_in_bins_list.append(num_35_50)
    num_members_in_bins_list.append(num_50_65)
    num_members_in_bins_list.append(num_greater_65)
   
#    print(num_members_in_bins_list)
    #get our upper limit for the graph
    max_members_bins=max(num_members_in_bins_list)
    #x-axis
    age_bins=["18-25","25-35","35-50","50-65", ">65"]
    #format graph and spit it out
    x=np.arange(len(age_bins))
    width=.3
    figure(num=None, figsize=(25,15), dpi=80, facecolor='w', edgecolor='k')
    plt.bar(x, num_members_in_bins_list, width=width)
    plt.xticks(x, age_bins)
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.title('Number of members in age categories', fontsize=30)
    plt.xlabel('Age categories', fontsize=30)
    plt.ylabel('Number of members', fontsize=30, )
    plt.ylim(0,max_members_bins)
    plt.show()
       
def Year():
    #load our data
    msd=np.loadtxt('memberdata.csv', dtype='str', skiprows=1, usecols=[7], delimiter=',')
    med=np.loadtxt('memberdata.csv', dtype='str', skiprows=1, usecols=[8], delimiter=',')
    year=np.timedelta64(1, 'Y')
 
    sorted_msd=sorted(msd)
    sorted_med=sorted(med)
   
    #first list of data
    msd_year_list=[]
    for i in sorted_msd:
        #skip row if data not present
        try:
            dt = datetime.strptime(i,'%m-%d-%Y')
            msd_year_list.append(dt.year)
        except ValueError as e:
            continue

 
    x_bin_counter=0
   
    year_bin = Counter(msd_year_list)
    year_span_bin = Counter({(1981, 2020): 0})
   
    for year, count in year_bin.items():
        # For every year instance, check if it falls in the following bins...
        for year_span in year_span_bin:
            # bins are keys in year_span_bin, with idx 0 min year, and idx 1 max year
            if year >= year_span[0] and year <= year_span[1]:
                # if the year meets criteria, put its count of instances into this bin
                year_span_bin[year_span] += count
 
    for i in year_bin:
        for x in range(1981,2020):
            if i == x:
                x_bin_counter+=1
 
    #---------------
    #2nd list of data
    med_year_list_z=[]
 
    for i in sorted_med:
        try:
            dt = datetime.strptime(i,'%m-%d-%Y')
            med_year_list_z.append(dt.year)
        except ValueError as e:
            continue
 
    z_bin_counter=0
   
    year_bin_z = Counter(med_year_list_z)
    msd_year_bin = Counter(msd_year_list)
   
    year_span_bin_z = Counter({(1981, 2020): 0})
   
    for year_z, count in year_bin_z.items():
        # For every year instance, check if it falls in the following bins...
        for year_span_z in year_span_bin_z:
            # bins are keys in year_span_bin, with idx 0 min year, and idx 1 max year
            if year_z >= year_span_z[0] and year_z <= year_span_z[1]:
                # if the year meets criteria, put its count of instances into this bin
                year_span_bin_z[year_span_z] += count
 
    for i in year_bin_z:
        for x in range(1981,2020):
            if i == x:
                z_bin_counter+=1
 
    #---------------------------------------
    #combine the two graphs
    #template from https://matplotlib.org/examples/api/barchart_demo.html
    med_padded = []
    msd_padded = []
    #get the same number of bins for each set of data in case of them them does't have a member in that year
    for year in range(1981, 2021):
        med_padded.append(year_bin_z.get(year, 0))
        msd_padded.append(msd_year_bin.get(year, 0))
   
    figure(num=None, figsize=(25,15), dpi=80, facecolor='w', edgecolor='k')
    width = .25
    x = np.arange(1981, 2021)
    x2 = x+width
   
    z = med_padded
    y = msd_padded
    #format and spit out graph
    ax = plt.subplot(111)
    ax.bar(x, y, width=width, color='b', align='center')
    ax.bar(x2, z, width=width, color='r', align='center')
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels([str(xi) for xi in x], rotation='vertical')
    ax.tick_params(axis='both', which='major', labelsize=20)
    plt.legend(['New members', 'Members Left'], loc='upper center', prop={'size':20})
    plt.title('Number of members added vs left', fontsize=30)
    plt.xlabel('year', fontsize=30)
    plt.ylabel('number of members', fontsize=30, )
   
    plt.show()
 
if __name__ == "__main__":
    aparser = ArgumentParser()
    aparser.add_argument('--graph', type=str, choices=['Age', 'Status', 'Year'])
    args = aparser.parse_args()
    if args.graph is None:
        ui_loop()
    else:
        if args.graph == 'Age':
            print('Age graph')
            Age()
        elif args.graph == 'Status':
            print('Status graph')
            Status()
        elif args.graph == 'Year':
            print('Year graph')
            Year()