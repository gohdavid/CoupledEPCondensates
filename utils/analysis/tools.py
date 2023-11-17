#!/usr/bin/env python
from utils.file_operations import input_parse
from utils.simulation_helper import set_mesh_geometry
from utils.analysis.make_movies import write_movies_two_component_2d
import os
import argparse
import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import  ConvexHull
import scipy.interpolate as interp
from sklearn.cluster import DBSCAN
from pathlib import Path
from typing import Union, Optional


class simDir:
    def __init__(self,
                 directory: str,
                 movie_parameters: str = "movie_parameters.txt"):
        self.directory = Path(directory)

        # Parse simulation parameter input. Simulation directories have this file by
        # default.
        self.params_file: str = self.directory / "input_params.txt"
        self.params = input_parse(self.params_file)

        # Simulation directories have this file by default.
        self.hdf5_file: str =  self.directory / "spatial_variables.hdf5"

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

    def run(self, geo: bool=True, hdf5: bool=True,
            plot_limits: bool=True, condensate: bool=True):
        if geo:
            # Load Gmsh geometry
            self.geometry = set_mesh_geometry(self.params)
            self.xy = np.vstack((self.geometry.mesh.x, self.geometry.mesh.y)).T
        if hdf5:
            # Load concentration profile
            with h5py.File(self.hdf5_file, mode="r") as concentration_dynamics:
                # Read concentration profile data from files
                self.concentration_profile = []
                for i in range(int(self.movie_params['num_components'])):
                    conc_arr = concentration_dynamics[f'c_{i}'][:]
                    conc_arr = conc_arr[~np.all(conc_arr == 0, axis=1)]
                    self.concentration_profile.append(conc_arr)
            self.n_frames = len(self.concentration_profile[0])
        if plot_limits:
            self.getPlotLimits()

    def makeSubdirectory(self, subdirectory: str):
        # Make a directory within the simulation directory
        subdir_path = self.directory / subdirectory
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
    def makeFigure(self,
                   i:int,
                   n_rows:int=4,
                   n_cols:int=4):
        n_frames = n_rows*n_cols
        subdir_path = self.makeSubdirectory("figures")
        frames = np.linspace(0, self.concentration_profile[0].shape[0]-1, num=n_frames, dtype=int)
        fig = plt.figure(figsize=(6*(n_rows),6*(n_cols)))
        gs = fig.add_gridspec(n_rows,n_cols)
        axes = [fig.add_subplot(gs[i,j]) for i in range(n_cols) for j in range(n_rows)]
        for t, frame in enumerate(frames):
            # Generate and save plots
            # axes = axes.flatten()
            cs = axes[t].tricontourf(self.geometry.mesh.x,
                                     self.geometry.mesh.y,
                                     self.concentration_profile[i][frame],
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

    def condensate(self,
                   i:int=0,
                   resample_num_points:int=1000):
        self.threshold = self.params["c_bar_1"]
        self.condensate_conc = self.concentration_profile[i].copy()
        self.mask = self.condensate_conc>self.threshold
        self.condensate_conc[~self.mask]=0
        self.com = ((self.condensate_conc*self.geometry.mesh.cellVolumes)\
            @ self.xy)\
            /np.tile((self.condensate_conc*self.geometry.mesh.cellVolumes)\
            .sum(axis=1),(2,1)).T

        edge_lst = []
        for n in range(len(self.mask)):
            condensate_coords = self.xy[self.mask[n]]
            arr = self.resample_path(condensate_coords,resample_num_points)
            edge_lst.append(arr)
        self.edge_arr = np.array(edge_lst)
        xydist = self.edge_arr.max(axis=1)-self.edge_arr.min(axis=1)
        ratio = xydist[:,0]/xydist[:,1]
        self.eccentricity = np.sqrt(np.where(ratio<1,1-ratio**2,1-1/ratio**2))
        self.radius = np.sqrt(((self.edge_arr-self.com[:,None,:])**2).sum(axis=2))
        return self.com, self.eccentricity, self.radius

    def n_condensate(self):
        n_cluster_lst = []
        for n in range(self.n_frames):
            n_clusters = self.dbscan(self.xy[self.mask[n]])
            n_cluster_lst.append(n_clusters)
        return np.array(n_cluster_lst)

    def dbscan(self,
               coords:np.ndarray):
        db = DBSCAN(eps=0.3, min_samples=10).fit(coords)
        labels = db.labels_
        dbscan = len(set(labels)) - (1 if -1 in labels else 0)
        return dbscan

    def resample_path(self,
                      points:np.ndarray,
                      num_points:Optional[int]=None):
        hull = ConvexHull(points)
        hull_path = hull.vertices
        boundary = points[hull_path, :]
        # Calculate the cumulative distance along the path
        distance = np.cumsum(np.sqrt(np.sum(np.diff(boundary, axis=0)**2, axis=1)))
        distance = np.insert(distance, 0, 0)  # Insert a 0 at the beginning

        # Default number of resample points
        if not num_points:
            num_points = len(boundary)

        # Interpolate boundary uniformly over the cumulative distance
        interp_func = interp.interp1d(distance, boundary, kind="linear", axis=0)
        new_distances = np.linspace(0, distance[-1], 1000)
        new_points = interp_func(new_distances)

        return new_points