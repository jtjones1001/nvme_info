;---------------------------------------------------------------------
; Windows installer for NVMe Info Electron Application
;---------------------------------------------------------------------
!include "MUI2.nsh"
!include LogicLib.nsh 
!include x64.nsh
 
Name "NVMe Info"
OutFile "..\dist\NVMeInfo-setup.exe"
Unicode True
RequestExecutionLevel admin
 
!getdllversion "..\dist\win-unpacked\NVMeInfo.exe" expv_

!define App         "NVMeInfo"
!define ProductName "NVMe Info"
!define Company     "Epic"
!define Version "${expv_1}.${expv_2}.${expv_3}.${expv_4}"

Caption "${ProductName} Setup (${Version})"

InstallDir "C:\Program Files\${App}"
InstallDirRegKey HKCU "Software\${App}" ""

Var /GLOBAL UserHomepath  
;--------------------------------
;Interface Settings
;--------------------------------
!define MUI_ABORTWARNING

; MUI Settings / Icons
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install-nsis.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\orange-uninstall-nsis.ico"
 
; MUI Settings / Header
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-r-nsis.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-uninstall-r-nsis.bmp"
 
; MUI Settings / Wizard
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\orange-nsis.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\orange-uninstall-nsis.bmp"

;--------------------------------
;Pages
;--------------------------------
!insertmacro MUI_PAGE_LICENSE "License.txt"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
  
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
;--------------------------------
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections
;--------------------------------
Section "Dummy Section" SecDummy
	ReadEnvStr $UserHomepath  HOMEPATH
 
	SetOutPath "$INSTDIR"
	File /r /x "linux_installer.sh" "..\dist\win-unpacked\*.*"
	SetOutPath "$desktop"
	CreateShortcut "$desktop\${ProductName}.lnk" "$instdir\${App}.exe"		
	System::Call 'Shell32::SHChangeNotify(i 0x8000000, i 0, i 0, i 0)'	
				
    EnVar::SetHKLM  
	EnVar::Check "NVMEINFO_RESULTS_PATH" "NULL";
	Pop $0
	${If} $0 != "0"
		EnVar::AddValue "NVMEINFO_RESULTS_PATH" "$UserHomepath\Documents\nvmeinfo"
		DetailPrint "Updated NVMEINFO_RESULTS_PATH to $UserHomepath\Documents\nvmeinfo"
	${Else}
		DetailPrint "NVMEINFO_RESULTS_PATH already exists"
	${EndIf}
	
	EnVar::AddValue "NVMEINFO_INSTALL_PATH" "$INSTDIR"
	DetailPrint "Updated NVMEINFO_INSTALL_PATH to $INSTDIR"

    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=50
  
   	WriteRegStr HKLM "Software\${Company}\${App}" "" $INSTDIR
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${App}" "DisplayName" "${ProductName} ${Version}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${App}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
				 
	WriteUninstaller "$instdir\Uninstall.exe"
	
SectionEnd

;--------------------------------
; Descriptions
;--------------------------------
	LangString DESC_SecDummy ${LANG_ENGLISH} "A test section."

	VIProductVersion "${Version}"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${ProductName}"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "Reads NVMe information"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${Company}"
;;	VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalTrademarks" "${ProductName} is a trademark of ${Company}"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "Copyright 2020"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${App}"
	VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${Version}"
 	VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${Version}"
;--------------------------------
; Uninstaller Section
;--------------------------------
Section "Uninstall"

	Delete "$INSTDIR\Uninstall.exe"
	Delete "$desktop\${ProductName}.lnk"
	Delete "$APPDATA\NvmeInfo\settings.json"
	
	DeleteRegKey /ifempty HKLM "Software\${Company}\${App}"
	
	EnVar::SetHKLM

	EnVar::Delete "NVMEINFO_RESULTS_PATH"  
 	EnVar::Delete "NVMEINFO_INSTALL_PATH"  
 	
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=50
	
	RMDir /R /REBOOTOK  "$INSTDIR"
  
SectionEnd
;--------------------------------
; Init function
;--------------------------------
Function .onInit
	${IfNot} ${RunningX64}
	MessageBox MB_OK|MB_ICONINFORMATION "This program runs on x64 machines only, exiting"
	Abort
	${EndIf}
	${DisableX64FSRedirection}
		
FunctionEnd 

