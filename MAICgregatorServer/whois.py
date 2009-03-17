import socket
import cPickle

from bsddb.db import *

# Home directory for databases
DB_HOME = "data/"

# Flags for environment creation
DB_ENV_CREATE_FLAGS = DB_CREATE | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_TXN
DB_ENV_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_TXN

# XML DB Name
DB_NAME = "MAICgregator.db"


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

    def __init__(self, dbHome = DB_HOME, dbName = DB_NAME):
        # Call methods for creating environments and DB object

        self.__createEnvironment(dbHome)
        self.__createDB(dbName)

        # Try and get our current whois store
        self.whois = self.get("whois")

        if (self.whois is None):
            self.put("whois", {})
            self.whois = {}

    def __createEnvironment(self, dbHome):
        self.dbHome = dbHome
        self.environment = DBEnv()
        self.environment.open(dbHome, DB_ENV_CREATE_FLAGS, 0)

    def __createDB(self, dbName):
        self.dbName = dbName
        self.db = DB(dbEnv = self.environment)
        self.db.open(dbName, dbtype = DB_HASH, flags = DB_CREATE)

    def put(self, key, value):
        """Put the value at key.  Pickle all data so that we don't have questions at load time."""

        pickledValue = cPickle.dumps(value)

        self.db.put(key, pickledValue)

    def get(self, key):
        """Get the value, and return it as an unpickled object.

        TODO: Need to handle key errors."""

        if (self.db.has_key(key) == False):
            return None

        pickledValue = self.db.get(key)

        return cPickle.loads(pickledValue)

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
        registrantIndex = responseSplit.index("Registrant:")
        result = responseSplit[registrantIndex + 1].strip()
        
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
            self.put("whois", self.whois)
            self.sync()
            return schoolName

    def sync(self):
        self.db.sync()

    def close(self):
        self.db.sync()
        self.db.close()
        self.environment.close()

