import sys
from Markov import *

markov = Markov()
try:
    markov.ExportWordList(sys.argv[1])
except:
    print("You probably forgot the filename")
