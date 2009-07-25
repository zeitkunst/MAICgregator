# The code in MAICgregator is available under the GNU GPL V3 (http://www.gnu.   org/copyleft/gpl.html) with the following modifications:

# The words "you", "licensee", and "recipient" are redefined to be as follows:  "You", "licensee", and "recipient" is defined as anyone as long as s/he is not  an EXCLUDED PERSON. An EXCLUDED PERSON is any individual, group, unit,          component, synergistic amalgamation, cash-cow, chunk, CEO, CFO, worker, or      organization of a corporation that is a member, as of the date of acquisition   of this software, of the Fortune 1000 list of the world's largest businesses.   (See http://money. cnn.com/magazines/fortune/global500/2008/full_list/ for an   example of the top 500.) An EXCLUDED PERSON shall also include anyone working   in a contractor, subcontractor, slave, or freelance capacity for any member of  the Fortune 1000 list of the world's largest businesses.

# Please see http://maicgregator.org/license.


import re
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

    if (domain == "umt.edu"):
        result = "University of Montana"

    return result

# Sometimes we need to have the zip code in order to pare down some of the data that we get, like with the USASpending queries...
def getEduWHOISPlusZip(domain, whoisServer = "whois.educause.net", port = 43):
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
        zipCodeRegex = re.compile("[A-Za-z\s]*\,\s[A-Za-z]{2}\s([0-9\-]{5,10})")
        zipCode = zipCodeRegex.findall(response)[0].split("-")[0]
        registrantIndex = responseSplit.index("Registrant:")
        result = responseSplit[registrantIndex + 1].strip()
    except ValueError:
        return None

    # HEINOUS, but the WHOIS entry doesn't help us here
    if (domain == "umich.edu"):
        result = "University of Michigan"
    return (result, zipCode)

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
