#--------------------------------------------------------------------------------------------------------------------
# Example PowerShell script that runs nvmecmd and generates a custom report file
#--------------------------------------------------------------------------------------------------------------------
# Copyright(c) 2021 Joseph Jones
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this softwareand associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and /or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#--------------------------------------------------------------------------------------------------------------------
param($NVMe=0)


try {

    $ErrorCount = 0

    #-------------------------------------------------------------------
    # Define constants and create working directory
    #-------------------------------------------------------------------   
    $NVMECMD  = '\Program Files\Epic\NVMeInfo\resources\nvmecmd\nvmecmd.exe'
 
 
    $WorkingDirectory = Join-Path (Resolve-Path $Env:EPIC_NVME_RESULTS_PATH).path (Join-Path 'reports'  (get-date).tostring(“yyyyMMdd_HHmmss”))
    $File = Join-Path  $WorkingDirectory  'report.log'
 
    New-Item $WorkingDirectory -ItemType Directory -ErrorAction SilentlyContinue | Out-Null

    #-------------------------------------------------------------------
    # Run nvmecmd
    #-------------------------------------------------------------------
    $NvmecmdArgs = "read --dir  $WorkingDirectory --nvme $nvme"
    
    $Process = Start-Process $NVMECMD -ArgumentList $NvmecmdArgs  -PassThru -WindowStyle Hidden -WorkingDirectory $WorkingDirectory   
    Wait-Process -TimeoutSec 10 -InputObject $Process -ErrorVariable TimeoutError
    if ($TimeoutError) {
        $Process.kill()
        throw ("nvmecmd timed out and was terminated")
    }
    #-------------------------------------------------------------------
    # Open the current file and write to custom report format
    #------------------------------------------------------------------
    $SourceInfo= Get-Content -Raw -Path (Join-Path $WorkingDirectory "nvme.info.json") | ConvertFrom-Json

    $Kwidth     =  -55                           # Width of first field for display and log file
    $Parameters =  $SourceInfo.nvme.parameters   # short hand for readability

    Tee-Object -FilePath $File -Append -InputObject ('-'*135) | Write-Host
    Tee-Object -FilePath $File -Append -InputObject (" EXAMPLE NVME REPORT ") | Write-Host
    Tee-Object -FilePath $File -Append -InputObject ('-'*135) | Write-Host  
 
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Subsystem Vendor'.value)" -f 'Vendor') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Model Number (MN)'.value)" -f 'Model') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Serial Number (SN)'.value)" -f 'Serial Number') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'IEEE OUI Identifier (IEEE)'.value)" -f 'IEEE OUI Identifier') | Write-Host        
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Namespace 1 IEEE Extended Unique Identifier (EUI64)'.value)" -f 'Namespace 1 EUID') | Write-Host     
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Namespace 1 Globally Unique Identifier (NGUID)'.value)" -f 'Namespace 1 NGUID') | Write-Host     
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Firmware Revision (FR)'.value)" -f 'Firmware') | Write-Host    
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Size'.value)" -f 'Size')  | Write-Host   
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Version (VER)'.value)" -f 'NVMe Version')   | Write-Host  

    Tee-Object -FilePath $File -Append -InputObject " " | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Percentage Used'.value)" -f 'Percentage Used') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Data Read'.value)" -f 'Data Read') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Data Written'.value)" -f 'Data Written')   | Write-Host    
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Power On Hours'.value)" -f 'Power-On Hours') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Power Cycles'.value)" -f 'Power Cycles') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Available Spare'.value)" -f 'Available Spare') | Write-Host  

    Tee-Object -FilePath $File -Append -InputObject " " | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Composite Temperature'.value)" -f 'Composite Temperature')
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Thermal Management Temperature 1 (TMT1)'.value)" -f 'Thermal Management Temperature 1 (TMT1)') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Thermal Management Temperature 2 (TMT2)'.value)" -f 'Thermal Management Temperature 2 (TMT2)') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Warning Composite Temperature Threshold (WCTEMP)'.value)" -f 'Warning Composite Temperature Threshold (WCTEMP)') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Critical Composite Temperature Threshold (CCTEMP)'.value)" -f 'Critical Composite Temperature Threshold (CCTEMP)') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Thermal Management Temperature 1 Time'.value)" -f 'Thermal Management Temperature 1 Time') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Thermal Management Temperature 2 Time'.value)" -f 'Thermal Management Temperature 2 Time') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Warning Composite Temperature Time'.value)" -f 'Warning Composite Temperature Time') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Critical Composite Temperature Time'.value)" -f 'Critical Composite Temperature Time') | Write-Host  

    Tee-Object -FilePath $File -Append -InputObject " " | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Critical Warnings'.value)" -f 'Critical Warnings') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Media and Data Integrity Errors'.value)" -f 'Media and Data Integrity Errors') | Write-Host  
    Tee-Object -FilePath $File -Append -InputObject ("  {0,$Kwidth} $($parameters.'Number Of Failed Self-Tests'.value)" -f 'Number Of Failed Self-Tests') | Write-Host  
  

    # Create a table with PCI information

    Tee-Object -FilePath $File -Append -InputObject " " | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  -------------------------------------------------------------------------------------------------------------------------------------"  | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  PCI        Vendor       Vendor ID    Device ID    Width             Speed                                 Location"  | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  -------------------------------------------------------------------------------------------------------------------------------------"  | Write-Host 
 
    $Line = ("  {0,-11}{1,-13}{2,-13}{3,-13}{4}{5}{6}" -f 
                    'Endpoint',
                    $parameters.'Controller Vendor'.value,
                    $parameters.'PCI Vendor ID (VID)'.value,
                    $parameters.'PCI Device ID'.value,
                    "$($parameters.'PCI Width'.value) (Rated: $($parameters.'PCI Rated Width'.value))    ",
                    "$($parameters.'PCI Speed'.value) (Rated: $($parameters.'PCI Rated Speed'.value))    ",
                    $parameters.'PCI Location'.value)

    Tee-Object -FilePath $File -Append -InputObject $Line | Write-Host 

    $Line = ("  {0,-11}{1,-13}{2,-13}{3,-13}{4,-19}{5,-37}{6}" -f  
                    'Root',
                    ' ',
                    $parameters.'Root PCI Vendor ID'.value,
                    $parameters.'Root PCI Device ID'.value,
                    ' ',
                    ' ',
                    $parameters.'Root PCI Location'.value)

    Tee-Object -FilePath $File -Append -InputObject $Line | Write-Host 

    # Create a table with power information

    Tee-Object -FilePath $File -Append -InputObject " " | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  -------------------------------------------------------------------------------------------------------------------------------------"  | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  State   NOP    Max        Active     Idle       Entry Latency   Exit Latency    ITPT          ITPS     RWL   RWT   RRL   RRT" | Write-Host 
    Tee-Object -FilePath $File -Append -InputObject "  -------------------------------------------------------------------------------------------------------------------------------------"  | Write-Host 
 
    For ($state=0; $state -lt $parameters.'Number of Power States Support (NPSS)'.value ; $state++) {
        $Line = "  {0,-8}" -f $state

        if ($parameters."Power State $state Non-Operational State (NOPS)".value -eq 'True') {
            $Line += "{0,-7}" -f 'Yes'
        }
        else {
            $Line += "{0,-7}" -f ' '
        }
        if ($parameters."Power State $state Maximum Power (MP)".value -eq "Not Reported") {
            $Line += "{0,-11}" -f ' '
        } else { 
            $Line += "{0,-11}" -f ($parameters."Power State $state Maximum Power (MP)".value.split()[0] + " W")
        }
 
        if ($parameters."Power State $state Active Power (ACTP)".value -eq "Not Reported") {
            $Line += "{0,-11}" -f ' '
        } else { 
            $Line += "{0,-11}" -f ($parameters."Power State $state Active Power (ACTP)".value.split()[0] + " W")
        }
        if ($parameters."Power State $state Idle Power (IDLP)".value -eq "Not Reported") {
            $Line += "{0,-11}" -f ' '
        } else { 
            $Line += "{0,-11}" -f ($parameters."Power State $state Idle Power (IDLP)".value.split()[0] + " W")
        }

        if ($parameters."Power State $state Entry Latency (ENLAT)".value -eq "Not Reported") {
            $Line += "{0,-16}" -f ' '
        } else { 
            $Line +=  "{0,-16}" -f ($parameters."Power State $state Entry Latency (ENLAT)".value.split('(')[0])
        }

        if ($parameters."Power State $state Exit Latency (EXLAT)".value -eq "Not Reported") {
            $Line += "{0,-16}" -f ' '
        } else { 
            $Line +=  "{0,-16}" -f ($parameters."Power State $state Exit Latency (EXLAT)".value.split('(')[0])
        }

        if ($parameters."Power State {state} Idle Time Prior to Transition (ITPT)") {
            $Line += "{0,-14}" -f  $parameters."Power State $state Idle Time Prior to Transition (ITPT)".value.split('(')[0] 
        } else { 
            $Line += "{0,-14}" -f ' '
        }

        if ($parameters."Power State $state Idle Transition Power State (ITPS)" -ne $null) {
            $Line += "{0,-9}" -f $parameters."Power State $state Idle Transition Power State (ITPS)".value.split('(')[0] 
        } else { 
            $Line += "{0,-9}" -f ' '
        }

        $Line += "{0,-6}" -f  $parameters."Power State $state Relative Write Latency (RWL)".value  
        $Line += "{0,-6}" -f  $parameters."Power State $state Relative Write Throughput (RWT)".value  
        $Line += "{0,-6}" -f  $parameters."Power State $state Relative Read Latency (RRL)".value  
        $Line += "{0,-6}" -f  $parameters."Power State $state Relative Read Throughput (RRT)".value  

        Tee-Object -FilePath $File -Append -InputObject $Line | Write-Host 
    }
 

}
catch {
   write-host ("Unexpected exception" + $_)
   $ErrorCount = 1000000
}

exit($ErrorCount)