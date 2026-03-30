#!/usr/bin/env bash

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Downloading MovieLens dataset..."
wget https://files.grouplens.org/datasets/movielens/ml-latest.zip

echo "Unzipping dataset..."
unzip ml-latest.zip

echo "Build completed!"