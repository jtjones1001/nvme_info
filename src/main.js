//------------------------------------------------------------------------------------------------------------------------------------------
// NVMe Info - electron GUI front end for nvme command line utility - Main Script
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
// The following Nodejs add-ins were used in this project:
//	  custom-electron-titlebar 			https://www.npmjs.com/package/custom-electron-titlebar
//	  dateformat				        https://www.npmjs.com/package/dateformat
//	  electron-log				        https://www.npmjs.com/package/electron-log
//	  electron-unhandled			    https://www.npmjs.com/package/electron-unhandled
// 	  find-remove				        https://www.npmjs.com/package/find-remove
//
// Font Awesome fonts are used in this project: https://fontawesome.com/
//------------------------------------------------------------------------------------------------------------------------------------------
"use strict";

const betaTag = " ** BETA **";
//------------------------------------------------------------------------------------------------------------------------------------------
// First setup the logging with my preferences for any debug issues. By default, it writes logs to the following locations:
//    on Linux: ~/.config/{app name}/logs/{process type}.log
//    on macOS: ~/Library/Logs/{app name}/{process type}.log
//    on Windows: %USERPROFILE%\AppData\Roaming\{app name}\logs\{process type}.log
//------------------------------------------------------------------------------------------------------------------------------------------
const { app, BrowserWindow, shell, dialog } = require('electron')
const log = require('electron-log');       

log.variables.label = 'main.js';
log.transports.console.format = '{h}:{i}:{s}.{ms} [{level}] {label} : {text}';
log.transports.file.maxSize = 131072;
log.transports.file.getFile();

if (app.isPackaged) {
  log.transports.console.level = 'debug';  //start with debug then go to info after some proving time
  log.transports.file.level = 'debug';   
}
else {
  log.transports.console.level = 'verbose';  
  log.transports.file.level = 'verbose'; 
} 
//------------------------------------------------------------------------------------------------------------------------------------------
// Setup error handlers
//------------------------------------------------------------------------------------------------------------------------------------------
const unhandled = require('electron-unhandled');
const path  = require('path');
const appInternalLogs = path.join(app.getPath("userData"), "logs");
 
const warning = exports.warning = (msg) => {
    dialog.showMessageBoxSync({type: "warning", message: msg, title: "NVMeInfo Warning", buttons: ["OK"]});
}

const fatalError = exports.fatalError = (msg) => {
    log.error("NVMeInfo Fatal Error: " + msg);
    dialog.showErrorBox("NVMeInfo Fatal Error",  msg + "\n\nSend logs to developer, click OK to view logs");
    if (process.platform === 'linux') { shell.showItemInFolder(appInternalLogs + "/*"); }
    else                              { shell.openPath(appInternalLogs); }  
    app.exit(1);
}
const unhandledFatalError = exports.unhandledFatalError = (error_msg) => {
    log.error("Unhandled Fatal Error called");
    fatalError(error_msg.stack);
}
unhandled({ logger: error => { unhandledFatalError(error) } });
//------------------------------------------------------------------------------------------------------------------------------------------
// Load the rest of the libraries
//------------------------------------------------------------------------------------------------------------------------------------------
const fs    = require('fs');
const os    = require('os');
const dateFormat  = require('dateformat');  
const findRemoveSync  = require('find-remove')
const { spawn  } = require('child_process'); 
//------------------------------------------------------------------------------------------------------------------------------------------
// Log all the info on who is running this and what it is running on
//------------------------------------------------------------------------------------------------------------------------------------------
var rulesPath,cmdPath,basePath,nvmeAppName,osRelease,nvmecmdPath,settingsFile,readCmdFile

if (app.isPackaged) {
    settingsFile = path.join(app.getPath('userData'),"settings.json");
    basePath = path.dirname(app.getPath("exe"));
}
else {
    settingsFile = path.join(__dirname,"settings.json");     
    basePath = path.dirname(__dirname);
}    

if (process.platform === 'win32') {
    osRelease   = "Windows " + os.release();
    nvmeAppName = 'nvmecmd.exe';
    nvmecmdPath = path.join(basePath, 'resources', 'nvmecmd');
    readCmdFile = path.join(basePath, 'resources','nvmecmd','read.cmd.json');
}
else {
    osRelease   =  "linux " + os.release();
    nvmeAppName = './nvmecmd';
    nvmecmdPath = path.join(basePath, 'resources', 'nvmecmd');
    readCmdFile = path.join(basePath, 'resources','nvmecmd','read.cmd.json');
}
rulesPath = nvmecmdPath
cmdPath = nvmecmdPath

