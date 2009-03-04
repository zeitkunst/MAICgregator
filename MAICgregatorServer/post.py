import cookielib
import os
import urllib
import urllib2

COOKIEFILE = "cookies.lwp"

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

    fp = open(query + " STTR.txt", "w")
    fp.write(result)
    fp.close()


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

