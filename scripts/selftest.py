#--------------------------------------------------------------------------------------------------------------------
# Example script to read info before and after self-test
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
import sys,os, argparse
from lib.test import *

#--------------------------------------------------------------------------------------------------------------------
# Read the command line parameters  
#--------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Reads info before self-test and verifies info after', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--nvme', type=int, default=0, help='NVMe drive number', metavar='#')
args = parser.parse_args()
#--------------------------------------------------------------------------------------------------------------------
# Run the test, return zero on pass non-zero on fail
#--------------------------------------------------------------------------------------------------------------------
try:
    test = start_test(1,"Short-Self-Test","")
    #-------------------------------------------------------------------
    # Step 1: Read info before starting the self-test
    #-------------------------------------------------------------------
    step = start_step(1,"Read-Info",test)
    working_directory = f"{step['directory']}"
    starting_info = os.path.join(working_directory,"nvme.info.json")  # Save this path for compare at the end

    nvmecmd_args =  [NVMECMD,                         # path to nvmecmd executable defined in lib
                    "read",                           # cmd file to read the NVMe information
                    "--rules",f"default",             # verify against the default rules
                    "--dir",f"{working_directory}",   # run in the working directory
                    "--nvme",f"{args.nvme}"]          # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

    step['code'] = run_step_process(nvmecmd_args, working_directory)  # Save nvmecmd return code in step[code]
    if step['code'] != 0: step['errors'] = 1                          # if nvmecmd did not return 0 step failed
    end_step(step,test)
    #-------------------------------------------------------------------
    # Step 2: Run self-test
    #-------------------------------------------------------------------
    step = start_step(2,"Run-Self-Test",test)
    working_directory = f"{step['directory']}"
    selftest_timeout = 120

    nvmecmd_args =  [NVMECMD,                          # path to nvmecmd executable defined in lib
                    "short-self-test",                 # cmd file to run the self-test
                    "--dir",f"{working_directory}",    # run in the working directory
                    "--nvme",f"{args.nvme}"]           # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

    step['code'] = run_step_process(nvmecmd_args, working_directory, selftest_timeout)
    if step['code'] != 0: step['errors'] = 1
    end_step(step,test)
    #-------------------------------------------------------------------
    # Step 3: Get info again and compare against prior info
    #-------------------------------------------------------------------
    step = start_step(3,"Verify-Info",test)
    working_directory = f"{step['directory']}"
    ending_info = os.path.join(working_directory,"nvme.info.json")  # Save this path for later

    nvmecmd_args =  [NVMECMD,                         # path to nvmecmd executable defined in lib
                    "read",                           # cmd file to read the NVMe information
                    "--rules",f"default",             # verify against the default rules
                    "--compare",f"{starting_info}",   # compare against the info read before the test
                    "--dir",f"{working_directory}",   # run in the working directory
                    "--nvme",f"{args.nvme}"]          # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

    step['code'] = run_step_process(nvmecmd_args, working_directory)
    if step['code'] != 0: step['errors'] = 1
    end_step(step,test)
    #-------------------------------------------------------------------
    # Test complete, write results and exit
    #-------------------------------------------------------------------
    end_test(test) 
    os._exit(test['errors'])
    
except:
    logger.exception('ERROR:  Test aborted because of unhandled exception:')
    os._exit(TEST_CASE_EXCEPTION)
