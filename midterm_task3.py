# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 12:22:03 2019

@author: Tim
"""
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib.pyplot import figure
#list all status options and sort them
statuses = ["None", "Basic", "Silver", "Gold", "Platinum"]
sorted_statuses=sorted(statuses)

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
    members_age=np.loadtxt('memberdata.csv', dtype='datetime64', skiprows=1, usecols=[4], delimiter=',')
    list_of_ages=[]
    #calculate age of each member
    for i in members_age:
#        print(i)
        # https://stackoverflow.com/a/18215499
        list_of_ages.append((np.datetime64('today')-np.datetime64(i)).astype('timedelta64[Y]') / np.timedelta64(1, 'Y'))

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
    msd=np.loadtxt('memberdata.csv', dtype='datetime64', skiprows=1, usecols=[7], delimiter=',')
    med=np.loadtxt('memberdata.csv', dtype='datetime64', skiprows=1, usecols=[8], delimiter=',')
    year=np.timedelta64(1, 'Y')

    sorted_msd=sorted(msd)
    sorted_med=sorted(med)
    
    #first list of data
    msd_year_list=[]
    for i in sorted_msd:
        #skip row if data not present
        if i.astype(object) is None:
            continue
        year=i.astype(object).year
        msd_year_list.append(year)

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
        if i.astype(object) is None:
            continue
        year_z=i.astype(object).year
        med_year_list_z.append(year_z)

    z_bin_counter=0
    
    year_bin_z = Counter(med_year_list_z)
    msd_year_bin = Counter(msd_year_list)
    
    year_span_bin_z = Counter({(1981, 2020): 0})
    
    for year, count in year_bin_z.items():
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
