import cPickle
import re
import time
import random

from bsddb.db import *
from dbxml import *
import feedparser
from BeautifulSoup import BeautifulSoup
import RDF

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
DB_ENV_CREATE_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN | DB_THREAD
DB_ENV_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_LOCK | DB_INIT_MPOOL | DB_INIT_TXN | DB_THREAD

# XML DB Name
DB_XML_NAME = "MAICgregator.dbxml"

class SchoolData(object):
    """Class for dealing with school data and querying our data stores."""

    MONTH = 60 *60 * 24 * 30
    DAY = 60 *60 * 24

    def __init__(self, schoolName, storage = None):
        """What school name are we dealing with here?"""
        
        schoolName = schoolName.replace("-", " ")

        self.schoolName = schoolName

        self.schoolMetadataStore = SchoolMetadataStore()

        try:
            self.environment = DBEnv()
            self.environment.set_lk_max_locks(10000)
            self.environment.open(DB_HOME + "xml/", DB_ENV_CREATE_FLAGS, 0)

            self.mgr = XmlManager(self.environment, 0)
        
            uc = self.mgr.createUpdateContext()
            self.container = self.mgr.createContainer(DB_XML_NAME, DBXML_TRANSACTIONAL)
       
      
            xtxn = self.mgr.createTransaction()
            self.container.putDocument(xtxn, r"initialization", r"<init>MAICgregator begun!</init>", uc)
            self.container.sync()
            xtxn.commit()

        except XmlContainerExists:
            self.environment = DBEnv()
            self.environment.open(DB_HOME + "xml/", DB_ENV_FLAGS, 0)
            self.mgr = XmlManager(self.environment, 0)

            self.container = self.mgr.openContainer(DB_XML_NAME, DBXML_TRANSACTIONAL)
        except XmlDatabaseError, e:
            print "Some kind of strange error: "
            print e.getDbErrno()
            print dir(e)
            #return

        # Initialize or get metadata
        try:
            self.schoolMetadata = self.schoolMetadataStore.get(schoolName)
        except TypeError:
            self.schoolMetadata = self.createSchoolInfo()

        if (storage):
            self.storage = storage
            self.model = model
        else:
            # Get RDF model
            self.storage = RDF.HashStorage('data/trustees/MAICgregator', options="hash-type='bdb'")
            self.model = RDF.Model(self.storage)
        self.maicNS = RDF.NS("http://maicgregator.org/MAIC#")

    def getXML(self):
        timestamp = self.schoolMetadata['XML']['timestamp']
        schoolNameCompact = self.schoolName.replace(" ", "")
        schoolNameCompactGrants = schoolNameCompact + "Grants"
        schoolNameCompactContracts = schoolNameCompact + "Contracts"

        if ((timestamp is None)):
            data = post.USASpendingQuery(self.schoolName)
            grants = data[0]
            contracts = data[1]
            
            try:
                uc = self.mgr.createUpdateContext()
                xtxn = self.mgr.createTransaction()
                self.container.putDocument(schoolNameCompactGrants, grants, uc)
                self.container.sync()
                xtxn.commit()

                uc = self.mgr.createUpdateContext()
                xtxn = self.mgr.createTransaction()
                self.container.putDocument(schoolNameCompactContracts, contracts, uc)
                self.container.sync()
                xtxn.commit()
    
                self.schoolMetadata['XML']['timestamp'] = time.time()
                self.sync()
            except XmlException, inst:
                print "XMLException (", inst.exceptionCode, "):", inst.what

                if inst.exceptionCode == DATABASE_ERROR:
                    print "Database error code:", inst.dbError
            
            print "setting timestamp"
            self.schoolMetadata['XML']['timestamp'] = time.time()
            self.sync()
        else:
            pass
        
        qc = self.mgr.createQueryContext() 
        qc.setNamespace("xs", "http://www.w3.org/2001/XMLSchema")
        grantsQuery = """for $record in doc("dbxml:/%s/%s")//record
let $agency_name := data($record/project_and_award_info/agency_name)
let $project_description := data($record/project_and_award_info/project_description)
let $fed_funding_amount := number($record/action/fed_funding_amount)
let $federal_award_id := data($record/project_and_award_info/federal_award_id)
let $delim := "^"
where contains($record/project_and_award_info/maj_agency_cat, "Defense")
order by $fed_funding_amount descending
return <result>{$project_description,$delim,$federal_award_id,$delim,$agency_name,$delim,$fed_funding_amount}</result>"""
        contractsQuery = """for $record in doc("dbxml:/%s/%s")//record
let $agency_name := data($record/purchaser_information/contractingOfficeAgencyID)
let $project_description := data($record/contract_information/descriptionOfContractRequirement)
let $fed_funding_amount := number($record/amounts/obligatedAmount)
let $federal_award_id := data($record/record_information/IDVPIID)
let $delim := "^"
where contains($record/purchaser_information/maj_agency_cat, "Defense")
order by $fed_funding_amount descending
return <result>{$project_description,$delim,$federal_award_id,$delim,$agency_name,$delim,$fed_funding_amount}</result>"""
       
        #print xquery % (DB_XML_NAME, self.schoolName.replace(" ", ""))
