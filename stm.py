import os
import igor
import numpy as np
import igor.binarywave as bw
from PIL import Image, ImageFont, ImageDraw

from datetime import date
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, Table #Spacer
from reportlab.lib.styles import getSampleStyleSheet

import win_unicode_console
win_unicode_console.enable()

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

        canvas2.drawImage("Logo2.png", LEFT, HEIGHT - 3*cm, height = 2*cm, width = 6*cm, preserveAspectRatio = True, mask = 'auto')

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

def getName():
    return input("File directory: ")

if __name__ == '__main__':
    name = getName()

    ibw = IBW(name)
    ibw.generateFiles()
