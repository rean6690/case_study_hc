import os
import requests
import numpy as np
import pandas as pd

from datetime import datetime
from datetime import date
from datetime import timedelta
import matplotlib.pyplot as plt
#from configparser import ConfigParser
#config = ConfigParser()
#config.read('config.ini')

import xlrd
excel_config = xlrd.open_workbook("fallstudie.xlsm")
first_sheet = excel_config.sheet_by_index(0)

#api info: https://open-platform.theguardian.com/documentation/
from_date = first_sheet.cell_value(1,0)

today = date.today()
keyword = first_sheet.cell_value(0,0)
my_path = first_sheet.cell_value(2,0)

#from_date = config.get('DEFAULT', 'from_date')
#keyword = config.get('DEFAULT', 'keyword')
#my_path = config.get('DEFAULT', 'path') + "keyword_%s\\" %keyword

#print(from_date2)
#print(from_date)


my_path = my_path + "keyword_%s\\" %keyword
#my_path="C:\\users\\work\\desktop\\fallstudie_holidaycheck\\keyword_%s\\" %keyword
API_ENDPOINT = "http://content.guardianapis.com/search"
page_size = 200 #max=200
api_key = "f0f5a5fc-3f60-4dc4-9956-61f3b9c2c5b9"
parameter = {
    "q": keyword,
    "from-date": from_date,
    "order-by": "oldest",
    "show-fields": "none",
    "page-size": page_size,
    "currentPage": "all",
    "api-key": api_key,
    "page": 1
} 
response = requests.get(API_ENDPOINT, parameter)
data_json = response.json()
      
total_count = data_json["response"]["total"] #Anzahl der Artikel
total_pages = data_json["response"]["pages"] #Anzahl der Pages
print(total_count,"gefundene Artikel mit keyword:", keyword, "Zeitraum:",from_date,"-",today)

data = pd.DataFrame(index = range(total_count), columns = ["date","section","url"])
n=0
for pages in range(total_pages-1):
    pages +=1
    #get_data
    parameter["page"] = pages 
    response = requests.get(API_ENDPOINT, parameter)
    data_json = response.json()
    
    for i in range(page_size):
        #time
        date = data_json["response"]["results"][i]["webPublicationDate"]
        date, time = date.split("T")
        date = datetime.strptime(date, '%Y-%m-%d')
        data.at[n+i,"date"] = date
        #section
        data.at[n+i,"section"] = data_json["response"]["results"][i]["sectionName"]
        #url
        data.at[n+i,"url"] = data_json["response"]["results"][i]["webUrl"]
    n=pages*page_size
    
#get_data    
parameter["page"] = total_pages #last page
response = requests.get(API_ENDPOINT, parameter)
data_json = response.json()

rest = total_count -((total_pages-1)*page_size)
for i in range(rest):
    #time
    date = data_json["response"]["results"][i]["webPublicationDate"]
    date, time = date.split("T")
    date = datetime.strptime(date, '%Y-%m-%d')
    data.at[n+i,"date"] = date
    #section
    data.at[n+i,"section"] = data_json["response"]["results"][i]["sectionName"]
    #url
    data.at[n+i,"url"] = data_json["response"]["results"][i]["webUrl"]
    
#dataframe mit Anzahl der veröffentichten Artikel pro Tag 
date_freq = data["date"].value_counts()
date_freq = pd.DataFrame({"date":date_freq.index, "count":date_freq.values})
date_freq = date_freq.sort_values(by="date")

#fehlende Daten hinzufügen (=Tage an denen kein Artikel erschienen ist), 
#um Verzerrung in grafischer Darstellung und Durchschnittsberechnung zu vermeinden
r = pd.date_range(start=date_freq.date.min(), end=date_freq.date.max())
date_freq_full = date_freq.set_index('date').reindex(r).fillna(0.0).rename_axis('date').reset_index()

#Durchschnitt der veröffentlichten Artikel pro Tag (Tage ohne Veröffentlichung zählen auch)
mean = round(date_freq_full["count"].mean(),2)
print("Im Schnitt werden",mean,"Artikel pro Tag mit dem Keyword",keyword,"veröffentlicht.\n")

#In welcher section werden die meisten Artikel veröffentlicht?
section_freq = data["section"].value_counts()
print("Die section:",section_freq.index[0], "ist mit",section_freq[0],"Artikeln die am häufigsten vorkommende section.\n" )
section_freq = pd.DataFrame({"section":section_freq.index, "count":section_freq.values, "percent":section_freq.values/total_count})
section_freq = section_freq.round({'percent': 2})
print(section_freq.head())

if len(section_freq)>5:  
    labels = section_freq["section"].head(5).values
    sizes = section_freq["percent"].head(5).values
    labels = np.append (labels, "others")
    sizes = np.append (sizes, sum(section_freq.tail(len(section_freq)-5)["percent"]))
else:
    labels = section_freq["section"].values
    sizes = section_freq["percent"].values

fig1, ax1 = plt.subplots()
ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
plt.show()


#99% Percentil um Ausreißer zu definieren
percentil = np.percentile(date_freq_full["count"], 99)
max_count = date_freq_full[date_freq_full["count"]>percentil]

#plot
plt.figure(figsize=(20,10))
plt.plot_date(date_freq_full["date"], date_freq_full["count"],linestyle="solid", marker="None")
plt.title("Veröffentlichte Artikel von The Guardian mit dem keyword: "+str(keyword)+ "\nzeitliche Entwicklung der Anzahl der Artikel, Zeitraum: "+str(from_date)+" bis "+str(today),size=20)
plt.ylabel("count",size=15)
plt.xlabel("date",size=15)
plt.grid(True)
#plt.grid(which='major', linestyle='-', linewidth='0.5', color='black')
#plt.grid(which='minor', linestyle=':', linewidth='0.2', color='black')
plt.tick_params(which='both',top=False,left=False,right=False,bottom=True) 
plt.ylim(0, date_freq["count"].max(axis=0)+1)
plt.xlim(from_date,today+timedelta(days=30))
plt.xticks(rotation=45)


for index, row in max_count.iterrows():
    date = row["date"]
    date = date.strftime("%Y-%m-%d")
    count = row["count"]
    plt.annotate(date, xy=(date, count), xytext=(date, count),
            arrowprops=dict(facecolor="red", shrink=0.01),
            )
    
try: 
    os.mkdir(my_path)  
except OSError:
       plt.savefig(my_path + "report_%s.pdf" %today)
plt.savefig(my_path + "report_%s.pdf" %today)
plt.show()

#get url from every article from corresponding date
pd.set_option('display.max_colwidth', -1)
url = data[data["date"]==max_count["date"].iloc[0]]
url = url["url"]
url    