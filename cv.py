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


    
def download_data(data_fn):
    try:
        data_url='https://api.coronavirus.data.gov.uk/v2/data?areaType=overview&metric=hospitalCases&metric=newAdmissions&metric=newCasesByPublishDate&metric=newDeaths28DaysByPublishDate&format=csv'
    
        s=requests.get(data_url).content
        data=pd.read_csv(io.StringIO(s.decode('utf-8')))
        data=data.drop(['areaCode','areaName', 'areaType'], axis=1).set_index('date')
        data.index = pd.to_datetime(data.index)
        data = data.sort_index()
        renames={'hospitalCases': 'inHospital',
                 'newAdmissions': 'admissions',
                 'newCasesByPublishDate': 'newCases',
                 'newDeaths28DaysByPublishDate': 'deaths'}

        data=data.rename(columns=renames)
        
        data.to_hdf(data_fn, 'data')
        print('Fresh data downloaded and save to ', data_fn)
        return data
    except Exception as e:
        print('Error downloading', e)
        return None


datafile=datetime.today().strftime('data_%Y%m%d.h5')

try:
    
    data = pd.read_hdf(datafile)
    print('Reading today datafile', datafile) 
except Exception as e:
    #print("can not read ", datafile, e)
    print('Try download fresh data for today')    
    data = download_data(datafile)
    if data is None:
        print('use old data.h5')
        data = pd.read_hdf('data.h5')
        

    
    

import numpy as np

import bokeh
from bokeh.io import show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, RangeTool, HoverTool
from bokeh.plotting import figure
from bokeh.io import output_file, show
from bokeh.plotting import figure, output_file, save
from bokeh.models import LinearAxis, Range1d



rm=data.rolling(7).mean()
data['ymd'] = [x.strftime("%Y-%m-%d") for x in data.index]

colors = {'inHospital': 'green',
 'admissions': 'orange',
 'newCases': 'blue',
 'deaths': 'red'}


def plot_p(data, cols, start_date, end_date):
    
    p = figure(plot_height=200, plot_width=400, tools="xpan", toolbar_location=None,
               x_axis_type="datetime", x_axis_location="above",
               background_fill_color="#efefef", 
               y_range=[0, data[cols].max().max()],
               x_range=(start_date, end_date))
    
    # Set up hover tool
    #colors = dict(zip(data.columns, bokeh.palettes.d3['Category10'][4]))
    
    
    source = ColumnDataSource(data=data)
    hover = bokeh.models.HoverTool(tooltips=[('Date', '@ymd'),
                                             ('Death','@deaths'),
                                             ('Admissions', '@admissions'),
                                             ('InHospital', '@inHospital'),
                                             ('NewCase','@newCases')])
    p.add_tools(hover)
    
        
    #p.yaxis.axis_label = "New Case/In hospital"
    #p.extra_y_ranges = {"y2": Range1d(start=0, end=data.admissions.max())}
    #p.add_layout(LinearAxis(y_range_name="y2", axis_label="Admission/Death"), 'right')
    
    for c in cols:
        p.line('date', c , source=source, color=colors[c], legend_label=c)#y_range_name="y2")
    
    p.legend.click_policy="hide"
    p.legend.location = 'top_left'
    #p.add_layout(p.legend[0], 'right')
    return p

dates = data.index 

i = rm.newCases.gt(rm.newCases[-1]).argmax()
#i=data.newCases.gt(data.newCases[-1]).argmax()
source = ColumnDataSource(data=data)

cols1=[ 'deaths', 'admissions']
cols2=[ 'newCases', 'inHospital']

p1 = plot_p(data, cols1, dates[-28], dates[-1])
p2 = plot_p(data, cols1, dates[i-27], dates[i])
p3 = plot_p(data, cols2, dates[-28], dates[-1])
p4 = plot_p(data, cols2, dates[i-27], dates[i])

p4.x_range = p2.x_range

select = figure(title="Drag the middle and edges of the selection box to change the range above",
                plot_height=130, plot_width=800, y_range=p4.y_range,
                x_axis_type="datetime", y_axis_type=None,
                tools="", toolbar_location=None, background_fill_color="#efefef")



range_tool = RangeTool(x_range=p2.x_range)
range_tool.overlay.fill_color = "navy"
range_tool.overlay.fill_alpha = 0.2

for c in [ 'deaths', 'admissions', 'newCases', 'inHospital']:
    select.line('date', c, source=source, color=colors[c])
select.ygrid.grid_line_color = None
select.add_tools(range_tool)
select.toolbar.active_multi = range_tool


output_file("uk.html")
save(column(row(p1, p3), row(p2, p4), select))