log.info(' ');
log.info('-----------------------------------------------------------------------------------------------------');
log.info(app.getName() + ' v' + app.getVersion() + betaTag + ' started');
log.info('-----------------------------------------------------------------------------------------------------');
log.info(' ');
log.info("Hostname:     " + os.hostname());
log.info("Username:     " + os.userInfo().username);
log.info("Process ID:   " + process.pid);
log.info("App Packaged: " + app.isPackaged);
log.info("OS:           " + osRelease);
log.info("Path:         " + basePath);
log.info("nvme app:     " + nvmeAppName);
log.info("nvme path:    " + nvmecmdPath);
log.info("Rules Path:   " + rulesPath);
log.info("Cmd Path:     " + cmdPath);
log.info(' ');
//------------------------------------------------------------------------------------------------------------------------------------------
// Setup the variables and constants
//------------------------------------------------------------------------------------------------------------------------------------------
const nvmecmdTimeoutInMs = 10000;  
const nvmecmdNoDrives = 18;
const nvmecmdExceptionCode = 17;
const nvmecmdUsageError = 16;
const dateFormatString = "yyyy.mm.dd-hh.MM.ss.l";

var appSettings = {
    logDayIndex: 1,
    appViewFilterPath: path.join(basePath, 'resources', 'view_filters'),
    appLogPath: path.join(app.getPath('documents'), app.getName()),
    nvmecmdRulesFilePath: rulesPath,
    nvmecmdCmdFilePath: cmdPath,
    nvmecmdPath: nvmecmdPath
};
 
//------------------------------------------------------------------------------------------------------------------------------------------
// Override default settings with settings.json if exists
//------------------------------------------------------------------------------------------------------------------------------------------
const loadSettingsFile = () => {
    if (fs.existsSync(settingsFile)) {
        try {
            log.info("Reading settings file: " + settingsFile);
            let appSettingsRaw  = fs.readFileSync(settingsFile);
            let appTempSettings = JSON.parse(appSettingsRaw); 
            appSettings = appTempSettings;
            log.info("Settings loaded:");
            log.info(appSettings);
        }
        catch(error) {
            let msg = "Failed to read settings: " + settingsFile + "\n\nApplication settings have been reset to defaults\n\nError message: " + error.message;
            dialog.showMessageBoxSync({type: "warning", message: msg, title: "NVMeInfo Warning", buttons: ["OK"]});
            fs.unlinkSync(settingsFile);
        }
    }
}
//------------------------------------------------------------------------------------------------------------------------------------------
// Delete old log files
//------------------------------------------------------------------------------------------------------------------------------------------
const deleteOldLogs = (index) => {
    let total_seconds;

    try {
        if (index === 0)      { total_seconds = 3600 * 24 * 1; }
        else if (index === 1) { total_seconds = 3600 * 24 * 3; }
        else if (index == 2) { total_seconds = 3600 * 24 * 10; }
        else if (index === 3) { total_seconds = 3600 * 24 * 30; }
        else { return; }
    
        let deletedLogs = findRemoveSync(appSettings['appLogPath'], { dir: "*", test: false, age: { seconds: total_seconds }});
    
        if (Object.keys(deletedLogs).length != 0) {
            log.info("deleted " + Object.keys(deletedLogs).length  + " logs older than " + (total_seconds/(3600*24)) + " day(s)");
        }
        else {
            log.info("No logs deleted, found no logs older than " + (total_seconds/(3600*24)) + " day(s)");    
        }
    }
    catch(error){
        let msg = "Failed to delete old log files \n\nError code: " + error.code + "\nError message: " + error.message;
        dialog.showMessageBoxSync({type: "warning", message: msg, title: "NVMeInfo Warning", buttons: ["OK"]}); 
    }
}
//------------------------------------------------------------------------------------------------------------------------------------------
// Functions to start app and windows, standard Electron boilerplate
//------------------------------------------------------------------------------------------------------------------------------------------
app.on('ready', () => {
    createWindow();
    if (app.isPackaged === false) mainWindow.webContents.openDevTools();
    loadSettingsFile();
    deleteOldLogs(appSettings['logDayIndex']);
});
app.on('window-all-closed', () => {
    abortRunningNvmecmd();
    if (process.platform !== 'darwin') { app.quit(); }
});
app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) { createWindow(); }
});
//------------------------------------------------------------------------------------------------------------------------------------------
// Create the app main window, set background color to w/a fuzzy font issue, set height and width to desired //,preload: path.join(app.getAppPath(), 'preload.js')
//------------------------------------------------------------------------------------------------------------------------------------------
var mainWindow;

