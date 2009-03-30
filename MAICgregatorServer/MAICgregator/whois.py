import socket
import cPickle
import time

from bsddb3.db import *

from db import DBManager

def getEduWHOIS(domain, whoisServer = "whois.educause.net", port = 43):
    # Make sure we're only looking up the root domain, not the entire domain name
    domainSplit = domain.split(".")
    host = domainSplit[-2] + "." + domainSplit[-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((whoisServer, port))
    s.send(host + "\r\n")

    response = ""
    while True:
        data = s.recv(4096)
        response += data

        if data == '':
            break
    s.close()

    responseSplit = response.split("\n")
    registrantIndex = responseSplit.index("Registrant:")
    result = responseSplit[registrantIndex + 1].strip()
    
    # HEINOUS, but the WHOIS entry doesn't help us here
    if (domain == "umich.edu"):
        result = "University of Michigan"
    return result

class WhoisStore(object):
    """Class for storing metadata about schools that we can check before we go directly to the XML (and other types) data store."""

    def __init__(self, dbManager = None):
        # Call methods for creating environments and DB object

        # Setup our DBManager object
        if (dbManager is None):
            self.dbManager = DBManager()
        else:
            self.dbManager = dbManager

        # Try and get our current whois store
        self.whois = self.dbManager.get("whois")

        if (self.whois is None):
            self.dbManager.put("whois", {})
            self.whois = {}

    def _getEduWHOIS(self, domain, whoisServer = "whois.educause.net", port = 43):
        # Make sure we're only looking up the root domain, not the entire domain name
        domainSplit = domain.split(".")
        host = domainSplit[-2] + "." + domainSplit[-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((whoisServer, port))
        s.send(host + "\r\n")
    
        response = ""
        while True:
            data = s.recv(4096)
            response += data
    
            if data == '':
                break
        s.close()
    
        responseSplit = response.split("\n")
        try:
            registrantIndex = responseSplit.index("Registrant:")
            result = responseSplit[registrantIndex + 1].strip()
        except ValueError:
            return None

        # HEINOUS, but the WHOIS entry doesn't help us here
        if (domain == "umich.edu"):
            result = "University of Michigan"
        return result

    def getSchoolName(self, hostname):
        try:
            return self.whois[hostname]
        except KeyError:
            schoolName = self._getEduWHOIS(hostname)
            self.whois[hostname] = schoolName
            self.dbManager.put("whois", self.whois)
            return schoolName
