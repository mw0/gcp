#!/bin/python

import subprocess
import urllib2
import json
import sys
import time

fetcher = urllib2.build_opener()

def scrape_me_some_pix(searchTerm, maxCt, offset):
    searchTerm = '+'.join(searchTerm.split())
    maxCt = int(maxCt)
    offset = int(offset)
    for startIndex in range(offset, maxCt + offset, 4):
        if (startIndex - offset) % 80 == 0 and startIndex > offset:
            time.sleep(61)
        searchURL = "http://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=" \
                    + searchTerm + "&start={0}".format(startIndex)
        print "\n{0}\n".format(searchURL)
        f = fetcher.open(searchURL)
        json_reply = json.load(f)
        if json_reply['responseStatus'] != 200:
            print "Problems Houston!\n"
            print "startIndex: {0}".format(startIndex)
            print searchURL
            print "Response status code: {0}\n".format(json_reply['responseStatus'])
        else:
            results = json_reply['responseData']['results']

            for item in results:
                print item['url']
                subprocess.call(["wget", "--no-clobber", "--progress=dot",
                                 item['url']])

if __name__ == '__main__':
    '''
    Usage:

    scrapteGI.py <search term> [<max count>] [<offset>]
    where

    <search term>	term to search for
    <max count>		mostly-useless limit on number of items to return
			(Google limits to 40 or so)
    <offset>		starting image to start scrape (useful for re-starts)
    '''

    maxCt = 60
    offset = 0
    searchTerm = 'puppies!'

    if len(sys.argv) == 2:
        searchTerm = sys.argv[1]
    elif len(sys.argv) == 3:
        searchTerm = sys.argv[1]
        maxCt = sys.argv[2]
    elif len(sys.argv) == 4:
        searchTerm = sys.argv[1]
        maxCt = sys.argv[2]
        offset = sys.argv[3]

    if len(sys.argv) > 4:
        print "\nIgnoring extra command line arguments.\n"

    print "\nscrapteGI.py '{0}' {1} {2}\n\n".format(searchTerm, maxCt, offset)
    scrape_me_some_pix(searchTerm, maxCt, offset)
