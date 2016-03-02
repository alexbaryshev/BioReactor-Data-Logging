"""
Written By: Michael Newton
For: Winkler Lab/CSE599 Winter Quarter 2016
Purpose: Uses Bokeh to plot sample data from Bioreactor while incorporating Widgets

To Do:
+ Properly impart functionality to check box button group
+ Increase generality of code to allow for any data frame
"""

import numpy as np
import pandas as pd
from bokeh.charts import *
from bokeh.io import show, output_file, vform
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import CheckboxButtonGroup

# Accept/Setup Dataframe to be Plotted
sample_data_live = 'sampledatalive.csv'
sample = pd.read_csv(sample_data_live, parse_dates = [0])
sampleSI = sample.set_index('Date')

source = ColumnDataSource(data=sampleSI)

# Plot a Specified Column in Dataframe
lineplot = Line(sampleSI['DO'], xlabel='Date', ylabel='DO', legend="top_left")
checkbox_button_group = CheckboxButtonGroup(labels=["DO"], active=[0, 1])

# This callback is apparently only usable for a slider
# callback = CustomJS(args=dict(source=source), code="""
#     var data = source.get('data');
#     var f = cb_obj.get('value')
#     x = data['x']
#     y = data['y']
#     for (i = 0; i < x.length; i++) {
#         y[i] = Math.pow(x[i], f)
#         }
#         source.trigger('change');
# """)

output_file("doplot.html", title="DO Line Plot")
show(vform(checkbox_button_group, lineplot))