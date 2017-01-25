import urllib2
from StringIO import StringIO

url = 'https://translate.google.com/translate_tts?ie=UTF-8&q=hello&tl=en&total=1&idx=0&textlen=5&tk=487900.80448&client=t&prev=input&ttsspeed=0.24'
file_name = '/home/mehdi/hello.mpga'

header = {
  'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
}

response = urllib2.urlopen(urllib2.Request(url, headers=header))

maintype = response.headers['Content-Type'].split(';')[0].lower()
print maintype

with open(file_name, 'wb') as f:
  f.write(response.read())

