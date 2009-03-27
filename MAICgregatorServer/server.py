#!/usr/bin/env python

import urllib
import urllib2
import datetime

import feedparser
import PyRSS2Gen
from BeautifulSoup import BeautifulSoup
import smartypants
from bsddb.db import *

import post
import web
import whois
import db

version = "0.01"

# Home directory for databases
DB_HOME = "data/"

# Flags for environment creation
DB_ENV_CREATE_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_LOCK | DB_INIT_MPOOL | DB_INIT_TXN | DB_THREAD
DB_ENV_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_LOCK | DB_INIT_MPOOL | DB_INIT_TXN | DB_THREAD

# XML DB Name
DB_NAME = "MAICgregator.db"

# Setup REST-like service
# URLs of the form:
# /MAICgregator, /MAICgregator/about
#   * About the service
# /MAICgregator/help
#   * Help text
# /MAICgregator/all/somewhere.edu
#   * Return all information for somewhere.edu
#   Note: "all" is to be determined :-)
# /MAICgregator/DoDBR/somewhere.edu
#   * Return DoDBR information for somewhere.edu
# and so on...

urls = (
    '/MAICgregator', 'index',
    '/MAICgregator/', 'index',
    '/MAICgregator/statement', 'statement',
    '/MAICgregator/help', 'help',
    '/MAICgregator/DoDBR/(.*?)', 'DoDBR',
    '/MAICgregator/STTR/(.*?)', 'STTR',
    '/MAICgregator/PRNews/(.*?)', 'PRNews',
    '/MAICgregator/TrusteeSearch/(.*?)', 'TrusteeSearch',
    '/MAICgregator/TrusteeImage/(.*?)', 'TrusteeImage',
    '/MAICgregator/TrusteeRelationshipSearch/(.*?)', 'TrusteeSearch',
    '/MAICgregator/GoogleNews/(.*?)', 'GoogleNews',
    '/MAICgregator/Aggregate/(.*?)/(.*?)', 'Aggregate',
    '/MAICgregator/feed/rss/(.*?)/(.*?)', 'RSS',
    '/MAICgregator/RSS', 'RSSList',
    '/MAICgregator/FAQ', 'FAQ',
    '/MAICgregator/faq', 'FAQ',
    '/MAICgregator/name/(.*?)', 'name'
)
"""
"""

render = web.template.render('templates/', base = 'layout', cache = False)

class index:
    def GET(self):
        return render.index(version)

class help:
    def GET(self):
        return render.help(version)

class FAQ:
    def GET(self):
        fp = open('data/FAQ.txt')
        FAQlist = smartypants.smartyPants("".join(fp.readlines()))
        fp.close()
        FAQs = FAQlist.split('#@!')
        FAQs = [FAQ.split('!@#') for FAQ in FAQs]
        return render.FAQ(FAQs)

class RSSList:
    def GET(self):
        whoisStore = whois.WhoisStore()
        schoolNamesList = list(zip(whoisStore.whois.keys(), whoisStore.whois.values()))
        schoolNamesList.sort()
        
        return render.RSS(schoolNamesList)

class TrusteeImage:
    def GET(self, personName):
        return post.TrusteeImage(personName)

class name:
    def GET(self, hostname):
        whoisStore = whois.WhoisStore()
        return whoisStore.getSchoolName(hostname)

