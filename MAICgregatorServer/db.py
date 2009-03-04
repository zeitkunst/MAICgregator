import cPickle
import time

from bsddb.db import *
from dbxml import *
import feedparser

import post

"""
Let's say we have one main class, that contains the SchoolMetadataStore class and the soon-to-be-written class that deals with the XML data store.  Then, this main class looks at the two different stores to determine whether or not there is data currently there.  If there is, take that data (unless it's expired for some reason).  If there isn't, use the methods from post.py to go and fetch it.

The main class will call appropriate methods in the XML class to pull requisite stuff from the XML files via xpath/xquery.

So, format of data in the SchoolMetadataStore class will be as follows:
    For each type of data, we have a timestamp.  We then check this timestamp as a way of having a certain type of cache system.

    For XML:
        timestamp
        fetched (bool)

    For STTR:
        timestamp
        data

    GoogleNews
        timestamp
        data

    PRNews
        timestamp
        data

    Trustee info:
        timestamp
        ?

"""

# Home directory for databases
DB_HOME = "data/"

# Flags for environment creation
DB_ENV_CREATE_FLAGS = DB_CREATE | DB_INIT_LOCK | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_TXN
DB_ENV_FLAGS = DB_INIT_LOCK | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_TXN

class SchoolData(object):
    """Class for dealing with school data and querying our data stores."""

    MONTH = 60 *60 * 24 * 30
    DAY = 60 *60 * 24

    def __init__(self, schoolName):
        """What school name are we dealing with here?"""

        self.schoolName = schoolName

        self.schoolMetadataStore = SchoolMetadataStore()

        try:
            self.schoolMetadata = self.schoolMetadataStore.get(schoolName)
        except TypeError:
            self.schoolMetadata = self.createSchoolInfo()

    def getXML(self):
        return self.schoolMetadata['XML']

    def getSTTR(self):
        timestamp = self.schoolMetadata['STTR']['timestamp']

        if ((timestamp is None) or (time.time() >= (timestamp + self.MONTH))):
            data = post.STTRQuery(self.schoolName)

            self.schoolMetadata['STTR']['data'] = data 
            self.schoolMetadata['STTR']['timestamp'] = time.time()
            self.sync()

            result = ""
            # TODO
            # HEINOUS: need to sort the keys before we return this, or
            # only return the interesting data
            for item in data:
                result += "\t".join(item.values()) + "\n"
            return result
        else:
            data = self.schoolMetadata['STTR']['data']
            result = ""
            for item in data:
                result += "\t".join(item.values()) + "\n"
            return result


    def getGoogleNews(self):
        timestamp = self.schoolMetadata['GoogleNews']['timestamp']

        if ((timestamp is None) or (time.time() >= (timestamp + self.DAY))):
            data = post.GoogleNewsQuery(self.schoolName)
            parsedData = feedparser.parse(data)

            output = []

            for entry in parsedData['entries']:
                temp = {}
                temp['title'] = entry['title']
                temp['summary'] = entry['summary']
                output.append(temp)
            self.schoolMetadata['GoogleNews']['data'] = output
            self.schoolMetadata['GoogleNews']['timestamp'] = time.time()
            self.sync()

            toReturn = "\n".join(data['summary'] for data in self.schoolMetadata['GoogleNews']['data'])
            return toReturn
        else:
            toReturn = "\n".join(data['summary'] for data in self.schoolMetadata['GoogleNews']['data'])
            return toReturn

    def getPRNews(self):
        return self.schoolMetadata['PRNews']

    def createSchoolInfo(self):
        data = {}
        data['XML'] = {'timestamp': None, 'fetched': False}
        data['STTR'] = {'timestamp': None, 'data': None}
        data['GoogleNews'] = {'timestamp': None, 'data': None}
        data['PRNews'] = {'timestamp': None, 'data': None}

        self.schoolMetadataStore.put(self.schoolName, data)
        self.schoolMetadata = data

        return data

    def sync(self):
        self.schoolMetadataStore.put(self.schoolName, self.schoolMetadata)

    def close(self):
        self.sync()
        self.schoolMetadataStore.sync()
        self.schoolMetadataStore.close()

class SchoolMetadataStore(object):
    """Class for storing metadata about schools that we can check before we go directly to the XML (and other types) data store."""

    def __init__(self, dbHome = DB_HOME, dbName = "MAICgregator.db"):
        # Call methods for creating environments and DB object

        self.__createEnvironment(dbHome)
        self.__createDB(dbName)

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

        pickledValue = self.db.get(key)

        return cPickle.loads(pickledValue)

    def sync(self):
        self.db.sync()

    def close(self):
        self.db.sync()
        self.db.close()

        del self.environment
        del self.db

"""mgr = XmlManager()
container = mgr.createContainer("test.MAICxml")
container.putDocument(bookName, foobar, uc)
document = container.getDocument(bookName)
s = document.getContent()
document.getName()
container.sync()
qc = mgr.createQueryContext()
results = mgr.query("collection('test.MAICxml')//project_and_award_info[maj_agency_cat='Department of Defense']", qc)
for value in results:
    print value.asString()"""
