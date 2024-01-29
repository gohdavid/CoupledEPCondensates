"""Module to initialize figure styles in Seaborn.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import scienceplots
import numpy as np

def rcparams():
    mpl.style.use('default')
    plt.style.use(['science', 'nature', 'no-latex'])
    plt.rcParams.update({
        'figure.figsize': (3, 2),
        'xtick.direction': 'out',
        'ytick.direction': 'out',
        'ytick.right': False,
        'xtick.top': False,
        'xtick.minor.visible': False,
        'ytick.minor.visible': False,
        'axes.grid': False,
        'axes.spines.right': False,
        'axes.spines.top': False,
        'font.sans-serif': 'MLMSans10',
        'figure.dpi': 300,
    })

    plt.rcParams['figure.facecolor'] = 'white'

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

sns.lineplot(x=[0,1],y=[0,1])
rcparams()
plt.close()