#return <results>{data($x/project_description),$delim,data($x/agency_name)}</results>"""
        #results = self.mgr.query("collection('%s')//record/                               project_and_award_info[maj_agency_cat='Department of Defense']" % DB_XML_NAME, qc)
        xtxn = self.mgr.createTransaction()
        DoDGrants = self.mgr.query(grantsQuery % (DB_XML_NAME, schoolNameCompactGrants), qc)
        DoDContracts = self.mgr.query(contractsQuery % (DB_XML_NAME, schoolNameCompactContracts), qc)
        xtxn.commit()

        finalResults = []
        regex = re.compile("<result>(.+?)</result")
        for item in DoDGrants:
            item = regex.findall(item.asString())[0]
            toAdd = "\t".join([value.strip() for value in item.split("^")])
            finalResults.append("grant\t" + toAdd)

        for item in DoDContracts:
            item = regex.findall(item.asString())[0]
            toAdd = "\t".join([value.strip() for value in item.split("^")])
            finalResults.append("contract\t" + toAdd)

        return "\n".join(finalResults)

    def getTrustees(self):
        #trusteeList = post.TrusteeSearch(self.schoolName)
        
        try:
            timestamp = self.schoolMetadata['Trustees']['timestamp']
        except KeyError:
            self.schoolMetadata['Trustees'] = {}
            self.schoolMetadata['Trustees']['timestamp'] = None
            timestamp = None
        
        trusteeResults = []
        if ((timestamp is None) or (time.time() >= (timestamp + self.MONTH))):
            trusteeList = post.TrusteeSearch(self.schoolName)
            
            if (trusteeList != []):
                HasName = self.maicNS['HasName']
                IsTrusteeOf = self.maicNS['IsTrusteeOf']
                schoolNameCompact = self.schoolName.replace(" ", "")
                for trustee in trusteeList:
                    name = self.maicNS[trustee.replace(" ", "")]
                    school = self.maicNS[schoolNameCompact]
    
                    statement = RDF.Statement(name, HasName, trustee)
                    self.model.add_statement(statement)
    
                    statement = RDF.Statement(name, IsTrusteeOf, school)
                    self.model.add_statement(statement)
    
                self.model.sync()

                # For the moment, we only set the time if we're certain we got the right trustee results 
                self.schoolMetadata['Trustees']['timestamp'] = time.time()
                self.sync()
                
                trusteeResults = self.getTrusteeNamesFromModel()
                trusteeImages = self.getTrusteeImagesFromModel()
            else:
                trusteeResults = []
                trusteeImages = []
        else:
            trusteeResults = self.getTrusteeNamesFromModel()
            trusteeImages = self.getTrusteeImagesFromModel()
            
        if ((trusteeResults != []) and (trusteeImages != [])):
            trustees = list(zip(trusteeResults, trusteeImages))
            trustees = ["\t".join(list(trustee)) for trustee in trustees]
            return "\n".join(trustees)
        else:
            return None

    def getTrusteeNamesFromModel(self):
        schoolNameCompact = self.schoolName.replace(" ", "")
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?name
            WHERE {
                ?x maic:IsTrusteeOf maic:%s . 
                ?x maic:HasName ?name .
            }
            ORDER BY ?x""" % schoolNameCompact

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.model)

        return [result['name'].literal_value['string'] for result in results]

    def getTrusteeImagesFromModel(self):
        schoolNameCompact = self.schoolName.replace(" ", "")
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?image ?x
            WHERE {
                ?x maic:IsTrusteeOf maic:%s . 
                ?x maic:HasImage ?image .
            }
            ORDER BY ?x""" % schoolNameCompact

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.model)
        
        return [result['image'].literal_value['string'] for result in results]

    def _deleteTrusteeImages(self):
        schoolNameCompact = self.schoolName.replace(" ", "")
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?image ?x
            WHERE {
                ?x maic:IsTrusteeOf maic:%s . 
                ?x maic:HasImage ?image .
            }
            ORDER BY ?x""" % schoolNameCompact

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.model)

        HasImage = self.maicNS['HasImage']
        for result in results:
            del self.model[RDF.Statement(result['x'], HasImage, result['image'])]

    def updateTrusteeImages(self):
        """Get the latest trustee images from the Google Image Search results"""
        # Delete images from database before we update them
        self._deleteTrusteeImages()

        # Then go through and update things
        trusteeNames = self.getTrusteeNamesFromModel()
        HasImage = self.maicNS['HasImage']
        schoolNameCompact = self.schoolName.replace(" ", "")
        for trusteeName in trusteeNames:
            trusteeNameCompact = str(trusteeName.replace(" ", ""))
            name = self.maicNS[trusteeNameCompact]
            imageSrc = post.TrusteeImage(trusteeName)
            if (imageSrc is None):
                print "searching without quotes"
                imageSrc = post.TrusteeImage(trusteeName, withQuotes = False)
                if (imageSrc is None):
                    imageSrc = ""

            statement = RDF.Statement(name, HasImage, imageSrc)
            print imageSrc
            self.model.add_statement(statement)
            randSleep = random.randrange(5, 15)
            print "Finished %s, sleeping for %d" % (trusteeName, randSleep)
            time.sleep(randSleep)

        self.model.sync()

    def getSTTR(self):
        # TODO
        # Need to follow at least one page of the STTR site so that we can refresh/get session cookies so that people won't be stymied by it
        # Or, we need to figure out a better way of searching for these things...
        timestamp = self.schoolMetadata['STTR']['timestamp']

        if ((timestamp is None) or (time.time() >= (timestamp + self.MONTH))):
            data = post.STTRQuery(self.schoolName)

            self.schoolMetadata['STTR']['data'] = data 
            self.schoolMetadata['STTR']['timestamp'] = time.time()
            self.sync()

            return data
        else:
            data = self.schoolMetadata['STTR']['data']
            return data 

    def getPRNews(self):
        timestamp = self.schoolMetadata['PRNews']['timestamp']

        if ((timestamp is None) or (time.time() >= (timestamp + self.DAY))):
            data = post.MarketwireQuery(self.schoolName)

            soup = BeautifulSoup(data)
            
            # Get the links in the mainContent div
            mainContent = soup.find("div", "mainContent")
            links = mainContent.findAll("a")
            
            linksLength = len(links)
            linksParsed = links[2:linksLength - 4]
            
            # Since each link has some newlines in it, this is going to screw up my responses later
            linksCleaned = []
            for item in linksParsed:
                linksCleaned.append(str(item).replace("\n", ""))

            self.schoolMetadata['PRNews']['data'] = linksCleaned
            self.schoolMetadata['PRNews']['timestamp'] = time.time()
            self.sync()

            return linksCleaned
        else:
            data = self.schoolMetadata['PRNews']['data']
            return data 


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
        #self.schoolMetadataStore.sync()
        self.container.sync()

    def close(self):
        self.sync()
        #self.container.close()
        del self.container
        #self.environment.close(0)
        #self.schoolMetadataStore.sync()
        #self.schoolMetadataStore.close()

    def _deleteXML(self):
        """This method removes the XML files from the database, as well as setting the timestamp value to be none."""
        schoolNameCompact = self.schoolName.replace(" ", "")
        schoolNameCompactGrants = schoolNameCompact + "Grants"
        schoolNameCompactContracts = schoolNameCompact + "Contracts"
        
        try:
            uc = self.mgr.createUpdateContext()
            xtxn = self.mgr.createTransaction()
            self.container.deleteDocument(schoolNameCompactGrants, uc)
            self.container.sync()
            xtxn.commit()
        except XmlDocumentNotFound:
            pass

        try:
            uc = self.mgr.createUpdateContext()
            xtxn = self.mgr.createTransaction()
            self.container.deleteDocument(schoolNameCompactContracts, uc)
            self.container.sync()
            xtxn.commit()
        except XmlDocumentNotFound:
            pass

        self.schoolMetadata['XML']['timestamp'] = None
        self.sync()

class SchoolMetadataStore(object):
    """Class for storing metadata about schools that we can check before we go directly to the XML (and other types) data store."""

    def __init__(self, dbHome = DB_HOME, dbName = "MAICgregator.db"):
        # Call methods for creating environments and DB object
        pass
        #self.__createEnvironment(dbHome)
        #self.__createDB(dbName)

    def __createEnvironment(self, dbHome):
        self.dbHome = dbHome
        self.environment = DBEnv()
        self.environment.set_flags(DB_AUTO_COMMIT, True)
        self.environment.open(dbHome, DB_ENV_CREATE_FLAGS, 0)

    def __createDB(self, dbName):
        self.dbName = dbName
        self.db = DB(dbEnv = self.environment)
        xtxn = self.environment.txn_begin()
        self.db.open(dbName, dbtype = DB_HASH, flags = DB_CREATE, txn = xtxn)
        xtxn.commit()

    def put(self, key, value):
        """Put the value at key.  Pickle all data so that we don't have questions at load time."""
        self.open()
        pickledValue = cPickle.dumps(value)
        xtxn = self.environment.txn_begin()
        returnValue = self.db.put(key, pickledValue, txn = xtxn)
        xtxn.commit()
        self.sync()
        self.close()

    def get(self, key):
        """Get the value, and return it as an unpickled object.

        TODO: Need to handle key errors."""
        
        self.open()
        pickledValue = self.db.get(key)
        self.close()
        return cPickle.loads(pickledValue)

    def sync(self):
        self.db.sync()

    def open(self, dbHome = DB_HOME, dbName = "MAICgregator.db"):
        self.__createEnvironment(dbHome)
        self.__createDB(dbName)

    def close(self):
        self.db.sync()
        self.db.close()
        self.environment.close()

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
