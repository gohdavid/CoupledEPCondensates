"""Module to initialize figure styles in Matplotlib and Seaborn.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import scienceplots
import numpy as np
from pathlib import Path

def get_size_inches(frac_x, frac_y):
    cm_in_inch = 2.54
    prl_col_size = 8.5 / cm_in_inch
    return [frac_x * prl_col_size, frac_y * 1.0 * prl_col_size]

def cm2inch(*tupl):
    cm_in_inch = 2.54
    if isinstance(tupl[0], tuple):
        return tuple(i/cm_in_inch for i in tupl[0])
    else:
        return tuple(i/cm_in_inch for i in tupl)

# Converting from cm to inches for e.g., fig.set_size_inches(8.5*_CM,8.5*_CM*aspect_ratio)
# Generally use aspect_ratio 1/2, 2/3, or 3/4
_CM = 1/2.54

# Use as plt.savefig(_FIGURE_DIR/"name.pdf")
# Generally save as svg or pdf (vector graphics) for Adobe Illustrator, Affinity Designer, or Inkscape
# Save as SVG or rasterize as JPG for the website
_FIGURE_DIR = Path("/nfs/arupclab001/davidgoh/CoupledEPCondensates/figures")

def rcparams():
    mpl.style.use('default')
    plt.style.use(['science', 'nature'])
    plt.rcParams.update({
        # 'backend': 'ps',
        'savefig.format': 'pdf',

        'font.size': 8,
        'font.family': 'sans-serif',
        'font.sans-serif': 'Helvetica',
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'text.usetex': False,
        
        'lines.linewidth':1.5,
        
        'figure.figsize': get_size_inches(1, 2/3),

        'xtick.direction': 'out',
        'xtick.top': False,
        'xtick.bottom': True,
        'xtick.minor.visible': False,
        'xtick.labelsize': 8,
        'xtick.minor.size': 2,
        'xtick.minor.width': 0.5,
        'xtick.major.pad': 3,
        'xtick.major.size': 3,
        'xtick.major.width': 1,
        
        'ytick.direction': 'out',
        'ytick.right': False,
        'ytick.left': True,
        'ytick.minor.visible': False,
        'ytick.labelsize': 8,
        'ytick.direction': 'out',
        'ytick.minor.size': 2,
        'ytick.minor.width': 0.5,
        'ytick.major.pad': 3,
        'ytick.major.size': 3,
        'ytick.major.width': 1,

        'axes.grid': False,
        'axes.edgecolor': 'black',
        'axes.facecolor': 'white',
        'axes.spines.right': False,
        'axes.spines.top': False,
        'axes.titlesize': 8,
        'axes.titlepad': 5,
        'axes.labelsize': 8,
        'axes.linewidth': 1,
        
        'legend.fontsize': 8,
        
        'figure.facecolor': 'white',
        'figure.dpi': 200,
        
        'savefig.transparent': True
    })

def add_arrow(line, number=10, direction='right', size=3, color=None):
    """
    add an arrow to a line.

    line:       Line2D object
    position:   x-position of the arrow. If None, mean of xdata is taken
    direction:  'left' or 'right'
    size:       size of the arrow in fontsize points
    color:      if None, line color is taken.
    """
    if color is None:
        color = line.get_color()

    xdata = line.get_xdata()
    ydata = line.get_ydata()
    
    positions = np.linspace(xdata[1:-1].min(),xdata[1:-1].max(),number)
    for position in positions:
        # find closest index
        start_ind = np.argmin(np.absolute(xdata - position))
        if direction == 'right':
            end_ind = start_ind + 1
        else:
            end_ind = start_ind - 1

        line.axes.annotate('',
            xytext=(xdata[start_ind], ydata[start_ind]),
            xy=(xdata[end_ind], ydata[end_ind]),
            arrowprops=dict(arrowstyle="->", color=color),
            size=size
        )

# Seaborn needs to plot before you load mpl.rcParams for it to work
sns.lineplot(x=[0,1],y=[0,1])
rcparams()
# Remove the seaborn plot
plt.close()