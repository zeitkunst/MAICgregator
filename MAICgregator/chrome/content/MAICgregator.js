window.addEventListener("load", function(){ MAICgregator._init(); }, false);

var MAICgregator = {
    preferences: null,
    request: null,
    doc: null,
    logStream: null,
    logFile: null,
    logDisabled: false,
    previousState: null,
    currentState: null,
    dataTypeList: new Array("DoDBR", "DoDSTTR", "GoogleNewsSearch", "PRNewsSearch", "TrusteeRelationshipSearch"), 

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
        updateMAICgregatorButton();
        if(appcontent)
            appcontent.addEventListener("DOMContentLoaded", MAICgregator.onPageLoad, true);

    },

    onPageLoad: function(aEvent) {
        //$jq("#wrapper").css("background-color", "#000000");
        //$jq = jQuery.noConflict();
        MAICgregator.doc = aEvent.originalTarget;

        // Load jquery into the page
        $jq = jQuery.noConflict();

        // For each jquery call we have to provide the context, which is MAICgregator.doc (i.e., the currently loaded page)
        //$jq("#wrapper", MAICgregator.doc).css("color", "#00FF00");

        var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
        var enumerator = wm.getEnumerator("navigator:browser");

        // Update the preferences in case something has changed
        MAICgregator._readPrefs();

        MAICgregator.currentState = MAICgregator.interject;
        if (MAICgregator.currentState == "None") {
            MAICgregator.previousState = "All";
        } else {
            MAICgregator.previousState = "None";
        }

        // Are even supposed to interject?
        if (MAICgregator.interject == "None") {
            return;
        }

        var loc = MAICgregator.doc.location.href;

        var reg = new RegExp("http://(.+?).edu/");
        var regExpResult = reg.exec(loc);

        if (loc != null && regExpResult != null) {
            var hostPart = regExpResult[1];
            var hostParts = hostPart.split(".");
            var schoolHost = hostParts[hostParts.length - 1] + ".edu";
            
            MAICgregator.request = Components.classes["@mozilla.org/xmlextras/xmlhttprequest;1"].createInstance(Components.interfaces.nsIXMLHttpRequest);

            if (MAICgregator.request.channel instanceof Components.interfaces.nsISupportsPriority) {
                MAICgregator.request.channel.priority = Components.interfaces.nsISupportsPriority.PRIORITY_LOWEST;
              }

            // Update the preferences in case something has changed
            MAICgregator._readPrefs();
            
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
                MAICgregator.request.open("GET", MAICgregator.serverURL + "Aggregate/" + schoolHost + "/" + queryString, true);
                MAICgregator.request.onreadystatechange = MAICgregator.processAggregate;
                MAICgregator.request.send(null);
            }
           
            // Are we showing status messages?
            if (MAICgregator.infoStatus) {
                infoDivNode = MAICgregator.doc.createElement("div");
                infoDivNode.id = "MAICgregatorInfo";
                infoDivNode.style.styleFloat = "left";
                infoDivNode.style.clear = "both";
                infoDivNode.style.position = "absolute";
                infoDivNode.style.top = "0em";
                infoDivNode.style.left = "0em";
    
                spanNode = MAICgregator.doc.createElement("span");
                spanNode.style.backgroundColor = "#DF1111";
                spanNode.style.color = "#EFEF11";
                spanNode.appendChild(MAICgregator.doc.createTextNode("Making data request..."));
                infoDivNode.appendChild(spanNode);
                MAICgregator.doc.body.insertBefore(infoDivNode, MAICgregator.doc.body.childNodes[0]);
                MAICgregator.infoDivNode = infoDivNode;

            }

        }
    },

    processAggregate: function() {
        if (MAICgregator.request.readyState < 4) {
            return;
        }

        var results = MAICgregator.request.responseXML;
        var newsNode = MAICgregator.findNewsNode();
        
        if (results == null) {
            if (newsNode != null) {
                newsNode.innerHTML = "<div><p>There was some problem MAICgregating the data...the tubes must be stuck or something.  Please try again in a bit, or if the problem persists, <a href=\"mailto:info --at-- maicgregator ---dot--- org\">e-mail</a> us and tell us the site you were trying to view.</p></div>";
                return;
            }
        }
        
        if ((newsNode != null)) {
            var errorNode = results.getElementsByTagName("error")[0];

            if (errorNode != null) {
                // TODO
                // Make and process errors
                newsNode.innerHTML = "";
                return;
            }

            // Otherwise, start processing the divs
            newsNode.innerHTML = "";
            h2Node = MAICgregator.doc.createElement("h2");
            h2Node.appendChild(MAICgregator.doc.createTextNode("Current Alternative News:"));
            newsNode.appendChild(h2Node);
 
            if (MAICgregator.infoStatus) {
                MAICgregator.infoDivNode.firstChild.innerHTML = "Processing results...";
            }
           
            var processResults = MAICgregator._processXMLResults(results);
            var nodesToAdd = processResults[0];
            var newaTags = processResults[1];

            if (MAICgregator.randomize) {
                allaTags = MAICgregator.doc.getElementsByTagName("a");

                for (index = 0; index < allaTags.length; index++) {
                    randomIndex = Math.floor(Math.random() * newaTags.length);
                    
                    var currentaTag = allaTags[index];
                    var replacementaTag = newaTags[randomIndex];
                    currentaTag.href = replacementaTag.href;
                }
            }

            for (addIndex = 0; addIndex < nodesToAdd.length; addIndex++) {
                newsNode.appendChild(nodesToAdd[addIndex]);
            }

            if (MAICgregator.infoStatus) {
                MAICgregator.infoDivNode.style.display = "none";
            }

        } else if ((newsNode == null) && (MAICgregator.interject == "All")) {
            if (MAICgregator.infoStatus) {
                MAICgregator.infoDivNode.firstChild.innerHTML = "Processing results...";
            }
            var processResults = MAICgregator._processXMLResults(results);
            var nodesToAdd = processResults[0];
            var newaTags = processResults[1];

            divNode = MAICgregator.doc.createElement("div");
            divNode.style.position = "absolute";
            divNode.style.top = "3em";
            divNode.style.left = "3em";
            divNode.style.width = "22em";
            divNode.style.opacity = "0.85";
            divNode.style.padding = "0.5em 0.5em";
            divNode.style.backgroundColor = "#333";
            divNode.style.zIndex = "55";

            newsDivNode = MAICgregator.doc.createElement("div");
            newsDivNode.style.opacity = "1.0";
            newsDivNode.style.padding = "0.5em";
            newsDivNode.style.backgroundColor = "#eee";
            h2Node = MAICgregator.doc.createElement("h2");
            h2Node.appendChild(MAICgregator.doc.createTextNode("Current Alternative News:"));
            newsDivNode.appendChild(h2Node);
            for (addIndex = 0; addIndex < nodesToAdd.length; addIndex++) {
                newsDivNode.appendChild(nodesToAdd[addIndex]);
            }
            divNode.appendChild(newsDivNode);

            if (MAICgregator.randomize) {
                allaTags = MAICgregator.doc.getElementsByTagName("a");

                for (index = 0; index < allaTags.length; index++) {
                    randomIndex = Math.floor(Math.random() * newaTags.length);
                    
                    var currentaTag = allaTags[index];
                    var replacementaTag = newaTags[randomIndex];
                    currentaTag.href = replacementaTag.href;
                }
            }
            
            MAICgregator.doc.body.insertBefore(divNode, MAICgregator.doc.body.childNodes[0]);
            if (MAICgregator.infoStatus) {
                MAICgregator.infoDivNode.style.display = "none";
            }

        }
    },
    
    _processXMLResults: function(results) {
        var methodMapping = {
            'DoDBR': MAICgregator.processDoDBRResults,
            'DoDSTTR': MAICgregator.processDoDSTTRResults,
            'GoogleNewsSearch': MAICgregator.processGoogleNewsResults,
            'PRNewsSearch': MAICgregator.processPRNewsResults,
            'TrusteeRelationshipSearch': MAICgregator.processTrusteeRelationshipSearchResults
        };

        var linkNameMapping = {
            'DoDBR': "DoD Basic Research",
            'DoDSTTR': "DoD STTR Grants",
            'GoogleNewsSearch': "Google News Search",
            'PRNewsSearch': "PR News Search",
            'TrusteeRelationshipSearch': "Trustee Relationship Search" 
        };

        returnArray = new Array();

        nodesToAdd = new Array();
        newaTags = new Array();
        for (index in MAICgregator.dataTypes) {
            var dataType = MAICgregator.dataTypes[index];
            var dataNode = results.getElementsByTagName(dataType)[0];
            method = methodMapping[dataType];
            newDivNode = method(dataNode);
            newDivNode.style.display = "none";

            if (MAICgregator.randomize) {
                var aTagsToAdd = newDivNode.getElementsByTagName("a");
                for (aTagIndex = 0; aTagIndex < aTagsToAdd.length; aTagIndex++) {
                    newaTags.push(aTagsToAdd[aTagIndex]);
                }
            }

            pNode = MAICgregator.doc.createElement("p");
            aNode = MAICgregator.doc.createElement("a");
            aNode.href = "#" + dataType;
            aNode.className = "MAICgregator" + dataType;
            aNode.addEventListener("click", function() {
                divNodeToDisplay = MAICgregator.doc.getElementById(this.className);

                if (divNodeToDisplay == null) {
                    return;
                }

                if (divNodeToDisplay.style.display == "block") {
                    divNodeToDisplay.style.display = "none";
                } else if (divNodeToDisplay.style.display == "none") {
                    divNodeToDisplay.style.display = "block";
                }
            }, false);

            aNodeText = MAICgregator.doc.createTextNode(linkNameMapping[dataType]);
            aNode.appendChild(aNodeText);
            pNode.appendChild(aNode);
            
            nodesToAdd.push(pNode);
            nodesToAdd.push(newDivNode);
            //newsNode.appendChild(pNode);
            //newsNode.appendChild(newDivNode);
            
        }
        returnArray.push(nodesToAdd);
        returnArray.push(newaTags);

        return returnArray;

    },

    processGoogleNewsResults: function(results) {
        if (!results) {
            divNode = MAICgregator.doc.createElement("div");
            divNode.setAttribute("id", "MAICgregatorGoogleNewsSearch");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("No results"));
            divNode.appendChild(h3Node);
            return divNode;
        }

        var children = results.getElementsByTagName("table");
        var newChildren = new Array();

        for (index = 0; index < children.length; index++) {
            newChildren.push(children[index].cloneNode(true));
        }

        divNode = MAICgregator.doc.createElement("div");
        divNode.setAttribute("id", "MAICgregatorGoogleNewsSearch");
        h3Node = MAICgregator.doc.createElement("h3");
        h3Node.appendChild(MAICgregator.doc.createTextNode("Google News Search Results"));
        divNode.appendChild(h3Node);

        for (index = 0; index < newChildren.length; index++) {
            // TODO
            // MONDO HEINOUS
            // I'm not sure why I need to go through the craziness of the following, as I should be able to just append the table nodes; I can do that, but then the links aren't clickable.  It's very very strange...
            pNode = MAICgregator.doc.createElement("p");
            aNode = newChildren[index].getElementsByTagName("a")[0];
            fontNodeLocation = newChildren[index].getElementsByTagName("div")[1].getElementsByTagName("font")[1];
            fontNodeInfo = newChildren[index].getElementsByTagName("div")[1].getElementsByTagName("font")[2];
            
            href = aNode.getAttribute("href");
            textNodes = aNode.childNodes;

            aNodeNew = MAICgregator.doc.createElement("a");
            aNodeNew.setAttribute("href", href);
            for (aIndex = 0; aIndex < textNodes.length; aIndex++) {
                toAppend = textNodes[aIndex];
                aNodeNew.appendChild(toAppend);
            }
            pNode.appendChild(aNodeNew);

            descNode = MAICgregator.doc.createElement("p");
            locationData = fontNodeLocation.firstChild.nodeValue;
            for (fontIndex = 0; fontIndex < fontNodeInfo.childNodes.length; fontIndex++) {
                if (fontNodeInfo.childNodes[fontIndex].nodeType == 3) {
                    infoData = fontNodeInfo.childNodes[fontIndex].nodeValue;
                }
            }
            //infoData = fontNodeInfo.firstChild.nodeValue;
            textNode = MAICgregator.doc.createTextNode(locationData + "  " + infoData);
            descNode.appendChild(textNode);
            pNode.appendChild(descNode);


            divNode.appendChild(pNode);
        }
        //newsNode.innerHTML = "";
        //newsNode.appendChild(divNode);
        return divNode;
    },
 
    processDoDBRResults: function(results) {
        //var results = getNodeValue(results);
        resultsText = "";
        for (index = 0; index < results.childNodes.length; index++) {
            resultsText += results.childNodes[index].nodeValue;
        }
        // Parse our formatted STTR data
        itemArray = resultsText.split("\n");
        if (itemArray[1] == "") {
            divNode = MAICgregator.doc.createElement("div");
            divNode.setAttribute("id", "MAICgregatorDoDBR");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("No Results"));
            divNode.appendChild(h3Node);
            return divNode;
        }        

        // Get a random item from our result
        randomIndex = Math.floor(Math.random() * itemArray.length);
        
        // Save our methods
        //createElement = MAICgregator.doc.createElement;
        //createTextNode = MAICgregator.doc.createTextNode;
        
        divNode = MAICgregator.doc.createElement("div");
        divNode.setAttribute("id", "MAICgregatorDoDBR");
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

        //newsNode.innerHTML = "";
        //newsNode.appendChild(divNode);
        return divNode;
    },

    processDoDSTTRResults: function(results) {
        var results = getNodeValue(results);
        results = new String(results);
        results = results.trim();
        // Parse our formatted STTR data
        itemArray = results.split("\n");
        
        if (itemArray[0] == "") {
            divNode = MAICgregator.doc.createElement("div");
            divNode.setAttribute("id", "MAICgregatorDoDSTTR");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("No Results"));
            divNode.appendChild(h3Node);

            return divNode;
        } 

        // Get a random item from our result
        randomIndex = Math.floor(Math.random() * itemArray.length);
        
        // Save our methods
        //createElement = MAICgregator.doc.createElement;
        //createTextNode = MAICgregator.doc.createTextNode;
        
        divNode = MAICgregator.doc.createElement("div");
        divNode.setAttribute("id", "MAICgregatorDoDSTTR");
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

        // Sometimes we don't have an abstract...
        if (WholeAbstract) {
            pNode = MAICgregator.doc.createElement("p");
            pNode.appendChild(MAICgregator.doc.createTextNode(WholeAbstract.trim()));
            divNode.appendChild(pNode);
        }

        //newsNode.innerHTML = "";
        //newsNode.appendChild(divNode);
        return divNode;
    },
 
    processPRNewsResults: function(results) {
        childNodes = results.getElementsByTagName("a");
        
        divNode = MAICgregator.doc.createElement("div");
        divNode.setAttribute("id", "MAICgregatorPRNewsSearch");
        h3Node = MAICgregator.doc.createElement("h3");
        h3Node.appendChild(MAICgregator.doc.createTextNode("Recent Press Releases:"));
        divNode.appendChild(h3Node);
      
        // TODO
        // HEINOUS, fix this
        // For some reason the really messed up ordering below seems to work...don't ask me why 
        //newsNode.innerHTML = "";
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

        //newsNode.appendChild(divNode);
        return divNode;
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

            if (itemArray[1] == "") {
                divNode = MAICgregator.doc.createElement("div");
                divNode.setAttribute("id", "MAICgregatorTrusteeRelationshipSearch");
                h3Node = MAICgregator.doc.createElement("h3");
                h3Node.appendChild(MAICgregator.doc.createTextNode("No Results"));
                divNode.appendChild(h3Node);

                return divNode;
            }        

            divNode = MAICgregator.doc.createElement("div");
            divNode.setAttribute("id", "MAICgregatorTrusteeRelationshipSearch");
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
        
        itemArray = results.split("\n");
        if ((itemArray[1] == "") || (itemArray[1] == "None")) {
            divNode = MAICgregator.doc.createElement("div");
            divNode.setAttribute("id", "MAICgregatorTrusteeRelationshipSearch");
            h3Node = MAICgregator.doc.createElement("h3");
            h3Node.appendChild(MAICgregator.doc.createTextNode("No Results"));
            divNode.appendChild(h3Node);

            return divNode;
        }        

        divNode = MAICgregator.doc.createElement("div");
        divNode.setAttribute("id", "MAICgregatorTrusteeRelationshipSearch");
        h3Node = MAICgregator.doc.createElement("h3");
        h3Node.appendChild(MAICgregator.doc.createTextNode("Members of the Board of Trustees"));
        divNode.appendChild(h3Node);

        ulNode = MAICgregator.doc.createElement("ul");

        currentImageList = MAICgregator.doc.getElementsByTagName("img");
        currentObjectList = MAICgregator.doc.getElementsByTagName("object");
        currentEmbedList = MAICgregator.doc.getElementsByTagName("embed");
        for (index in itemArray) {
            liNode = MAICgregator.doc.createElement("ul");
            trusteeInfo = itemArray[index].split("\t");
            name = trusteeInfo[0];
            
            // Do we have an image?            
            if (trusteeInfo.length > 1) {
                if (trusteeInfo[1] != "") {

                    if (MAICgregator.trusteeImages == "Random") {
                        // Use the following for placing the random divs of images
                        imgNode = MAICgregator._createImageNode(trusteeInfo[0], trusteeInfo[1]);
                        MAICgregator.doc.body.appendChild(imgNode); 
                    } else if (MAICgregator.trusteeImages == "Replace") {
                        // Otherwise, replace images inline
                        // Get all Images on the page
                        randomIndex = Math.floor(Math.random() * currentImageList.length);
                        currentImageList[randomIndex].src = trusteeInfo[1];
                        currentImageList[randomIndex].alt = trusteeInfo[0];
                    }
                }
            }

            aNode = MAICgregator.doc.createElement("a");
            aNode.setAttribute("href", "http://www.google.com/search?&q=" + encodeURI(name + " trustee"));
            textNode = MAICgregator.doc.createTextNode(name);
            aNode.appendChild(textNode);

            liNode.appendChild(aNode);
            ulNode.appendChild(liNode);
        }
        divNode.appendChild(ulNode);

        //newsNode.innerHTML = "";
        //newsNode.appendChild(divNode);
        return divNode;
    },


    findNewsNode: function() {
        var newsNode = MAICgregator.doc.getElementById("news");
        
        if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p" && newsNode.nodeName.toLowerCase() != "table" && newsNode.nodeName.toLowerCase() != "td") {
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
            var newsNode = MAICgregator.doc.getElementById("story1");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("column_four");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("column1");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("center");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("content_block");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("billboard");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("feature");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("t_content");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        // Special for harvard's front page at harvard.edu
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("featuredtext");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        // Special for hbs front page
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("centercol");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        // for university of minnesota
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("header_sub");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        // for university of iowa 
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("news_obj_outer");
            if (newsNode != null && newsNode.nodeName.toLowerCase() != "div" && newsNode.nodeName.toLowerCase() != "p") {
                newsNode = null;
            }
        }

        // take over top nav buttons, if necessary
        if (newsNode == null) {
            var newsNode = MAICgregator.doc.getElementById("topNavButtons");
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

    _createImageNode: function(name, link) {
        // Need to add:
        // p tag that holds the person's name, and a link to the google image search results
        // onhover event handler that would raise the div?
        divNode = MAICgregator.doc.createElement("div");
        divNode.style.position = "absolute";
        randomTop = Math.floor(Math.random() * 50);
        randomTop = randomTop.toString();
        randomLeft = Math.floor(Math.random() * 50);
        randomLeft = randomLeft.toString();
        divNode.style.top = randomTop + "em"; 
        divNode.style.left = randomLeft + "em"; 
        divNode.style.zIndex = "20"; 
        divNode.style.opacity = "0.85"; 
        aNode = MAICgregator.doc.createElement("a");
        aNode.href = link; 
        imgNode = MAICgregator.doc.createElement("img");
        imgNode.src = link;
        imgNode.width = 200;
        aNode.appendChild(imgNode);

        pNode = MAICgregator.doc.createElement("p");
        pNode.style.backgroundColor = "#eee";
        pNode.style.padding = "0.5em";
        searchaNode = MAICgregator.doc.createElement("a");
        searchaNode.href = "http://images.google.com/images?q=" + escape("\"" + name + "\""); 
        searchaNode.appendChild(MAICgregator.doc.createTextNode(name));
        pNode.appendChild(searchaNode);
        
        imgContainerNode = MAICgregator.doc.createElement("div");
        imgContainerNode.style.margin = "0em";
        imgContainerNode.appendChild(aNode);
        divNode.appendChild(imgContainerNode);
        divNode.appendChild(pNode);
        return divNode;
    },    

    _cout: function(msg) {
        var consoleService = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
        consoleService.logStringMessage(msg);
    },

    _readPrefs: function() {
        var prefs = this._getPrefs();

        // Read current preferences
        this.interject = prefs.getCharPref("interject");
        this.trusteeImages = prefs.getCharPref("trusteeImages");
        this.DoDBR = prefs.getBoolPref("DoDBR");
        this.DoDSTTR = prefs.getBoolPref("DoDSTTR");
        this.DHS = prefs.getBoolPref("DHS");
        this.GoogleNewsSearch = prefs.getBoolPref("GoogleNewsSearch");
        this.PRNewsSearch = prefs.getBoolPref("PRNewsSearch");
        this.TrusteeRelationshipSearch = prefs.getBoolPref("TrusteeRelationshipSearch");
        this.randomize = prefs.getBoolPref("randomize");
        this.infoStatus = prefs.getBoolPref("infoStatus");
        this.serverURL = prefs.getCharPref("serverURL");
        
    },

    _savePreferences: function() {
        var prefs = this._getPrefs();

        // Set char preferences
        prefs.setCharPref("interject", this.interject);
        prefs.setCharPref("serverURL", this.serverURL);
        prefs.setCharPref("trusteeImages", this.trusteeImages);

        // Set boolean preferences
        prefs.setBoolPref("DoDBR", this.DoDBR);
        prefs.setBoolPref("DoDSTTR", this.DoDSTTR);
        prefs.setBoolPref("DHS", this.DHS);
        prefs.setBoolPref("GoogleNewsSearch", this.GoogleNewsSearch);
        prefs.setBoolPref("PRNewsSearch", this.PRNewsSearch);
        prefs.setBoolPref("TrusteeRelationshipSearch", this.TrusteeRelationshipSearch);
        prefs.setBoolPref("randomize", this.randomize);
        prefs.setBoolPref("infoStatus", this.infoStatus);
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

function updateMAICgregatorButton() {
    MAICgregator._readPrefs();
    currentState = MAICgregator.interject;
    var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
    var enumerator = wm.getEnumerator("navigator:browser");

    if (currentState == "None") {
        buttonStyle = "url('chrome://MAICgregator/skin/icon24Disabled.png')";
    } else {
        buttonStyle = "url('chrome://MAICgregator/skin/icon24.png')";

    }

    while(enumerator.hasMoreElements()) {
        var win = enumerator.getNext();
        buttonNode = win.document.getElementById("MAICgregatorToolbarButton");
        buttonNode.style.listStyleImage = buttonStyle;
    }

}

function toggleMAICgregator() {
    currentState = MAICgregator.interject;
    var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
    var enumerator = wm.getEnumerator("navigator:browser");
        //
    if (currentState == "None") {
        if (MAICgregator.previousState == null) {
            MAICgregator.interject = "All";
        } else {
            MAICgregator.interject = MAICgregator.previousState;
        }
        buttonNode = document.getElementById("MAICgregatorToolbarButton");
        //buttonNode.style.listStyleImage = "url('chrome://MAICgregator/skin/icon24.png')";
        buttonStyle = "url('chrome://MAICgregator/skin/icon24.png')";
    } else {
        if (MAICgregator.previousState == null) {
            MAICgregator.interject = "None";
        } else {
            MAICgregator.interject = MAICgregator.previousState;
        }
        buttonNode = document.getElementById("MAICgregatorToolbarButton");
        //buttonNode.style.listStyleImage = "url('chrome://MAICgregator/skin/icon24Disabled.png')";
        buttonStyle = "url('chrome://MAICgregator/skin/icon24Disabled.png')";

    }

    while(enumerator.hasMoreElements()) {
        var win = enumerator.getNext();
        buttonNode = win.document.getElementById("MAICgregatorToolbarButton");
        buttonNode.style.listStyleImage = buttonStyle;
    }

    MAICgregator.previousState = currentState;
    MAICgregator._savePreferences();
}
