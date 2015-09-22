#!/bin/python

from bs4 import BeautifulSoup
import requests
import re
import urllib2
import os


def get_soup(url, header):
    return BeautifulSoup(urllib2.urlopen(urllib2.Request(url,headers=header)))

# you can change the query for the image  here  
query = "Terminator 3 Movie"
query= query.split()
query='+'.join(query)
url="https://www.google.com/search?q={0}&biw=981&bih=867&source=lnms&tbm=isch&sa=X&ved=0CAcQ_AUoAmoVChMI9Mei1P2AyAIVgX6SCh0dbwMz".format(query)

print url
header = {'User-Agent': 'Mozilla/5.0'} 
soup = get_soup(url,header)

images = [a['src'] for a in soup.find_all("img", {"src": re.compile("gstatic.com")})]
#print images
for img in images:
  raw_img = urllib2.urlopen(img).read()
# suffix = (img.split('.'))[-1]
  suffix = 'jpg'
  #add the directory for your image here 
  DIR="./"
  cntr = len([i for i in os.listdir(DIR) if query in i]) + 1
  print DIR, query, cntr, suffix
  f = open("{0}{1}{2:03d}.{3}".format(DIR, query, cntr, suffix), 'wb')
# DIR + query + "_"+ str(cntr)+".jpg", 'wb')
  f.write(raw_img)
  f.close()
