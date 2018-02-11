import pyqtgraph as pg

from pyqtgraph.exporters import ImageExporter
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np


data = np.genfromtxt("Image0001/AmplitudeRetrace.csv", delimiter=",")

data = data[:, ::-1]

iw = pg.image()
img = pg.ImageItem()
iw.addItem(img)
iw.view.setRange(QtCore.QRectF(0, 0, 255, 255*1.1))

img.setImage(data)
# img.scale(4e-5, 4e-5)

text = pg.TextItem("UNIANDES", anchor = (0.5, 1.0))
text.setParentItem(iw.view)
text.setPos(600/2, 640*0.9)

scale = pg.ScaleBar(size = 100, suffix='m')
scale.setParentItem(iw.view)
scale.anchor((1, 1), (1, 0.95), offset=(-40, 0))

exporter = ImageExporter(iw.view)
exporter.export('image_'+'.png')
