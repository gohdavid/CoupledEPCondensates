#!/usr/bin/env python
from utils.file_operations import input_parse
from utils.simulation_helper import set_mesh_geometry
from utils.analysis.make_movies import write_movies_two_component_2d
import os
import argparse
import h5py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

class simDir:
    def __init__(self,
                 directory: str,
                 movie_parameters: str = "movie_parameters.txt"):
        self.directory = directory

        # Parse simulation parameter input. Simulation directories have this file by
        # default.
        self.params_file: str = os.path.join(self.directory, "input_params.txt")
        self.params = input_parse(self.params_file)

        # Simulation directories have this file by default.
        self.hdf5_file: str =  os.path.join(self.directory, "spatial_variables.hdf5")

        # Parse movie parameter input.
        self.movie_params_file = movie_parameters
        if os.path.isfile(self.movie_params_file):
            self.movie_params = input_parse(self.movie_params_file)
        else:
            print("Using default movie parameters.")
            self.movie_params = {'num_components': 2.0,
                                 'color_map': ['Blues', 'Reds'],
                                 'titles': ['Protein', 'RNA'],
                                 'figure_size': [15, 6]}
    def run(self, geo: bool = True, hdf5: bool = True):
        if geo:
            # Load Gmsh geometry
            self.geometry = set_mesh_geometry(self.params)
        if hdf5:
            # Load concentration profile
            with h5py.File(self.hdf5_file, mode="r") as concentration_dynamics:
                # Read concentration profile data from files
                self.concentration_profile = []
                for i in range(int(self.movie_params['num_components'])):
                    conc_arr = concentration_dynamics[f'c_{i}'][:]
                    conc_arr = conc_arr[~np.all(conc_arr == 0, axis=1)]
                    self.concentration_profile.append(conc_arr)
    def makeSubdirectory(self, subdirectory: str):
        # Make a directory within the simulation directory
        subdir_path = os.path.join(self.directory, subdirectory)
        try:
            os.mkdir(subdir_path)
            print("Successfully made the directory " + subdir_path + " ...")
        except OSError:
            print(subdir_path + " directory already exists")
        return subdir_path

    def getPlotLimits(self):
        # Get upper and lower limits of the concentration values from the concentration profile data
        self.plotting_range = []
        conc = self.concentration_profile
        for i in range(int(self.movie_params['num_components'])):
            # Check if plotting range is explicitly specified in movie_parameters
            if 'c{index}_range'.format(index=i) in self.movie_params.keys():
                self.plotting_range.append(self.movie_params['c{index}_range'.format(index=i)])
            else:
                min_value = conc[i].min()
                max_value = conc[i].max()
                self.plotting_range.append([min_value, max_value])

    def makeMovie(self):
        write_movies_two_component_2d(self.directory,
                                      self.hdf5_file,
                                      self.movie_params,
                                      self.geometry.mesh)
    def makeFigure(self,i,
                   n_rows:int=4,
                   n_cols:int=4):
        self.getPlotLimits()
        n_frames = n_rows*n_cols
        subdir_path = self.makeSubdirectory("figures")
        frames = np.linspace(0, self.concentration_profile[0].shape[0]-1, num=n_frames, dtype=int)
        fig = plt.figure(figsize=(6*(n_rows),6*(n_cols)))
        gs = fig.add_gridspec(n_rows,n_cols)
        axes = [fig.add_subplot(gs[i,j]) for i in range(n_cols) for j in range(n_rows)]
        for t, frame in enumerate(frames):
            # Generate and save plots
            # axes = axes.flatten()
            cs = axes[t].tricontourf(self.geometry.mesh.x, self.geometry.mesh.y, self.concentration_profile[i][frame],
                                levels=np.linspace(int(self.plotting_range[i][0]*100)*0.01,
                                                    int(self.plotting_range[i][1]*100)*0.01,
                                                    256),
                                cmap=self.movie_params['color_map'][i])
            border = plt.Circle((0,0), self.params["radius"],
                                color='tab:gray', fill=False, linewidth=2)
            axes[t].add_patch(border)
            axes[t].autoscale_view()
            axes[t].xaxis.set_tick_params(labelbottom=False, bottom=False)
            axes[t].yaxis.set_tick_params(labelleft=False, left=False)
            axes[t].set_aspect('equal', 'box')
            plt.setp(axes[t].spines.values(), visible=False)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        cbar = fig.colorbar(cs,
                            ax=axes,
                            ticks=np.linspace(int(self.plotting_range[i][0]*100)*0.01,
                                            int(self.plotting_range[i][1]*100)*0.01,
                                            3),
                            shrink=0.6
                            )
        cbar.ax.tick_params(labelsize=30)
        fig.suptitle(self.movie_params['titles'][i], fontsize=40)
        fig.savefig(fname=subdir_path + \
            '/{}.png'.format(self.movie_params['titles'][i]),
                    dpi=300, format='png')
        return fig

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Directory name to search for hdf5 files and generate movies')
    parser.add_argument('--i', help="Simulation directory", required=True)
    parser.add_argument('--m', help="Path to movie parameters file", default="movie_params.txt")

    args = parser.parse_args()

    folder = args.i
    movie_params = args.m
    sim = simDir(folder,movie_params)
    sim.run()
    sim.makeMovie()
    sim.makeFigure(i=0)
    sim.makeFigure(i=1)
