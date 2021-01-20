#--------------------------------------------------------------------------------------------------------------------
# Example python script that runs a few functional tests on NVMe drives.  Goal is to demonstrate how to use nvmecmd 
# and fio to define custom NVMe tests.  This is an example only and is not a comprehensive set of tests. 
#
# For new drives use the --new switch to check the drive against new-drive.rules.json
# To use custom cmd and/or rules use --path to specify directory with cmd and rules subdirectories
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
import sys,os, argparse, time, logging, csv
from test import *
from datetime import datetime

#--------------------------------------------------------------------------------------------------------------------
# Read the command line parameters using argparse 
#--------------------------------------------------------------------------------------------------------------------
parser = argparse.ArgumentParser(description='Runs functional tests on NVMe drive', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--nvme',   type=int, default=0, help='NVMe drive number', metavar='#')
parser.add_argument('--volume', type=str, default=DEFAULT_VOLUME, help='Volume to run fio (e.g. c:)', metavar='<dir>')
parser.add_argument('--dir',    type=str, default='', help='Directory to log results', metavar='<dir>')
parser.add_argument('--path',   type=str, default=NVMECMD_RESOURCES, help='Path to directory with cmd and rules subdirectories', metavar='<dir>')
parser.add_argument('--new',    default=False, action=argparse.BooleanOptionalAction, help="Checks new-drives rules")
parser.add_argument('--tests',  type=int, nargs="+", default=[1,2,3,4,5,6,7,8,9],  help="List of tests to run (e.g. 1 4 5 6)")

args = parser.parse_args()

if os.path.dirname(args.volume) != args.volume:
    print(f"Volume {args.volume} is not a legal volume.  Windows example: c:")
    os._exit(1)

if args.dir == "":   
    args.dir = os.path.join(os.path.abspath('.'), 'checkout', datetime.now().strftime("%Y%m%d_%H%M%S"))

#--------------------------------------------------------------------------------------------------------------------
# Setup the logging
#--------------------------------------------------------------------------------------------------------------------
try:
    os.makedirs(args.dir)
except FileExistsError:
    pass
except:
    logger.error(f">>>> FATAL ERROR:  Failed to make directory {args.dir}")
    os._exit(1)

logger = logging.getLogger('nvme_logger')
 
fileHandler = logging.FileHandler(os.path.join(args.dir,'checkout.log'))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

#--------------------------------------------------------------------------------------------------------------------
# Setup vars 
#--------------------------------------------------------------------------------------------------------------------
cmd_directory   = os.path.join(args.path)     # User specifies location for this
rules_directory = os.path.join(args.path)     # User specifies location for this
script_errors   = 0                           # Track script errors here for return value
step            = {}

idle_times_ms   = [0,20,50,70,90,150,200,500,700,900,1000,1200,1500 ]

#--------------------------------------------------------------------------------------------------------------------
# Start testing...
#--------------------------------------------------------------------------------------------------------------------
try:
    
    #################################################################################################################
    #  Test - Verify new-drive and feature rules
    #################################################################################################################
    if 1 in args.tests or 9 in args.tests:
            
        test = start_test(1,"Nvme-Verify-Info",args.dir)

        #-------------------------------------------------------------------
        # Step 1: Read info and verify against customer features
        #-------------------------------------------------------------------
        step = start_step("Verify-Features-And-Errors",test)

        working_directory = f"{step['directory']}"                                   # directory created by start_step for logging
        cmd_file          = os.path.join(cmd_directory,'read.cmd.json')              # use cmd file from the specified path
        rules_file        = os.path.join(rules_directory,'user-features.rules.json')      # use rules file from the specified path
        ref_info_file     = os.path.join(working_directory,"nvme.info.json")

        nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                   # cmd file to read the NVMe information   
                        "--dir",f"{working_directory}",  # log to the directory created by start_step
                        "--rules",f"{rules_file}",       # Verify features rules                     
                        "--nvme",f"{args.nvme}"]         # NVMe drive number 

        step['code'] = run_step_process(nvmecmd_args, working_directory)  # run nvmecmd in directory created by start_step

        log_report(ref_info_file,args.nvme,False)                         # Display the report on the NVMe drive being tested
        test['errors'] += end_step(step) 
        #-------------------------------------------------------------------
        # Step 2: If --new specified verify info against new-drive rules
        #-------------------------------------------------------------------
        if args.new:

            step = start_step("Verify-New-Drive-Rules",test)

            working_directory = f"{step['directory']}"                                   # directory created by start_step for logging
            cmd_file          = os.path.join(cmd_directory,'read.cmd.json')              # use cmd file from the specified path
            rules_file        = os.path.join(rules_directory,'unused-drive.rules.json')     # use rules file from the specified path

            nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                            f"{cmd_file}",                   # cmd file to read the NVMe information   
                            "--dir",f"{working_directory}",  # log to the directory created by start_step
                            "--rules",f"{rules_file}",       # Verify new drive rules                     
                            "--nvme",f"{args.nvme}"]         # NVMe drive number 

            step['code'] = run_step_process(nvmecmd_args, working_directory)    # run process in directory created by start_step
            test['errors'] += end_step(step)    
        
        script_errors += end_test(test)     
        #-------------------------------------------------------------------
        # If test failed abort so can update the cmd/rules if needed
        #-------------------------------------------------------------------
        if script_errors:
            os._exit(test['errors'])
    
    #################################################################################################################
    #  Test - Run Self-Tests
    #################################################################################################################  
    if 2 in args.tests:
            
        test = start_test(2,"Nvme-Self-Tests",args.dir)
    
        #-------------------------------------------------------------------
        # Step 1: Run short self-test
        #-------------------------------------------------------------------
        step = start_step("Short-Self-Test",test)

        working_directory = f"{step['directory']}"                             # directory created by start_step for logging
        cmd_file          = os.path.join(cmd_directory,'self-test.cmd.json')   # use cmd file from the specified path

        nvmecmd_args =  [NVMECMD,                         # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                    # cmd file to run the short self-test
                        "--dir",f"{working_directory}",  # log to the directory created by start_step
                        "--nvme",f"{args.nvme}"]         # NVMe drive number 

        step['code'] = run_step_process(nvmecmd_args, working_directory)
        test['errors'] += end_step(step) 
    
        if ("Windows" == platform.system()):
            logger.info("\t\tWaiting 10 minutes for Windows workaround")
            logger.info("")
            time.sleep(600)
        #-------------------------------------------------------------------
        # Step 2: Run extended self-test
        #-------------------------------------------------------------------
        step = start_step("Extended-Self-Test",test)
    
        working_directory = f"{step['directory']}"                             # directory created by start_step for logging
        cmd_file          = os.path.join(cmd_directory,'self-test.cmd.json')   # use cmd file from the specified path

        nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                   # cmd file to run the extended self-test 
                        "--dir",f"{working_directory}",  # log to the directory created by start_step
                        "--extended",                    # run the extended self-test                        
                        "--nvme",f"{args.nvme}"]         # NVMe drive number

        step['code'] = run_step_process(nvmecmd_args, working_directory)
        test['errors'] += end_step(step) 
        script_errors += end_test(test)     
        #-------------------------------------------------------------------
        # If test failed abort so can update the cmd/rules if needed
        #-------------------------------------------------------------------
        if script_errors:
            os._exit(test['errors'])
        
    #################################################################################################################
    #  Test - Check admin command reliability 
    #################################################################################################################
    if 3 in args.tests: 

        test = start_test(3,"Command-Reliability",args.dir)

        #-------------------------------------------------------------------
        # Step 1: Read info, verify against customer features, and compare
        #-------------------------------------------------------------------
        step = start_step("Read-Verify-Compare-1K",test)

        working_directory = f"{step['directory']}"                                   # directory created by start_step for logging
        cmd_file          = os.path.join(cmd_directory,'read.cmd.json')               # use cmd file from the specified path
        rules_file        = os.path.join(rules_directory,'user-features.rules.json')      # use rules file from the specified path
        summary_file      = os.path.join(working_directory,"read.summary.json")

        nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                   # cmd file to read the NVMe information   
                        "--dir",f"{working_directory}",  # log to the directory created by start_step
                        "--rules",f"{rules_file}",       # Verify features rules   
                        "--samples","1000",              # set number of samples to read
                        "--interval","500",              # set interval in mS                                          
                        "--nvme",f"{args.nvme}"]         # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

        step['code'] = run_step_process(nvmecmd_args, working_directory)
        test['errors'] += end_step(step) 
        #-------------------------------------------------------------------
        # Parse the data on the admin commands
        #-------------------------------------------------------------------
        step  = start_step("Log-Admin-Times",test)
        csv_path = os.path.join(step['directory'],"admin_commands.csv")
        step['code'] =  parse_admin_commands( summary_file, csv_path) 
        test['errors'] += end_step(step) 

        script_errors += end_test(test) 
     
    #################################################################################################################
    #  Test - Log Page 2 Sweep (SMART baseline)
    #################################################################################################################
    if 4 in args.tests:

        test = start_test(4,"LogPage02-Sweep",args.dir)
        step = start_step("Read",test)
        logger.info("")

        with open(os.path.join(f"{step['directory']}","logpage2_sweep.csv"), mode='w', newline='') as results_csv_file:

            csv_writer = csv.writer(results_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Idle(ms)','Avg(ms)','Min(ms)','Max(ms)','Count'])

            for interval in idle_times_ms:

                working_directory = os.path.join(f"{step['directory']}",f"{interval}mS")
                os.makedirs(working_directory) 
                cmd_file          = os.path.join(cmd_directory,f"logpage02.cmd.json")  
                summary_file      = os.path.join(working_directory,"read.summary.json")
                csv_path          = os.path.join( working_directory, "admin_commands.csv")

                if interval > 999: sample = 100
                else: sample = 200

                nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                                f"{cmd_file}",                   # cmd file to read the NVMe information   
                                "--samples",f"{sample}",  
                                "--interval",f"{interval}",      # set interval in mS
                                "--dir",f"{working_directory}",  # log to the directory created by start_step                  
                                "--nvme",f"{args.nvme}"]         # NVMe drive number 

                step['code'] += run_step_process(nvmecmd_args, working_directory) 
                avg_ms, min_ms, max_ms, count = get_admin_command("Get Log Page 2", summary_file, csv_path, 2) 
                interval_name = f"Idle {interval}mS then read log page"
                logger.info(f"\t    {interval_name:35} Avg: {avg_ms:6.2f}mS    Min: {min_ms:6.2f}mS    Max: {max_ms:6.2f}mS      Count: {count:6}")
                csv_writer.writerow([f"{interval}",f"{avg_ms}",f"{min_ms}",f"{max_ms}",f"{count}"])

        logger.info("")

        test['errors'] += end_step(step)
        script_errors  += end_test(test) 
    #################################################################################################################
    #  Test - Log Page 3 Sweep  
    #################################################################################################################
    if 5 in args.tests:

            test = start_test(5,"LogPage03-Sweep",args.dir)
            step = start_step("Read",test)
            logger.info("")

            with open(os.path.join(f"{step['directory']}","logpage3_sweep.csv"), mode='w', newline='') as results_csv_file:

                csv_writer = csv.writer(results_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(['Idle(ms)','Avg(ms)','Min(ms)','Max(ms)','Count'])

                for interval in idle_times_ms:

                    working_directory = os.path.join(f"{step['directory']}",f"{interval}mS")
                    os.makedirs(working_directory) 
                    cmd_file          = os.path.join(cmd_directory,f"logpage03.cmd.json")  
                    summary_file      = os.path.join(working_directory,"read.summary.json")
                    csv_path          = os.path.join( working_directory, "admin_commands.csv")

                    if interval > 999: sample = 100
                    else: sample = 200

                    nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                                    f"{cmd_file}",                   # cmd file to read the NVMe information   
                                    "--samples",f"{sample}",         
                                    "--interval",f"{interval}",      # set interval in mS
                                    "--dir",f"{working_directory}",  # log to the directory created by start_step                  
                                    "--nvme",f"{args.nvme}"]         # NVMe drive number 

                    step['code'] += run_step_process(nvmecmd_args, working_directory) 
                    avg_ms, min_ms, max_ms, count = get_admin_command("Get Log Page 3", summary_file, csv_path, 2) 
                    interval_name = f"Idle {interval}mS then read log page"
                    logger.info(f"\t    {interval_name:35} Avg: {avg_ms:6.2f}mS    Min: {min_ms:6.2f}mS    Max: {max_ms:6.2f}mS      Count: {count:6}")
                    csv_writer.writerow([f"{interval}",f"{avg_ms}",f"{min_ms}",f"{max_ms}",f"{count}"])

            logger.info("")

            test['errors'] += end_step(step)
            script_errors +=  end_test(test) 
 
    #################################################################################################################
    #  Setup fio target file if using fio
    #################################################################################################################
    if (6 in args.tests) or (7 in args.tests) or (8 in args.tests):

        temp_fio_target_file = os.path.abspath( os.path.join(args.volume,os.sep,"fio","target.bin"))
        fio_target_file = temp_fio_target_file.replace(":",r"\:")

        working_directory = os.path.join(args.dir,'fio_setup')
        os.makedirs(working_directory)

        try: 
            os.remove(temp_fio_target_file)
        except: 
            pass

        fio_startup_delay = 420                         # delay in seconds before starting fio after monitor to get baseline
        fio_size          = '16g'                       # file size
        fio_end_delay     = 420                         # delay to wait after fio completes, allows drive to cool down
        fio_runtime       = 720                         # time in seconds to run fio

        fio_rand_block_sizes   = ['4k']                 # block sizes for fio
        fio_rand_read_percent  = ['0','100']            # do read and write for fio
        fio_rand_threads       = 1                      # number of threads for fio
        fio_rand_depth         = 8                      # queue depth

        fio_seq_block_sizes   = ['1024k']               # block sizes for fio
        fio_seq_read_percent  = ['0','100']             # do read and write for fio
        fio_seq_threads       = 2                       # number of threads for fio
        fio_seq_depth         = 64                      # queue depth

        fio_base_args = [FIO,                             # path to fio executable
                        "--name=fio-setup",               # name for job
                        f"--ioengine={FIO_ASYNC_IO}",     # asynchronous IO engine (Window/Linux are different)
                        "--direct=1",                     # non-buffered IO
                        "--numjobs=1",                    # Number of threads
                        "--thread",                       # Generate threads 
                        "--rw=write",                     # Access seq for speed 
                        "--iodepth=32",                   # Big queue depth for speed
                        "--bs=1024k",                     # Big block size for speed
                        "--output-format=json",           # Use json output so easy to read and parse later
                        f"--filename={fio_target_file}",  # use one file so generated only once
                        f"--size={fio_size}"]             # size of data
        
        setup_result = run_step_process(fio_base_args, working_directory,300)
        #-------------------------------------------------------------------
        # If test failed abort so can update the cmd/rules if needed
        #-------------------------------------------------------------------
        if setup_result:
            os._exit(1)
    #################################################################################################################
    #  Test - Random Read Sweep
    #################################################################################################################
    if 6 in args.tests:    
            
        test = start_test(6,"Random Read Sweep",args.dir)
        step = start_step("Read",test)

        fio_base_args = [FIO,                             # path to fio executable
                        "--name=fio-burst",               # name for job
                        f"--ioengine={FIO_ASYNC_IO}",     # asynchronous IO engine (Window/Linux are different)
                        "--direct=1",                     # non-buffered IO
                        "--numjobs=1",                    # Number of threads
                        "--thread",                       # Generate threads 
                        "--rw=randread",                  # Access randomly 
                        "--iodepth=1",                    # IO or queue depth
                        "--thinktime_blocks=1",           # read one block then wait
                        "--bs=4k",                        # one 4K block 
                        "--runtime=180",                  # run time in seconds
                        "--time_based",                   # run time specified
                        "--output-format=json",           # Use json output so easy to read and parse later
                        f"--filename={fio_target_file}",  # use one file so generated only once
                        f"--size={fio_size}"]   

        # log summary in a csv file and fio files in subdirectories named after interval time

        with open(os.path.join(f"{step['directory']}","random_read_sweep.csv"), mode='w', newline='') as results_csv_file:

            csv_writer = csv.writer(results_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Idle(ms)','Avg(ms)','Min(ms)','Max(ms)','Count'])

            for interval in idle_times_ms:

                working_directory = os.path.join(f"{step['directory']}",f"{interval}mS")
                os.makedirs(working_directory) 
        
                if interval == 0: thinktime_us = 1
                else: thinktime_us = interval * 1000

                fio_args = fio_base_args.copy()                    

                fio_args.append(f"--output={working_directory}\\fio.json")  
                fio_args.append(f"--thinktime={thinktime_us}")      

                test['errors']  += run_step_process(fio_args, working_directory, 240)

                ref_file = open(f"{working_directory}\\fio.json") 
                json_fio = json.load(ref_file) 
                ref_file.close() 

                min_ms = float(json_fio['jobs'][0]['read']['lat_ns']['min'])/NS_IN_MS 
                max_ms = float(json_fio['jobs'][0]['read']['lat_ns']['max'])/NS_IN_MS 
                avg_ms = float(json_fio['jobs'][0]['read']['lat_ns']['mean'])/NS_IN_MS 
                count  = int(json_fio['jobs'][0]['read']['lat_ns']['N'])

                interval_name = f"Idle {interval}mS then random 4k read"
            
                logger.info(f"\t    {interval_name:40} Avg: {avg_ms:6.2f}mS    Min: {min_ms:6.2f}mS    Max: {max_ms:6.2f}mS      Count: {count:6}")
                csv_writer.writerow([f"{interval}",f"{avg_ms}",f"{min_ms}",f"{max_ms}",f"{count}"])

        logger.info("")

        test['errors'] += end_step(step)
        script_errors +=  end_test(test)           
    #################################################################################################################
    #  Test - Random Performance, single burst, fast monitor
    #################################################################################################################
    if 7 in args.tests: 
            
        test = start_test(7,"Random-Peformance-Monitor",args.dir)

        #-------------------------------------------------------------------
        # Step 1: Start nvmecmd and let run until done 
        #-------------------------------------------------------------------
        step = start_step("Start-Monitor",test)

        working_directory = monitor_directory = f"{step['directory']}"
        cmd_file          = os.path.join(cmd_directory,'logpage02.cmd.json')
        summary_file      = os.path.join(working_directory,"read.summary.json")

        nvmecmd_args =  [NVMECMD,                         # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                    # cmd file to read log page 2 every few seconds until ctrl-c sent to app
                        "--dir",f"{working_directory}",   # run in the working directory
                        "--samples","1000000",            # set number of samples to read
                        "--interval","2000",              # set interval in mS                         
                        "--nvme",f"{args.nvme}"]          # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

        nvmecmd_process, nvmecmd_start_time = start_step_process(nvmecmd_args, working_directory)

        if nvmecmd_process == None:
            logger.error('>>>> FATAL ERROR: nvmecmd failed to start.  Verify nvmecmd installed correctly')
            os._exit(TEST_CASE_EXCEPTION)  

        try:
            nvmecmd_process.wait(fio_startup_delay)
            logger.error('>>>> FATAL ERROR: Test aborted because nvmecmd exited.  Verify NVMe drive number is correct')
            os._exit(TEST_CASE_EXCEPTION)    
        except subprocess.TimeoutExpired:
            pass

        test['errors'] += end_step(step)
        #-------------------------------------------------------------------
        # Run fio
        #-------------------------------------------------------------------
        fio_file_paths  = []  # Save file paths here so can parse later
        
        fio_base_args = [FIO,                             # path to fio executable
                        "--name=fio-burst",               # name for job
                        f"--ioengine={FIO_ASYNC_IO}",     # asynchronous IO engine (Window/Linux are different)
                        "--direct=1",                     # non-buffered IO
                        f"--numjobs={fio_rand_threads}",  # Number of threads
                        "--thread",                       # Generate threads 
                        "--rw=randrw",                    # Access randomly 
                        f"--iodepth={fio_rand_depth}",   # IO or queue depth
                        f"--runtime={fio_runtime}",       # run time in seconds
                        "--time_based",                   # run time specified
                        "--output-format=json",           # Use json output so easy to read and parse later
                        f"--filename={fio_target_file}",  # use one file so generated only once
                        f"--size={fio_size}"]             # size of data
        
        for read_percentage in fio_rand_read_percent:
            for block_size in fio_rand_block_sizes:
                
                step = start_step(f"fio-rd{read_percentage}-bs4K",test)
                working_directory = f"{step['directory']}"         # directory created by start_step for logging
                fio_args = fio_base_args.copy()                    # fresh copy for each step

                fio_args.append(f"--output={working_directory}\\fio.json")  # log to directory created by start_step
                fio_args.append(f"--rwmixread={read_percentage}")           # set read percentage
                fio_args.append(f"--bs={block_size}")                       # set block size
                fio_file_paths.append(f"{working_directory}\\fio.json")     # track log file for later use

                test['errors']    += run_step_process(fio_args, working_directory,(fio_runtime + 300))
                time.sleep(fio_end_delay)

            test['errors'] += end_step(step)
        #-------------------------------------------------------------------
        # Signal nvmecmd to finish to stop monitoring
        #-------------------------------------------------------------------
        step = start_step("Stop-Monitor",test)
        step['code'] =  stop_monitor(monitor_directory, nvmecmd_process)
        test['errors'] += end_step(step)

        #-------------------------------------------------------------------
        # Parse the data on the admin commands
        #-------------------------------------------------------------------
        step  = start_step("Parse-Admin-Commands",test)
        csv_path = os.path.join(step['directory'],"admin_commands.csv")
        step['code'] =  parse_admin_commands( summary_file, csv_path) 
        test['errors'] += end_step(step)

        #-------------------------------------------------------------------
        # Parse the fio data
        #-------------------------------------------------------------------
        step  = start_step("Parse-Fio",test)
        step['code'] =  parse_fio_data(fio_file_paths,temp_fio_target_file)
        test['errors'] += end_step(step)
        script_errors += end_test(test) 

    #################################################################################################################
    #  Test - Sequential Performance, single burst, fast monitor
    #################################################################################################################
    if 8 in args.tests:  
            
        test = start_test(8,"Sequential-Peformance-Monitor",args.dir)

        #-------------------------------------------------------------------
        # Step 1: Start nvmecmd and let run until done 
        #-------------------------------------------------------------------
        step = start_step("Start-Monitor",test)

        working_directory = monitor_directory = f"{step['directory']}"
        cmd_file          = os.path.join(cmd_directory,'logpage02.cmd.json')
        summary_file      = os.path.join(working_directory,"read.summary.json")

        nvmecmd_args =  [NVMECMD,                         # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                    # cmd file to read log page 2 every few seconds until ctrl-c sent to app
                        "--dir",f"{working_directory}",   # run in the working directory
                        "--samples","1000000",            # set number of samples to read
                        "--interval","2000",              # set interval in mS                          
                        "--nvme",f"{args.nvme}"]          # NVMe drive number.  e.g. 0 for nvme0 or physicaldrive0

        nvmecmd_process, nvmecmd_start_time = start_step_process(nvmecmd_args, working_directory)

        if nvmecmd_process == None:
            logger.error('>>>> FATAL ERROR: nvmecmd failed to start.  Verify nvmecmd installed correctly')
            os._exit(TEST_CASE_EXCEPTION)  

        try:
            nvmecmd_process.wait(fio_startup_delay)
            logger.error('>>>> FATAL ERROR: Test aborted because nvmecmd exited.  Verify NVMe drive number is correct')
            os._exit(TEST_CASE_EXCEPTION)    
        except subprocess.TimeoutExpired:
            pass

        test['errors'] += end_step(step)
        #-------------------------------------------------------------------
        # Run fio
        #-------------------------------------------------------------------
        fio_file_paths  = []  # Save file paths here so can parse later
        
        fio_base_args = [FIO,                             # path to fio executable
                        "--name=fio-burst",               # name for job
                        f"--ioengine={FIO_ASYNC_IO}",     # asynchronous IO engine (Window/Linux are different)
                        "--direct=1",                     # non-buffered IO
                        f"--numjobs={fio_seq_threads}",   # Number of threads
                        "--thread",                       # Generate threads 
                        f"--rw=rw",                       # Access randomly 
                        f"--iodepth={fio_seq_depth}",     # IO or queue depth
                        f"--runtime={fio_runtime}",       # run time in seconds
                        "--time_based",                   # run time specified
                        "--output-format=json",           # Use json output so easy to read and parse later
                        f"--filename={fio_target_file}",  # use one file so generated only once
                        f"--size={fio_size}"]             # size of data
        
        for read_percentage in fio_seq_read_percent:
            for block_size in fio_seq_block_sizes:

                step = start_step(f"fio-rd{read_percentage}-bs{block_size}",test)
                working_directory = f"{step['directory']}"         # directory created by start_step for logging
                fio_args = fio_base_args.copy()                    # fresh copy for each step

                fio_args.append(f"--output={working_directory}\\fio.json")  # log to directory created by start_step
                fio_args.append(f"--rwmixread={read_percentage}")           # set read percentage
                fio_args.append(f"--bs={block_size}")                       # set block size

                fio_file_paths.append(f"{working_directory}\\fio.json")     # track log file for later use

                test['errors']    += run_step_process(fio_args, working_directory,(fio_runtime + 300))
                time.sleep(fio_end_delay)

                test['errors'] += end_step(step)
        #-------------------------------------------------------------------
        # Signal nvmecmd to finish to stop monitoring
        #-------------------------------------------------------------------
        step = start_step("Stop-Monitor",test)
        step['code'] =  stop_monitor(monitor_directory, nvmecmd_process)
        test['errors'] += end_step(step)

        #-------------------------------------------------------------------
        # Parse the data on the admin commands
        #-------------------------------------------------------------------
        step  = start_step("Parse-Admin-Commands",test)
        csv_path = os.path.join(step['directory'],"admin_commands.csv")

        step['code'] =  parse_admin_commands( summary_file, csv_path) 

        test['errors'] += end_step(step)
        #-------------------------------------------------------------------
        # Parse the fio data
        #-------------------------------------------------------------------
        step  = start_step("Parse-Fio",test)

        step['code'] =  parse_fio_data(fio_file_paths,temp_fio_target_file)

        test['errors'] += end_step(step)
        script_errors += end_test(test) 

    #################################################################################################################
    #  Test - Compare date and time references
    #################################################################################################################
    if 9 in args.tests:

        test = start_test(9,"Nvme-Compare-Times",args.dir)

        #-------------------------------------------------------------------
        # Step 1: Get latest information
        #-------------------------------------------------------------------
        step = start_step("Read-Drive-Info",test)

        working_directory = f"{step['directory']}"                                   # directory created by start_step for logging
        cmd_file          = os.path.join(cmd_directory,'read.cmd.json')              # use cmd file from the specified path
        last_info_file    = os.path.join(working_directory,"nvme.info.json")         # save this for compare

        nvmecmd_args =  [NVMECMD,                        # path to nvmecmd executable defined in lib
                        f"{cmd_file}",                   # cmd file to read the NVMe information   
                        "--dir",f"{working_directory}",  # log to the directory created by start_step                  
                        "--nvme",f"{args.nvme}"]         # NVMe drive number 

        step['code'] = run_step_process(nvmecmd_args, step['directory'])    # run process in directory created by start_step
        test['errors'] += end_step(step)   
        #-------------------------------------------------------------------
        # Step 2: Compare date and times against the reference
        #-------------------------------------------------------------------
        step  = start_step("Compare-Time",test)
        
        step['code'] = compare_time(ref_info_file, last_info_file)          # this function defined in test.py
        test['errors'] += end_step(step)
        script_errors +=  end_test(test)
    #################################################################################################################
    # Exit the script
    ################################################################################################################# 
    try:    os.remove(temp_fio_target_file)
    except: pass

    os._exit(script_errors)

except:
    logger.exception('ERROR:  Checkout script aborted because of unhandled exception:')
    os._exit(1)
