window.onload = initialize;

// global request variable
var request;

// Initialize on window load
function initialize() {
    // Get our search button and setup an event listener
    selectNode = document.getElementById("SchoolSelect");
    if (selectNode != null) {
        //selectNode.addEventListener("change", selectItemSelected, false);
        selectNode.onchange = selectItemSelected;
    }
	request = null;
	createRequest();	


    // Setup our request object
}

function selectItemSelected() {
	//if (this.keyCode == 8) return;
	var url="http://maicgregator.org/MAICgregator/Aggregate/" + escape(this.value) + "/TrusteeRelationshipSearch";
 
	request.open("GET",url,true);
	request.onreadystatechange = processTrustees;
	request.send(null);
    
    document.getElementById("message").innerHTML = "Searching for trustees...";
}

/*
 *
 * Actually process the results of the AJAX query
 *
 */
function processTrustees() {

	if (request.readyState < 4)  {
		return;
    } else {
        document.getElementById("message").innerHTML = "Searching complete.";
    }

	trustees = request.responseXML;
    trusteeResultsNode = trustees.getElementsByTagName("TrusteeRelationshipSearch")[0];

    schoolSelectNode = document.getElementById("SchoolSelect");
    schoolSelectNode.disabled = "disabled";

    trusteeResults = trusteeResultsNode.firstChild.nodeValue;
    trusteeResults = trusteeResults.split("\n");
    if (trusteeResults[1] == "None") {
        fieldsetNode = document.getElementById("TrusteeInfoFieldset");
        fieldsetNode.style.display = "block";
        buttonNode = document.getElementById("submitTrusteeInfo");
        buttonNode.onclick = processInfo;

    } else {
        trusteeSelectNode = document.getElementById("TrusteeSelect");
    
        for (index in trusteeResults) {
            trustee = trusteeResults[index].split("\t");
            optionNode = document.createElement("option");
            optionNode.value = trustee[0].replace(/ /g, "");
            optionNode.appendChild(document.createTextNode(trustee[0]));
            trusteeSelectNode.appendChild(optionNode);
        }
        fieldsetNode = document.getElementById("TrusteeUpdateInfoFieldset");
        fieldsetNode.style.display = "block";
        buttonNode = document.getElementById("submitTrusteeInfoUpdate");
        buttonNode.onclick = processUpdateInfo;

    }

}

function processUpdateInfo() {
    hostname = document.getElementById("SchoolSelect");
    hostname = hostname.value;
    trusteeURL = document.getElementById("trusteeURL");
    trusteeURL = trusteeURL.value;
    trusteeBio = document.getElementById("trusteeBio");
    trusteeBio = trusteeBio.value;
    trusteeResource = document.getElementById("TrusteeSelect");
    trusteeResource = trusteeResource.value;
    human = document.getElementById("humanUpdateInfo");
    // Wow, this is an equaion...programming using CS and web standards really gets you sometimes...
    human = human.value;

    params = "hostname=" + escape(hostname) + "&trusteeResource=" + escape(trusteeResource) + "&trusteeURL=" + escape(trusteeURL) + "&trusteeBio=" + escape(trusteeBio) + "&human=" + escape(human);
    url = "http://maicgregator.org/UpdateTrusteeInfo";
    request.open("POST", url, true);

    //Send the proper header information along with the request
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("Content-length", params.length);
    request.setRequestHeader("Connection", "close");

    request.send(params);
    request.onreadystatechange = doneUpdateInfo;
}

function processInfo() {
    hostname = document.getElementById("SchoolSelect");
    hostname = hostname.value;
    trusteeInfo = document.getElementById("trusteeInfo");
    trusteeInfo = trusteeInfo.value;
    human = document.getElementById("humanInfo");
    // Wow, this is an equaion...programming using CS and web standards really gets you sometimes...
    human = human.value;

    // This really needs to be done using an AJAX post request...
    params = "hostname=" + escape(hostname) + "&trusteeInfo=" + escape(trusteeInfo) + "&human=" + escape(human);
    url = "http://maicgregator.org/UpdateTrusteeInfo";
    request.open("POST", url, true);
    //Send the proper header information along with the request
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    request.setRequestHeader("Content-length", params.length);
    request.setRequestHeader("Connection", "close");

    request.send(params);
    request.onreadystatechange = doneUpdateInfo;
}

function doneUpdateInfo() {

	if (request.readyState < 4)  {
		return;
    } else {
        response = request.responseText;
        if (response == "NotHuman") {
            document.getElementById("message").innerHTML = "Need to enter in the name of the site...think \"maicgregator\".";

        } else {
            document.getElementById("message").innerHTML = "Trustee information update complete; thanks!";

        }
        //document.getElementById("TrusteeUpdateInfoFieldset").style.display = "none";
        //document.getElementById("TrusteeSchoolNames").style.display = "none";
    }
}

function createRequest() {

	try {
		request = new XMLHttpRequest();
	} catch (trymicrosoft) {
		try {
			request = new ActiveXObject("Msxml2.XMLHTTP");
		} catch (othermicrosoft) {
			try {
				request = new ActiveXObject("Microsoft.XMLHTTP");
			} catch (failed) {
				request = null;
			}
		}
	}
	
	if (request == null) {
		alert("Error creating request object!");
	}

}

// Empty function for no results
function doNothing() {return false;}

function trim(str)
{
  return str.replace(/^\s+|\s+$/g, '')
};
