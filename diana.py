from stm import IBW
from glob import glob

files = glob('AFM/*.ibw')
for file in files:
    ibw = IBW(file)
    try:
        ibw.generateFiles()
    except Exception as e:
        print(file)
        print(e)
