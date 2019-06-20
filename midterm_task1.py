# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 12:51:50 2019

@author: timpa
"""
from dateutil.relativedelta import relativedelta

import csv
import string
import random
from random import randint
from datetime import date, timedelta
#with open(filename, 'a', newline='') as csvfile:
#generate all header stuff

fieldnames = ['Mno', 'First name', 'MI', 'Last name', 'DoB', 'Address', 'Status', 'msd', 'med', 'rdate', 'Phone', 'Email', 'Notes']
nonessential_fields = {'med', 'Email', 'Notes', 'Address', 'MI'}
First_name_list=["jay", "jim", "roy", "axel", "billy", "charlie", "jax", 
"gina", "paul","ringo", "ally", "nicky", "cam", "ari", "trudie", "cal", "carl", 
"lady", "lauren","ichabod", "arthur", "ashley", "drake", "kim", "julio", "lorraine", 
"floyd", "janet","lydia", "charles", "pedro", "bradley"]

Last_name_list=["barker", "style", "spirits", "murphy", "blacker", "bleacher", "rogers",
"warren", "keller","Gaynelle","Hanna","Maud","Sang","Dawne","Florencio","Elvin"
,"Deangelo","Nannette","Jack","Lucy","Tyesha","Hal","Emory","Irma","Leticia","Imelda","Synthia","Adelaida"]
statuses = ["None", "Basic", "Silver", "Gold", "Platinum"]


min_m_date = date(1981, 1, 1)
#min_b_date = date(min_m_date.year - 18, min_m_date.month, min_m_date.day)
year = relativedelta(days=1)
lifespan = 80 * year
renewal_span = 5 * year
imma_adult = 18 * year
min_b_date = date.today() - imma_adult

def rndm_bdate():
    return min_b_date - timedelta(days=randint(0, lifespan.days))

def rndm_mdate(bdate):
    is_18_when = bdate + imma_adult
    
    if is_18_when > min_m_date:
        return is_18_when + timedelta(days=random.randint(0, (date.today() - is_18_when).days))
    else:
        return min_m_date + timedelta(days=random.randint(0, (date.today() - min_m_date).days))

def rndm_edate(mdate):
    return mdate + timedelta(days=random.randint(0, (date.today() - mdate).days))

def rndm_rdate(mdate):
    return mdate + timedelta(days=randint(0, renewal_span.days))

def rndm_addr():
    address_fmt = "{0} {1} {2}"
    street_no = str(random.randint(0, 1E5-1)).zfill(5)
    street_name = ''.join(random.choices(string.ascii_letters, k=randint(4, 10)))
    street_type = random.choice(["St", "Ave", "Rd", "Blvd", "Dr"])
    return address_fmt.format(street_no, street_name, street_type)

def rndm_record(used_ids=set(), used_ppl=set()):
    mno = str(randint(0,999999)).zfill(6)
    if mno in used_ids:
        while mno in used_ids:
            mno = str(randint(0,999999)).zfill(6)
    used_ids.add(mno)
    
    fname = random.choice(First_name_list)
    lname = random.choice(Last_name_list)
    dob = rndm_bdate()
    ppl = (fname, lname, dob)
    if ppl in used_ppl:
        while ppl in used_ppl:
            fname = random.choice(First_name_list)
            lname = random.choice(Last_name_list)
            dob = rndm_bdate()
            ppl = (fname, lname, dob)
    used_ppl.add(ppl)
    
    msd = rndm_mdate(dob)
    med = rndm_edate(msd)

    return {
        'First name': fname,
        'Last name': lname,
        'Mno': mno,
        'MI': random.choice(string.ascii_uppercase),
        'DoB': dob,
        'Address': rndm_addr(),
        'Status': random.choice(statuses),
        'msd': msd,
        'med': med,
        'rdate': rndm_rdate(msd),
        'Phone': str(randint(0, 1E10-1)).zfill(10),
    }
    


"""
Mno:
    239832:
        {member deets}
    120921:
        {member deets 2}
Last name:
    Harry:
        {member deets}
    Barry:
        {member deets 2}
"""


def gen_member_data(filename: str='memberdata.csv', num_mems: int=1000):
    with open(filename, 'w', newline='') as csvfile:
        writer=csv.DictWriter(csvfile, restval='missing this category', fieldnames=fieldnames)
        writer.writeheader()
        used_ids = set()
        used_ppl = set()
        for i in range(num_mems):
            record = rndm_record(used_ids=used_ids, used_ppl=used_ppl)
            writer.writerow(record)

if __name__ == "__main__":
    gen_member_data()
