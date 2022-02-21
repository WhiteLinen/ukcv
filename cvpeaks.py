# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import io
import requests
from datetime import datetime

import bokeh
from bokeh.io import show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, RangeTool, HoverTool
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.plotting import figure, output_file, save
from bokeh.models import LinearAxis, Range1d, PreText
from bokeh.transform import dodge

saved_data_fn='data.csv'
    
def download_data(data_fn):
    try:
        data_url='https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&'+\
        'metric=covidOccupiedMVBeds&metric=hospitalCases&'+\
        'metric=newAdmissions&metric=newCasesByPublishDate&'+\
        'metric=newDeaths28DaysByPublishDate&format=csv'
    
        s=requests.get(data_url).content
        data=pd.read_csv(io.StringIO(s.decode('utf-8')))
        data=data.drop(['areaCode','areaName', 'areaType'], axis=1).set_index('date')
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()
        renames={'hospitalCases': 'inHospital',
                 'covidOccupiedMVBeds': 'mvBeds',
                 'newAdmissions': 'admissions',                 
                 'newCasesByPublishDate': 'newCases',
                 'newDeaths28DaysByPublishDate': 'deaths'}

        data=data.rename(columns=renames)
       
        data.to_hdf(data_fn, 'data')
        data.to_csv(saved_data_fn)
        
        print('Fresh data downloaded and save to ', data_fn, saved_data_fn)
        return data
    except Exception as e:
        print('Error downloading', e)
        return None


today_fn=datetime.today().strftime('data_%Y%m%d.h5')

try:
    data = pd.read_hdf(today_fn)
    print('Reading today datafile', today_fn) 
except Exception as e:
    #print("can not read ", datafile, e)
    print('Try download fresh data for today')    
    data = download_data(today_fn)
if data is None:
    print('use last saved', saved_data_fn)
    data = pd.read_csv(saved_data_fn, index_col=0)
    data.index = pd.to_datetime(data.index)
    

data['newCases(k)'] = data['newCases']/1000

data['inHospital(10s)'] = data['inHospital']/10



cols=[ 'newCases', 'inHospital(10s)', 'admissions', 'mvBeds', 'deaths']
cols=[ 'newCases', 'inHospital', 'mvBeds', 'deaths']

for c in cols:
    data[c+'_rollingmean'] = data[c].rolling(7).mean()
    data[c+'_rollingsum'] = data[c].rolling(7).sum()
rm=data.rolling(7).mean()
data['ymd'] = [x.strftime("%Y-%m-%d") for x in data.index]

colors = {'inHospital(10s)': 'brown',
          'inHospital': 'brown',
 'admissions': 'orange',
 'newCases(k)': 'green',
 'newCases': 'green',
 'mvBeds': 'blue',
 'deaths': 'red'}

peaks=['2020-04-10', '2021-1-11', '2021-09-10', '2022-01-03']

def plot_p(data, source, col, start_date, end_date):
    dmin=data[col+'_rollingmean'][start_date: end_date].min()
    dmax=data[col+'_rollingmean'][start_date: end_date].max()
    newCaseMax=data['newCases_rollingsum'][start_date: end_date].max()
    inHospitalMax=data['inHospital_rollingmean'][start_date: end_date].max()
    title = f'{col},{dmax*100/newCaseMax:.2f}% of 7 day newcase sum, {dmax*100/inHospitalMax:.2f}% of hospitalization'
    p = figure(plot_height=200, plot_width=400, tools="xpan", 
               toolbar_location=None,
               title= title, 
               x_axis_type="datetime", x_axis_location="above",
               background_fill_color="#efefef", 
               y_range=[((dmin-100)//100)*100, ((dmax+100)//100)*100],
               x_range=(start_date, end_date))
    
    # Set up hover tool
    #colors = dict(zip(data.columns, bokeh.palettes.d3['Category10'][4]))
    
    
    hover = bokeh.models.HoverTool(tooltips=[('Date', '@ymd'),
                                             ('Death','@deaths'),
                                              ('onVentilator', '@mvBeds'),
                                             ('Admissions', '@admissions'),
                                             ('InHospital', '@inHospital'),
                                            
                                             ('NewCase','@newCases')])
    p.add_tools(hover)
    
        
    #p.yaxis.axis_label = "New Case/In hospital"
    #p.extra_y_ranges = {"y2": Range1d(start=0, end=data.admissions.max())}
    #p.add_layout(LinearAxis(y_range_name="y2", axis_label="Admission/Death"), 'right')
    #p.vbar(x=data.index.values, top=col, width=0.2, source=source,  color=colors[col])
    p.line('date', col , source=source, color=colors[col])#y_range_name="y2")
    p.line('date', col+'_rollingmean', source=source, color=colors[col], line_dash='dotted')
    #p.legend.click_policy="hide"
    #p.legend.location = 'top_left'
    #p.add_layout(p.legend[0], 'right')
    return p

dates = data.index 

i=rm.admissions[:-30].idxmax() 
#i = rm.newCases.gt(rm.newCases[-1]).idxmax()

#i=data.newCases.gt(data.newCases[-1]).argmax()

#print(i)
source = ColumnDataSource(data=data)

rows=[]

p1x=None
p2x=None

for pi in range(len(peaks)):
    ps=[]
    for col in cols:
        i= datetime.strptime(peaks[pi], '%Y-%m-%d')
        p = plot_p(data, source, col, i-pd.Timedelta(14, unit="d"), i+ pd.Timedelta(28, unit="d"))
        ps.append(p)
    rows.append(column(ps))

output_file("index.html")


#save(column(PreText(text='Recent Month'), row(row1), PreText(text='Historical'), row(row2), select))
show(row(rows))
