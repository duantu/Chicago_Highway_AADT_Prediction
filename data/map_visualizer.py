#use command "python3 map_visualizer.py" to run

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import collections  as mc
from matplotlib.lines import Line2D
import matplotlib.ticker as ticker
import matplotlib.markers
from matplotlib.widgets import RectangleSelector, CheckButtons

#Data frame setup from gnn_test.ipynb:
datadir = "../data/"
datafilename = "Certainty.xlsx"
datafilepath = datadir + datafilename

columns_selected = ['Category', 'Project', 'Link ID', 'ANODE', 'BNODE', 'A X_COORD', 'A Y_COORD', 'B X_COORD', 'B Y_COORD','# of lanes-A',
                    'Capacity-A (veh/h)']

df1 = pd.read_excel(datafilepath, sheet_name='P0', usecols = columns_selected)
df1_unique = df1.drop_duplicates(subset=['Link ID']).dropna(subset=['Link ID', 'A X_COORD', 'A Y_COORD', 'B X_COORD', 'B Y_COORD'])

a_nodes = df1_unique[['ANODE', 'A X_COORD', 'A Y_COORD']].rename(columns={"ANODE": "node_id", "A X_COORD": "x_coord", "A Y_COORD": "y_coord"})
b_nodes = df1_unique[['BNODE', 'B X_COORD', 'B Y_COORD']].rename(columns={"BNODE": "node_id", "B X_COORD": "x_coord", "B Y_COORD": "y_coord"})
nodes = pd.concat([a_nodes, b_nodes]).drop_duplicates().apply(pd.to_numeric)
# There are duplicate node_ids with different coordinates!
# For an example:
# print(nodes.loc[nodes['node_id'] == 11175])
# TODO: Figure out why
nodes = nodes.drop_duplicates(subset=['node_id'])

a_edges = df1_unique[['Link ID', 'ANODE', 'BNODE', 'Capacity-A (veh/h)']].rename(columns={'Link ID': 'edge_id', "ANODE": "src", "BNODE": "dest", "Capacity-A (veh/h)": "capacity"})
b_edges = df1_unique[['Link ID', 'BNODE', 'ANODE', 'Capacity-A (veh/h)']].rename(columns={'Link ID': 'edge_id', "BNODE": "src", "ANODE": "dest", "Capacity-A (veh/h)": "capacity"})
edges = pd.concat([a_edges, b_edges]).drop_duplicates().apply(pd.to_numeric)
# There are duplicate edge_ids with different src,dest and different capacities!
# For an example:
# print(edges.loc[edges['edge_id'] == 9197])
# TODO: Figure out why
edges = edges.drop_duplicates(subset=['edge_id'])

# For now, we treat AADT(2010)-A as the only response variable
df2 = pd.read_excel(datafilepath, sheet_name='P0').drop_duplicates(subset=['Link ID']).dropna(subset=['Link ID','AADT(2010)-A'])
df2 = df2[['Link ID', '# of lanes-A', 'AADT(2010)-A']].rename(columns={'Link ID': 'edge_id', '# of lanes-A': '#lanes','AADT(2010)-A':'AADT-A'}).drop_duplicates().apply(pd.to_numeric)
edges = edges.merge(right=df2, on=['edge_id'], how='left')

pd.set_option('expand_frame_repr', False)
df1_unique = df1_unique.rename(columns = {'# of lanes-A' : '#lanes-A', 'Capacity-A (veh/h)' : 'Capacity-A'} )

# VISUALIZER BELOW ############

#adds arrow objects to plot, returns an array of arrow objects, reference number 10 and 11 below
def add_edge_direction(ax, segments, arrow_color, arrow_length=0.1, buffer_edge = False):
    ret_array = []

    for segment in segments:
        x1, y1 = segment[0] #A coords, src
        x2, y2 = segment[1] #B coords, dest

        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        dx, dy =  (x2 - x1) * arrow_length, (y2 - y1)* arrow_length

        if not buffer_edge:
            arrow = ax.arrow(x, y, dx, dy, width = 8, ec = (0,0,0,1.0), fc = arrow_color,shape = 'full',
                     head_width = 15, length_includes_head=False,zorder=3)
            ret_array.append(arrow)
        else:
            arrow = ax.arrow(x, y, dx, dy, width = 8, ec = (0,0,0,1.0), fc = arrow_color,shape = 'full',
                     head_width = 15, length_includes_head=False,zorder=3)
            ret_array.append(arrow)
    return ret_array

