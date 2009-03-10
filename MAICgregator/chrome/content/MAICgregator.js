window.addEventListener("load", function(){ MAICgregator._init(); }, false);

var MAICgregator = {
    preferences: null,
    request: null,
    doc: null,
    logStream: null,
    logFile: null,
    logDisabled: false,

    // Return a preferences instance
    _getPrefs: function() {
        if (!this.preferences){
            var prefSvc = Components.classes["@mozilla.org/preferences-service;1"].getService(Components.interfaces.nsIPrefService);
            this.preferences = prefSvc.getBranch("extensions.MAICgregator.");
        }
        return this.preferences;
    },

    // Methods to run when we initialize
    _init: function() {
        // Do initializations before we setup the event handler
        this._readPrefs();

        // Setup event listeners for page load
        var appcontent = document.getElementById("appcontent");   // browser
        if(appcontent)
            appcontent.addEventListener("DOMContentLoaded", MAICgregator.onPageLoad, true);
    },

    onPageLoad: function(aEvent) {
        MAICgregator.doc = aEvent.originalTarget;

        var loc = MAICgregator.doc.location.href;

        var reg = new RegExp("http://(.+?).edu/");
        var regExpResult = reg.exec(loc);

        if (loc != null && regExpResult != null) {
            p = MAICgregator.doc.createElement("p");
            var hostPart = regExpResult[1];
            var hostParts = hostPart.split(".");
            var schoolHost = hostParts[hostParts.length - 1] + ".edu";
            
            MAICgregator.request = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"].createInstance(Components.interfaces.nsIXMLHttpRequest);

            if (MAICgregator.request.channel instanceof Components.interfaces.nsISupportsPriority) {
                MAICgregator.request.channel.priority = Components.interfaces.nsISupportsPriority.PRIORITY_LOWEST;
              }

            // Update the preferences in case something has changed
            MAICgregator._readPrefs();
            /*
            if (MAICgregator.GoogleNewsSearch) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/GoogleNews/" + schoolHost, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processGoogleNewsRequest;
                MAICgregator.request.send(null);
            }
            if (MAICgregator.DoDSTTR) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/STTR/" + schoolHost, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processSTTRRequest;
                MAICgregator.request.send(null);
            }

            */
            /*
            if (MAICgregator.DoDBR) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/DoDBR/" + schoolHost, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processDoDBRRequest;
                MAICgregator.request.send(null);
            }
            if (MAICgregator.PRNewsSearch) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/PRNews/" + schoolHost, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processPRNewsRequest;
                MAICgregator.request.send(null);
            }

            */
            
            queryString = "";
            dataTypes = new Array();                        
            if (MAICgregator.DoDBR) {
                queryString += "DoDBR+";
                dataTypes.push("DoDBR");
            }

            if (MAICgregator.DoDSTTR) {
                queryString += "DoDSTTR+";
                dataTypes.push("DoDSTTR");
            }

            if (MAICgregator.GoogleNewsSearch) {
                queryString += "GoogleNewsSearch+";
                dataTypes.push("GoogleNewsSearch");
            }

            if (MAICgregator.PRNewsSearch) {
                queryString += "PRNewsSearch+";
                dataTypes.push("PRNewsSearch");
            }

            if (MAICgregator.TrusteeRelationshipSearch) {
                queryString += "TrusteeRelationshipSearch";
                dataTypes.push("TrusteeRelationshipSearch");
            }

            // Check if we have a + at the end of the query string
            qLength = queryString.length;
            if (queryString.lastIndexOf("+") == (qLength - 1)) {
                queryString = queryString.substring(0, qLength - 1);
            }            

            MAICgregator.dataTypes = dataTypes;
            if (queryString.length > 0) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/Aggregate/" + schoolHost + "/" + queryString, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processAggregate;
                MAICgregator.request.send(null);
            }


            /*
            if (MAICgregator.TrusteeRelationshipSearch) {
                MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/TrusteeRelationshipSearch/" + schoolHost, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processTrusteeRelationshipSearchRequest;
                MAICgregator.request.send(null);
            }
            */
            //MAICgregator._log("testing");
            //p.appendChild(doc.createTextNode(schoolHost));
            //doc.body.appendChild(p);
        }
    },

    processAggregate: function() {
        if (MAICgregator.request.readyState < 4) {
            return;
        }
        var methodMapping = {
            'DoDBR': MAICgregator.processDoDBRResults,
            'DoDSTTR': MAICgregator.processDoDSTTRResults,
            'GoogleNewsSearch': MAICgregator.processGoogleNewsResults,
            'PRNewsSearch': MAICgregator.processPRNewsResults,
            'TrusteeRelationshipSearch': MAICgregator.processTrusteeRelationshipSearchResults
        };

        var results = MAICgregator.request.responseXML;
        var newsNode = MAICgregator.findNewsNode();
        
        if (newsNode != null) {
            var errorNode = results.getElementsByTagName("error")[0];
            
            for (index in MAICgregator.dataTypes) {
                var dataType = MAICgregator.dataTypes[index]
                var dataNode = results.getElementsByTagName(dataType)[0];
                method = methodMapping[dataType];
                method(dataNode);
            }
            //MAICgregator.processTrusteeRelationshipSearchResults(getNodeValue(TrusteeData));
        }
    },

    processGoogleNewsResults: function(results) {
        var children = results.getElementsByTagName("table");
        var newsNode = MAICgregator.findNewsNode();
        if (newsNode != null) {
            newsNode.innerHTML = "";
            divNode = MAICgregator.doc.createElement("div");
            for (index = 0; index < children.length; index++) {
                pNode = MAICgregator.doc.createElement("p");
                pNode.appendChild(children[index].cloneNode(true));
                divNode.appendChild(pNode);
            }
            newsNode.appendChild(divNode);
        }
    },
 
    processDoDBRResults: function(results) {
        var results = getNodeValue(results);
        var newsNode = MAICgregator.findNewsNode();

        if (newsNode != null) {
            // Parse our formatted STTR data
            itemArray = results.split("\n");

            // Get a random item from our result
            randomIndex = Math.floor(Math.random() * itemArray.length);
            
            // Save our methods
            //createElement = MAICgregator.doc.createElement;
            //createTextNode = MAICgregator.doc.createTextNode;
            
            divNode = MAICgregator.doc.createElement("div");
            grantsArray = new Array();
            contractsArray = new Array();

            for (itemIndex in itemArray) {
                data = itemArray[itemIndex].split("\t");
                if (data[0] == "grant") {
                    grantsArray.push(itemArray[itemIndex]);
                } else if (data[0] == "contract") {
                    contractsArray.push(itemArray[itemIndex]);
                }
            }

            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Department of Defense Basic Research Grants"));
            divNode.appendChild(h3Node);
            ulNode = MAICgregator.doc.createElement("ul");

            for (itemIndex in grantsArray) {
                data = grantsArray[itemIndex].split("\t");
                type = data[0];
                title = data[1];
                awardId = data[2];
                agency = data[3];
                amount = parseFloat(data[4]);
                
                liNode = MAICgregator.doc.createElement("li");
                textToAdd = "<strong>$" + amount + "</strong> from the <strong>" + agency + "</strong> to study <em>" + title + "</em> with a Federal Award ID of " + awardId;
                liNode.innerHTML = textToAdd;
                ulNode.appendChild(liNode);

            }                
            divNode.appendChild(ulNode);

            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Department of Defense Basic Research Contracts"));
            divNode.appendChild(h3Node);
            ulNode = MAICgregator.doc.createElement("ul");

            for (itemIndex in contractsArray) {
                data = contractsArray[itemIndex].split("\t");
                type = data[0];
                title = data[1];
                awardId = data[2];
                agency = data[3];
                amount = parseFloat(data[4]);
                
                liNode = MAICgregator.doc.createElement("li");
                textToAdd = "<strong>$" + amount + "</strong> from the <strong>" + agency + "</strong> to study <em>" + title + "</em> with a Federal Award ID of " + awardId;
                liNode.innerHTML = textToAdd;
                ulNode.appendChild(liNode);

            }                
            divNode.appendChild(ulNode);

            newsNode.innerHTML = "";
            newsNode.appendChild(divNode);
        }
    },

    processDoDSTTRResults: function(results) {
        var results = getNodeValue(results);
        var newsNode = MAICgregator.findNewsNode();

        if (newsNode != null) {
            // Parse our formatted STTR data
            itemArray = results.split("\n");

            // Get a random item from our result
            randomIndex = Math.floor(Math.random() * itemArray.length);
            
            // Save our methods
            //createElement = MAICgregator.doc.createElement;
            //createTextNode = MAICgregator.doc.createTextNode;
            
            divNode = MAICgregator.doc.createElement("div");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Department of Defense STTR grants"));
            divNode.appendChild(h3Node);

            data = itemArray[randomIndex].split("\t");
            PK_AWARDS = data[0];
            AGENCY = data[1];
            CONTRACT = data[2];
            AWARD_AMT = data[3];
            PI_NAME = data[4];
            FIRM = data[5];
            URL = data[6];
            PRO_TITLE = data[7];
            WholeAbstract = data[8];
            
            h4Node = MAICgregator.doc.createElement("h4");
            h4Node.innerHTML = "<a href=\"http://www.dodsbir.net/Awards/SrchResultsDtlsForm.asp?RanNo=0&bookmark=" + PK_AWARDS.trim() + "\">" + PRO_TITLE.trim() + "</a>";
            //h4Node.appendChild(createTextNode(PRO_TITLE.trim());
            divNode.appendChild(h4Node);

            // TODO
            // Highlight "military" words in the following, like:
            // military, civilian, army, radar, defense, war, etc.
            // Use methods like indexOf, substr, etc to split the text up
            pNode = MAICgregator.doc.createElement("p");
            textToInsert = "<strong>$" + AWARD_AMT.trim() + "</strong> from the <strong>" + AGENCY.trim() + "</strong> to <a href=\"http://www.google.com/search?q=" + escape(FIRM.trim()) + "\">" + FIRM.trim() + "</a> and <a href=\"http://www.google.com/search?q=" + escape(PI_NAME.trim()) + "\">" + PI_NAME.trim() + "</a>";

            //textToInsert = "<strong>" + AGENCY.trim() + "</strong>" + "<em>" + PRO_TITLE.trim() + "</em>" + " <strong>$" + AWARD_AMT.trim() + "</strong>" + WholeAbstract.trim();
            pNode.innerHTML = textToInsert;
            divNode.appendChild(pNode);
            
            pNode = MAICgregator.doc.createElement("p");
            pNode.appendChild(MAICgregator.doc.createTextNode(WholeAbstract.trim()));
            divNode.appendChild(pNode);

            newsNode.innerHTML = "";
            newsNode.appendChild(divNode);
        }
    },
 
    processPRNewsResults: function(results) {
        childNodes = results.getElementsByTagName("a");
        var newsNode = MAICgregator.findNewsNode();
        
        if (newsNode != null) {
            // Parse our formatted STTR data

            
            divNode = MAICgregator.doc.createElement("div");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Recent Press Releases:"));
            divNode.appendChild(h3Node);
          
            // TODO
            // HEINOUS, fix this
            // For some reason the really messed up ordering below seems to work...don't ask me why 
            newsNode.innerHTML = "";
            //newsNode.appendChild(divNode);
            // Start creating our list
            for (index = 0; index < childNodes.length; index++) {
                pNode = MAICgregator.doc.createElement("p");
                aNode = childNodes[index];
                
                href = aNode.getAttribute("href");
                text = aNode.childNodes[1].nodeValue;

                aNodeNew = MAICgregator.doc.createElement("a");
                aNodeNew.setAttribute("href", href);
                aNodeNewText = MAICgregator.doc.createTextNode(text);
                aNodeNew.appendChild(aNodeNewText);

                pNode.appendChild(aNodeNew);
                divNode.appendChild(pNode);
            }

            newsNode.appendChild(divNode);
        }
    },

    processTrusteeRelationshipSearchRequest: function() {
        if (MAICgregator.request.readyState < 4) {
            return;
        }

        var results = MAICgregator.request.responseText;
        var newsNode = MAICgregator.findNewsNode();

        if (newsNode != null) {
            // Parse our formatted STTR data
            itemArray = results.split("\n");

            divNode = MAICgregator.doc.createElement("div");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Members of the Board of Trustees"));
            divNode.appendChild(h3Node);

            ulNode = MAICgregator.doc.createElement("ul");
            for (index in itemArray) {
                liNode = MAICgregator.doc.createElement("ul");
                name = itemArray[index];

                aNode = MAICgregator.doc.createElement("a");
                aNode.setAttribute("href", "http://www.google.com/search?&q=" + encodeURI(name + " trustee"));
                textNode = MAICgregator.doc.createTextNode(name);
                aNode.appendChild(textNode);

                liNode.appendChild(aNode);
                ulNode.appendChild(liNode);
            }
            divNode.appendChild(ulNode);

            newsNode.innerHTML = "";
            newsNode.appendChild(divNode);
        }
    },

    processTrusteeRelationshipSearchResults: function(results) {
        var results = getNodeValue(results);
        var newsNode = MAICgregator.findNewsNode();

        if (newsNode != null) {
            // Parse our formatted STTR data
            itemArray = results.split("\n");

            divNode = MAICgregator.doc.createElement("div");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("Members of the Board of Trustees"));
            divNode.appendChild(h3Node);

            ulNode = MAICgregator.doc.createElement("ul");
            for (index in itemArray) {
                liNode = MAICgregator.doc.createElement("ul");
                name = itemArray[index];

                aNode = MAICgregator.doc.createElement("a");
                aNode.setAttribute("href", "http://www.google.com/search?&q=" + encodeURI(name + " trustee"));
                textNode = MAICgregator.doc.createTextNode(name);
                aNode.appendChild(textNode);

                liNode.appendChild(aNode);
                ulNode.appendChild(liNode);
            }
            divNode.appendChild(ulNode);

            newsNode.innerHTML = "";
            newsNode.appendChild(divNode);
        }
    },


    findNewsNode: function() {
        var newsNode = MAICgregator.doc.getElementById("news");
        
        if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p" && newsNode.nodeName.toLowerCase() != "table") {
            newsNode = null;
        }

        // Start cascade of other options
        // Also, headlines, events, NewsContainer, etc.            
        // TODO
        //  * make this less brittle :-) 
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("headlines");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }
 
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("dropshadow-headlines");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("nccontent");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }
  
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("events");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("highlights");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("NewsContainer");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("newsline");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("newscenter");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("newsAndEvents");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("hpevents");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        // If we can't find any seeming news entries, take over the spotlight  or feature element(s)
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("spotlight");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("features");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("sg_feats");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }

        }


        // Finally, check for possible li elements that have news
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("news");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "li") {
                newsNode = null;
            }
        }
        
        // Specialness for USC
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("welcome");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "td") {
                newsNode = null;
            }
        }

        // And finally, since Caltech's home page is so strangely done...
        // TODO
        // This doesn't quite work because their news is also done by ajax and replaces _my_ content :-)
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("contentDiv");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        return newsNode;

    },

    

    _cout: function(msg) {
        var consoleService = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
        consoleService.logStringMessage(msg);
    },

    _readPrefs: function() {
        var prefs = this._getPrefs();

        // Read current preferences
        this.interject = prefs.getCharPref("interject");
        this.DoDBR = prefs.getBoolPref("DoDBR");
        this.DoDSTTR = prefs.getBoolPref("DoDSTTR");
        this.DHS = prefs.getBoolPref("DHS");
        this.GoogleNewsSearch = prefs.getBoolPref("GoogleNewsSearch");
        this.PRNewsSearch = prefs.getBoolPref("PRNewsSearch");
        this.TrusteeRelationshipSearch = prefs.getBoolPref("TrusteeRelationshipSearch");
        
    },

    _savePreferences: function() {
        var prefs = this._getPrefs();

        // Set char preferences
        prefs.setCharPref("interject", this.interject);

        // Set boolean preferences
        prefs.setBoolPref("DoDBR", this.DoDBR);
        prefs.setBoolPref("DoDSTTR", this.DoDSTTR);
        prefs.setBoolPref("DHS", this.DHS);
        prefs.setBoolPref("GoogleNewsSearch", this.GoogleNewsSearch);
        prefs.setBoolPref("PRNewsSearch", this.PRNewsSearch);
        prefs.setBoolPref("TrusteeRelationshipSearch", this.TrusteeRelationshipSearch);
    },
    
    _foo: function() {
        return "foo";
    },

    _createProfileFile: function(name) {
        try {
            // get profile directory
            var file = Components.classes["@mozilla.org/file/directory_service;1"].getService(Components.interfaces.nsIProperties).get("ProfD", Components.interfaces.nsIFile);
        } catch(ex) {
            return null;     
        }
        
        try {
            file.append("MAICgregator");
            if (!file.exists()|| !file.isDirectory())
                file.create(Components.interfaces.nsIFile.DIRECTORY_TYPE, 0777);
            file.append(name);
        } catch(ex) {
            return null;            
        }
        return file;
    },

    // From
    // trackmenot
    _log: function(msg) {
        if (this.logDisabled)
            return;

        try {
            if (!this.logStream) {
                if (!this.logFile)
                    this.logFile = this._createProfileFile("MAICgregator.log");
                    this.logStream = Components.classes["@mozilla.org/network/file-output-stream;1"].createInstance(Components.interfaces.nsIFileOutputStream );

                    this.logStream.init(this.logFile, 0x02 | 0x08 | 0x10, 0644, 0);
                    const head="[STREAM] action=refresh | file=tmn_log.txt | " + new Date().toGMTString()+"\n";
                    this.logStream.write(head, head.length);
                    this.logStream.flush();
            }
            
            if (msg != null) {
                msg += " | "+new Date().toGMTString()+" |\n";
                if (this.logStream){
                    this.logStream.write(msg, msg.length);
                    this.logStream.flush();
                } else {
                
                }
            }                                   

        } catch (ex) {

        }

    }

}

function getNodeValue(node) {
    return node.firstChild.nodeValue;
}

function showPreferencesDialog(){
      window.open("chrome://MAICgregator/content/options.xul", "MAICgregatorPreferences", "chrome,dialog,centerscreen,alwaysRaised");
}

String.prototype.trim = function() {
      return this.replace(/^\s+|\s+$/g, "");
}


function testAJAX() {
    if (this.request.readyState < 4) {
        return;
    }
        
    var results = this.request.responseText;
    var p = this.doc.createElement("p");
    p.appendChild(doc.createTextNode(results));
    this.doc.body.appendChild(p);
}
