import cookielib
import os
import urllib
import urllib2
import re
import shutil
import tempfile

from BeautifulSoup import BeautifulSoup
import html5lib
from html5lib import treebuilders

"""
can use sites like:
    http://cornell.erecruiting.com/corp/employer_cf_list?page_id=career_fairs&channel_id=university&_tcgis_public_fairs=%3Ctcgis+tag%3D%224%22+page%3D%223%22%3E%3C%2Ftcgis%3E
    to start to find public career fairs for schools.  need to look for even more sites to see what are the other major players in the field

    something to look at here, as well, if we could just figure things out with the site:
        https://virginia-csm.symplicity.com/events/students.php?cf=SJIF09&cck=1&au=&ck=
    also:
        https://wsu-csm.symplicity.com/events/students.php?cf=spring2009

    and something like this is quite extensive:
        http://www.careers.uiowa.edu/fairs/spring_participants09.cfm#
    but hard to figure out ahead of time

    maybe here:
        http://efair.careerlink.com/

    this seems like its hidden behind passwords:
        http://www.ucanintern.com/
        https://nic-csm.symplicity.com/students/
"""

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
    faadsQuery = "http://www.usaspending.gov/faads/faads.php?datype=X&detail=4&sortby=f&recipient_name=%s&fiscal_year=2008" % urllib.quote(query)
    fpdsQuery = "http://www.usaspending.gov/fpds/fpds.php?datype=X&detail=4&sortby=f&fiscal_year=2008&company_name=%s" % urllib.quote(query)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(faadsQuery)
    faads = response.read()
 
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(fpdsQuery)
    fpds = response.read()
   
    return (faads, fpds)

