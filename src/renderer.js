//------------------------------------------------------------------------------------------------------------------------------------------
// NVMe Info - electron GUI front end for nvme command line utility - Renderer Script
//------------------------------------------------------------------------------------------------------------------------------------------
// Copyright(c) 2021 Joseph Jones
//
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation 
// files(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, 
// merge, publish, distribute, sublicense, and /or sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions :
//
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES 
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
// LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR 
// IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
//------------------------------------------------------------------------------------------------------------------------------------------
"use strict";

unhandled({ logger: error => { mainProcess.unhandledFatalError(error) }});
//------------------------------------------------------------------------------------------------------------------------------------------
// First setup the logging with my preferences for any debug issues
// By default, it writes logs to the following locations:
//    on Linux: ~/.config/{app name}/logs/{process type}.logc
//    on macOS: ~/Library/Logs/{app name}/{process type}.log
//    on Windows: %USERPROFILE%\AppData\Roaming\{app name}\logs\{process type}.log
//------------------------------------------------------------------------------------------------------------------------------------------
rlog.variables.label = 'renderer.js';
rlog.transports.file.maxSize = 131072;
rlog.transports.file.getFile();
rlog.info("renderer started");
//------------------------------------------------------------------------------------------------------------------------------------------
// Setup custom title bar
//------------------------------------------------------------------------------------------------------------------------------------------
document.title = mainProcess.getTitle();
new customTitlebar.Titlebar({
    backgroundColor: customTitlebar.Color.fromHex('#0c4080'),
    titleHorizontalAlignment: "left",
    unfocusEffect: false,
    shadow: true,
    menu: null
});
//------------------------------------------------------------------------------------------------------------------------------------------
// Setup vars and constants
//------------------------------------------------------------------------------------------------------------------------------------------
var nvmeAll = [];
var nvmeSummary = [];
var nvmeSmart = [];
var nvmeInfoJson = [];

const fileIcon  = '<i style="float:right;padding-left: 10px; padding-right:10px; line-height: 30px; font-size:16px; " class="fas fa-file"></i>';
const caretDown = '<i style="float:right;padding-left: 10px; padding-right:10px; line-height: 28px; font-size:24px;" class="fas fa-caret-down"></i>';
var summaryFilterArray = mainProcess.getViewFilter('SUMMARY.filter.json');
var allFilterArray     = mainProcess.getViewFilter('ALL.filter.json');
var smartFilterArray   = mainProcess.getViewFilter('SMART.filter.json');
const platform           = mainProcess.getPlatform();
// ------------------------------------------------------------------------------------
// Misc Functions  
// ------------------------------------------------------------------------------------
document.getElementById("app-logs").addEventListener("click", function () { mainProcess.showAppLogs();})
document.getElementById("help").addEventListener("click",     function () { mainProcess.help();})
 
const setActivePage = (sidebarItem,container) => {
    rlog.verbose("Setting active page to: "  +  sidebarItem.id)
    let activeSidebars = document.getElementsByClassName("sidebar-active");
    let allPages = document.getElementsByClassName("page-container");
    for (let i = 0; i < allPages.length; i++)          { allPages[i].style.display = "none"; }
    for (let i = 0; i < activeSidebars.length; i++)    { activeSidebars[i].className = activeSidebars[i].className.replace("sidebar-active", "");}
    sidebarItem.className += " sidebar-active";
    container.style.display = "block";     	
}

const clearDashboardResults = () => {
    dashboardHasData = false
    dashboardTables.style.display    = "none";  
}

const clearReadResults = () => {
    nvmeSummary = [];
    nvmeSmart = [];
    nvmeAll = [];
    readinfoData = [];

    readHasData = false;
    readinfoTable.style.display = "none";
    readinfoBanner.style.display = "none";
 
}

const clearCompareResults = () => {
    compareinfoData = [];
    compareHasData = false;
    compareinfoBanner.style.display = "none";
}
const clearVerifyResults = () => {
    verifyinfoData = [];
    verifyHasData  = false;
    verifyinfoBanner.style.display = "none";
}
const clearResults = () => {	 
    rlog.verbose("Clearing all results");
    clearDashboardResults();
    clearReadResults();
    clearCompareResults();
    clearVerifyResults();
}
// ------------------------------------------------------------------------------------
//  Settings
// ------------------------------------------------------------------------------------
var appSettings = mainProcess.getSettings();

document.getElementById("restore-settings").addEventListener("click", function () { mainProcess.setDefaultSettings(); })
document.getElementById("log-path").addEventListener("click",         function () { mainProcess.changeLogPath(); })

// document.getElementById("view-filter-path").addEventListener("click", function () { mainProcess.changeFilterPath(); })

