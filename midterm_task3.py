# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 12:22:03 2019

@author: Tim
"""
import numpy as np
import matplotlib.pyplot as plt
import datetime
from datetime import date
import midterm_task2


#def status_graph():
#    plt.bar(membership_status, number_of_members)
#    plt.xticks(np.arange(4), "Basic","Silver","Gold","Platinum")
#    plt.xlabel('membership status')
#    plt.ylabel('number of members')
#    plt.ylim(0,#max number of members)
#             
#def age_graph:
#    plt.bar(age, number_of_members)
#    plt.xticks(np.arange(5), "18-25","25-35","35-50","50-65", ">65")
#    plt.xlabel('age categories')
#    plt.ylabel('number of members')
#    plt.ylim(0,#max number of members)
#             
#def year_graph:
#    legend=['new members added', 'members left']
#    #change the means to members added vs left
#    womenMeans = (25, 32, 34, 20, 25)
#    menMeans = (20, 35, 30, 35, 27)
#    year = [1981,1982,1983,1984,1985,1986,1987,1988,1989,1990]
#    #Calculate optimal width
#    width = np.min(np.diff(year))/4
#    
#    fig = plt.figure()
#    ax = fig.add_subplot(111)
#    ax.bar(year-width,womenMeans,width,color='b',label='-Ymin')
#    ax.bar(year,menMeans,width,color='r',label='Ymax')
#    ax.set_xlabel('years')
#    ax.set_ylabel('number of members')
#    plt.legend(legend,loc=1)
#    plt.show()
#    plt.bar(year,new_members,members_left)
#    plt.xticks(np.arange(1981,2019))
#    plt.xlabel('years')
#    plt.ylabel('number of members')

legend=['new members added', 'members left']
womenMeans = (25, 32, 34, 20, 25)
menMeans = (20, 35, 30, 35, 27)
year = [1981,1982,1983,1984,1985]
start = datetime.datetime(1981,1,1)
end = datetime.datetime.today()
daterange = [start + datetime.timedelta(days=x) for x in range(0, (end-start).days)]
#Calculate optimal width
width = np.min(np.diff(daterange))/4
daterange = str([start + datetime.timedelta(days=x) for x in range(0, (end-start).days)])
fig = plt.figure()
ax = fig.add_subplot(111)
ax.bar(daterange-width,womenMeans,width,color='b',label='-Ymin')
ax.bar(daterange,menMeans,width,color='r',label='Ymax')
ax.set_xlabel('years')
ax.set_ylabel('number of members')
plt.legend(legend,loc=1)
plt.show()

#python Manage_members.py --graph <mode>