const createWindow = () => {
    log.info("Creating window");
    mainWindow = new BrowserWindow({ webPreferences: { contextIsolation: false, nodeIntegration: false, enableRemoteModule: true, preload: path.join(__dirname, 'preload.js') }, backgroundColor: '#fff', show: false, minHeight: 400, minWidth: 1050, width: 1250, height: 625, frame: false });
    mainWindow.setMenuBarVisibility(false)
    mainWindow.loadFile(path.join(__dirname, 'main.html'));
    log.info("Loading main.html");
    mainWindow.once('ready-to-show', () => { mainWindow.show(); })
};
//------------------------------------------------------------------------------------------------------------------------------------------
// Functions to open folder with logs, linux and windows work differently 
//------------------------------------------------------------------------------------------------------------------------------------------
const showActiveLogs = exports.showActiveLogs = (path) => {
    log.verbose("Opening log folder : " + path);
    if (process.platform === 'linux') { shell.showItemInFolder(path + "/*"); }
    else                              { shell.openPath(path);  } 
}
const showAppLogs = exports.showAppLogs = () => {
    log.verbose("Opening app logs : " + appInternalLogs);
    if (process.platform === 'linux') { shell.showItemInFolder(appInternalLogs + "/*"); }
    else                              { shell.openPath(appInternalLogs); }   
}
//------------------------------------------------------------------------------------------------------------------------------------------
// Misc functions
//------------------------------------------------------------------------------------------------------------------------------------------
const getTitle = exports.getTitle = () => { return "NVMe Info - " + app.getVersion() + betaTag ; };
const getPlatform = exports.getPlatform = () => { return process.platform; };

const help = exports.help = () => {
    let userGuide = path.join(basePath, 'resources','documentation','NVMeInfo_User_Guide.pdf');
    log.debug("Displayed user guide " + userGuide);
    shell.openPath(userGuide);
}
const getSettings=  exports.getSettings = () => {
    return appSettings;
}
const changeSettings = exports.changeSettings = (settings) => {
    try {
        if (settings["logDayIndex"] != appSettings["logDayIndex"]) {  deleteOldLogs(settings["logDayIndex"]); }
        appSettings = settings;
        fs.writeFileSync(settingsFile, JSON.stringify(settings));
        log.info("Settings changed");
    }
    catch(error) {
        let msg = "Failed to write settings: " + settingsFile + "\n\nSettings were not updated \n\nError message: " + error.message;
        log.error(msg);
        dialog.showMessageBoxSync({type: "warning", message: msg, title: "NVMeInfo Warning", buttons: ["OK"]});
    }  
}
const selectCompareFile = exports.selectCompareFile = () => {
    let fileSelected = dialog.showOpenDialogSync(mainWindow,{ defaultPath: appSettings['appLogPath'], filters: [{ name: 'NVMe Info', extensions: ['info.json'] }], properties: ['openFile'] });
    log.verbose("Compare file selected : " + fileSelected);
    if (fileSelected == undefined) return;
    mainWindow.webContents.send('compare-file', fileSelected);
}
const selectRulesFile = exports.selectRulesFile = () => {
    let fileSelected = dialog.showOpenDialogSync(mainWindow,{ defaultPath: appSettings['nvmecmdRulesFilePath'], filters: [{ name: 'NVme Rules', extensions: ['rules.json'] }], properties: ['openFile'] });
    log.verbose("Rule file selected : " + fileSelected);
    if (fileSelected == undefined) return;
    mainWindow.webContents.send('verify-file', fileSelected);
}
const changeLogPath = exports.changeLogPath = () => {  
    let logDir = dialog.showOpenDialogSync({ defaultPath: appSettings['appLogPath'], properties: ['openDirectory'] });
    if (logDir == undefined) return;
    appSettings['appLogPath'] = logDir[0];  
    changeSettings(appSettings);
    log.verbose("Log path changed to: " + logDir);
    mainWindow.webContents.send('settings', appSettings);
}
const setDefaultSettings = exports.setDefaultSettings = () => {  
    if (fs.existsSync(settingsFile)) {
        log.info("Deleting settings file")
        fs.unlinkSync(settingsFile); 
    }
    appSettings = {
        logDayIndex: 1,
        appViewFilterPath: path.join(basePath, 'resources', 'view_filters'),
        appLogPath: path.join(app.getPath('documents'), app.getName()),
        nvmecmdRulesFilePath: rulesPath,
        nvmecmdCmdFilePath: cmdPath,
        nvmecmdPath: nvmecmdPath
    };
    changeSettings(appSettings);
    log.info("Restored default settings");
    log.info(appSettings);
    mainWindow.webContents.send('settings', appSettings);
}
const changeFilterPath = exports.changeFilterPath = () => {
    let logDir = dialog.showOpenDialogSync({ defaultPath: appSettings['appViewFilterPath'], properties: ['openDirectory'] });
    if (logDir == undefined) return;
    appSettings['appViewFilterPath'] = logDir[0];
    changeSettings(appSettings);
 
    log.verbose("View filter path changed to: " + logDir);
    mainWindow.webContents.send('settings', appSettings);
}
//------------------------------------------------------------------------------------------------------------------------------------------
// These functions run the nvmecmd utility
//------------------------------------------------------------------------------------------------------------------------------------------
var nvme, isNvmecmdRunning = false, isNvmecmdTimeout = false