document.getElementById("log-delete-days").addEventListener("change", function () { 
    appSettings.logDayIndex = this.selectedIndex;
    mainProcess.changeSettings(appSettings);
})
document.getElementById("settings").addEventListener("click", function () { 
    setActivePage(document.getElementById("settings"), document.getElementById("settings-container"));
})
const updateSettingsPage = (settings) => {
    appSettings = settings;
    document.getElementById("log-delete-days").selectedIndex = appSettings["logDayIndex"];
    document.getElementById("log-path").innerText            = appSettings["appLogPath"];
    document.getElementById("view-filter-path").innerText    = appSettings["appViewFilterPath"];
    document.getElementById("nvmecmd-path").innerText        = appSettings["nvmecmdPath"];
    rlog.info("Updated settings");
    rlog.info(appSettings);
}
preloadIpc.on('settings', (event,settings) => { updateSettingsPage(settings); })
updateSettingsPage(appSettings);
// ------------------------------------------------------------------------------------
//  Dashboard
// ------------------------------------------------------------------------------------
const dashboardSidebar   = document.getElementById("sidebar-dashboard");
const dashboardTables    = document.getElementById("dashboard-tables");
const dashboardContainer = document.getElementById("dashboard-container");
var   dashboardHasData   = false
const viewDashboard = () => {  
    setActivePage(dashboardSidebar,dashboardContainer);
    if (initialized) {
        if (dashboardHasData === false) {
            let drive = document.getElementById('db-drive-info-select').textContent.split(" ")[1];
            runDashboardInfo(drive);
        }
    }
    else {
        runDashboardInfo('*');
    }
}
const runDashboardInfo = (drive) => {  
    rlog.verbose("Getting dashboard info on drive " + drive);
    clearDashboardResults();
  //  readinfoRead.disabled = true;
 //   readinfoLogs.disabled = true;
  //  readinfoSearch.disabled = true;
 //   disableActiveComboButton();
	mainProcess.runNvmecmd('Dashboard',[drive]);
}
dashboardSidebar.addEventListener("click",  function () { viewDashboard(); })
// ------------------------------------------------------------------------------------
//  Read Info page 
// ------------------------------------------------------------------------------------
const readinfoContainer = document.getElementById("readinfo-container");
const readinfoSearch    = document.getElementById("readinfo-search");
const readinfoSidebar   = document.getElementById("sidebar-read-info");
const readinfoRead      = document.getElementById("read-info");
const readinfoLogs      = document.getElementById("readinfo-logs");
const readinfoTable     = document.getElementById("read-info-table");
const readinfoBanner    = document.getElementById("read-info-banner");
const comboSelectButton = document.getElementById("combo-button-select");
const filterArray       = mainProcess.getMenuOptions();

var readinfoLogPath = null;
var readinfoData = [];
var readHasData = false;
var readMessage  = ""
 
readinfoSidebar.addEventListener("click",  function () { viewReadInfo(); })
readinfoRead.addEventListener("click",     function () { runReadInfo( document.getElementById('read-drive-info-select').textContent.split(" ")[1]); })
readinfoLogs.addEventListener("click",     function () { mainProcess.showActiveLogs(readinfoLogPath);});

const viewReadInfo = () => {
    if (readHasData === false) {   
        readinfoRead.disabled = false;
        readinfoLogs.disabled = true;
        readinfoSearch.disabled = true;
        disableActiveComboButton();
        readinfoTable.style.display = "none";
        readinfoBanner.style.display = "none";
    }
    setActivePage(readinfoSidebar, readinfoContainer);
}
 const runReadInfo = (drive) => {  
    rlog.verbose("Request to read info on drive " + drive);
    clearReadResults();
    readinfoRead.disabled = true;
    readinfoLogs.disabled = true;
    readinfoSearch.disabled = true;
    disableActiveComboButton();
	mainProcess.runNvmecmd('ReadInfo',[drive]);
}
document.getElementById("view-summary-info").addEventListener("click",function () { 
    clearActiveComboButton();
    document.getElementById("view-summary-info").className = "combo-button-left btn-active";
    readinfoData = nvmeSummary;
    buildActiveTable(readinfoData,readinfoTable);
    if (readinfoData.length != 0) {
        readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters. "  + readMessage;
    }
})
document.getElementById("view-smart-info").addEventListener("click",function () {  
    clearActiveComboButton();
    document.getElementById("view-smart-info").className = "combo-button-middle btn-active";
    readinfoData = nvmeSmart;
    buildActiveTable(readinfoData,readinfoTable);
    if (readinfoData.length != 0) {
        readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters. "  + readMessage;
    }
})
document.getElementById("view-all-info").addEventListener("click",function () {  
    clearActiveComboButton();
    document.getElementById("view-all-info").className = "combo-button-middle btn-active";
    readinfoData = nvmeAll;
    buildActiveTable(readinfoData,readinfoTable);
    if (readinfoData.length != 0) {
        readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters. "  + readMessage;
    }
})
const getFilterReadInfo = (name) => {
    let data = [];
    let customFileName = name + ".filter.json";
    let FilterArray  = mainProcess.getViewFilter(customFileName);
    for (let parameter of FilterArray["filter"]) {
        let parameterInfo = nvmeInfoJson.nvme.parameters[parameter]
        if (parameterInfo != null) data.push(parameterInfo)
    }
    return data;
}
function clearActiveComboButton() {
    document.getElementById("view-summary-info").classList.remove("btn-active");
    document.getElementById("view-smart-info").classList.remove("btn-active");
    document.getElementById("view-all-info").classList.remove("btn-active");
    if (document.getElementById("combo-button-select-select") != null) {
        document.getElementById("combo-button-select-select").classList.remove("btn-active");
    }
}
function disableActiveComboButton() {
     document.getElementById("view-summary-info").disabled = true;
     document.getElementById("view-smart-info").disabled = true;
     document.getElementById("view-all-info").disabled = true;
     if (document.getElementById("combo-button-select-select") != null) {
         document.getElementById("combo-button-select-select").classList.add("select-disabled");
     }
}
function enableActiveComboButton() {
    document.getElementById("view-summary-info").disabled = false;
    document.getElementById("view-smart-info").disabled = false;
    document.getElementById("view-all-info").disabled = false;
    if (document.getElementById("combo-button-select-select") != null) {
        document.getElementById("combo-button-select-select").classList.remove("select-disabled");
    } 
}
var comboSelect = document.createElement("DIV");
comboSelect.setAttribute("class", "select-selected select-disabled");  //start with it disabled
comboSelect.innerHTML = filterArray[0] + caretDown;
comboSelect.id = "combo-button-select-select";

