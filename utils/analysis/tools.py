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
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from scipy.signal import find_peaks
import matplotlib as mpl
from utils import plot
import multiprocessing as mp
import pandas as pd


class simDir:
    def __init__(self,
                 directory: str,
                 movie_parameters: str = "movie_parameters.txt"):
        self.directory = Path(directory)

        # Parse selfulation parameter input. selfulation directories have this file by
        # default.
        self.params_file = self.directory / "input_params.txt"
        self.params = input_parse(self.params_file)

        # selfulation directories have this file by default.
        self.hdf5_file: str =  self.directory / "spatial_variables.hdf5"

        # Parse movie parameter input.
        self.movie_params_file = movie_parameters
        if os.path.isfile(self.movie_params_file):
            self.movie_params = input_parse(self.movie_params_file)
        elif self.params["n_concentrations"] == 2.0:
            # print("Using default movie parameters.")
            self.movie_params = {'num_components': 2.0,
                                 'color_map': ['Blues', 'Reds'],
                                 'titles': ['Protein', 'RNA'],
                                 'figure_size': [14, 6],
                                 'frequency': 1}
        elif self.params["n_concentrations"] == 3.0:
            # print("Using default movie parameters.")
            self.movie_params = {'num_components': 3.0,
                                 'color_map': ['Blues', 'Reds', 'Greens'],
                                 'titles': ['Protein', 'RNA', 'Active Protein'],
                                 'figure_size': [22.5, 6],
                                 'frequency': 20}

    def run(self, geo: bool=True, hdf5: bool=True,
            plot_limits: bool=True, condensate: bool=True,
            start=0, end=-1):
        if geo:
            # Load Gmsh geometry
            self.geometry = set_mesh_geometry(self.params)
            self.xy = self.geometry.mesh.cellCenters.value.T
        if hdf5:
            # Load concentration profile
            with h5py.File(self.hdf5_file, mode="r") as concentration_dynamics:
                # Read concentration profile data from files
                self.concentration_profile = []
                for i in range(int(self.movie_params['num_components'])):
                    conc_arr = concentration_dynamics[f'c_{i}'][start:end]
                    conc_arr = conc_arr[~np.all(conc_arr == 0, axis=1)]
                    self.concentration_profile.append(conc_arr)
                if "t" in concentration_dynamics.keys():
                    self.time = np.ravel(concentration_dynamics["t"][start:end])
                
            self.n_frames = len(self.concentration_profile[0])
        if plot_limits:
            self.getPlotLimits()

    def makeSubdirectory(self, subdirectory:str):
        # Make a directory within the selfulation directory
        subdir_path = self.directory / subdirectory
        subdir_path.mkdir(exist_ok=True)
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

    def makeMovie(self,fps):
        write_movies_two_component_2d(self.directory,
                                      self.hdf5_file.name,
                                      self.movie_params,
                                      self.geometry.mesh,
                                      fps = fps)
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
        fig.savefig(fname=subdir_path /
            '{}.png'.format(self.movie_params['titles'][i]),
                    dpi=300, format='png')
        return fig
    def frameFigure(self,
                   i:int,
                   t:int,
                   cmap=None):
        cmap = cmap or self.movie_params['color_map'][i]
        fig,ax = plt.subplots()
        cs = ax.tricontourf(self.geometry.mesh.x,
                            self.geometry.mesh.y,
                            self.concentration_profile[i][t],
                            levels = np.linspace(int(np.floor(self.plotting_range[i][0]*100))*0.01,
                                                    int(np.ceil(self.plotting_range[i][1]*100))*0.01,
                                                    256),
                            cmap=cmap)
        # border = plt.Circle((0,0), self.params["radius"],
        #                     color='tab:gray', fill=False, linewidth=2)
        # ax.add_patch(border)
        ax.autoscale_view()
        ax.xaxis.set_tick_params(labelbottom=False, bottom=False)
        ax.yaxis.set_tick_params(labelleft=False, left=False)
        ax.set_aspect('equal', 'box')
        plt.setp(ax.spines.values(), visible=False)
        # cbar = fig.colorbar(cs,
        #                     ax=ax,
        #                     ticks=np.linspace(int(self.plotting_range[i][0]*100)*0.01,
        #                                     int(self.plotting_range[i][1]*100)*0.01,
        #                                     3),
        #                     shrink=0.6
        #                     )
        # cbar.ax.tick_params(labelsize=30)
        return fig,ax

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
            if condensate_coords.size == 0:
                arr = np.empty((resample_num_points,2))
                arr[:] = np.nan
            else:
                arr = self.resample_path(condensate_coords,resample_num_points)
            edge_lst.append(arr)
        self.edge_arr = np.array(edge_lst)
        xydist = self.edge_arr.max(axis=1)-self.edge_arr.min(axis=1)
        self.aspect_ratio = xydist[:,0]/xydist[:,1]
        self.eccentricity = np.sqrt(np.where(self.aspect_ratio<1,1-self.aspect_ratio**2,1-1/self.aspect_ratio**2))
        self.radius = np.sqrt(((self.edge_arr-self.com[:,None,:])**2).sum(axis=2))
        self.radius_variance = np.var(self.radius,axis=1)

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


    def condensate_property_plot(self):
        cmap = mpl.colormaps["Paired"].colors
        if not hasattr(self,"com"):
            self.condensate()
        com = self.com[~np.isnan(self.com).any(axis=1),:]
        e = self.eccentricity[~np.isnan(self.eccentricity)]
        r = self.radius[~np.isnan(self.radius).any(axis=1),:]
        y = com[:,0]
        f = uniform_filter1d(y,5)
        fig, ax = plt.subplots(2,2)
        axes = np.ravel(ax)
        fig.set_size_inches((6,3))
        axes[0].plot(y,label="Raw",color=cmap[0])
        axes[0].plot(f,label="Uniform filter",color=cmap[1])
        axes[0].legend()
        axes[0].set_xlabel("Frame")
        axes[0].set_ylabel("Distance\nfrom locus")
        axes[1].plot(y,-np.gradient(y),label="Raw",color=cmap[0])
        axes[1].plot(f,-np.gradient(f),label="Uniform filter",color=cmap[1])
        axes[1].set_xlabel("Distance\nfrom locus")
        axes[1].set_ylim(bottom=0)
        axes[1].set_ylabel("Condensate\nvelocity")
        axes[1].legend()
        axes[2].plot(e)
        axes[2].set_ylabel("Eccentricity")
        axes[2].set_xlabel("Frame")
        axes[3].plot(self.radius_variance)
        axes[3].set_ylabel("Radius\nvariance")
        axes[3].set_xlabel("Frame")
        fig.tight_layout()
        self.makeSubdirectory("figures")
        fig.savefig(self.directory / "figures" / "condensate.png")

    def rna(self):
        volumes = self.geometry.mesh.cellVolumes
        volume_vector = np.reshape(volumes,(len(volumes),1))
        self.rna_amount = np.ravel(self.concentration_profile[1]@volume_vector)
    
    def write_analysis(self):
        dct = {}
        time = getattr(self,"time",np.ones(self.n_frames)*np.nan)
        dct["time"] = time
        dct["center_of_mass"] = self.com[:,0]
        dct["eccentricity"] = self.eccentricity
        dct["variance_of_radius"] = self.radius_variance
        dct["mean_radius"] = np.mean(self.radius,axis=1)
        dct["rna_amount"] = self.rna_amount
        dct["c_light"] = np.nanmean(np.where(~self.mask,self.concentration_profile[0],np.nan),axis=1)
        dct["c_dense"] = np.nanmean(np.where(self.mask,self.concentration_profile[0],np.nan),axis=1)
        dct["volume"] = (self.mask*self.geometry.mesh.cellVolumes).sum(axis=1)
        velocity = np.diff(self.com[:,0])/np.diff(time)
        dct["velocity"] = velocity
        dct["aspect"] = self.aspect_ratio
        # dct["speed"] = np.abs(velocity)
        df = pd.DataFrame.from_dict(dct,orient="index").T
        df.to_csv(self.directory / "analysis.csv")

    def periodicity(self,tinit,peak_kw={},trough_kw={}):
        if not hasattr(self,"rna_amount"):
            self.rna()
        start = np.argmin((self.time-tinit)**2)
        self.peaks = find_peaks(self.rna_amount[start:],**peak_kw)[0] + start
        self.troughs = find_peaks(-self.rna_amount[start:],**trough_kw)[0] + start
            
