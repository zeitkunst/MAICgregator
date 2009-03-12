window.addEventListener("load", function() { populatePreferences(); }, false);

function populatePreferences() {
    var checkbox = null;
    var radiogroup = null;

    // Set radiogroup options
    radiogroup = document.getElementById("MAICgregatorInterject");
    if (radiogroup != null) {
        if (MAICgregator.interject == "All") {
            radiogroup.selectedIndex = 0;
        } else if (MAICgregator.interject == "Home") {
            radiogroup.selectedIndex = 1;
        } else if (MAICgregator.interject == "News") {
            radiogroup.selectedIndex = 2;
        }
    }

    // Set checkbox options
    checkbox = document.getElementById("DoDBR");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.DoDBR);

    checkbox = document.getElementById("DoDSTTR");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.DoDSTTR);

    checkbox = document.getElementById("DHS");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.DHS);

    checkbox = document.getElementById("GoogleNewsSearch");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.GoogleNewsSearch);

    checkbox = document.getElementById("PRNewsSearch");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.PRNewsSearch);

    checkbox = document.getElementById("TrusteeRelationshipSearch");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.TrusteeRelationshipSearch);

    checkbox = document.getElementById("randomize");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.randomize);

    checkbox = document.getElementById("infoStatus");
    if (checkbox != null)
        checkbox.setAttribute("checked", MAICgregator.infoStatus);


}

function savePreferences() {
    var appcontent = document.getElementById("appcontent");

    var checkbox = null;
    var radiogroup = null;

    // Set radiogroup options
    radiogroup = document.getElementById("MAICgregatorInterject");
    if (radiogroup != null) {
        var index = radiogroup.selectedIndex;

        if (index == 0) {
            MAICgregator.interject = "All";
        } else if (index == 1) {
            MAICgregator.interject = "Home";
        } else if (index == 2) {
            MAICgregator.interject = "News";
        }
    }

    // Set checkbox options
    checkbox = document.getElementById("DoDBR");
    if (checkbox != null)
        MAICgregator.DoDBR = checkbox.checked;

    checkbox = document.getElementById("DoDSTTR");
    if (checkbox != null)
        MAICgregator.DoDSTTR = checkbox.checked;

    checkbox = document.getElementById("DHS");
    if (checkbox != null)
        MAICgregator.DHS = checkbox.checked;

    checkbox = document.getElementById("GoogleNewsSearch");
    if (checkbox != null)
        MAICgregator.GoogleNewsSearch = checkbox.checked;

    checkbox = document.getElementById("PRNewsSearch");
    if (checkbox != null)
        MAICgregator.PRNewsSearch = checkbox.checked;

    checkbox = document.getElementById("TrusteeRelationshipSearch");
    if (checkbox != null)
        MAICgregator.TrusteeRelationshipSearch = checkbox.checked;

    checkbox = document.getElementById("randomize");
    if (checkbox != null)
        MAICgregator.randomize = checkbox.checked;

    checkbox = document.getElementById("infoStatus");
    if (checkbox != null)
        MAICgregator.infoStatus = checkbox.checked;

    MAICgregator._savePreferences();
}
