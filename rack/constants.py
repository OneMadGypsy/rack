import os, re
from   dataclasses import MISSING

#app directory
CWD = os.getcwd()

#directories
DAT = os.path.join(CWD, 'dat')
if not os.path.isdir(DAT):
    os.mkdir(DAT)

UNIQUE     = MISSING
UNIQUE_SEP = '_'
FOREIGNKEY = re.compile(r'fk_(?P<key>[\w\d]+)').fullmatch
ISUNIQUE   = re.compile(fr'(?P<type>[\w\d]+){UNIQUE_SEP}(?P<id>\d+)').fullmatch