#default parameters for map:
detailed_projects = [3,4,5]

#declare projects df
projects_df = df1_unique

#initialize plot and datastructures
fig,ax = plt.subplots(figsize = (12,8))

color_dict = {1:(1.0, 0.0, 0.0, 1.0),
              2:(0.0, 0.5, 0.0, 1.0),
              3:(1.0, 0.5, 0.0, 1.0),
              4:(0.5, 1.0, 1.0, 1.0),
              5:(1.0, 0.0, 1.0, 1.0),
              6:(0.5, 0.2, 0.8, 1.0)}

lc_label_dict = {}
nodes_label_dict = {}
arrows_label_dict = {}

#loop to plot line collections ("roads"), referenced source 3 from below
for project_num in detailed_projects:

    #add 'projects' line collection
    project_subset = projects_df[(projects_df['Project'] == project_num) & (projects_df['Category'] == 'Project')]

    project_srcs  = zip(project_subset['A X_COORD'], project_subset['A Y_COORD'])
    project_dests  = zip(project_subset['B X_COORD'], project_subset['B Y_COORD'])
    project_lines = [list(a) for a in zip(project_srcs, project_dests)]

    project_linecollect = mc.LineCollection(project_lines,colors = color_dict[project_num], linewidths = 2.0)
    ax.add_collection(project_linecollect)

    lc_label_dict['Project ' + str(project_num)] = project_linecollect

    #add nodes for projects
    project_node_scatter = ax.scatter(pd.concat([project_subset['A X_COORD'], project_subset['B X_COORD']]),
               pd.concat([project_subset['A Y_COORD'], project_subset['B Y_COORD']]),
               c = [color_dict[project_num]], edgecolor = 'black', linewidth = 0.5, marker= 'o',zorder = 2)

    nodes_label_dict['Project ' + str(project_num) + '\nnodes/arrows'] = project_node_scatter

    #add edge arrows for project lines
    project_arrows = add_edge_direction(ax,project_lines, arrow_color = color_dict[project_num],arrow_length=0.1)
    arrows_label_dict['Project ' + str(project_num) + '\nnodes/arrows'] = project_arrows

    #add buffer line collection
    buffer_subset = projects_df[(projects_df['Project'] == project_num) & (projects_df['Category'] != 'Project')]

    buffer_srcs = zip(buffer_subset['A X_COORD'], buffer_subset['A Y_COORD'])
    buffer_dests  = zip(buffer_subset['B X_COORD'], buffer_subset['B Y_COORD'])
    buffer_lines = [list(b) for b in zip(buffer_srcs, buffer_dests)]

    buffer_linecollect = mc.LineCollection(buffer_lines, colors = color_dict[project_num][:3] + (0.6,), linewidths = 0.5)
    ax.add_collection(buffer_linecollect)

    lc_label_dict['Project ' + str(project_num) + ' buffer'] = buffer_linecollect

    #add nodes for buffers
    buffer_node_scatter = ax.scatter(pd.concat([buffer_subset['A X_COORD'], buffer_subset['B X_COORD']]),
               pd.concat([buffer_subset['A Y_COORD'], buffer_subset['B Y_COORD']]),
               c = [color_dict[project_num][:3] + (0.6,)], alpha = 0.6, edgecolor = 'black',linewidth = 0.5, marker= '.',zorder = 2)
    nodes_label_dict['Project ' + str(project_num) + ' buffer \nnodes/arrows']  = buffer_node_scatter

    #add edge arrows for buffer lines
    buffer_arrows = add_edge_direction(ax,buffer_lines, arrow_color = color_dict[project_num],arrow_length=0.1, buffer_edge = True)
    arrows_label_dict['Project ' + str(project_num) + ' buffer \nnodes/arrows'] = buffer_arrows

