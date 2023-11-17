#!/usr/bin/env python
from utils.file_operations import input_parse
from utils.simulation_helper import set_mesh_geometry
from utils.analysis.make_movies import write_movies_two_component_2d
import os
import argparse
import h5py
import numpy as np
import matplotlib.pyplot as plt

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
    def run(self, geo: bool = False, hdf5: bool = False):
        if geo:
            # Load Gmsh geometry
            self.geometry = set_mesh_geometry(self.params)
        if hdf5:
            # Load concentration profile
            with h5py.File(self.hdf5_file, mode="r") as concentration_dynamics:
                # Read concentration profile data from files
                self.concentration_profile = []
                for i in range(int(self.movie_params['num_components'])):
                    self.concentration_profile.append(
                        concentration_dynamics['c_{index}'.format(index=i)][:]
                        )
    def makeSubdirectory(self,subdirectory):
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
        conc = sim.concentration_profile
        for i in range(int(sim.movie_params['num_components'])):
            # Check if plotting range is explicitly specified in movie_parameters
            if 'c{index}_range'.format(index=i) in sim.movie_params.keys():
                self.plotting_range.append(sim.movie_params['c{index}_range'.format(index=i)])
            else:
                min_value = conc[i].min()
                max_value = conc[i].max()
                self.plotting_range.append([min_value, max_value])

    def makeMovie(self):
        write_movies_two_component_2d(self.directory,
                                      self.hdf5_file,
                                      self.movie_params,
                                      self.geometry.mesh)
    def makeProteinFigure(self):
        subdir_path = self.makeSubdirectory("figures")

        # Generate and save plots
        fig, ax = plt.subplots(1, int(self.movie_params['num_components']), figsize=self.movie_params['figure_size'])
        for i in range(int(self.movie_params['num_components'])):
            cs = ax[i].tricontourf(self.geometry.mesh.x, self.geometry.mesh.y, self.concentration_profile[i][t],
                                levels=np.linspace(int(self.plotting_range[i][0]*100)*0.01,
                                                    int(self.plotting_range[i][1]*100)*0.01,
                                                    256),
                                cmap=self.movie_params['color_map'][i])
            # ax[i].tick_params(axis='both', which='major', labelsize=20)
            ax[i].xaxis.set_tick_params(labelbottom=False)
            ax[i].yaxis.set_tick_params(labelleft=False)
            cbar = fig.colorbar(cs, ax=ax[i], ticks=np.linspace(int(self.plotting_range[i][0]*100)*0.01,
                                                                int(self.plotting_range[i][1]*100)*0.01,
                                                                3))
            cbar.ax.tick_params(labelsize=30)
            ax[i].set_title(self.movie_params['titles'][i], fontsize=40)
        fig.savefig(fname=subdir_path + '/Movie_step_{step}.png'.format(step=t), dpi=300, format='png')
        plt.close(fig)


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
