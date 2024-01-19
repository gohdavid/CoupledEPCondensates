#!/usr/bin/env python
import argparse
from utils.analysis.tools import simDir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Directory name to search for hdf5 files and generate movies')
    parser.add_argument('--i', help="Simulation directory", required=True)
    parser.add_argument('--m', help="Path to movie parameters file", default="movie_params.txt")
    parser.add_argument('--fps', help="FPS", default="30")
    # parser.add_argument('--snapshots', action=argparse.BooleanOptionalAction)
    # parser.add_argument('--movie', action=argparse.BooleanOptionalAction)
    # parser.add_argument('--properties', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    folder = args.i
    fps = args.fps
    movie_params = args.m
    sim = simDir(folder,movie_params)
    sim.run()
    # if args.movie:
    sim.makeMovie(int(fps))
    # if args.figures:
    sim.makeFigure(i=0)
    sim.makeFigure(i=1)
    # if args.properties:
    sim.condensate_property_plot()