var comboHolder = document.createElement("DIV");
comboHolder.setAttribute("class", "select-items select-hide");
comboHolder.id = "combo-button-select-holder";

comboSelectButton.appendChild(comboSelect);

for (let index = 0; index < filterArray.length; index++) {
    var filterOption = document.createElement("DIV");
    filterOption.innerHTML = filterArray[index];
    if (index === 0) { filterOption.style.borderTopRightRadius = "4px"; }
    if (index === (filterArray.length - 1)) { filterOption.style.borderBottomRightRadius = "4px"; }

    filterOption.addEventListener("click", function (event) {
        document.getElementById("combo-button-select-select").innerHTML = this.innerHTML + caretDown;
        clearActiveComboButton();
        document.getElementById("combo-button-select-select").className = "select-selected btn-active"
        readinfoData = getFilterReadInfo(this.innerHTML);
        buildActiveTable(readinfoData, readinfoTable);
        if (readinfoData.length != 0) {
            readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters. "  + readMessage;
        }
    });
    comboHolder.appendChild(filterOption);
    rlog.info("Added option " + filterOption.innerHTML);
}
comboSelectButton.appendChild(comboHolder);

comboSelect.addEventListener("click", function (event) {
    event.stopPropagation();

    if (readinfoDriveHolder.classList.contains("select-hide") === false) {
        readinfoDriveSelect.innerHTML = readinfoDriveSelect.innerHTML.replace("caret-up", "caret-down");
        readinfoDriveHolder.classList.add("select-hide");
    }
    this.nextSibling.classList.toggle("select-hide");

    if (this.innerHTML.indexOf("caret-down") === -1) { this.innerHTML = this.innerHTML.replace("caret-up", "caret-down"); }
    else { this.innerHTML = this.innerHTML.replace("caret-down", "caret-up"); }
});
// ------------------------------------------------------------------------------------
//  Compare Info page 
// ------------------------------------------------------------------------------------
const compareinfoContainer = document.getElementById("compareinfo-container");
const compareinfoSearch    = document.getElementById("compare-search");
const compareinfoFileName  = document.getElementById("compare-ref-file");
const compareinfoSidebar   = document.getElementById("sidebar-compare-info");
const compareinfoLogs      = document.getElementById("compare-logs-btn");
const compareinfoRead      = document.getElementById("compare-info");
const compareinfoTable     = document.getElementById("compare-table");
const compareinfoBanner    = document.getElementById("compare-info-banner");
const compareAll           = document.getElementById("compare-all-btn");

var defaultMismatches, allMismatches;
var compareinfoLogPath = null;
var compareHasData = false;
var compareinfoData = [];

compareinfoLogs.addEventListener("click",      function () { mainProcess.showActiveLogs(compareinfoLogPath);})
compareinfoFileName.addEventListener("click",  function () { mainProcess.selectCompareFile(); })
compareinfoSidebar.addEventListener("click",   function () { viewComparePage(); })
compareinfoRead.addEventListener("click",      function () { runCompareInfo( document.getElementById('compare-drive-info-select').textContent.split(" ")[1]); })