#plot formatting
ax.autoscale()
ax.set_aspect('equal', 'box')
ax.margins(x = 0.05, y = 0.05, tight = True)
# plt.xticks(rotation=60)

y_formatter = ticker.ScalarFormatter(useMathText=True, useOffset = False)
y_formatter.set_scientific(True)
y_formatter.set_powerlimits((0,0))

x_formatter = ticker.ScalarFormatter(useMathText=True, useOffset = False)
x_formatter.set_scientific(True)
x_formatter.set_powerlimits((0,0))

ax.yaxis.set_major_formatter(y_formatter)
ax.xaxis.set_major_formatter(x_formatter)

default_xs = (350107.415, 506799.885)
default_ys = (4541720.225, 4668930.275)
ax.set_xlim(default_xs)
ax.set_ylim(default_ys)

ax.set_title('Selected Projects')
fig.canvas.manager.set_window_title('Interactive map')
ax.set_xlabel('X Coord', fontsize =12)
ax.set_ylabel('Y Coord', fontsize =12)

plot_xy_coords = [default_xs[0], default_xs[1], default_ys[0], default_ys[1]]

#project lines checkbox legend , from matplotlib reference number 1 and 9 below
line_colors = [l.get_color() for l in lc_label_dict.values()]

lines_checkbox_ax = fig.add_axes([0.85, 0.5, 0.145, 0.3])
lines_check = CheckButtons(
    ax=lines_checkbox_ax,
    labels=lc_label_dict.keys(),
    actives=[l.get_visible() for l in lc_label_dict.values()],
    frame_props={'edgecolor': line_colors},
    check_props={'facecolor': line_colors},
)
def line_checkbox_callback(label):
        ln = lc_label_dict[label]
        ln.set_visible(not ln.get_visible())
        ln.figure.canvas.draw_idle()
lines_check.on_clicked(line_checkbox_callback)

#nodes and arrows plot checkbox legend
nodes_checkbox_ax = fig.add_axes([0.85, 0.15, 0.145, 0.3])
nodes_check = CheckButtons(
    ax=nodes_checkbox_ax,
    labels=nodes_label_dict.keys(),
    actives=[l.get_visible() for l in nodes_label_dict.values()],
    frame_props={'edgecolor': line_colors},
    check_props={'facecolor': line_colors},
)
def nodes_checkbox_callback(label):
        ln = nodes_label_dict[label]
        arrows = arrows_label_dict[label]
        for arrow in arrows:
            arrow.set_visible(not arrow.get_visible())
        ln.set_visible(not ln.get_visible())
        ln.figure.canvas.draw_idle()
nodes_check.on_clicked(nodes_checkbox_callback)

#zoom with RectangleSelector, from matplotlib reference number 2 and 4 below
def reset_selector(event):
    if event.key == ' ':
        ax.set_xlim(plot_xy_coords[0],plot_xy_coords[1])
        ax.set_ylim(plot_xy_coords[2],plot_xy_coords[3])
        fig.canvas.draw_idle()

# Function to be executed after Rectangle selection
def onselect_function(eclick, erelease):
    extent = rect_selector.extents
    if (extent[0] != extent[1]) and (extent[2] != extent[3]):
        ax.set_xlim((extent[0], extent[1]))
        ax.set_ylim((extent[2], extent[3]))
        fig.canvas.draw_idle()

rect_selector = RectangleSelector(ax, onselect_function, button=[1])
fig.canvas.mpl_connect('key_press_event', reset_selector)

#reference number 6
map_description = "Left Click and drag to \nselect a section \nto zoom. \n\n Press spacebar to \nreset zoom."
plt.figtext(0.025, 0.8, map_description, fontsize=10, bbox=dict(facecolor='white', alpha=0.3))
plt.show()

