from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtNetwork import *
import sys


# Subclass QNetworkAccessManager Here
class NetworkAccessManager(QNetworkAccessManager):
    # Save image data in QByteArray buffer to the disk (google_image_logo.png
    # in the same directory)
    @pyqtSlot()
    def slotFinished(self):
        print 'finished'
        self.messageBuffer += self.reply.readAll()
        imageFile = QFile("/home/mehdi/google_image_logo.png")
        if (imageFile.open(QIODevice.WriteOnly)):
            imageFile.write(self.messageBuffer)
            imageFile.close()
            QMessageBox.information(None, "Hello!", "File has been saved!")
        else:
            QMessageBox.critical(None, "Hello!", "Error saving file!")

    # Append current data to the buffer every time readyRead() signal is emitted
    @pyqtSlot()
    def slotReadData(self):
        print 'new data'
        self.messageBuffer += self.reply.readAll()

    def __init__(self):
        QNetworkAccessManager.__init__(self)
        self.messageBuffer = QByteArray()
        url = QUrl("http://upload.wikimedia.org/wikipedia/commons/f/fe/Google_Images_Logo.png")
        req = QNetworkRequest(url)
        self.reply = self.get(req)

        QObject.connect(self.reply, SIGNAL("readyRead()"), self, SLOT("slotReadData()"))
        QObject.connect(self.reply, SIGNAL("finished()"), self, SLOT("slotFinished()"))
        # End of NetworkAccessManager Class


###################################

def main():
    app = QApplication(sys.argv)
    networkAccessManager = NetworkAccessManager()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
