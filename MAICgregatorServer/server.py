#!/usr/bin/env python

import urllib

import feedparser

import post
import web
import whois
import db

version = "0.01"

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
    '/MAICgregator/about', 'about',
    '/MAICgregator/help', 'help',
    '/MAICgregator/DoDBR/(.*?)', 'DoDBR',
    '/MAICgregator/STTR/(.*?)', 'STTR',
    '/MAICgregator/PRNews/(.*?)', 'PRNews',
    '/MAICgregator/TrusteeSearch/(.*?)', 'TrusteeSearch',
    '/MAICgregator/TrusteeRelationshipSearch/(.*?)', 'TrusteeSearch',
    '/MAICgregator/GoogleNews/(.*?)', 'GoogleNews',
    '/MAICgregator/Aggregate/(.*?)/(.*?)', 'Aggregate',
    '/MAICgregator/name/(.*?)', 'name'
)
"""
"""

render = web.template.render('templates/', cache = False)

class index:
    def GET(self):
        return "This is MAICgregator server, version %s" % version

class help:
    def GET(self):
        help = web.template.frender('templates/help.html')
        return help(version)

class name:
    def GET(self, hostname):
        whoisStore = whois.WhoisStore()
        return whoisStore.getSchoolName(hostname)

class ProcessBase(object):
    schoolMapping = {}
    whoisStore = None

    def __init__(self):
        # Setup the school data object dictionary
        pass

    def getWhois(self):
        if (self.whoisStore == None):
            self.whoisStore = whois.WhoisStore()

        return self.whoisStore

    def getSchoolData(self, schoolName):
        if not (self.schoolMapping.has_key(schoolName)):
            self.schoolMapping[schoolName] = db.SchoolData(schoolName)
        return self.schoolMapping[schoolName]

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
            output += "\t".join(unicode(contract[key], errors='replace') for key in usefulKeys) + "\n"
        
        
        return output

class Aggregate(ProcessBase):

    def GET(self, hostname, params):
        process = ProcessSingleton.getProcess()
        print process.schoolMapping

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

class about:
    def GET(self):
        about = web.template.frender('templates/about.html')
        return about(version)

class process:
    def GET(self, data):
        return data

if __name__ == "__main__":
    app = web.application(urls, globals())
    try:
        app.run()
    except KeyboardInterrupt:
        print "got a keyboard interrupt"
