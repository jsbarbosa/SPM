import os
import igor
import numpy as np
import igor.binarywave as bw
from PIL import Image, ImageFont, ImageDraw

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

if __name__ == '__main__':
    name = input("File directory: ")

    ibw = IBW(name)
    ibw.generateFiles()
