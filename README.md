# NVMe Info
View information about NVMe SSD drives in your Windows or Linux computer using this open source application

NVMe Info was created with the following goals:
  - Provide a way to read NVMe information on computers with the following OS: Linux, Windows, WinPE
  - Provide a GUI with a simple interface that runs in both Linux and Windows OS
  - Provide a command line utility for advanced users interested in automation and additional features (e.g. self-test)
  
# Documentation
For a quick overview and details on the command line utility see the videos here:  www.epicutils.com 

The documentation folder contains User Guides for the NVMe Info GUI  and nvmecmd command line applications

# About
This project was started as a fun way to sandbox the electron framework, NodeJS, html, JavaScript, C++, python, NSIS, PowerShell, github, and web development using WIX.  

Future plans include (1) adding options to format, sanitize, and firmware update (2) decoding the persistent event log (3) adding more use case documentation (4) adding support to decode more 1.4 features and log pages 

# Installation on Windows
 - Download and run NVMeInfo-setup.exe from the latest release
 - Double click the NVMe Info icon on the desktop to run the application

# Installation on Linux
 - Download the tar.gz file from the latest release
 - Extract the file to the install directory (e.g. /opt/nvmeinfo)
 - Set permissions on nvmecmd to allow accessing NVMe devices 
    -  sudo setcap cap_sys_rawio,cap_sys_admin,cap_dac_override=ep /opt/nvmeinfo/resources/nvmecmd/nvmecmd
 - Setup the environment variables.  For example...
    - export NVMEINFO_INSTALL_PATH=/opt/nvmeinfo
    - export NVMEINFO_RESULTS_PATH=/home/joe/Documents/nvmeinfo
 - From the install directory type nvmeinfo from terminal

# Advanced Use Cases
NVMe Info uses a command line utility called nvmecmd to read the information.  Integration of nvmecmd with a scripting language (e.g. python) can provide additional features.    Here are some examples, see documentation\use_cases for some additional details.
 - Create custom text reports
 - Verify NVMe SSD is unused (new)
 - Verify NVMe SSD features reqiured by the user are supported
 - Measure the exit latency of power states
 - Determine if an NVMe SSD throttles performance and if so, the "almost real time" performance loss
 - Measure the "almost real time" read/write bandwidth, drive temperature, and throttling during a workload
 - Verify the timestamp is correct and accurate
 - Verify the SMART counters are working as expected
 - Measure the time NVMe admin commands take to complete
 - Run short and extended self-tests
 - Compare NVMe SSD state against a prior state.  

# Acknowledgements
NVMe Info is created using the electron framework			https://www.electronjs.org/

The following Nodejs add-ins are used in the project:
 - custom-electron-titlebar 			https://www.npmjs.com/package/custom-electron-titlebar
 - dateformat				https://www.npmjs.com/package/dateformat
 - electron-log				https://www.npmjs.com/package/electron-log
 - electron-unhandled			https://www.npmjs.com/package/electron-unhandled 
 - find-remove				    https://www.npmjs.com/package/find-remove

The following background patterns are used from Toptal Subtle Patterns:
 - https://www.toptal.com/designers/subtlepatterns/white-wall-3/
 - https://www.toptal.com/designers/subtlepatterns/white-plaster/

Some of the icons are from Font Awesome				https://fontawesome.com/

Electron-builder is used to create the distribution: https://www.electron.build/

NSIS is used to create the Windows installer: https://nsis.sourceforge.io/Main_Page
 - NSIS add-ins or plug-ins:
   - MUI2.nsh			https://nsis.sourceforge.io/Docs/Modern%20UI%202/Readme.html
   - LogicLib.nsh 			https://nsis.sourceforge.io/LogicLib
   - NSIS EnVar			https://nsis.sourceforge.io/EnVar_plug-in

Refer to the nvmecmd project for acknowledgements on the nvmecmd utility.