const runNvmecmd = exports.runNvmecmd = (nvmecmdCommandType, nvmecmdParameters) => {
    
    const nvmecmdLogfile = 'nvme.info.json';
    let nvmecmdAction = ''
    let nvmecmdLogPath = ''

    // Get start time to create log folder and calculate total time later
    //--------------------------------------------------------------------
    try {
        var startTime = Date.now();
        nvmecmdLogPath = path.join(appSettings['appLogPath'], nvmecmdCommandType, dateFormat(startTime, dateFormatString));
        fs.mkdirSync(nvmecmdLogPath, { recursive: true });
        log.verbose("Created " + nvmecmdLogPath);
    }
    catch (error) {
        log.error("runNvmecmd failed to create directory.  Code: " + error.code + "Message: " + error.message + " Directory " + nvmecmdLogPath);
        fatalError("Failed to create log directory:\n" + nvmecmdLogPath)
        return;
    }
    let localNvmecmdParameters = [];

    if (nvmecmdCommandType === 'Dashboard') {

        nvmecmdAction = 'Read information'; 
        
        localNvmecmdParameters.push(readCmdFile);  
        localNvmecmdParameters.push(("--nvme"));
        localNvmecmdParameters.push((nvmecmdParameters[0]));
        localNvmecmdParameters.push(("--dir"));
        localNvmecmdParameters.push((nvmecmdLogPath));

    }
    else if (nvmecmdCommandType === 'ReadInfo') {
        nvmecmdAction = 'Read information';
        localNvmecmdParameters.push(readCmdFile);   
        localNvmecmdParameters.push(("--nvme"));
        localNvmecmdParameters.push((nvmecmdParameters[0]));
        localNvmecmdParameters.push(("--dir"));
        localNvmecmdParameters.push((nvmecmdLogPath));

    }
    else if (nvmecmdCommandType === 'CompareInfo') {
        nvmecmdAction = 'Compare information';

        localNvmecmdParameters.push(readCmdFile);   
        localNvmecmdParameters.push(("--nvme"));
        localNvmecmdParameters.push((nvmecmdParameters[0]));
        localNvmecmdParameters.push(("--dir"));
        localNvmecmdParameters.push((nvmecmdLogPath));
        localNvmecmdParameters.push(("--compare"));
        localNvmecmdParameters.push((nvmecmdParameters[1]));

    }
    else if (nvmecmdCommandType === 'VerifyInfo') {
        nvmecmdAction = 'Verify information';

        localNvmecmdParameters.push(readCmdFile);   
        localNvmecmdParameters.push(("--nvme"));
        localNvmecmdParameters.push((nvmecmdParameters[0]));
        localNvmecmdParameters.push(("--dir"));
        localNvmecmdParameters.push((nvmecmdLogPath));
        localNvmecmdParameters.push(("--rules"));
        localNvmecmdParameters.push((nvmecmdParameters[1]));
    }
    else {
        fatalError("Unknown nvmecmdCommandType " + nvmecmdCommandType);
    }

    // If app already running stop it and try again
    //--------------------------------------------- 
    if (isNvmecmdRunning) {
        abortRunningNvmecmd();
        setTimeout(runNvmecmd, 50, nvmecmdCommandType, nvmecmdParameters);
        return
    }
    // Now start the app
    //---------------------
    isNvmecmdRunning = true
    isNvmecmdTimeout = false

    let timeoutId = setTimeout(timeoutRunningApp, nvmecmdTimeoutInMs);
    nvme = spawn(nvmeAppName, localNvmecmdParameters, { cwd: nvmecmdPath });

    log.verbose("runNvmecmd overhead is " + (Date.now() - startTime) / 1000.0 + " seconds");
    log.verbose("Starting " + nvmeAppName + " in " + nvmecmdPath + " with " + localNvmecmdParameters);
    //------------------------------------------------------------------------------------------------------------------------------------------
    // This is called when nvmecmd completes or fails to start
    //------------------------------------------------------------------------------------------------------------------------------------------
    nvme.on('error', (appError) => {
        log.error('Error spawning nvmecmd : (' + appError.message + ')');
    })
    nvme.on('exit', (code) => {
        clearTimeout(timeoutId);
        let seconds = (Date.now() - startTime) / 1000.0;

        // nvmecmd aborted, did not complete
        //------------------------------------
        if (code == null) {
            if (isNvmecmdTimeout) {
                log.error(nvmecmdAction + " timed out and aborted at " + seconds + " seconds");
                mainWindow.webContents.send('nvmecmd-end', -1, nvmecmdAction + " timed out and aborted at " + seconds + " seconds", 0, null, nvmecmdLogPath);
            }
            else {
                log.error(nvmecmdAction + " aborted by user");

                // try/catch around this to avoid error when exits app, nvmecmd is aborted, and render no longer running
                
                try { mainWindow.webContents.send('nvmecmd-end', -1, nvmecmdAction + " aborted by user", 0, null, nvmecmdLogPath);}
                catch {}
            }
        }
        // nvmecmd aborted with exceptions and log cannot be trusted
        //-------------------------------------------------------------
        else if (code == nvmecmdExceptionCode) {
            log.error(nvmecmdAction + " failed with exception " + code + " after " + seconds + " seconds");
            let textdata = fs.readFileSync(path.join(nvmecmdLogPath, "nvmecmd.trace.log"),'utf-8');
            log.error(textdata);          
            mainWindow.webContents.send('nvmecmd-end', -1, nvmeAppName + " failed with exception " + code + " after " + seconds + " seconds", 0, null, nvmecmdLogPath);
        }
        // nvmecmd aborted with usage error and did not create the logs
        //-------------------------------------------------------------
        else if (code == nvmecmdUsageError) {
            log.error(nvmecmdAction + " failed with usage error " + code + " after " + seconds + " seconds");
            let textdata = fs.readFileSync(path.join(nvmecmdLogPath, "nvmecmd.trace.log"),'utf-8');
            log.error(textdata);
            mainWindow.webContents.send('nvmecmd-end', -1, nvmeAppName + " failed with usage error after " + seconds + " seconds", 0, null, nvmecmdLogPath);
        }
        // nvmecmd aborted because no drives were found
        //-------------------------------------------------------------
        else if (code == nvmecmdNoDrives) {
            log.error("No NVMe drives found, exiting");
            dialog.showErrorBox("NVMeInfo Fatal Error", "No NVMe drives found, click OK to exit");
            app.exit(1);            
        }        
        else {
            // nvmecmd completed and should have created the logs
            //----------------------------------------------------
            try {
                let rawdata = fs.readFileSync(path.join(nvmecmdLogPath, nvmecmdLogfile));
                let jsonInfo = JSON.parse(rawdata);

                log.verbose(nvmecmdAction + " completed with code " + code + " in " + seconds);
                mainWindow.webContents.send('nvmecmd-end', code, null, seconds, jsonInfo, nvmecmdLogPath);
                log.info(jsonInfo._metadata.system)
            }
            catch (error) {
                log.error(nvmecmdAction + " completed with code " + code + " in " + seconds + " seconds but could not parse log file '" + nvmecmdLogfile + "'");
                let textdata = fs.readFileSync(path.join(nvmecmdLogPath, "nvmecmd.trace.log"),'utf-8');
                log.error(textdata);     
                mainWindow.webContents.send('nvmecmd-end', -1, nvmecmdAction + " completed with code " + code + " in " + seconds + " seconds but could not parse log file '" + nvmecmdLogfile + "'", 0, null, nvmecmdLogPath);
            }
        }
        isNvmecmdRunning = false;
    })

    // Check if started and send error message if needed
    //-----------------------------------------------------------------
    if (nvme.pid != undefined) {
        log.verbose("Nvme application started with process ID " + nvme.pid);
    }
    else {
        log.error(nvmeAppName +  " failed to start");
        mainWindow.webContents.send('nvmecmd-end', -1, nvmecmdPath + "\n" + nvmeAppName + " failed to start", 0, null, nvmecmdLogPath);
        isNvmecmdRunning = false;
    }
}
// Set flag to indicate app did not exit in time   
//----------------------------------------------- 
const timeoutRunningApp = () => {
    isNvmecmdTimeout = true;
    abortRunningNvmecmd();
}
// Abort the app if running
//-------------------------- 
const abortRunningNvmecmd = () => {
    if (nvme == null) { return }
    if (nvme.exitCode == null) {
        try {
            nvme.kill();
            log.verbose('abortRunningNvmecmd:  nvme kill status: ' + nvme.killed);
        } catch (error) {
            fatalError("Failed to kill process: " + error.message);
        }
    }
    else {
        log.verbose('abortRunningNvmecmd:  nvme not running');
    }
}
//------------------------------------------------------------------------------------------------------------------------------------------
// These functions get the view filters
//------------------------------------------------------------------------------------------------------------------------------------------
const getViewFilter = exports.getViewFilter = (filterFilename) => {
    try{
        let filterFile = path.join(appSettings['appViewFilterPath'], filterFilename);
        let rawData = fs.readFileSync(filterFile);
        let parseData = JSON.parse(rawData);
        log.verbose("getViewFilter read " + filterFilename + " with length: " + parseData["filter"].length);
        return parseData;
    }
    catch(error) {
        let msg = "Failed to read view filter file : " + filterFilename;
        msg += "\n\nVerify file is present and has correct JSON format\n\nError message: " + error.message;
        dialog.showMessageBoxSync({type: "warning", message: msg, title: "NVMeInfo Warning", buttons: ["OK"]});
        let parseData = JSON.parse('{ "filter":[]}');
        return parseData;
    }
}
const getMenuOptions = exports.getMenuOptions = () => {
    let filter_array = [];
    let requiredFiles = 0;
    try {
        log.info("Reading view filters from directory " + appSettings['appViewFilterPath']);
        let files =  fs.readdirSync(appSettings['appViewFilterPath']);
        files.forEach(function (file) {
            if (file.toLowerCase().endsWith('.filter.json')) {
                let name = file.split('.')[0].toUpperCase();
                log.verbose("getMenuOptions adding view filter menu option: " + name)
                let filterInfo = getViewFilter(name + ".filter.json");  // This is done to check for format errors on startup

                if ((name !== 'ALL') && (name !== 'SMART') && (name !== 'SUMMARY')) {     
                    if ( filterInfo["filter"].length != 0) { filter_array.push(name); } // don't add if file has no entries              
                }
                else {
                    requiredFiles += 1
                }
            }
        });
        if (requiredFiles !== 3) {
            fatalError("Missing one or more required View Filter Files\n\nVerify ALL, SUMMARY, and SMART view filters exist in directory\n\n" + appSettings['appViewFilterPath']);
        }
    }
    catch(error) {
        fatalError("Failed to get view filter files in directory\n" + appSettings['appViewFilterPath'] + "\n\nError Message: " + error.message);
    }
    return filter_array;
}
