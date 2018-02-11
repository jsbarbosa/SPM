import os
import numpy as np
import igor.binarywave as bw

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.exporters import ImageExporter
from pyqtgraph import GraphicsObject, GraphicsWidgetAnchor

class ScaleBar(GraphicsObject, GraphicsWidgetAnchor):
    """
    Displays a rectangular bar to indicate the relative scale of objects on the view.
    """
    def __init__(self, label_number, size, width=5, brush=None, pen=None, suffix='m', offset=None):
        GraphicsObject.__init__(self)
        GraphicsWidgetAnchor.__init__(self)
        self.setFlag(self.ItemHasNoContents)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

        if brush is None:
            brush = pg.getConfigOption('foreground')
        self.brush = pg.mkBrush(brush)
        self.pen = pg.mkPen(pen)
        self._width = width
        self.size = size
        if offset == None:
            offset = (0,0)
        self.offset = offset

        self.bar = QtGui.QGraphicsRectItem()
        self.bar.setPen(self.pen)
        self.bar.setBrush(self.brush)
        self.bar.setParentItem(self)

        self.text = pg.TextItem(text=pg.siFormat(label_number, suffix=suffix), anchor=(0.5,1))
        self.text.setParentItem(self)


    def parentChanged(self):
        view = self.parentItem()
        if view is None:
            return
        view.sigRangeChanged.connect(self.updateBar)
        self.updateBar()


    def updateBar(self):
        view = self.parentItem()
        if view is None:
            return
        p1 = view.mapFromViewToItem(self, QtCore.QPointF(0,0))
        p2 = view.mapFromViewToItem(self, QtCore.QPointF(self.size,0))
        w = (p2-p1).x()
        self.bar.setRect(QtCore.QRectF(-w, 0, w, self._width))
        self.text.setPos(-w/2., 0)

    def boundingRect(self):
        return QtCore.QRectF()

    def setParentItem(self, p):
        ret = GraphicsObject.setParentItem(self, p)
        if self.offset is not None:
            offset = pg.Point(self.offset)
            anchorx = 1 if offset[0] <= 0 else 0
            anchory = 1 if offset[1] <= 0 else 0
            anchor = (anchorx, anchory)
            self.anchor(itemPos=anchor, parentPos=anchor, offset=offset)
        return ret

class IBW(object):
    def __init__(self, filename):
        self.filename = filename
        self.file = bw.load(self.filename)

    def getParameters(self):
        values = self.file['wave']['note']
        parameters = values.replace(b'\xb0', b'').decode().replace('\r', '\r\n')
        return parameters

    def getData(self):
        return self.file['wave']['wData']

    def getLabels(self):
        labels = self.file['wave']['labels']
        labels = [item for subs in labels for item in subs]

        labels_ = []
        for label in labels:
            if len(label) > 0:
                labels_.append(label.decode())

        return labels_

    def generateFiles(self, data_extension = "csv", parameters_extension = "txt"):
        folder = ".".join(self.filename.split('.')[:-1])
        try:
            os.mkdir(folder)
        except FileExistsError:
            pass

        data = self.getData()
        labels = self.getLabels()
        params = self.getParameters()

        scale = float(params.splitlines()[0].split(":")[1])

        old_cwd = os.getcwd()
        os.chdir(os.path.join(old_cwd, folder))

        params_name = "parameters." + parameters_extension

        with open(params_name, "w") as file: file.write(params)

        for (i, label) in enumerate(labels):
            d = data[:, :, i]
            self.plotData(d, label, scale)
            d_name = label + "." + data_extension
            np.savetxt(d_name, d, delimiter=',', newline='\r\n', fmt = '%.8e')

        os.chdir(old_cwd)

    def plotData(self, data, label, scale):
        data = data[:, ::-1]
        y, x = data.shape

        iw = pg.image()
        img = pg.ImageItem()

        iw.addItem(img)

        iw.view.setRange(QtCore.QRectF(0, 0, scale, scale*1.1))

        img.setImage(data)
        img.scale(scale/x, scale/y)

        textU = pg.TextItem("UNIANDES", anchor = (1, 1.0))
        textU.setParentItem(iw.view)
        textU.setPos(x*1.5, y*2.25)

        textL = pg.TextItem(label.upper(), anchor = (0, 1.0))
        textL.setParentItem(iw.view)
        textL.setPos(x*0.25, y*2.25)

        factor = 5
        fixer = 65
        image_size = factor * x - 2*fixer
        # size_coeff = 2*image_size/x

        size = x/5

        scale = ScaleBar(label_number = size*scale/x, size = 2*size, suffix='m')
        scale.setParentItem(iw.view)
        scale.anchor((1, 1), (1, 0.95), offset=(-fixer, 0))

        exporter = ImageExporter(iw.view)
        exporter.parameters()['width'] = factor*x
        exporter.export(label + '.png')

name = "Image0001.ibw"

ibw = IBW(name)
ibw.generateFiles()
