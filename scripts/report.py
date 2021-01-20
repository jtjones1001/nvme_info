#--------------------------------------------------------------------------------------------------------------------
# Stand alone example python script that runs nvmecmd and generates a custom report file
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
import sys,platform,subprocess,os,pathlib,logging,json,argparse
from test import *
from datetime import datetime

#-------------------------------------------------------------------
# Read the command line 
#-------------------------------------------------------------------
parser = argparse.ArgumentParser(description='create custom nvme report', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('nvme',type=int, nargs='?', default=0, help='NVMe drive number', metavar='#')
args = parser.parse_args()

try:
    #-------------------------------------------------------------------
    # Define constants and create working directory
    #-------------------------------------------------------------------   
    now = datetime.now() 
    working_directory = os.path.join(os.environ['NVMEINFO_RESULTS_PATH'] ,'Reports',now.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(working_directory)

    report_file = os.path.join(working_directory,"report.log") 
    read_cmd_file = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd','read.cmd.json')
    #-------------------------------------------------------------------
    # Enable logging with logging module but can use any logger 
    #-------------------------------------------------------------------
    logger = logging.getLogger('nvme_logger')
    
    fileHandler = logging.FileHandler(report_file)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)
    #-------------------------------------------------------------------
    # Run nvmecmd
    #-------------------------------------------------------------------
    nvmecmd_args =  [NVMECMD,                               # path to nvmecmd executable 
                    f"{read_cmd_file}",                     # cmd file to read the NVMe information    
                    "--dir",f"{working_directory}",         # run in the working directory specified
                    "--nvme",f"{args.nvme}"]                # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0
    try:
        nvmecmd_process = subprocess.Popen(nvmecmd_args, cwd=working_directory, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        nvmecmd_process.wait(10)  # 10 second timeout

        if (nvmecmd_process.returncode != 0):
            logger.info(f" Failed to read information on drive {args.nvme}, verify drive number is correct")
            os._exit(nvmecmd_process.returncode)

    except subprocess.TimeoutExpired:
        os.kill(nvmecmd_process.pid)
        logger.exception(f"nvmecmd timed out and was terminated")
        os._exit(1)
    #-------------------------------------------------------------------
    # Open the current file and write to custom report format
    #-------------------------------------------------------------------    
    log_report( os.path.join(working_directory,"nvme.info.json"), args.nvme, True)   

    os._exit(0)

except:
    logger.exception('Script aborted because of unhandled exception')
    os._exit(1)