class ProcessBase(object):
    schoolMapping = {}
    whoisStore = None

    def __init__(self):
        # Setup the school data object dictionary
        #self.__createEnvironment(DB_HOME)
        pass

    def getWhois(self):
        if (self.whoisStore == None):
            self.whoisStore = whois.WhoisStore()

        return self.whoisStore

    def getSchoolData(self, schoolName):
        if not (self.schoolMapping.has_key(schoolName)):
            self.schoolMapping[schoolName] = db.SchoolData(schoolName)
        return self.schoolMapping[schoolName]

    def __createEnvironment(self, dbHome):
        self.dbHome = dbHome
        self.environment = DBEnv()
        self.environment.open(dbHome, DB_ENV_CREATE_FLAGS, 0)

    def GoogleNewsSearch(self, hostname):
        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)

        #schoolData = db.SchoolData(schoolName)
        schoolData = self.getSchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        print "|| MAICgregator server || Getting Google News"
        results = schoolData.getGoogleNews()
        #schoolData.close()
        return results

    def GoogleNewsSearchRSS2(self, hostname):
        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        print "|| MAICgregator server || Getting Google News RSS"
        results = schoolData.getGoogleNews()
        soup = BeautifulSoup(results)

        tables = soup.findAll("table")
        items = []
        for table in tables:
            timestamp = schoolData.schoolMetadata['PRNews']['timestamp']
            
            title = "".join(unicode(item) for item in table.a.contents)
            description = unicode(table.findAll("font")[3])
            url = table.a['href']

            item = PyRSS2Gen.RSSItem(title = title,
                    link = url,
                    description = description,
                    guid = PyRSS2Gen.Guid(url),
                    categories = ["Google News"],
                    author = schoolName,
                    pubDate = datetime.datetime.fromtimestamp(timestamp))
            items.append(item)

        return items

    def TrusteeRelationshipSearch(self, hostname):
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)

        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        print "|| MAICgregator server || Getting Trustee data"
        results = schoolData.getTrustees()
        
        return results

    def TrusteeImages(self, hostname):
        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)
        
        trusteeImages = schoolData.getTrusteeImagesFromModel()
        
        output = ""
        for image in trusteeImages:
            output += "<img width='200' src='%s'/>" % image

        return output

    def TrusteeRelationshipSearchRSS2(self, hostname):
        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        print "|| MAICgregator server || Getting Trustee RSS data"
        results = schoolData.getTrustees()

        resultList = results.split("\n")
        items = []
        for result in resultList:
            timestamp = schoolData.schoolMetadata['Trustees']['timestamp']
            url = "http://www.google.com/search?&q=" + urllib.quote(result + " trustee")
            item = PyRSS2Gen.RSSItem(title = result,
                    link = url,
                    description = result,
                    guid = PyRSS2Gen.Guid(url),
                    categories = ["Trustee"],
                    pubDate = datetime.datetime.fromtimestamp(timestamp))
            items.append(item)

        return items
       
        return results

    def DoDBR(self, hostname):
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        print "|| MAICgregator server || Getting DoDBR data"
        results = schoolData.getXML()
        
        return results

    def DoDBRRSS2(self, hostname):
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        print "|| MAICgregator server || Getting DoDBR RSS data"
        results = schoolData.getXML()
        
        resultList = results.split("\n")
        items = []
        for result in resultList:
            timestamp = schoolData.schoolMetadata['XML']['timestamp']
            data = result.split("\t")
            title = data[1]
            type = data[0]
            id = data[2]
            agency = data[3]
            amount = float(data[4])
            item = PyRSS2Gen.RSSItem(title = title,
                    link = "#",
                    description = "%s from the %s in the amount of $%f with id %s" % (type, agency, amount, id),
                    guid = PyRSS2Gen.Guid(title),
                    categories = ["DoD", type],
                    pubDate = datetime.datetime.fromtimestamp(timestamp))
            items.append(item)

        return items

    def PRNewsSearch(self, hostname):
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        print "|| MAICgregator server || Getting PR data"
        web.header('Content-Encoding', 'utf-8')
        results = u"\n".join(unicode(item, "utf-8") for item in schoolData.getPRNews())
        
        return results

    def PRNewsSearchRSS2(self, hostname):
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        print "|| MAICgregator server || Getting PR data"
        #web.header('Content-Encoding', 'utf-8')
        #results = u"\n".join(unicode(item, "utf-8") for item in schoolData.getPRNews())
        results = schoolData.getPRNews()
        items = []
        for result in results:
            timestamp = schoolData.schoolMetadata['PRNews']['timestamp']
            soup = BeautifulSoup(result)
            title = soup.a.contents[1].strip()
            description = title
            url = soup.a['href']

            item = PyRSS2Gen.RSSItem(title = title,
                    link = url,
                    description = description,
                    guid = PyRSS2Gen.Guid(url),
                    categories = ["PR News"],
                    author = schoolName,
                    pubDate = datetime.datetime.fromtimestamp(timestamp))
            items.append(item)

        return items

    def DoDSTTR(self, hostname):
        # Interesting keys to return in our result
        usefulKeys = ["PK_AWARDS", "AGENCY", "CONTRACT", "AWARD_AMT", "PI_NAME", "FIRM", "URL", "PRO_TITLE", "WholeAbstract"]
        # TODO
        # Deal with case when we don't get a school name back
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        print "|| MAICgregator server || Getting STTR data"
        STTRData = schoolData.getSTTR()
        
        output = ""
        for contract in STTRData:
            output += "\t".join(unicode(contract[key], errors='ignore') for key in usefulKeys) + "\n"
        
        output = output.replace("<", "&lt;")
        output = output.replace(">", "&gt;")
        return output

    def DoDSTTRRSS2(self, hostname):
        # Interesting keys to return in our result
        usefulKeys = ["PK_AWARDS", "AGENCY", "CONTRACT", "AWARD_AMT", "PI_NAME", "FIRM", "URL", "PRO_TITLE", "WholeAbstract"]
        # TODO
        # Deal with case when we don't get a school name back
        #whoisStore = whois.WhoisStore()
        #schoolName = whoisStore.getSchoolName(hostname)
        #schoolData = db.SchoolData(schoolName)

        whoisStore = self.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)
        schoolData = self.getSchoolData(schoolName)

        print "|| MAICgregator server || Getting STTR RSS data"
        STTRData = schoolData.getSTTR()
        
        items = []
        for contract in STTRData:
            timestamp = schoolData.schoolMetadata['STTR']['timestamp']
            title = contract["PRO_TITLE"]
            abstract = contract["WholeAbstract"]
            amount = float(contract["AWARD_AMT"])
            piName = contract["PI_NAME"]
            firm = contract["FIRM"]
            url = contract["URL"]
            agency = contract["AGENCY"]
            
            description = """%f from the %s to %s and %s
            <br/>
            <br/>
            %s""" % (amount, agency, piName, firm, abstract)

            item = PyRSS2Gen.RSSItem(title = title,
                    link = "http://" + url,
                    description = description,
                    guid = PyRSS2Gen.Guid(url),
                    categories = ["DoD", "STTR"],
                                     author = schoolName,
                    pubDate = datetime.datetime.fromtimestamp(timestamp))
            items.append(item)

        return items
   
