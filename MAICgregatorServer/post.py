import cookielib
import os
import urllib
import urllib2
import re

COOKIEFILE = "cookies.lwp"

# Pre-comile all of our regular expressions
SPLIT_STRING = "           **********************************************************************          \r\n"
PRO_TITLE = re.compile("PRO_TITLE:(.+?)\r\n")
PK_AWARDS = re.compile("PK_AWARDS:(.+?)\r\n")
FIRM = re.compile("FIRM:(.+?)\r\n")
URL = re.compile("URL:(.+?)\r\n")
PI_NAME = re.compile("PI_NAME:(.+?)\r\n")
AWARD_AMT = re.compile("AWARD_AMT:(.+?)\r\n")

def STTRQuery(query):
    params = {'CRITERIA': query,
              'Program': 'STTR',
              'PICK LIST': 4,
              'SEARCH': 'Search',
              'STATE': 'All States',
              'SortIt': 1,
              'WhereFrom': 'FromHere',
              'agency': 'All DoD'}
    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6',
               'Referer': 'http://www.dodsbir.net/Awards/Default.asp',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    paramsEncoded = urllib.urlencode(params)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open('http://www.dodsbir.net/Awards/Default.asp')
    opener.close()

    url = 'http://www.dodsbir.net/Awards/SrchResultsDtlsList.asp'
    request = urllib2.Request(url, paramsEncoded, headers)
    handle = opener.open(request)
    #print handle.read()

    response = opener.open('http://www.dodsbir.net/Awards/PrintSelection.asp?FromBorC=B&Cnt=30')
    opener.close()

    response = opener.open('http://www.dodsbir.net/Awards/PrintFile1.asp?FromBorC=B')
    result = response.read()
    opener.close()
    
    return parseSTTRResult(result)
    #fp = open(query + " STTR.txt", "w")
    #fp.write(result)
    #fp.close()

def MarketwireQuery(query):
    params = {'grpSearch': 'K',
              'params': query}
    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6',
               'Referer': 'http://www.dodsbir.net/Awards/Default.asp',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    paramsEncoded = urllib.urlencode(params)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    url = 'http://www.marketwire.com/mw/search.do'
    request = urllib2.Request(url, paramsEncoded, headers)
    response = opener.open(request)
    result = response.read()
    opener.close()
    
    return result

def parseSTTRResult(result):
    # First, split the data based on the delimited in the file
    resultSplit = result.split(SPLIT_STRING)

    parsedResults = []
    for item in resultSplit:
        
        itemParsed = {}
        # Now go through each line of our item and add it to our dictionary
        for newItem in item.split("\r\n"):
            data = newItem.split(":")
            if (len(data) == 2):
                itemParsed[data[0]] = data[1]
            elif (len(data) > 2):
                itemParsed[data[0]] = "".join(data[1:])

        if (len(itemParsed) > 0):
            parsedResults.append(itemParsed)

    return parsedResults

def USASpendingQuery(query):
    # TODO
    # * Save this to our XML database
    # * Update so that after July 30 we move to current year (last fiscal year)
    urlPart1 = "http://www.usaspending.gov/faads/faads.php?reptype=r&database=faads&recipient_name="
    urlPart2 = "&duns_number=&recipient_city_name=&recipient_state_code=&recipient_cd=&recipient_zip=&recipient_county_name=&recip_cat_type=&asst_cat_type=&email=&dollar_tot=&fiscal_year=2008&first_year_range=&last_year_range=&detail=4&datype=X"
    url = urlPart1 + urllib.quote(query) + urlPart2
    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(url)
    result = response.read()

    fp = open(query + '.xml', 'w')
    fp.write(result)
    fp.close()

def GoogleNewsQuery(query):
    urlPart1 = "http://news.google.com/news?pz=1&ned=us&hl=en&q="
    urlPart2 = "&output=rss"
    url = urlPart1 + urllib.quote(query) + urlPart2
    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6'}

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    request = urllib2.Request(url, None, headers)
    handle = opener.open(request)
    return handle.read()