class springPhaseDiagram:
    def __init__(self,
                 directory: str,
                 sweep_file: str = "sweep_parameters.txt"):
        self.sweep_directory = Path(directory)
        self.sweep_file = self.sweep_directory / sweep_file
        self.sweep_parameters = [line.split(",")[0] for line in self.sweep_file.read_text().splitlines()]

    def extract_data(self,frame):
        simdir_paths = [file.parent for file in self.sweep_directory.glob("./*/input_params.txt")]
        processes = mp.Pool(8-1)
        self.results = processes.map(self.worker,[(path,frame) for path in simdir_paths])
        self.df = pd.DataFrame(self.results)
        if 'rest_length' in self.df.columns:
            self.df.loc[:, "rest_length"] = self.df["rest_length"].apply(lambda x: eval(x)[0]).astype(np.float64)
        self.df.loc[:, "k_tilde"] = self.df["k_tilde"].astype(np.float64)
    
    def worker(self,worker_input):
        simdir_path, frame = worker_input
        sim = simDir(simdir_path)
        param_values = sim.params
        relevant_params = {parameter: str(param_values[parameter]) for parameter in self.sweep_parameters}
        sim.run()
        sim.rna()
        sim.condensate()
        return relevant_params | {"rna_amount": sim.rna_amount.flatten()[frame],
                                "condensate_com": sim.com[frame,0],
                                "aspect_ratio": sim.aspect_ratio[frame],
                                "mask": sim.xy[sim.mask[frame,:],:],
                                "concentration": sim.concentration_profile[0][frame,:][sim.mask[frame,:]]}

