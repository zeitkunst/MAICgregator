# The code in MAICgregator is available under the GNU GPL V3 (http://www.gnu.   org/copyleft/gpl.html) with the following modifications:

# The words "you", "licensee", and "recipient" are redefined to be as follows:  "You", "licensee", and "recipient" is defined as anyone as long as s/he is not  an EXCLUDED PERSON. An EXCLUDED PERSON is any individual, group, unit,          component, synergistic amalgamation, cash-cow, chunk, CEO, CFO, worker, or      organization of a corporation that is a member, as of the date of acquisition   of this software, of the Fortune 1000 list of the world's largest businesses.   (See http://money. cnn.com/magazines/fortune/global500/2008/full_list/ for an   example of the top 500.) An EXCLUDED PERSON shall also include anyone working   in a contractor, subcontractor, slave, or freelance capacity for any member of  the Fortune 1000 list of the world's largest businesses.

# Please see http://maicgregator.org/license.


import cPickle
import re
import time
import random

from bsddb3.db import *
from dbxml import *
import feedparser
from BeautifulSoup import BeautifulSoup
import RDF

import post

# Home directory for databases
DB_HOME = "data/"
DB_XML_HOME = "data/xml/"

# Flags for environment creation
DB_ENV_CREATE_FLAGS = DB_CREATE | DB_RECOVER | DB_INIT_LOG | DB_INIT_MPOOL | DB_INIT_LOCK | DB_INIT_TXN | DB_THREAD

# XML DB Name
DB_NAME = "MAICgregator.db"
DB_XML_NAME = "MAICgregator.dbxml"

