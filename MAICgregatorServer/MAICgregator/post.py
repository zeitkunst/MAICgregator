# The code in MAICgregator is available under the GNU GPL V3 (http://www.gnu.   org/copyleft/gpl.html) with the following modifications:

# The words "you", "licensee", and "recipient" are redefined to be as follows:  "You", "licensee", and "recipient" is defined as anyone as long as s/he is not  an EXCLUDED PERSON. An EXCLUDED PERSON is any individual, group, unit,          component, synergistic amalgamation, cash-cow, chunk, CEO, CFO, worker, or      organization of a corporation that is a member, as of the date of acquisition   of this software, of the Fortune 1000 list of the world's largest businesses.   (See http://money. cnn.com/magazines/fortune/global500/2008/full_list/ for an   example of the top 500.) An EXCLUDED PERSON shall also include anyone working   in a contractor, subcontractor, slave, or freelance capacity for any member of  the Fortune 1000 list of the world's largest businesses.

# Please see http://maicgregator.org/license.


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
              'PICKLIST': 4,
              'SEARCH': 'Search',
              'STATE': 'All States',
              'SortIt': 1,
              'WhereFrom': 'basicAward',
              'agency': 'All DoD'}
    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6',
               'Referer': 'http://www.dodsbir.net/Awards/Default.asp',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

    paramsEncoded = urllib.urlencode(params)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    print "opening default page"
    try:
        response = opener.open('http://www.dodsbir.net/Awards/Default.asp')
    except urllib2.HTTPError, e:
        try:
            response = opener.open('http://www.dodsbir.net/Awards/Default.asp')
        except urllib2.HTTPError, e:
            print "unable to open default.asp"
            return ["Failed to connect...are we being blocked?"]

    opener.close()

    url = 'http://www.dodsbir.net/Awards/SrchSetCriteria.asp'
    request = urllib2.Request(url, paramsEncoded, headers)
    print "setting search criteria"
    try:
        handle = opener.open(request)
    except urllib2.HTTPError, e:
        try:
            handle = opener.open(request)
        except urllib2.HTTPError, e:
            try:
                handle = opener.open(request)
            except urllib2.HTTPError, e:
                print "unable to set search criteria"
                return ["Failed to connect...are we being blocked?"]

    url = 'http://www.dodsbir.net/Awards/SrchResultsDtlsList.asp'
    request = urllib2.Request(url, None, headers)
    print "opening results list page"
    try:
        handle = opener.open(request)
    except urllib2.HTTPError, e:
        try:
            handle = opener.open(request)
        except urllib2.HTTPError, e:
            try:
                handle = opener.open(request)
            except urllib2.HTTPError, e:
                print "unable to open results list page"
                return ["Failed to connect...are we being blocked?"]

    print "opening print selection page"
    try:
        response = opener.open('http://www.dodsbir.net/Awards/PrintSelection.asp?FromBorC=B&Cnt=30')
    except urllib2.HTTPError, e:
        try:
            response = opener.open('http://www.dodsbir.net/Awards/PrintSelection.asp?FromBorC=B&Cnt=30')
        except urllib2.HTTPError, e:
            print "unable to open print selection page"
            return ["Failed to connect...are we being blocked?"]

    opener.close()

    print "downloading file"
    try:
        response = opener.open('http://www.dodsbir.net/Awards/PrintFile1.asp?FromBorC=B')
    except urllib2.HTTPError, e:
        try:
            response = opener.open('http://www.dodsbir.net/Awards/PrintFile1.asp?FromBorC=B')
        except urllib2.HTTPError, e:
            print "unable to open file page"
            return ["Failed to connect...are we being blocked?"]

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