def periodicity_plot(sim,threshold,leftlim=0,rightlim=20000):
    sim.periodicity(threshold)
    rna = np.ravel(sim.rna_amount)
    com = np.ravel(sim.com[:,0])
    time = np.ravel(sim.time)
    fig,axes = plt.subplots(4,1,sharex=True)
    fig.set_size_inches(5,3)
    axes[0].plot(time,rna)
    start = np.argmin((time-threshold)**2)
    axes[0].scatter(time[sim.peaks],rna[sim.peaks],alpha=0.3)
    axes[0].scatter(time[sim.troughs],rna[sim.troughs],alpha=0.3)
    diffs = np.diff(time[sim.peaks],axis=0)
    locst = (time[sim.peaks][:-1] + time[sim.peaks][1:])/2
    for i in range(len(diffs)):
        axes[0].annotate(f"{diffs[i].item():.0f}",(locst[i],0),ha='center',rotation=90,
                         va='bottom')
    axes[1].plot(time,com)
    axes[2].plot(time,np.var(sim.radius,axis=1))
    axes[3].plot(time,sim.eccentricity)
    [ax.axvline(i, color='grey', ls='dashed') for i in time[sim.peaks] for ax in axes]
    axes[3].set_xlabel("Time")
    axes[0].set_ylabel("RNA\nAmount")
    axes[1].set_ylabel("Center of\nMass")
    axes[2].set_ylabel("Variance of\nRadius")
    axes[3].set_ylabel("Eccentricity")
    axes[3].set_xlim(left=leftlim,right=rightlim)
    return fig,axes,sim.peaks,sim.troughs