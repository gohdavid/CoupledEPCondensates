#!/usr/bin/env python

from utils.analysis.tools import simDir
from pathlib import Path
from utils import plot
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import argparse
from scipy.ndimage import gaussian_filter1d


def condensate_property_plot(folder):
    cmap = mpl.colormaps["Paired"].colors
    sim = simDir(folder)
    sim.run()
    com, e, r = sim.condensate()
    fig, ax = plt.subplots(2,2)
    axes = np.ravel(ax)
    fig.set_size_inches((6,3))
    x = np.arange(len(com[:,0]))
    y = com[:,0]
    f = gaussian_filter1d(y,15)
    axes[0].plot(y,
                    label="Raw",
                    color=cmap[0])
    axes[0].plot(f,
                    label="Gaussian filter",
                    color=cmap[1])
    axes[0].legend()
    axes[0].set_xlabel("Frame")
    axes[0].set_ylabel("Distance\nfrom locus")
    axes[1].plot(com[:,0],
                    -np.gradient(y),
                    label="Raw",
                    color=cmap[0])
    axes[1].plot(com[:,0],
                    -np.gradient(f),
                    label="Gaussian filter",
                    color=cmap[1])
    axes[1].set_xlabel("Distance\nfrom locus")
    axes[1].set_ylim(bottom=0)
    axes[1].set_ylabel("Condensate\nvelocity")
    axes[1].legend()
    axes[2].plot(e)
    axes[2].set_ylabel("Eccentricity")
    axes[2].set_xlabel("Frame")
    var_r = np.var(r,axis=1)
    axes[3].plot(var_r)
    axes[3].set_ylabel("Radius\nvariance")
    axes[3].set_xlabel("Frame")
    fig.tight_layout()
    fig.savefig(folder / "figures" / "condensate.png")

parser = argparse.ArgumentParser(description='Plot condensate properties')
parser.add_argument('-i', help="Simulation folder", required=True)
args = parser.parse_args()

folder = Path(args.i)
condensate_property_plot(folder)