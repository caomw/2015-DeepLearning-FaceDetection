__author__ = 'Tanuj'

import skimage.io as io
from os import walk
import re

FDDB_path = "./data/FDDB-folds/"

data = []

f = []
for (dirpath, dirnames, filenames) in walk(FDDB_path):
    f.extend(filenames)
    break

regex = re.compile(".*(ellipseList).*")
f = [m.group(0) for l in f for m in [regex.search(l)] if m]

file = open(FDDB_path + f[0], 'rb')
n = -1
mode = None
lines = file.readlines()

n_lines = len(lines)
i = 0

mode = None

while(i < n_lines):
    

    i += 1