class RSS(ProcessBase):
     def GET(self, hostname, params):
        process = ProcessSingleton.getProcess()
        whoisStore = process.getWhois()
        schoolName = whoisStore.getSchoolName(hostname)

        paramsMapping = {'GoogleNewsSearch': 'GoogleNews',
                    'DoDBR': 'XML',
                    'TrusteeRelationshipSearch': 'Trustees',
                    'DoDSTTR': 'STTR',
                    'PRNewsSearch': 'PRNews'}

        title = "MAICgregator feed for %s and data sources %s" % (schoolName, params)
        link = "http://maicgregator.org/MAICgregator/feed/rss" + hostname + "/" + params
        description = "This is an automatically generated RSS feed of information that is pertinent to the military-academic-industrical complex (MAIC) of %s.  Any questions or comments should go to info -at- maicgregator --dot-- org" % schoolName


        paramList = params.split("+")

        latestTimestamp = 0
        items = []
        for param in paramList:
            actualParam = paramsMapping[param]
            timestamp = process.getSchoolData(schoolName).schoolMetadata[actualParam]['timestamp']
            if (timestamp > latestTimestamp):
                latestTimestamp = timestamp
            resultFunction = getattr(process, param + "RSS2")
            results = resultFunction(hostname)
            items.extend(results)
        rss = PyRSS2Gen.RSS2(title = title,
                    link = link,
                    description = description,
                    lastBuildDate = datetime.datetime.fromtimestamp(latestTimestamp),
                    items = items)
        
        return rss.to_xml()

class Aggregate(ProcessBase):

    def GET(self, hostname, params):
        process = ProcessSingleton.getProcess()

        paramList = params.split("+")

        outputString = u"<?xml version=\"1.0\"?>\n"
        outputString += u"<results>\n"
        for param in paramList:
            outputString += u"\t<%s>\n" % param
            resultFunction = getattr(process, param)
            results = resultFunction(hostname)
            outputString += unicode(results)
            outputString += u"\n\t</%s>\n" % param
        outputString += u"</results>\n"

        web.header("Content-Type", "text/xml; charset=utf-8")
        # Simple replacement
        outputString = outputString.replace("&", "&amp;")
        return outputString

class ProcessSingleton(ProcessBase):
    process = None
    def getProcess():
        if ProcessSingleton.process == None:
            ProcessSingleton.process = ProcessBase()
        return ProcessSingleton.process
    getProcess = staticmethod(getProcess)

class GoogleNews:
    def GET(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages

        return schoolData.getGoogleNews()

class TrusteeSearch:
    def GET(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        return schoolData.getTrustees()

class DoDBR:
    def GET(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages

        return schoolData.getXML()

class PRNews:
    def GET(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        web.header('Content-Encoding', 'utf-8')
        return "\n".join(str(item) for item in schoolData.getPRNews())

class STTR:
    def GET(self, hostname):
        # Interesting keys to return in our result
        usefulKeys = ["PK_AWARDS", "AGENCY", "CONTRACT", "AWARD_AMT", "PI_NAME", "FIRM", "URL", "PRO_TITLE", "WholeAbstract"]
        # TODO
        # Deal with case when we don't get a school name back
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        STTRData = schoolData.getSTTR()

        output = u""
        for contract in STTRData:
            # TODO
            # Fix this to deal with the unicode characters properly
            output += u"\t".join(unicode(contract[key], errors='replace') for key in usefulKeys) + u"\n"

        web.header('Content-Encoding', 'utf-8')
        return output

class statement:
    def GET(self):
        return render.statement()

class process:
    def GET(self, data):
        return data

if __name__ == "__main__":
    try:
        app = web.application(urls, globals())
        app.run()
    except:
        print "got a keyboard interrupt"
