import os
import sys

import pandas as pd
from bokeh.client import push_session
from bokeh.io import output_file
from bokeh.models import HBox
from bokeh.plotting import figure, Figure, output_server, curdoc, show, gridplot
from random import shuffle
from bokeh.models import Range1d

from googledriveutils import find_folderid

# Prepare output to server
output_server("BioReactor_Data_Logging")

print find_folderid('Winkler Lab', 'root')
# Retrieves latest updated data file from google drive
curdir = os.path.join(__file__, os.pardir)
pardir = os.path.join(curdir, os.pardir)
py27dir = os.path.abspath(pardir) + '/py27googledriveconnect'
sys.path.insert(0, py27dir)
from downloader import download_latest

datafile = os.path.abspath(pardir) + '/Data_Management/R1data'
download_latest(1, 'R1data')

# Accept/Setup Dataframe to be Plotted
sample_data_live = datafile
sample = pd.read_csv(sample_data_live, parse_dates=[0])
sampleSI = sample.set_index('Date')
sampleSI = sampleSI.tail(10)

print sampleSI

x_low=sampleSI.index[1]
x_high=sampleSI.index[-1]

n_min = 2

# Initialize plot figures
plot1 = Figure(x_axis_type="datetime", plot_width=400, plot_height=400,
        x_range=[x_low- pd.DateOffset(minutes=n_min),x_high+ pd.DateOffset(minutes=n_min)],
        y_range=[-0.1,0.1])
plot2 = Figure(x_axis_type="datetime", plot_width=400, plot_height=400,
        x_range=[x_low- pd.DateOffset(minutes=n_min),x_high+ pd.DateOffset(minutes=n_min)],
        y_range=[0,100])
plot3 = Figure(x_axis_type="datetime", plot_width=400, plot_height=400,
        x_range=[x_low- pd.DateOffset(minutes=n_min),x_high+ pd.DateOffset(minutes=n_min)],
        y_range=[0,15])
plot4 = Figure(x_axis_type="datetime", plot_width=400, plot_height=400,
        x_range=[x_low- pd.DateOffset(minutes=n_min),x_high+ pd.DateOffset(minutes=n_min)],
        y_range=[0,800])
plot5 = Figure(x_axis_type="datetime", plot_width=400, plot_height=400,
        x_range=[x_low- pd.DateOffset(minutes=n_min),x_high+ pd.DateOffset(minutes=n_min)],
        y_range=[-200,200])


def make_plot(title1, plot1, title2, plot2, title3, plot3, title4, plot4, title5, plot5, sampleSI):
    plot1.title = title1
    plot2.title = title2
    plot3.title = title3
    plot4.title = title4
    plot5.title = title5
    plot1.circle(x=sampleSI.index, y=sampleSI[title1], color="navy")
    plot2.circle(x=sampleSI.index, y=sampleSI[title2], color="firebrick")
    plot3.circle(x=sampleSI.index, y=sampleSI[title3], color="#28D0B4", line_width=2)
    plot4.circle(x=sampleSI.index, y=sampleSI[title4], color="orange")
    plot5.circle(x=sampleSI.index, y=sampleSI[title5], color="black")
    #p = gridplot([[plot1, plot2], [plot3, plot4], [plot5, None]])
    p = gridplot([[plot1, plot2, plot3], [plot4, plot5, None]])
    return p


data_to_plot = 'DO'
datas = {
    'DO': {
        'name': 'DO mg/L',
        'title': 'Dissolved Oxygen'
    },
    'pH': {
        'name': 'pH',
        'title': 'pH'
    },
    'Ammonium': {
        'name': 'Ammonium',
        'title': 'NH4 Conc.'
    },
    'N2 Mass Flow Controller': {
        'name': 'N2 Mass Flow Controller',
        'title': 'N2 Flow Rate'
    },
    'Air Mass Flow Controller': {
        'name': 'Air Mass Flow Controller',
        'title': 'Air Flow Rate'
    }
}

# data_select = Select(value=data_to_plot, title='Data', options=sorted(datas.keys()))

#sampleSI = sampleSI.tail(10)
plot = make_plot(datas['DO']['name'], plot1, datas['Ammonium']['name'], plot2, datas['pH']['name'], plot3,
                 datas['N2 Mass Flow Controller']['name'], plot4, datas['Air Mass Flow Controller']['name'], plot5,
                 sampleSI)

#curdoc().add_root(HBox(plot))

#output_file("bokehplot.html", title="Bokeh Line Plot")
# show(HBox(plot))

session = push_session(curdoc())


def update():
    datafile = os.path.abspath(pardir) + '/Data_Management/R1data'
    download_latest(1, 'R1data')
    sample_data_live = datafile
    sample = pd.read_csv(sample_data_live, parse_dates=[0])
    sampleSI = sample.set_index('Date')
    sampleSI = sampleSI.tail(10)
    # source = ColumnDataSource(data=sampleSI)
    #<INSERT NAME OF FIGURE HERE>.x_range=Range1d(start=x_low, end=x_high)
    make_plot(datas['DO']['name'], plot1,
                    datas['Ammonium']['name'], plot2,
                    datas['pH']['name'], plot3,
                    datas['N2 Mass Flow Controller']['name'], plot4,
                    datas['Air Mass Flow Controller']['name'], plot5,
                    sampleSI)


curdoc().add_periodic_callback(update, 4000)
session.show()

session.loop_until_closed()



# # Set up streaming for data plots.
# while True:
#     # Somehow need to update the data of the source object "source"
#     datafile = os.path.abspath(pardir) + '/R1data.csv'
#     download_latest(1, 'R1data.csv')
#     sample_data_live = datafile
#     sample = pd.read_csv(sample_data_live, parse_dates=[0])
#     sampleSI = sample.set_index('Date')
#     source = ColumnDataSource(data=sampleSI)
#     plot = make_plot(datas['DO']['name'], plot1, datas['Ammonium']['name'], plot2, datas['pH']['name'], plot3,
#                  datas['N2 Mass Flow Controller']['name'], plot4, datas['Air Mass Flow Controller']['name'], plot5)
#     # Store the updated source on the server
#     curdoc().store_objects(source)
#     time.sleep(0.5)
