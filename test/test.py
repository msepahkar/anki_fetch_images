import sys
from PyQt4 import QtCore, QtGui, QtWebKit, QtNetwork

app = QtGui.QApplication(sys.argv)
dialog = QtGui.QDialog()
layout = QtGui.QVBoxLayout(dialog)
web_view = QtWebKit.QWebView()
layout.addWidget(web_view)

request = QtNetwork.QNetworkRequest()
request.setUrl(QtCore.QUrl("https://www.google.com/search?safe=active&site=&tbm=isch&source=hp&biw=1161&bih=655&q=allah&oq=allah&gs_l=img.3...1748.2393.0.2639.6.6.0.0.0.0.0.0..0.0....0...1ac.1.64.img..6.0.0.0.jrlwtcqdSk4"));
request.setRawHeader("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36")
web_view.load(request)
print web_view.page().settings().testAttribute( QtWebKit.QWebSettings.JavascriptEnabled )


# web_view.load(QtCore.QUrl('https://www.google.com/search?safe=active&site=&tbm=isch&source=hp&biw=1161&bih=655&q=allah&oq=allah&gs_l=img.3...1748.2393.0.2639.6.6.0.0.0.0.0.0..0.0....0...1ac.1.64.img..6.0.0.0.jrlwtcqdSk4'))
dialog.show()
app.exec_()