class DBManager(object):
    """This is a class that manages database environments, connections, and so on."""

    def __init__(self, dbHome = DB_HOME, dbName = DB_NAME, dbXMLName = DB_XML_NAME):
        self.dbHome = dbHome
        self.dbName = dbName
        self.dbXMLName = dbXMLName

        # Setup our environments
        self.createDBEnvironment()
        self.createDBXMLEnvironment()

        # Open the databases
        self.openDB()
        self.openDBXML()
        self.openRDF()

    def createDBEnvironment(self):
        self.dbEnvironment = DBEnv()
        self.dbEnvironment.set_flags(DB_AUTO_COMMIT, True)
        self.dbEnvironment.open(self.dbHome, DB_ENV_CREATE_FLAGS, 0)

    def createDBXMLEnvironment(self):
        self.dbXMLEnvironment = DBEnv()
        self.dbXMLEnvironment.set_flags(DB_AUTO_COMMIT, True)
        self.dbXMLEnvironment.set_cachesize(0, 256*1024*1024)
        self.dbXMLEnvironment.set_lk_max_locks(250000)
        self.dbXMLEnvironment.open(self.dbHome + "xml/", DB_ENV_CREATE_FLAGS, 0)
        self.mgr = XmlManager(self.dbXMLEnvironment, 0)

    def openRDF(self, storage = None):
        # Initialize and/or setup RDF
        if (storage):
            self.storage = storage
            self.model = model
        else:
            # Get Main RDF model
            self.storage = RDF.HashStorage('data/trustees/MAICgregator', options="hash-type='bdb'")
            self.model = RDF.Model(self.storage)

            # Get/create ToAdd model
            self.storageToAdd = RDF.HashStorage('data/trustees/MAICgregatorToAdd', options="hash-type='bdb'")
            self.modelToAdd = RDF.Model(self.storageToAdd)


    def openDB(self):
        self.db = DB(dbEnv = self.dbEnvironment)
        try:
            xtxn = self.dbEnvironment.txn_begin()
            self.db.open(self.dbName, dbtype = DB_HASH, flags = DB_CREATE, txn = xtxn)
            xtxn.commit()
        except Exception, e:
            print e

    def openDBXML(self):
        try:
            uc = self.mgr.createUpdateContext()
            self.container = self.mgr.createContainer(self.dbXMLName, DBXML_TRANSACTIONAL)
          
            xtxn = self.mgr.createTransaction()
            self.container.putDocument(xtxn, r"initialization", r"<init>MAICgregator begun!</init>", uc)
            self.container.sync()
            xtxn.commit()
        except XmlContainerExists:
            self.container = self.mgr.openContainer(self.dbXMLName, DBXML_TRANSACTIONAL)
        except XmlDatabaseError, e:
            print "Some kind of strange error: "
            print e.getDbErrno()

    def close(self):
        # TODO
        # HEINOUS
        # Need to make sure that there is nothing using the database before we try and close
        del self.container
        self.db.close()
        self.dbXMLEnvironment.close(0)
        self.dbEnvironment.close()

    def put(self, key, value):
        pickledValue = cPickle.dumps(value)
        try:
            xtxn = self.dbEnvironment.txn_begin()
            self.db.put(key, pickledValue, txn = xtxn)
            xtxn.commit()
            self.syncDB()
        except Exception, e:
            print e

    def get(self, key):
        try:
            if (self.db.has_key(key) == False):
                return None
        except DBRunRecoveryError:
            # TODO
            # Totally heinous, but it seems to work :-)
            print "PANIC: trying to close and run recovery"
            del self.model
            del self.container
            del self.mgr
            del self.db
            del self.dbXMLEnvironment
            del self.dbEnvironment

            # Setup our environments
            self.createDBEnvironment()
            self.createDBXMLEnvironment()
    
            # Open the databases
            self.openDB()
            self.openDBXML()
            self.openRDF()

        xtxn = self.dbEnvironment.txn_begin()
        pickledValue = self.db.get(key, txn = xtxn)
        xtxn.commit()
        return cPickle.loads(pickledValue)

    def syncDB(self):
        self.db.sync()

    def syncDBXML(self):
        self.container.sync()

    def putDocument(self, documentName, document):
        try:
            uc = self.mgr.createUpdateContext()
            xtxn = self.mgr.createTransaction()
            self.container.putDocument(xtxn, documentName, document, uc)
            self.container.sync()
            xtxn.commit()
            del xtxn
            del uc
            return True
        except XmlUniqueError:
            return False
        except XmlDatabaseError, inst:
            print "XMLException (", inst.exceptionCode, "):", inst.what
            if inst.exceptionCode == DATABASE_ERROR:
                print "Database error code:", inst.dbError

    def getDocument(self, documentName):
        uc = self.mgr.createUpdateContext()
        xtxn = self.mgr.createTransaction()
        document = self.container.getDocument(xtxn, documentName)
        documentData = document.getContent()
        xtxn.commit()
        del xtxn
        del uc

        return documentData

    def query(self, queryString):
        """ To test:
            doc("dbxml:/DB_XML_NAME/key/init")
            """
        qc = self.mgr.createQueryContext() 
        qc.setNamespace("xs", "http://www.w3.org/2001/XMLSchema")
        queryResults = self.mgr.query(queryString, qc)
        return queryResults

