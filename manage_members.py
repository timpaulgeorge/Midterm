# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 16:21:42 2019

@author: timpa
"""

from ctype_async_raise import ctype_async_raise
import gen_member_data

# please install from pip plox
from dateutil.relativedelta import relativedelta
import keyboard

import csv
from datetime import date, datetime
import functools
import os
import re
import sys
import threading

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
    os.replace('tmp.csv', filename)

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

if __name__ == "__main__":
    ui_loop()
