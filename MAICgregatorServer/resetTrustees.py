#!/usr/bin/env python
from MAICgregator import db, whois
from MAICgregator.db import SchoolData

print "loading db..."

dbManager = db.DBManager()
whoisStore = whois.WhoisStore(dbManager = dbManager)
schoolNames = whoisStore.whois.values()

for schoolName in schoolNames:
    if (schoolName is not None):
        print "working on schoolName ", schoolName
        school = db.SchoolData(schoolName, dbManager = dbManager)
    
        if (school.schoolMetadata.has_key('Trustees')):
            school.schoolMetadata['Trustees']['timestamp'] = None
        else:
            school.schoolMetadata['Trustees'] = {'timestamp': None}
    
        if (school.schoolMetadata.has_key('TrusteeImages')):
            school.schoolMetadata['TrusteeImages']['timestamp'] = None
        else:
            school.schoolMetadata['TrusteeImages'] = {'timestamp': None}
    
        dbManager.put(schoolName, school.schoolMetadata)
        dbManager.syncDB()
