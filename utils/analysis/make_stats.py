#!/usr/bin/env python
import argparse
from utils.analysis.tools import simDir
from pathlib import Path

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
    # if not (Path(folder) / "movies").exists():
    sim = simDir(folder,movie_params)
    sim.run()
    sim.condensate()
    sim.rna()
    sim.write_analysis()