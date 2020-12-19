import os
import sys
import igor
import ctypes
import numpy as np
import igor.binarywave as bw
from PIL import Image, ImageFont, ImageDraw, ImageQt

from threading import Thread

from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Table #Spacer
from reportlab.lib.styles import getSampleStyleSheet

if sys.platform == 'win32':
    import win_unicode_console
    win_unicode_console.enable()

from PyQt5 import QtCore, QtGui, QtWidgets

import images

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

    def generatePDF(self):
        WIDTH, HEIGHT = letter

        LEFT = 2*cm
        TOP = HEIGHT - 2*cm

        filename =  os.path.basename(self.filename)
        folder = ".".join(self.filename.split('.')[:-1])
        pdfname = os.path.join(folder, "Report.pdf")

        today_date = date.today().strftime('%d/%m/%Y')

        canvas2 = canvas.Canvas(pdfname, pagesize = letter)
        canvas2.setLineWidth(.3)
        canvas2.setFont('Helvetica', 11)

        # image = QtGui.QImage()
        # image.load(":/logo2.png")
        # newimg = image.convertToFormat(QtGui.QImage.Format_ARGB32)
        #
        # h, w = newimg.height(), newimg.width()
        #
        # data = np.zeros((h, w))
        #
        # for i in range(h):
        #     for j in range(w):
        #         val = newimg.pixel(j, i)
        #         data[i, j] = val
        # img = Image.fromarray(np.uint8(data))
        # # Extract the first channel
        # image = np.array(ptr, dtype = np.uint8).reshape(newimg.height(), newimg.width(), 4)[:,:,0].copy()
        # print(image)

        # canvas2.drawImage(img, LEFT, HEIGHT - 3*cm, height = 2*cm, width = 6*cm, preserveAspectRatio = True, mask = 'auto')

        canvas2.drawString(LEFT, 680, 'CENTRO DE MICROSCOPÍA')
        canvas2.drawString(LEFT, 660, 'UNIVERSIDAD DE LOS ANDES')
        canvas2.drawString(460, TOP, "Date:")
        canvas2.drawString(500, TOP, today_date)
        canvas2.line(490, TOP - 3, 560, TOP - 3)

        canvas2.drawString(350, TOP - 1*cm, "Source:")
        canvas2.drawString(400, TOP - 1*cm, filename)
        canvas2.line(390, TOP - 1*cm - 3, 560, TOP - 1*cm - 3)

        labels = self.getLabels()

        spacing = 1.5*cm
        size = 8*cm
        top = TOP - 3*cm - 3 - spacing
        bottom = top - size

        page = 1

        canvas2.line(50, top + spacing, WIDTH - 50, top + spacing)

        page_height = 30
        canvas2.drawString(WIDTH/2, page_height, "%d"%page)

        lines = int(np.ceil(len(labels)*0.5))

        for i in range(lines):
            name1 = folder + "/" + labels[i*2] + ".png"
            canvas2.drawImage(name1, LEFT, bottom, height = size, width = size,
            preserveAspectRatio = True)
            try:
                name2 = folder + "/" + labels[i*2 + 1] + ".png"
                canvas2.drawImage(name2, LEFT + size + spacing, bottom, height = size,
                width = size, preserveAspectRatio = True)
            except:
                pass

            top = bottom - spacing
            bottom = top - size

            if (bottom < 0) or (top < 0):
                canvas2.showPage()
                top = TOP
                bottom = top - size
                page += 1
                canvas2.drawString(WIDTH/2, page_height, "%d"%page)

        params = self.getParameters()
        lines = params.split('\r\n')
        lines = [line.split(':') for line in lines]
        params = params.replace('\n','<br />\n')

        nlines = 35

        temp = [lines[i*nlines : (i+1)*nlines] for i in range(len(lines)//nlines)]

        style = getSampleStyleSheet()["Normal"]

        npages = len(temp)

        for (i, line) in enumerate(temp):
            table = Table(line)
            table.wrapOn(canvas2, WIDTH - 100, HEIGHT - 100)
            table.drawOn(canvas2, LEFT, TOP - nlines*18)

            if i != npages - 1:
                canvas2.showPage()

                page += 1
                canvas2.drawString(WIDTH/2, page_height, "%d"%page)

        canvas2.save()


    def generateFiles(self, data_extension = "csv", parameters_extension = "txt"):
        print("Creating folder...")
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
        try:
            os.chdir(os.path.join(old_cwd, folder))

            params_name = "parameters." + parameters_extension

            print("Saving parameters...")
            with open(params_name, "w") as file: file.write(params)

            for (i, label) in enumerate(labels):
                d = data[:, :, i]
                print("Saving %s plot..."%label)
                self.plotData(d, label, scale)
                d_name = label + "." + data_extension
                print("Saving %s data..."%label)
                np.savetxt(d_name, d, delimiter=',', newline='\n', fmt = '%.8e')
        except:
            pass
        os.chdir(old_cwd)

        print("Saving PDF report...")
        self.generatePDF()

    def plotData(self, data, label, scale):
        data = data.T[::-1]
        x, y = data.shape

        m = data.min()
        rg = data.max() - m

        add_rows = 20

        data = (data - m)/rg
        data = (data *  255).astype(int)
        data = np.vstack((data, np.zeros((add_rows, x))))

        line = x // 5
        scale = (scale / 5) * 1e6

        data[y + add_rows//4 - 2 : y + add_rows//4 + 2, -line:] = 255


        im = Image.fromarray(data).convert('L')

        y_text =  y + add_rows / 4
        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("arial.ttf", int(add_rows/2))
        draw.text((x/2 - 20, y_text), "UNIANDES", font = font, fill = 255)
        draw.text((0, y_text), label.upper(), font = font, fill = 255)
        draw.text((x - line, y_text + add_rows / 6), "%.1f µm"%scale, font = font, fill = 255)

        im.save(label + ".png")

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app = None):
        QtWidgets.QMainWindow.__init__(self)

        self.app = app

        self.setFixedSize(600, 80)
        self.setWindowTitle("Igor Extractor")
        self.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.centralWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(11, 11, 11, 11)
        self.verticalLayout.setSpacing(6)

        self.frame1 = QtWidgets.QFrame()
        self.horizontalLayout1 = QtWidgets.QHBoxLayout(self.frame1)
        self.horizontalLayout1.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout1.setSpacing(6)

        self.label = QtWidgets.QLabel()
        self.label.setText("Directory:")

        self.lineEdit = QtWidgets.QLineEdit()
        self.button = QtWidgets.QPushButton("Browse")

        self.horizontalLayout1.addWidget(self.label)
        self.horizontalLayout1.addWidget(self.lineEdit)
        self.horizontalLayout1.addWidget(self.button)

        self.verticalLayout.addWidget(self.frame1)

        self.frame2 = QtWidgets.QFrame()
        self.horizontalLayout2 = QtWidgets.QHBoxLayout(self.frame2)
        self.horizontalLayout2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout2.setSpacing(6)
        self.horizontalLayout2.setAlignment(QtCore.Qt.AlignRight)

        self.g_button = QtWidgets.QPushButton("Extract")
        self.g_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout2.addWidget(self.g_button)

        self.verticalLayout.addWidget(self.frame2)

        self.directory = os.path.expanduser("~")

        self.button.clicked.connect(self.open)
        self.g_button.clicked.connect(self.extract)

    def open(self):
        dlg = QtWidgets.QFileDialog(directory = self.directory)

        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen)
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dlg.setNameFilters(["Igor files (*.ibw)"])
        if dlg.exec_():
            name = dlg.selectedFiles()[0]
            self.lineEdit.setText(name)
            self.directory = os.path.abspath(os.path.join(name, os.pardir))

    def extract(self):
        loc = self.lineEdit.text()
        try:
            ibw = IBW(loc)
            thread = Thread(target = self.threadFunc, args = (ibw,))
            thread.start()
        except Exception as e:
            error_text = str(e)
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText('An Error has ocurred.\n%s'%error_text)
            msg.setWindowTitle("Error")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            msg.exec_()

    def threadFunc(self, ibw):
        if self.app != None:
            self.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))

        self.g_button.setEnabled(False)
        ibw.generateFiles()
        self.g_button.setEnabled(True)

        if self.app != None:
            self.app.restoreOverrideCursor()

def getName():
    return input("File directory: ")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon(':/icon.ico')
    app.setWindowIcon(icon)
    app.processEvents()
    if sys.platform == 'win32':
        myappid = 'extractor.extractor.01' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    main = MainWindow(app)
    main.setWindowIcon(icon)
    main.show()
    app.exec_()
    # name = getName()
    #
    # ibw = IBW(name)
    # ibw.generateFiles()
