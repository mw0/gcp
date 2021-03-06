#!/bin/python

# sg.py
# Copyright Mark Wilber 2014.

# This is a test of web scraping/parsing in the semi-practical form of a
# text-based google search query.

# Usage:

# sg.py 'fedora python requests package'

# This sends a query request to Google, parses the responses and spews links
# (HTML format).
# Recognizing that Google returns results on multiple pages, this searches the
# end of each resulting page for links to addtional pages of links, looping
# through those until all results have been printed.


import sys, string
import requests, codecs, re, html2text
from BeautifulSoup import BeautifulSoup

def getPage(searchAppend):

    # Dynamically build the request URL:
    baseURL = "https://www.google.com"
    url = baseURL + searchAppend + '&tbm=isch'

    # Spoof headers so the request appears to be from a browser, not a bot:
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
        "accept-encoding": "gzip,deflate,sdch",
        "accept-language": "en-US,en;q=0.8",
    }

    # Make the request to the search url, passing in the the spoofed headers.
    r = requests.get(url, headers=headers) # assign the response to a variable r

    # Check the status code of the response to make sure the request went well
    print "status code: ", r.status_code
    if r.status_code <> 200:
        print("request denied")
        return
    else:
        print("scraping " + url)
        print ""

#   # Print web page after converting to UTF-8:
#   unicoded = r.text.encode("utf-8")
#   print "unicoded:"
#   print unicoded[:2500]
#   print ""

    # Convert the plaintext HTML markup into a DOM-like structure that we can
    # search:
    soup = BeautifulSoup(r.text)

    # Each result is an <li> element with class="g". This is our wrapper:
#   liElements = soup.findAll("li", {'class':"g"})
    aElements = soup.findAll("a", {'class':"rg_l"}, href=True)
#   print liElements
#   print ""

    # Iterate over each of the liElement:
#   for liElement in liElements:
    for aElement in aElements:

        print "aElement:"
        print aElement, "\n"
        print aElement['href']
        print ""
        print "len(aElements): {0}".format(len(aElements))

#   print "		--------------------------------------------"

    # Extract all tables contents:
    tables = soup.findAll("table", {'id':"nav"})
    print "tables:"
    print tables

    retStr = ''

    # There will likely be only one table element, but just in case do a loop:
    for table in tables:
#       print table
#       print ""

        # Extract from a table element href anchors:
        aElements = table.fetch('a', {'href':re.compile('.+')})
#       print ""
#       print "aElements:"
#       print aElements

#       print "		--------------------------------------------"
#       print ""

        for a in aElements:
#           print a.contents
            if a['href'] <> "":
#               print a.contents
#               print a['href']
                retStr = a['href']

#   print ""
#   print "		--------------------------------------------"
    return retStr

def scrape_google(keyword):

    lastStartNo = 0
    searchAppend = "/search?q={term}".format(term=keyword.strip().replace(" ", "+"), )
    print "{0}\n".format(searchAppend)
    searchAppend = getPage(searchAppend)
    print "searchAppend: {0}\n".format(searchAppend)
    startNo = int(re.search('\&start=([0-9]+)\&', searchAppend).group(1))
#   print lastStartNo, startNo

    # If additional pages linked, continue fetching until done:
    if startNo:
        while startNo > lastStartNo:
            lastStartNo = startNo
            searchAppend = getPage(searchAppend)
#           print searchAppend
            startNo = int(re.search('\&start=([0-9]+)\&', searchAppend).group(1))
#           print lastStartNo, startNo

    return

if __name__ == "__main__":

    # You can pass in a keyword or string to search for when you run the script
    # By default, we'll search for the "web scraping" keyword
    try:
        keyword = sys.argv[1]
    except IndexError:
        keyword = "web scraping"

    print ""
    scrape_google(keyword)