const viewComparePage = () => {  
    if (compareinfoFileName.classList.contains("default")) { compareinfoRead.disabled = true; }   
    else                                                   { compareinfoRead.disabled = false; }
    if (compareHasData === false) {
//    if (compareinfoBanner.style.display === "none") {
        compareinfoLogs.disabled = true;
        compareinfoSearch.disabled = true;
        compareinfoBanner.style.display = "none";
        compareinfoTable.style.display = "none";
        compareAll.disabled = true;
    }
    setActivePage(compareinfoSidebar, compareinfoContainer);
}
const runCompareInfo = (drive) => {  
    rlog.verbose("Request to compare info");
   
    clearCompareResults();
    compareinfoRead.disabled = true;
    compareinfoLogs.disabled = true;
    compareinfoSearch.disabled = true;
    compareinfoTable.style.display = "none";
    compareAll.disabled = true;

    mainProcess.runNvmecmd('CompareInfo',[drive, compareinfoFileName.textContent]);
}
compareAll.addEventListener("click", function () {

    if (compareAll.classList.contains("btn-active")) {compareinfoData = defaultMismatches; }
    else                                             {compareinfoData = allMismatches ;}

    compareAll.classList.toggle("btn-active");
    buildActiveTable(compareinfoData,compareinfoTable);
    compareinfoBanner.innerHTML = "Displaying " + compareinfoData.length + " of all " + allMismatches.length + " mismatches";

    if (compareinfoData.length === 0) { 
        compareinfoBanner.style.backgroundColor = "var(--pass-color)";
        compareinfoTable.style.display = "none";
        compareinfoSearch.disabled = true; 
    }
    else                             { 
        compareinfoBanner.style.backgroundColor = "var(--fail-color)";
        compareinfoTable.style.display = "table";
        compareinfoSearch.disabled = false;
    }
})
preloadIpc.on('compare-file', (event, file) => {
    clearCompareResults();
    compareinfoFileName.innerHTML = file + fileIcon;
    compareinfoFileName.classList.remove("default");
    compareinfoRead.disabled = false;
    viewComparePage();
})
// ------------------------------------------------------------------------------------
//  Verify Info page 
// ------------------------------------------------------------------------------------
const verifyinfoContainer = document.getElementById("verifyinfo-container");
const verifyinfoSearch   = document.getElementById("verify-search");
const verifyinfoFileName = document.getElementById("verify-rules-file");
const verifyinfoLogs     = document.getElementById("verify-logs-btn");
const verifyinfoSidebar  = document.getElementById("sidebar-verify-info");
const verifyinfoRead     = document.getElementById("verify-info");
const verifyinfoTable    = document.getElementById("verify-table");
const verifyinfoBanner   = document.getElementById("verify-info-banner");

var verifyinfoLogPath = null;
var verifyinfoData = [];
var verifyHasData = false;

verifyinfoRead.addEventListener("click",    function () { runVerifyInfo( document.getElementById('verify-drive-info-select').textContent.split(" ")[1]); })
verifyinfoSidebar.addEventListener("click", function () { viewVerifyPage();})
verifyinfoLogs.addEventListener("click",    function () { mainProcess.showActiveLogs(verifyinfoLogPath);})
verifyinfoFileName.addEventListener("click",function () { mainProcess.selectRulesFile();})

const viewVerifyPage = () => {  
    if (verifyinfoFileName.classList.contains("default")) { verifyinfoRead.disabled = true; }   
    if (verifyHasData === false) {
 //   if (verifyinfoBanner.style.display === "none") {
        verifyinfoLogs.disabled = true;
        verifyinfoSearch.disabled = true;
        verifyinfoTable.style.display = "none";
    }  
    setActivePage(verifyinfoSidebar, verifyinfoContainer);
}
const runVerifyInfo = (drive) => {  
    rlog.verbose("Request to verify info");

    clearVerifyResults();
    verifyinfoRead.disabled = true;
    verifyinfoLogs.disabled = true;
    verifyinfoSearch.disabled = true;
    verifyinfoTable.style.display = "none";

    mainProcess.runNvmecmd('VerifyInfo',[drive,verifyinfoFileName.textContent]);
}
preloadIpc.on('verify-file', (event, file) => {
    clearVerifyResults();
    verifyinfoFileName.innerHTML = file + fileIcon;
    verifyinfoFileName.classList.remove("default");
    verifyinfoRead.disabled = false;
    viewVerifyPage();
})
// ------------------------------------------------------------------------------------
// Table search and sort routines
// ------------------------------------------------------------------------------------
readinfoSearch.addEventListener("keyup",function () {
    let data = searchActiveTable(readinfoSearch.value, readinfoData)
    buildActiveTable(data,readinfoTable)
     
    readinfoBanner.innerHTML = "Displaying " + data.length + " of " + readinfoData.length + " parameters. " + readMessage;
})
compareinfoSearch.addEventListener("keyup",function () {
    let data = searchActiveTable(compareinfoSearch.value, compareinfoData)
    buildActiveTable(data,compareinfoTable)
    compareinfoBanner.innerHTML = "Displaying " + data.length + " of " + compareinfoData.length + " mismatches";
})
verifyinfoSearch.addEventListener("keyup",function () {
    let data = searchActiveTable(verifyinfoSearch.value, verifyinfoData)
    buildActiveTable(data,verifyinfoTable)
    verifyinfoBanner.innerHTML = "Displaying " + data.length + " of " + verifyinfoData.length + " violations";
})

