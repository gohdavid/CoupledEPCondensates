#!/usr/bin/env python
from utils.file_operations import input_parse
from utils.simulation_helper import set_mesh_geometry
from utils.analysis.make_movies import write_movies_two_component_2d
import os
import argparse

class simDir:
    def __init__(self,
                 directory: str,
                 movie_parameters: str = "movie_parameters.txt"):
        self.directory = directory
        self.params_file: str = os.path.join(self.directory, "input_params.txt")
        self.hdf5_file: str =  os.path.join(self.directory, "spatial_variables.hdf5")
        self.movie_params_file = movie_parameters
    def run(self):
        self.params = input_parse(self.params_file)
        if os.path.isfile(self.movie_params_file):
            self.movie_params = input_parse(self.movie_params_file)
        else:
            print("Using default movie parameters.")
            self.movie_params = {'num_components': 2.0,
                                 'color_map': ['Blues', 'Reds'],
                                 'titles': ['Protein', 'RNA'],
                                 'figure_size': [15, 6]}
        self.geometry = set_mesh_geometry(self.params)
    def makeMovie(self):
        write_movies_two_component_2d(self.directory,
                                      self.hdf5_file,
                                      self.movie_params,
                                      self.geometry.mesh)

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