def USASpendingQuery(query, zipCode = None):
    # TODO
    # * Save this to our XML database
    # * Update so that after July 30 we move to current year (last fiscal year)
    faadsQuery = "http://www.usaspending.gov/faads/faads.php?datype=X&detail=4&sortby=f&recipient_name=%s&fiscal_year=2008" % urllib.quote(query)

    if (zipCode is not None):
        fpdsQuery = "http://www.usaspending.gov/fpds/fpds.php?datype=X&detail=4&sortby=f&fiscal_year=2008&company_name=%s" % urllib.quote(query)
    else:
        fpdsQuery = "http://www.usaspending.gov/fpds/fpds.php?datype=X&detail=4&sortby=f&fiscal_year=2008&company_name=%s" % urllib.quote(query)

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(faadsQuery)
    faads = response.read()

    if (faads.find("No records found for the search criteria") != -1):
        faads = ""

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    response = opener.open(fpdsQuery)
    fpds = response.read()
 
    if (fpds.find("No records found for the search criteria") != -1):
        fpds = ""
  
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

    # go through each script tag and only accept it if we can find the imgres value
    imgScript = None
    for scriptTag in script:
        if (str(scriptTag).find("imgres?imgurl\\x3d") != -1):
            imgScript = str(scriptTag)
    
    # If we weren't able to find anything, just take the tag that has been the most useful, just so the following code works...
    if (imgScript is None):
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

def ClinicalTrialQuery(query):
    url = "http://clinicaltrials.gov/ct2/results?term=&recr=&rslt=&type=&cond=&intr=&outc=&lead=&spons=%s&spons_ex=Y&id=&state1=&cntry1=&state2=&cntry2=&state3=&cntry3=&locn=&gndr=&rcv_s=&rcv_e=&lup_s=&lup_e="
    url = url % urllib.quote(query)

    headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0. 6) Gecko/2009020911 Ubuntu/8.04 (hardy) Firefox/3.0.6'}

    cj = cookielib.LWPCookieJar()

    if os.path.isfile(COOKIEFILE):
        cj.load(COOKIEFILE)

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    request = urllib2.Request(url, None, headers)

    # TODO
    # HEINOUS
    # For some reason when using urllib2, when I try and do a query that returns no results, I get a 404 here, when in the browser I get an error message.  Something is strange here, but we'll have to let it sit for the moment.
    try:
        response = opener.open(request)
    except urllib2.HTTPError:
        return None

        #notFound = soup.findAll(text=re.compile("Found no studies with search of"))
        #return notFound

        #if (notFound):
        #    return False


    clinicalTrialData = response.read()
    opener.close()

    soup = BeautifulSoup(clinicalTrialData)

    dataTable = soup.findAll("table", {"class": "data_table"})
    links = dataTable[0].findAll("a")

    allLinks = []
    for link in links:
        href = link["href"]
        contents = link.contents[0]
        allLinks.append({'href': u"http://clinicaltrials.gov" + href, 'contents': contents})
    
    counter = 0
    for link in allLinks:

        url = link['href']
        response = opener.open(url)
        specificTrialData = response.read()
    
        soup = BeautifulSoup(specificTrialData)
        data = soup.findAll("table")
    
        institutions = []    
        def remove_html_tags(data):
            p = re.compile(r'<.*?>')
            return p.sub('', data)
    
        sponsors = data[8].findAll("tr")[0].findAll("td")[0].contents
        collaborators = data[8].findAll("tr")[1].findAll("td")[0].contents
    
        institutionsUnformatted = []
    
        # Do the sponsors first...
        for sponsor in sponsors:
            institutionsUnformatted.append(str(sponsor))
    
        institutionsUnformatted = "".join(institutionsUnformatted)
        institutionsUnformatted = institutionsUnformatted.split("<br />")
    
        for institution in institutionsUnformatted:
            institutions.append(remove_html_tags(institution).strip())
    
        # And then the collaborators...
        institutionsUnformatted = []
        for collaborator in collaborators:
            institutionsUnformatted.append(str(collaborator))
    
        institutionsUnformatted = "".join(institutionsUnformatted)
        institutionsUnformatted = institutionsUnformatted.split("<br />")
    
        for institution in institutionsUnformatted:
            institutions.append(remove_html_tags(institution).strip())
    
        allLinks[counter]['institutions'] = institutions
        counter += 1

    return allLinks

"""
div = soup.findAll("div")
imgDiv = div[10]
table = imgDiv.findAll("table")
111: tr = table[0].findAll("tr")
119: href = tr[0].td.a['href']
122: href.split("=")[1].split("&")[0]
"""