document.querySelectorAll('.results-table th').forEach(function (header, index) {
    header.addEventListener('click', function () {
        let tableData = readinfoData;
        if (this.parentNode.parentNode.parentNode.id === "compare-table") { tableData = compareinfoData; }
        if (this.parentNode.parentNode.parentNode.id === "verify-table")  { tableData = verifyinfoData; }
        let column = this.dataset.column
        let order = this.dataset.order
        if (order === 'desc') {
            this.dataset.order = "asc";
            tableData = tableData.sort((a, b) => a[column] > b[column] ? 1 : -1)
        } else {
            this.dataset.order = "desc";
            tableData = tableData.sort((a, b) => a[column] < b[column] ? 1 : -1)
        }
        buildActiveTable(tableData, this.parentNode.parentNode.parentNode)
    })
})
function searchActiveTable(value, data) {
    rlog.verbose("searchActiveTable:" + value)
    let startTime = Date.now();

    if (value === "") return data
    value = value.toLowerCase();
    var filteredData = []

    for (var i = 0; i < data.length; i++) {
        let hasValue = false;

        if (data[i].name != undefined && data[i].name.toLowerCase().includes(value))                 { hasValue = true; }
        if (data[i].description != undefined && data[i].description.toLowerCase().includes(value))   { hasValue = true; }
        if (data[i].value != undefined && data[i].value.toLowerCase().includes(value))               { hasValue = true; }
        if (data[i].result != undefined && data[i].result.toLowerCase().includes(value))             { hasValue = true; }
        if (data[i].delta != undefined && data[i].delta.toLowerCase().includes(value))               { hasValue = true; }
        if (data[i].compareValue != undefined && data[i].compareValue.toLowerCase().includes(value)) { hasValue = true; }
   
        if (hasValue) { filteredData.push(data[i]) }
    }
	rlog.verbose("searchViewTable: number of rows returned = " + filteredData.length + " in " +(Date.now() - startTime) / 1000.0  + " seconds"); 
    return filteredData;
}
function buildActiveTable(userData,activeTable) {
    if (userData === null) { rlog.info("Active table id " + activeTable.id + " with size is null"); }
    else                   { rlog.info("Active table id " + activeTable.id + " with size " + userData.length); }
	
    let startTime = Date.now();
    let mystring = "";  // load to string because faster
    var activeTableBody = activeTable.getElementsByTagName('tbody')[0];
    activeTableBody.innerHTML = '';

    rlog.debug("Table before build time " + (Date.now() - startTime) / 1000.0  + " seconds");
    
    if (activeTable.id === 'read-info-table') {
        let filteredData = searchActiveTable(readinfoSearch.value,userData);

		rlog.debug(filteredData.length);
		for (let i = 0; i < filteredData.length; i++) {
	        mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>                 
                <td>${filteredData[i].description}</td>
                </tr>`						 
		}
	}
	else if (activeTable.id === 'compare-table') {
        let filteredData = searchActiveTable(compareinfoSearch.value,userData);

		for (let i = 0; i < filteredData.length; i++) {
            mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>                 
                <td>${filteredData[i].compare_value}</td>
                <td>${filteredData[i].delta}</td>
                </tr>`
        }
	}
	else if (activeTable.id === 'verify-table') {
        let filteredData = searchActiveTable(verifyinfoSearch.value,userData);

		for (let i = 0; i < filteredData.length; i++) {
            mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>                 
                <td>${filteredData[i].rule}</td>
                </tr>`
        }
    }
	activeTableBody.innerHTML = mystring;
	rlog.debug("Table build time " + (Date.now() - startTime) / 1000.0  + " seconds");  
}
//------------------------------------------------------------------------------------------------------------------------------------------
//Functions to comm with main process.  preloadIpc defined in preload script
//------------------------------------------------------------------------------------------------------------------------------------------
var readinfoDriveHolder, readinfoDriveSelect, initialized = false

preloadIpc.on('nvmecmd-end', (event, code, nvmeMessage, nvmecmdRunTime, nvmecmdInfo, nvmecmdLogPath) => {

    rlog.info("nvmecmd-end called");

    nvmeInfoJson = nvmecmdInfo;

    const activePageId    =  document.getElementsByClassName("sidebar-active")[0].id;

    if (initialized === false) {

        if (code == -1) {
            if (platform != "win32") {
                mainProcess.fatalError("Initial nvmecmd read failed\nVerify permissions on nvmecmd, see install directions\n\n" + nvmeMessage);
            }
            else {
                mainProcess.fatalError("Initial nvmecmd read failed: \n\n" + nvmeMessage);
            }
        }
        else {
            if (nvmeInfoJson._metadata.system['nvme list'].length < 1) {
                mainProcess.fatalError("Initialization failed: \n\nNo NVMe drives found");
            }

            let driveArray = nvmeInfoJson._metadata.system['nvme list']
            for (let driveSelect of document.getElementsByClassName("drive-select")) {

                var currentSelection = document.createElement("DIV");
                currentSelection.setAttribute("class", "select-selected drive-select-type");
                currentSelection.innerHTML = driveArray[0] + caretDown;
                currentSelection.id = driveSelect.id + "-select";
                driveSelect.appendChild(currentSelection);

                var optionHolder = document.createElement("DIV");
                optionHolder.setAttribute("class", "select-items select-hide drive-holder-type");
                optionHolder.id = driveSelect.id + "-holder";
                optionHolder.style.boxShadow = "0 0 4px var(--darkestblue)";

                for (let index = 0; index < driveArray.length; index++) {

                    var driveOption = document.createElement("DIV");
                    driveOption.innerHTML = driveArray[index];
                    if (index === 0) {
                        driveOption.style.borderTopRightRadius = "4px";
                        driveOption.style.borderTopLeftRadius = "4px";
                    }
                    if (index === (driveArray.length - 1)) {
                        driveOption.style.borderBottomRightRadius = "4px";
                        driveOption.style.borderBottomLeftRadius = "4px";
                    }

                    driveOption.addEventListener("click", function (e) {
                        let driveSelectSelected = document.getElementsByClassName("select-selected drive-select-type");
                        rlog.info("Drive change to " + this.innerHTML)
                        for (let i = 0; i < driveSelectSelected.length; i++) {
                            driveSelectSelected[i].innerHTML = this.innerHTML + caretDown;
                        }
                        let drive = this.textContent.split(" ")[1];
                        clearResults();

                        if (this.parentNode.id === "db-drive-info-holder") { runReadInfo(drive); }
                        else if (this.parentNode.id === "read-drive-info-holder") {runReadInfo(drive); }
                        else if (this.parentNode.id === "compare-drive-info-holder") {
                            if (compareinfoRead.disabled) { viewComparePage(); }
                            else                          { runCompareInfo(drive); }
                        }
                        else { 
                            if (verifyinfoRead.disabled)  { viewVerifyPage(); }
                            else                          { runVerifyInfo(drive); }
                        }
                    });
                    optionHolder.appendChild(driveOption);
                }
                driveSelect.appendChild(optionHolder);

                currentSelection.addEventListener("click", function (event) {
                    event.stopPropagation();

                    if (comboHolder.classList.contains("select-hide") === false) {
                        comboSelect.innerHTML = comboSelect.innerHTML.replace("caret-up", "caret-down");
                        comboHolder.classList.add("select-hide");
                    }
                    this.nextSibling.classList.toggle("select-hide");

                    if (this.innerHTML.indexOf("caret-down") === -1) { this.innerHTML = this.innerHTML.replace("caret-up", "caret-down"); }
                    else { this.innerHTML = this.innerHTML.replace("caret-down", "caret-up"); }
                });
            }
            readinfoDriveHolder = document.getElementById("read-drive-info-holder");
            readinfoDriveSelect = document.getElementById("read-drive-info-select");
            initialized = true;
        }
    }
    if (activePageId === 'sidebar-dashboard') {
        try { 
            dashboardHasData = true;

            rlog.debug("Getting dashboard info")

            document.getElementById("db-health").textContent = "DRIVE HEALTH : " + nvmeInfoJson.nvme['health status'];  
     
            if       (nvmeInfoJson.nvme['health status'] === "GOOD" )     document.getElementById("db-health").style.backgroundColor =  "var(--good-color)";  
            else if  (nvmeInfoJson.nvme['health status'] === "SUSPECT")  document.getElementById("db-health").style.backgroundColor = "var(--suspect-color)";
            else    document.getElementById("db-health").style.backgroundColor =  "var(--poor-color)";

            document.getElementById("db-critical-warnings").textContent = nvmeInfoJson.nvme.parameters['Critical Warnings']['value']; 
            document.getElementById("db-media-errors").textContent = nvmeInfoJson.nvme.parameters['Media and Data Integrity Errors']['value']; 
            document.getElementById("db-self-tests-errors").textContent = nvmeInfoJson.nvme.parameters['Number Of Failed Self-Tests']['value']; 

            document.getElementById("db-percentage-used").textContent = nvmeInfoJson.nvme.parameters['Percentage Used']['value']; 
            document.getElementById("db-available-spare").textContent = nvmeInfoJson.nvme.parameters['Available Spare']['value']; 
            document.getElementById("db-poweron-hours").textContent = nvmeInfoJson.nvme.parameters['Power On Hours']['value']; 
            document.getElementById("db-data-read").textContent = nvmeInfoJson.nvme.parameters['Data Read']['value']; 
            document.getElementById("db-data-written").textContent = nvmeInfoJson.nvme.parameters['Data Written']['value']; 

            document.getElementById("db-temp-health").textContent = "THERMAL HEALTH : " + nvmeInfoJson.nvme['temp status'];  
     
            if       (nvmeInfoJson.nvme['temp status'] === "GOOD" )     document.getElementById("db-temp-health").style.backgroundColor = "var(--good-color)";  
            else if  (nvmeInfoJson.nvme['temp status'] === "SUSPECT") document.getElementById("db-temp-health").style.backgroundColor = "var(--suspect-color)";
            else     document.getElementById("db-temp-health").style.backgroundColor = "var(--poor-color)";

            document.getElementById("db-temperature").textContent = nvmeInfoJson.nvme.parameters['Composite Temperature']['value']; 

            // Host controlled throttling may not be supported
            rlog.verbose("Adding throttle information")
         
            if (nvmeInfoJson.nvme.parameters['Host Controlled Thermal Management (HCTMA)']['value'] == "Supported") {
                
                if (nvmeInfoJson.nvme.parameters['Thermal Management Temperature 1 (TMT1)']['value'] == "Disabled") {
                    document.getElementById("tmt1").textContent = "Minimum Throttle";
                    document.getElementById("db-min-throttle").textContent = "Disabled";   
                }
                else {
                    document.getElementById("tmt1").textContent = "Minimum Throttle at " + nvmeInfoJson.nvme.parameters['Thermal Management Temperature 1 (TMT1)']['value'];
                    let tmin = nvmeInfoJson.nvme.parameters['Thermal Management Temperature 1 Time']['value'].split(' ')[0].replace(',','');
                    document.getElementById("db-min-throttle").textContent =  (parseFloat(tmin) / 60.0).toFixed(1)  + " Minutes";
                }
                if (nvmeInfoJson.nvme.parameters['Thermal Management Temperature 2 (TMT2)']['value'] == "Disabled") {
                    document.getElementById("tmt2").textContent = "Medium Throttle";
                    document.getElementById("db-med-throttle").textContent = "Disabled";   
                }
                else {
                    document.getElementById("tmt2").textContent = "Medium Throttle at " + nvmeInfoJson.nvme.parameters['Thermal Management Temperature 2 (TMT2)']['value'];
                    let tmed = nvmeInfoJson.nvme.parameters['Thermal Management Temperature 2 Time']['value'].split(' ')[0].replace(',',''); 
                    document.getElementById("db-med-throttle").textContent =  (parseFloat(tmed) / 60.0).toFixed(1)  + " Minutes";
                }
            }
            else { 
                document.getElementById("tmt1").textContent = "Minimum Throttle";
                document.getElementById("db-min-throttle").textContent = "Not Supported";
                document.getElementById("tmt2").textContent = "Medium Throttle";
                document.getElementById("db-med-throttle").textContent = "Not Supported";   
            }
 
            rlog.info(".")

            document.getElementById("twarn").textContent = "Heavy Throttle at " + nvmeInfoJson.nvme.parameters['Warning Composite Temperature Threshold (WCTEMP)']['value'];
            document.getElementById("tcrit").textContent = "Maximum Throttle at " + nvmeInfoJson.nvme.parameters['Critical Composite Temperature Threshold (CCTEMP)']['value'];

            document.getElementById("db-hi-throttle").textContent = nvmeInfoJson.nvme.parameters['Warning Composite Temperature Time']['value'] + "utes"; 
            document.getElementById("db-max-throttle").textContent = nvmeInfoJson.nvme.parameters['Critical Composite Temperature Time']['value'] + "utes"; 
            rlog.info(".")

            document.getElementById("db-supplier").textContent = nvmeInfoJson.nvme.parameters['Controller Vendor']['value']; 
            document.getElementById("db-model").textContent = nvmeInfoJson.nvme.parameters['Model Number (MN)']['value']; 
            document.getElementById("db-size").textContent = nvmeInfoJson.nvme.parameters['Size']['value']; 
            document.getElementById("db-serial").textContent = nvmeInfoJson.nvme.parameters['Serial Number (SN)']['value']; 
            document.getElementById("db-firmware").textContent = nvmeInfoJson.nvme.parameters['Firmware Revision (FR)']['value']; 
            document.getElementById("db-location").textContent = "PCI " + nvmeInfoJson.nvme.parameters['PCI Location']['value']; 

            document.getElementById("db-read-status").textContent = nvmeInfoJson['_metadata']['read status']; 

            if  (nvmeInfoJson['_metadata']['read status'] === "All commands passed" ) document.getElementById("db-info").style.backgroundColor =  "var(--good-color)";  
            else  document.getElementById("db-info").style.backgroundColor =  "var(--suspect-color)";

            dashboardTables.style.display    = "block";  
        }
        catch(error) {
            mainProcess.fatalError("Could not parse nvmecmd nvme.info.json file.  Error: " + error.message);
        } 
    }
    else if (activePageId === 'sidebar-read-info') {
        readHasData = true;

        dashboardTables.style.display    = "block";  
        readinfoLogPath =  nvmecmdLogPath;
        readinfoBanner.style.display  = "block";
        readinfoRead.disabled   = false;
        readinfoLogs.disabled   = false;

        if (nvmeMessage != null) {
            readinfoBanner.innerHTML = nvmeMessage;
            readinfoBanner.style.backgroundColor = "var(--fail-color)";
        }
        else if ((code === 0) || (code === 21)) { 

            for (let parameter of allFilterArray["filter"]) {
                let parameterInfo = nvmeInfoJson.nvme.parameters[parameter]
                if (parameterInfo != null) nvmeAll.push(parameterInfo)
            }
            for (let parameter of summaryFilterArray["filter"]) {
                let parameterInfo = nvmeInfoJson.nvme.parameters[parameter]
                if (parameterInfo != null) nvmeSummary.push(parameterInfo)
            }
            for (let parameter of smartFilterArray["filter"]) {
                let parameterInfo = nvmeInfoJson.nvme.parameters[parameter]
                if (parameterInfo != null) nvmeSmart.push(parameterInfo)
            }
            if (document.getElementById("view-summary-info").classList.contains('btn-active')) {
                readinfoData = nvmeSummary;
            }
            else if (document.getElementById("view-smart-info").classList.contains('btn-active')) {
                readinfoData = nvmeSmart;
            }
            else if (document.getElementById("combo-button-select-select").classList.contains('btn-active')) { 
                readinfoData = getFilterReadInfo( document.getElementById("combo-button-select-select").textContent );
            }
            else {
                readinfoData = nvmeAll;
            }
            
            if (code === 0) {
                readMessage =  " Read in " + nvmecmdRunTime + " seconds." ;
                readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters." + readMessage;
                readinfoBanner.style.backgroundColor = "var(--pass-color)";
            }
            else {
                readMessage =  " Read in " + nvmecmdRunTime + " seconds. " + nvmeInfoJson['_metadata']['read status']  ;
                readinfoBanner.innerHTML = "Displaying " + readinfoData.length + " of " + nvmeAll.length + " parameters." + readMessage; ;
                readinfoBanner.style.backgroundColor = "var(--warn-color)";         
            }
            
            enableActiveComboButton();
            buildActiveTable(readinfoData,readinfoTable);
            readinfoSearch.disabled = false;
            readinfoTable.style.display = "table"; 
        }
        else  {
            readMessage = "Read information failed to complete with code " + code + " in " + nvmecmdRunTime + " seconds"; 
            readinfoBanner.innerHTML = readMessage;
            readinfoBanner.style.backgroundColor = "var(--fail-color)";
        }  
        rlog.info("Read Info Result: " +  readinfoBanner.innerHTML);
    }
    else if (activePageId === 'sidebar-compare-info') {
        compareHasData = true;

        compareinfoLogPath =  nvmecmdLogPath;
        compareinfoBanner.style.display  = "block";  
        compareinfoRead.disabled   = false;
        compareinfoLogs.disabled   = false;
        compareAll.disabled = false;

        if (nvmeMessage != null) {
            compareinfoBanner.innerHTML = nvmeMessage;
            compareinfoBanner.style.backgroundColor = "var(--fail-color)";
        }
        else if (nvmeInfoJson.hasOwnProperty('compare mismatches') == false || nvmeInfoJson.hasOwnProperty('all mismatches') == false) {
            compareinfoBanner.innerHTML = "Failed to compare.  nvmecmd nvme.info.json file missing 'compare mismatches' and/or 'all mismatches'.  Check Logs";
            compareinfoBanner.style.backgroundColor = "var(--fail-color)";
        }
        else {
            defaultMismatches = nvmeInfoJson['compare mismatches'];
            allMismatches     = nvmeInfoJson['all mismatches'];
            
            if (compareAll.classList.contains("btn-active")) { compareinfoData = allMismatches; }
            else                                             { compareinfoData = defaultMismatches; }

            if (allMismatches.length === 0) {
                compareinfoBanner.innerHTML = "Compare Info found no mismatches in " + nvmecmdRunTime + " seconds ";
                compareinfoBanner.style.backgroundColor = "var(--pass-color)";
            }
            else if (compareinfoData.length === 0) { 
                compareinfoBanner.innerHTML = "Displaying " + compareinfoData.length + " of all " + allMismatches.length + " mismatches read in " + nvmecmdRunTime + " seconds";
                compareinfoBanner.style.backgroundColor = "var(--pass-color)";
            }
            else  {
                buildActiveTable(compareinfoData,compareinfoTable);
                compareinfoBanner.innerHTML = "Displaying " + compareinfoData.length + " of all " + allMismatches.length + " mismatches read in " + nvmecmdRunTime + " seconds";
                compareinfoBanner.style.backgroundColor = "var(--fail-color)";
                compareinfoTable.style.display = "table";  
                compareinfoSearch.disabled = false;      
            }
        }
        rlog.info("Compare Info Result: " +  compareinfoBanner.innerHTML);
    }
    else if (activePageId === 'sidebar-verify-info') {
        verifyHasData = true;

        verifyinfoLogPath =  nvmecmdLogPath;
        verifyinfoRead.disabled   = false;
        verifyinfoLogs.disabled   = false;
        verifyinfoBanner.style.display  = "block";

        if (nvmeMessage != null) {
            verifyinfoBanner.innerHTML = nvmeMessage;
            verifyinfoBanner.style.backgroundColor = "var(--fail-color)";
        }
        else if (nvmeInfoJson.hasOwnProperty('rule violations') == false) {
            verifyinfoBanner.innerHTML = "Failed to verify.  nvmecmd nvme.info.json file missing 'rule violations'.  Check Logs";
            verifyinfoBanner.style.backgroundColor = "var(--fail-color)";
        }
        else if (code === 0) { 
            verifyinfoBanner.innerHTML = "Verify found NO rule violations in " + nvmecmdRunTime + " seconds ";
            verifyinfoBanner.style.backgroundColor = "var(--pass-color)";
        }
        else  {
            verifyinfoData  = nvmeInfoJson['rule violations']
            buildActiveTable(verifyinfoData,verifyinfoTable);
            verifyinfoBanner.innerHTML = "Displaying " + verifyinfoData.length + " rule violations in " + nvmecmdRunTime + " seconds";
            verifyinfoBanner.style.backgroundColor = "var(--fail-color)";
            verifyinfoTable.style.display = "table";  
            verifyinfoSearch.disabled = false;           
        }
        rlog.info("Verify Info Result: " +  verifyinfoBanner.innerHTML);
    }
});
document.onclick = function() {
    for (let select of document.getElementsByClassName("drive-select-type")) {
        select.innerHTML = select.innerHTML.replace("caret-up", "caret-down");
    }
    for (let holder of document.getElementsByClassName("drive-holder-type")) {
        holder.classList.add("select-hide");
    }
    comboSelect.innerHTML = comboSelect.innerHTML.replace("caret-up", "caret-down");
    comboHolder.classList.add("select-hide");
}
// ------------------------------------------------------------------------------------
//  Start the app on the dashboard
// ------------------------------------------------------------------------------------
viewDashboard();