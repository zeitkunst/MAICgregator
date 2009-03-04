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
            
            // Also, headlines, events, NewsContainer, etc.            
            /*
            var newsNode = MAICgregator.doc.getElementById("news");

            if (newsNode != null) {
                newsNode.innerHTML = "<h2>News</h2><ul><li id='testNode'>Military funding up 20%</li><li>Corporate sponsorships down 400%</li></ul>";
            }
            */

            MAICgregator.request = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"].createInstance(Components.interfaces.nsIXMLHttpRequest);

            if (MAICgregator.request.channel instanceof Components.interfaces.nsISupportsPriority) {
                MAICgregator.request.channel.priority = Components.interfaces.nsISupportsPriority.PRIORITY_LOWEST;
              }

            MAICgregator.request.open("GET", "http://localhost:8080/MAICgregator/GoogleNews/" + schoolHost, true);
            MAICgregator.request.onreadystatechange = MAICgregator.processRequest;
            MAICgregator.request.send(null);
            //MAICgregator._log("testing");
            //p.appendChild(doc.createTextNode(schoolHost));
            //doc.body.appendChild(p);
        }
    },

    processRequest: function() {
        if (MAICgregator.request.readyState < 4) {
            return;
        }

        var results = MAICgregator.request.responseText;
        var newsNode = MAICgregator.doc.getElementById("news");

        // Start cascade of other options
        // Also, headlines, events, NewsContainer, etc.            
        // TODO
        //  * make this less brittle :-) 
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("headlines");
        }
       
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("events");
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("highlights");
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("NewsContainer");
        }

        if (newsNode != null) {
            newsNode.innerHTML = results;
        }
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


function showPreferencesDialog(){
      window.open("chrome://MAICgregator/content/options.xul", "MAICgregatorPreferences", "chrome,dialog,centerscreen,alwaysRaised");
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