class SchoolData(object):
    """Class for dealing with school data and querying our data stores."""

    MONTH = 60 *60 * 24 * 30
    WEEK = 60 *60 * 24 * 7
    DAY = 60 *60 * 24
    updateTrusteeImagesLock = False

    def __init__(self, schoolName, dbManager = None, storage = None):
        """What school name are we dealing with here?"""
        
        schoolName = schoolName.replace("-", " ")

        self.schoolName = schoolName

        # Setup our DBManager object
        if (dbManager is None):
            self.dbManager = DBManager()
        else:
            self.dbManager = dbManager

        self.schoolDoDBR = None

        # Initialize or get metadata
        self.schoolMetadata = self.dbManager.get(schoolName)
        if (self.schoolMetadata is None):
            self.schoolMetadata = self.createSchoolInfo()

        self.maicNS = RDF.NS("http://maicgregator.org/MAIC#")

    def getXML(self):
        timestamp = self.schoolMetadata['XML']['timestamp']
        schoolNameCompact = self.schoolName.replace(" ", "")
        schoolNameCompactGrants = schoolNameCompact + "Grants"
        schoolNameCompactContracts = schoolNameCompact + "Contracts"

        # are our data dirty, mon?
        schoolMetadataDirty = False 

        if ((timestamp is None)):
            # In case we've been running a long time, make sure that we clear out old data first
            self.schoolDoDBR = None
            data = post.USASpendingQuery(self.schoolName)
            grants = data[0]
            contracts = data[1]
            
            try:
                returnValue = self.dbManager.putDocument(schoolNameCompactGrants, grants)
            except XmlDatabaseError, inst:
                print "XMLException (", inst.exceptionCode, "):", inst.what
                if inst.exceptionCode == DATABASE_ERROR:
                    print "Database error code:", inst.dbError

            if (returnValue == False):
                print "%s already exists" % schoolNameCompactGrants
            
            if (contracts.find("No records found for this search criteria") != -1):
                contracts = r"<results>no results found</results>"
            
            try:
                returnValue = self.dbManager.putDocument(schoolNameCompactContracts, contracts)
            except XmlDatabaseError, inst:
                print "XMLException (", inst.exceptionCode, "):", inst.what
                if inst.exceptionCode == DATABASE_ERROR:
                    print "Database error code:", inst.dbError

            if (returnValue == False):
                print "%s already exists" % schoolNameCompactContracts

            self.schoolMetadata['XML']['timestamp'] = time.time()
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        if (self.schoolDoDBR is None):
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
            try:
                DoDGrants = self.dbManager.query(grantsQuery % (DB_XML_NAME, schoolNameCompactGrants))
            except XmlDatabaseError:
                DoDGrants = []
            try:
                DoDContracts = self.dbManager.query(contractsQuery % (DB_XML_NAME, schoolNameCompactContracts))
            except XmlDatabaseError:
                DoDContracts = []

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

            self.schoolDoDBR = "\n".join(finalResults)

        return self.schoolDoDBR

    def getTrustees(self):
        #trusteeList = post.TrusteeSearch(self.schoolName)
        
        # are our data dirty, mon?
        schoolMetadataDirty = False 

        try:
            timestamp = self.schoolMetadata['Trustees']['timestamp']
        except KeyError:
            self.schoolMetadata['Trustees'] = {}
            self.schoolMetadata['Trustees']['timestamp'] = None
            timestamp = None
            schoolMetadataDirty = True
        
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
                    self.dbManager.model.add_statement(statement)
    
                    statement = RDF.Statement(name, IsTrusteeOf, school)
                    self.dbManager.model.add_statement(statement)
    
                self.dbManager.model.sync()

                # For the moment, we only set the time if we're certain we got the right trustee results 
                self.schoolMetadata['Trustees']['timestamp'] = time.time()
                schoolMetadataDirty = True
                
                trusteeResults = self.getTrusteeNamesFromModel()
                trusteeImages = self.getTrusteeImagesFromModel()
            else:
                self.schoolMetadata['Trustees']['timestamp'] = time.time()
                schoolMetadataDirty = True

                trusteeResults = []
                trusteeImages = []
        else:
            trusteeResults = self.getTrusteeNamesFromModel()
            trusteeImages = self.getTrusteeImagesFromModel()

        if (schoolMetadataDirty is True):
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        if ((trusteeResults != []) and (trusteeImages != [])):
            trustees = list(zip(trusteeResults, trusteeImages))
            trustees = ["\t".join(list(trustee)) for trustee in trustees]
            return "\n".join(trustees)
        elif (trusteeResults != []):
            return "\n".join(trusteeResults)

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

        results = nameQuery.execute(self.dbManager.model)

        return [result['name'].literal_value['string'] for result in results]

    def getTrusteeNamesAndResourcesFromModel(self):
        schoolNameCompact = self.schoolName.replace(" ", "")
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?name, ?x
            WHERE {
                ?x maic:IsTrusteeOf maic:%s . 
                ?x maic:HasName ?name .
            }
            ORDER BY ?x""" % schoolNameCompact

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.dbManager.model)

        toReturn = []
        for result in results:
            uri = result['x'].uri
            name = result['name'].literal_value['string']
            uri = str(uri).split("#")[1]
            toReturn.append([name, uri])

        return toReturn


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

        results = nameQuery.execute(self.dbManager.model)
        
        return [result['image'].literal_value['string'] for result in results]

    def getTrusteeURLToAddFromModel(self):
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?url ?x
            WHERE {
                ?x maic:HasURL ?url . 
            }
            ORDER BY ?x"""

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.dbManager.modelToAdd)
        values = []
        for result in results:
            values.append(list((str(result['x'].uri), result['url'].literal_value['string'])))
        return values

    def getTrusteeBioToAddFromModel(self):
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?bio ?x
            WHERE {
                ?x maic:HasBio ?bio. 
            }
            ORDER BY ?x"""

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.dbManager.modelToAdd)
        values = []
        for result in results:
            values.append(list((str(result['x'].uri), result['bio'].literal_value['string'])))
        return values

    def getTrusteeInfoToAddFromModel(self):
        query = """
            PREFIX maic: <http://maicgregator.org/MAIC#>
            SELECT ?info ?x
            WHERE {
                ?x maic:HasInfo ?info. 
            }
            ORDER BY ?x"""

        nameQuery = RDF.Query(query, query_language="sparql")

        results = nameQuery.execute(self.dbManager.modelToAdd)
        values = []
        for result in results:
            values.append(list((str(result['x'].uri), result['info'].literal_value['string'])))
        return values

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

        results = nameQuery.execute(self.dbManager.model)

        HasImage = self.maicNS['HasImage']
        for result in results:
            del self.dbManager.model[RDF.Statement(result['x'], HasImage, result['image'])]

    def addTrusteeInfo(self, data):
        school = self.maicNS[str(data['schoolName'])]

        if (data.has_key('trusteeURL')):
            name = self.maicNS[str(data['trusteeResource'])]
            HasURL = self.maicNS['HasURL']
            url = data['trusteeURL']

            statement = RDF.Statement(name, HasURL, url)
            if not (self.dbManager.modelToAdd.contains_statement(statement)):
                self.dbManager.modelToAdd.add_statement(statement)
                self.dbManager.modelToAdd.sync()

        if (data.has_key('trusteeInfo')):
            HasInfo = self.maicNS['HasInfo']
            url = data['trusteeInfo']

            statement = RDF.Statement(school, HasInfo, url)
            if not (self.dbManager.modelToAdd.contains_statement(statement)):
                self.dbManager.modelToAdd.add_statement(statement)
                self.dbManager.modelToAdd.sync()

        if (data.has_key('trusteeBio')):
            name = self.maicNS[str(data['trusteeResource'])]
            HasBio = self.maicNS['HasBio']
            url = data['trusteeBio']

            statement = RDF.Statement(name, HasBio, url)
            if not (self.dbManager.modelToAdd.contains_statement(statement)):
                self.dbManager.modelToAdd.add_statement(statement)
                self.dbManager.modelToAdd.sync()

    def updateTrusteeImages(self):
        """Get the latest trustee images from the Google Image Search results"""
        if (self.updateTrusteeImagesLock):
            return
        else:
            self.updateTrusteeImagesLock = True

        try:
            timestamp = self.schoolMetadata['TrusteeImages']['timestamp']
        except KeyError:
            self.schoolMetadata['TrusteeImages'] = {}
            self.schoolMetadata['TrusteeImages']['timestamp'] = None
            timestamp = None
            schoolMetadataDirty = True
        
        # TODO
        # Make sure that we put in some sort of "lock" so that two threads aren't trying to update things at once
        if ((timestamp is None) or (time.time() >= (timestamp + self.WEEK))):
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
                self.dbManager.model.add_statement(statement)
                randSleep = random.randrange(3, 10)
                print "Finished %s, sleeping for %d" % (trusteeName, randSleep)
                time.sleep(randSleep)
    
            self.dbManager.model.sync()

            self.schoolMetadata['TrusteeImages']['timestamp'] = time.time()
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        self.updateTrusteeImagesLock = False

    def getSTTR(self):
        # TODO
        # Need to follow at least one page of the STTR site so that we can refresh/get session cookies so that people won't be stymied by it
        # Or, we need to figure out a better way of searching for these things...
        timestamp = self.schoolMetadata['STTR']['timestamp']

        # are our data dirty, mon?
        schoolMetadataDirty = False 

        if ((timestamp is None) or (time.time() >= (timestamp + 4 * self.MONTH))):
        #if (timestamp is not None):
            data = post.STTRQuery(self.schoolName)

            self.schoolMetadata['STTR']['data'] = data 
            self.schoolMetadata['STTR']['timestamp'] = time.time()

            schoolMetadataDirty = True

        else:
            data = self.schoolMetadata['STTR']['data']

        if (schoolMetadataDirty is True):
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        return data

    def getClinicalTrials(self):
        # TODO
        # Need to follow at least one page of the STTR site so that we can refresh/get session cookies so that people won't be stymied by it
        # Or, we need to figure out a better way of searching for these things...
        try:
            timestamp = self.schoolMetadata['ClinicalTrials']['timestamp']
        except KeyError:
            self.schoolMetadata['ClinicalTrials'] = {}
            self.schoolMetadata['ClinicalTrials']['timestamp'] = None
            timestamp = None

        # For the moment, always do the query, so set timestamp to None
        timestamp = None

        # are our data dirty, mon?
        schoolMetadataDirty = False 

        if ((timestamp is None) or (time.time() >= (timestamp + self.MONTH))):
            data = post.ClinicalTrialsQuery(self.schoolName)

            self.schoolMetadata['ClinicalTrials']['data'] = data 
            self.schoolMetadata['ClinicalTrials']['timestamp'] = time.time()

            schoolMetadataDirty = True

        else:
            data = self.schoolMetadata['ClinicalTrials']['data']

        if (schoolMetadataDirty is True):
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        return data


    def getPRNews(self):
        timestamp = self.schoolMetadata['PRNews']['timestamp']
        
        # are our data dirty, mon?
        schoolMetadataDirty = False 

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
            
            schoolMetadataDirty = True

            data = linksCleaned
        else:
            data = self.schoolMetadata['PRNews']['data']

        if (schoolMetadataDirty is True):
            self.dbManager.put(self.schoolName, self.schoolMetadata)
        
        return data

    def getGoogleNews(self):
        timestamp = self.schoolMetadata['GoogleNews']['timestamp']

        # are our data dirty, mon?
        schoolMetadataDirty = False 

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

            schoolMetadataDirty = True

            toReturn = "\n".join(data['summary'] for data in self.schoolMetadata['GoogleNews']['data'])
        else:
            toReturn = "\n".join(data['summary'] for data in self.schoolMetadata['GoogleNews']['data'])

        if (schoolMetadataDirty is True):
            self.dbManager.put(self.schoolName, self.schoolMetadata)

        return toReturn

    def createSchoolInfo(self):
        data = {}
        data['XML'] = {'timestamp': None, 'fetched': False}
        data['STTR'] = {'timestamp': None, 'data': None}
        data['GoogleNews'] = {'timestamp': None, 'data': None}
        data['PRNews'] = {'timestamp': None, 'data': None}

        self.dbManager.put(self.schoolName, data)
        self.schoolMetadata = data

        return data

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

    def __init__(self, environment = None, db = None, dbHome = DB_HOME, dbName = "MAICgregator.db"):
        # Call methods for creating environments and DB object
        self.dbEnvironment = environment
        self.db = db 

    def __createEnvironment(self, dbHome):
        self.dbHome = dbHome
        if (self.dbEnvironment is None):
            self.dbEnvironment = DBEnv()
            self.dbEnvironment.set_flags(DB_AUTO_COMMIT, True)
            self.dbEnvironment.open(dbHome, DB_ENV_CREATE_FLAGS, 0)

    def __createDB(self, dbName):
        self.dbName = dbName
        if (self.db is None):
            self.db = DB(dbEnv = self.dbEnvironment)
            try:
                xtxn = self.dbEnvironment.txn_begin()
                self.db.open(dbName, dbtype = DB_HASH, flags = DB_CREATE, txn = xtxn)
                xtxn.commit()
            except Exception, e:
                print e

    def open(self, dbHome = DB_HOME, dbName = "MAICgregator.db"):
        self.__createEnvironment(dbHome)
        self.__createDB(dbName)

    def put(self, key, value):
        """Put the value at key.  Pickle all data so that we don't have questions at load time."""
        pickledValue = cPickle.dumps(value)
        try:
            xtxn = self.dbEnvironment.txn_begin()
            self.db.put(key, pickledValue, txn = xtxn)
            xtxn.commit()
            self.db.sync()
        except Exception, e:
            print e

    def get(self, key):
        """Get the value, and return it as an unpickled object.

        TODO: Need to handle key errors."""
        if (self.db.has_key(key) == False):
            return None
        pickledValue = self.db.get(key)
        return cPickle.loads(pickledValue)

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