#references:
# 1. https://matplotlib.org/stable/api/widgets_api.html#matplotlib.widgets.CheckButtons
# 2. https://matplotlib.org/stable/gallery/widgets/rectangle_selector.html
# 3. https://matplotlib.org/stable/api/collections_api.html#matplotlib.collections.LineCollection
# 4. https://www.geeksforgeeks.org/matplotlib-rectangle-selector/
# 5. https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.text.html
# 6. https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.figtext.html
# 7. https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html
# 8. https://matplotlib.org/stable/api/markers_api.html#module-matplotlib.markers
# 9. https://matplotlib.org/stable/gallery/widgets/check_buttons.html
# 10.https://stackoverflow.com/questions/34017866/arrow-on-a-line-plot
# 11.https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.arrow.html

#VISUALIZER OF ALL PROJECTS:
#visualize projects and buffer zones
def visualize_allprojects(projects, projects_df , show_buffer = True):
    fig,ax = plt.subplots(figsize = (9,9))
    color_dict = {1:(1.0, 0.0, 0.0, 1.0),
              2:(0.0, 0.5, 0.0, 1.0),
              3:(1.0, 0.5, 0.0, 1.0),
              4:(0.5, 1.0, 1.0, 1.0),
              5:(1.0, 0.0, 1.0, 1.0),
              6:(0.5, 0.2, 0.8, 1.0)}

    legend_labels =[]

    for project_num in projects:
        project_subset = projects_df[(projects_df['Project'] == project_num) & (projects_df['Category'] == 'Project')]

        #from code in cell above and stackoverflow post above
        project_srcs  = zip(project_subset['A X_COORD'], project_subset['A Y_COORD'])
        project_dests  = zip(project_subset['B X_COORD'], project_subset['B Y_COORD'])
        project_lines = [list(a) for a in zip(project_srcs, project_dests)]
        project_linecollect = mc.LineCollection(project_lines,colors = color_dict[project_num], linewidths = 2.0)

        ax.add_collection(project_linecollect)

        #placeholder label for linecollection
        legend_labels.append(Line2D([0], [0], color=color_dict[project_num], linewidth=2.0, label='Project ' + str(project_num)))
        if (show_buffer):
            buffer_subset = projects_df[(projects_df['Project'] == project_num) & (projects_df['Category'] != 'Project')]

            buffer_srcs = zip(buffer_subset['A X_COORD'], buffer_subset['A Y_COORD'])
            buffer_dests  = zip(buffer_subset['B X_COORD'], buffer_subset['B Y_COORD'])
            buffer_lines = [list(b) for b in zip(buffer_srcs, buffer_dests)]
            buffer_linecollect = mc.LineCollection(buffer_lines, colors = color_dict[project_num][:3] + (0.6,), linewidths = 0.5)
            ax.add_collection(buffer_linecollect)

    ax.autoscale()
    ax.set_aspect('equal', 'box')
    ax.margins(x = 0.05, y = 0.05, tight = True)
    # plt.xticks(rotation=60)

    y_formatter = ticker.ScalarFormatter(useMathText=True, useOffset = False)
    y_formatter.set_scientific(True)
    y_formatter.set_powerlimits((0,0))

    x_formatter = ticker.ScalarFormatter(useMathText=True, useOffset = False)
    x_formatter.set_scientific(True)
    x_formatter.set_powerlimits((0,0))

    ax.yaxis.set_major_formatter(y_formatter)
    ax.xaxis.set_major_formatter(x_formatter)

    ax.set_xlim((330169, 507749.3))
    ax.set_ylim((4539702.3, 4711306.7))
    # print(ax.get_xlim())
    # print(ax.get_ylim())
    ax.set_title('All Projects')
    ax.set_xlabel('X Coord', fontsize =12)
    ax.set_ylabel('Y Coord', fontsize = 12)
    ax.legend(handles=legend_labels)
    plt.show()

viz_subset = df1_unique

#Input array to visualization function, list of projects numbers 1-6 to visualize
all_projects = [1,2,3,4,5,6]
#line below visualizes all_projects
visualize_allprojects(all_projects, viz_subset, show_buffer = True)