def TrusteeSearch(query):
    # get from http://foundationcenter.org/findfunders/990finder/
    # also: http://www.muckety.com/Query
    # foo = trustees.split("Form 990, Part V-A - Current Officers, Directors, Trustees, and Key Employees:")
    # try this regex: regex = re.compile("([A-Z]+\s[A-Z]*\s[A-Z0-9]+).+?\s[A-Z]+\,\s[A-Z]{2}\s[0-9]{5}", flags=re.M)
    # And then: regex = re.compile("([\sA-Z]+)", re.M)

    # Remove any final "at (location)" from query names
    if (query.find("at ") != -1):
        query = query.split("at ")[0].strip()
    
    params = {'990_type': 'A',
              'action': 'Find',
              'ei': '',
              'fn': query,
              'fy': '2007',
              'st': '',
              'zp': ''}
    # HEINOUSness for Harvard; search for the fellows instead, and go back to 2006 since they haven't uploaded anything more recent
    if (query == "Harvard University"):
        query = "President and Fellows of Harvard College"
        params = {'990_type': 'A',
              'action': 'Find',
              'ei': '',
              'fn': query,
              'fy': '2006',
              'st': '',
              'zp': ''}

    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6'}

    paramsEncoded = urllib.urlencode(params)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    url = 'http://dynamodata.fdncenter.org/990s/990search/esearch.php'
    request = urllib2.Request(url, paramsEncoded, headers)
    response = opener.open(request)
    result = response.read()
    opener.close()

    # Parse data
    soup = BeautifulSoup(result)
    table = soup.find(text=re.compile("documents \ndisplayed"))
    entries = table.findParent().findNextSiblings('p')
    schoolRegex = re.compile("\s*[^a-zA-Z0-9]+\s%s\n" % query)
    schoolRegexResearchFoundation = re.compile("\s*Research\sFoundation\sof\s%s\n" % query)
    schoolRegexFoundation = re.compile("\s*[a-zA-Z0-9]*\s%s\sFoundation[\sa-zA-Z,\.]*\n" % query)
    schoolRegexSchool = re.compile("\s*[a-zA-Z0-9]*\s%s\sSchool\n" % query)
    links = entries[0].findAll("a")    
    
    formLink = []
    for link in links:
        if schoolRegex.match(link.contents[0]):
            formLink.append(link.attrs[0])

    # State schools sometimes give their names as SchoolName Foundation
    if (len(formLink) == 0):
        for link in links:
            if schoolRegexFoundation.match(link.contents[0]):
                formLink.append(link.attrs[0])

    # Or as SchoolName School
    if (len(formLink) == 0):
        for link in links:
            if schoolRegexSchool.match(link.contents[0]):
                formLink.append(link.attrs[0])

    # Or, for some state systems, Research Foundation of School
    if (len(formLink) == 0):
        for link in links:
            if schoolRegexResearchFoundation.match(link.contents[0]):
                formLink.append(link.attrs[0])

    print formLink    
    trustees = []
    if (len(formLink) >= 1):
        href = formLink[0][1]
        tempDir = tempfile.mkdtemp()

        request = urllib2.Request(href)
        response = opener.open(request)
        result = response.read()
       
        # TODO
        # HEINOUS, need to make cross-platform
        pdfFilename = tempDir + "/" + query.replace(" ", "") + ".pdf"
        fp = open(pdfFilename, "w")
        fp.write(result)
        fp.close()

        # Convert file to text
        txtFilename = tempDir + "/" + query.replace(" ", "") + ".txt"
        # TODO
        # make this less brittle
        os.system("/usr/bin/pdftotext %s %s" % (pdfFilename, txtFilename))

        fp = open(txtFilename, "r")
        data = fp.readlines()
        fp.close()
        data = "".join(data)
        split990Data = data.split("Form 990, Part V-A - Current Officers, Directors, Trustees, and Key Employees:")
        split990Data = split990Data[1:len(split990Data) - 1]
        
        # TODO
        # Fix regex that now captures "and other allowances\n\nNAME" since we're matching upper and lowercase letters now
        trusteeRegex = re.compile("([A-Za-z\]\[]+\s*[A-Za-z]*\s+[A-Za-z]*\s*[A-Za-z0-9\'\^]+\s).+?\s[A-Za-z0-9\s']+\s*\,\s*[A-Za-z\s]{2,3}\s[0-9]{5,9}", flags=re.M)
        trusteeRegexNewlines = re.compile("and other allowances\\n\\n([A-Za-z\]\[]+\s*[A-Za-z]*\s+[A-Za-z]*\s*[A-Za-z0-9\'\^]+\s)")
        stripNumbersRegex = re.compile("([A-Za-z\[\]\s]+)[0-9]*")
        for trusteeSet in split990Data:
            trusteeList = trusteeRegex.findall(trusteeSet)

            # The main regex screws up the first name, so lets get that and update it
            trusteeFirstItem = trusteeRegexNewlines.findall(trusteeSet)
            if (len(trusteeFirstItem) > 0):
                trusteeList[0] = trusteeFirstItem[0]
            
            # TODO
            # Need to have heuristics for the following:
            # University of Texas...different regex
            # University of Massachusetts...different regex
            trusteeList = map(stripNumbersRegex.findall, trusteeList)
            trusteeList = [item[0].strip() for item in trusteeList]
            trusteeList = [item.title() for item in trusteeList]
            trusteeList = [item.replace("]", "") for item in trusteeList]
            trusteeList = [item.replace("^", "") for item in trusteeList]
            
            # TODO
            # HEINOUS
            # University of Oregon, University of Iowa...take care of ending "Po" characters
            # This would remove anyone with a last name of Po...but I'm not sure how to fix the problem at the moment
            trusteeList = [item.replace(" Po", "") for item in trusteeList]
            trustees.extend(trusteeList)
        
        # cleanup
        # TODO
        # enable when we're ready
        #shutil.rmtree(tempDir)

    return trustees

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

def TrusteeImage(personName, withQuotes = True):
    # TODO
    # Make option to search for names without quotes as well.
    opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0. 6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6'}
    if (withQuotes):
        url = "http://images.google.com/images?hl=en&q=" + urllib.quote("\"" + personName + "\"")
    else:
        url = "http://images.google.com/images?hl=en&q=" + urllib.quote(personName)

    request = urllib2.Request(url, None, headers)
    response = opener.open(request)
    results = response.read()
    parser = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("beautifulsoup"))
    soup = parser.parse(results)
    script = soup.findAll("script")

    # TODO
    # Make this less brittle; go through each script tag and only accept it if we can find the imgres value
    imgScript = str(script[4])
    imgList = imgScript.split("imgres?imgurl\\x3d")

    imgSrc = None
    imgList = imgList[1:]
    for img in imgList:
        if (img.find("muckety") == -1):
            imgSrc = img
            break
    #print "imgSrc IS: " + imgSrc

    if (imgSrc != None):
        return imgSrc.split("\\x26")[0]
    else:
        return None

"""
div = soup.findAll("div")
imgDiv = div[10]
table = imgDiv.findAll("table")
111: tr = table[0].findAll("tr")
119: href = tr[0].td.a['href']
122: href.split("=")[1].split("&")[0]
"""
