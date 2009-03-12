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
        return whois.getEduWHOIS(hostname)

class ProcessBase(object):
    def GoogleNewsSearch(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        results = schoolData.getGoogleNews()
        schoolData.close()
        return results

    def TrusteeRelationshipSearch(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        results = schoolData.getTrustees()
        schoolData.close()
        return results

    def DoDBR(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        results = schoolData.getXML()
        schoolData.close()
        return results

    def PRNewsSearch(self, hostname):
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        # TODO
        # Make this less atomic; allow the ability to return smaller chunks, random bits, etc.
        # This means we need to come up with a REST api, as well as return error messages
        web.header('Content-Encoding', 'utf-8')
        results = u"\n".join(unicode(item, "utf-8") for item in schoolData.getPRNews())
        schoolData.close()
        return results

    def DoDSTTR(self, hostname):
        # Interesting keys to return in our result
        usefulKeys = ["PK_AWARDS", "AGENCY", "CONTRACT", "AWARD_AMT", "PI_NAME", "FIRM", "URL", "PRO_TITLE", "WholeAbstract"]
        # TODO
        # Deal with case when we don't get a school name back
        schoolName = whois.getEduWHOIS(hostname)
        schoolData = db.SchoolData(schoolName)

        STTRData = schoolData.getSTTR()
        
        output = ""
        for contract in STTRData:
            output += "\t".join(unicode(contract[key], errors='replace') for key in usefulKeys) + "\n"
        
        schoolData.close()
        return output

class Aggregate(ProcessBase):

    def GET(self, hostname, params):
        paramList = params.split("+")

        outputString = u"<?xml version=\"1.0\"?>\n"
        outputString += u"<results>\n"
        for param in paramList:
            outputString += u"\t<%s>\n" % param
            resultFunction = getattr(self, param)
            results = resultFunction(hostname)
            outputString += results
            outputString += u"\n\t</%s>\n" % param
        outputString += u"</results>\n"

        web.header("Content-Type", "text/xml; charset=utf-8")
        # Simple replacement
        outputString = outputString.replace("&", "&amp;")
        return outputString

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
