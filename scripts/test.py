#--------------------------------------------------------------------------------------------------------------------
#  Simple functions for logging tests and running processes
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
import sys,platform,subprocess,time,os,pathlib,logging,json,shutil,glob,signal,csv 
from datetime import datetime

logFormatter = logging.Formatter("[%(asctime)s]  %(message)s")
logger = logging.getLogger('nvme_logger')

consoleHandler = logging.StreamHandler() 
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)

TEST_CASE_EXCEPTION = 2
USAGE_ERROR_CODE    = 16
READINFO_FAIL_CODE  = 21

NS_IN_MS     = 1000*1000
MS_IN_SEC    = 1000
MS_IN_MIN    = 60*1000
MS_IN_HR     = 60*60*1000
BYTES_IN_GB  = 1000*1000*1000

if ("Windows" == platform.system()):
 
    try:
        import winreg
        access_registry = winreg.ConnectRegistry(None,winreg.HKEY_LOCAL_MACHINE)
        access_key = winreg.OpenKey(access_registry,r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\WinPE")

        NVMECMD = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd','nvmecmd.exe')
        NVMECMD_RESOURCES = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd')
        FIO          = r"\Program Files\fio\fio.exe"
        FIO_ASYNC_IO = "windowsaio"
        DEFAULT_VOLUME = 'c:'
   
    except:
        NVMECMD = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd','nvmecmd.exe')
        NVMECMD_RESOURCES = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd')
        FIO          = r"\Program Files\fio\fio.exe"
        FIO_ASYNC_IO = "windowsaio"
        DEFAULT_VOLUME = 'c:'

else:
    NVMECMD = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd','nvmecmd')
    NVMECMD_RESOURCES = os.path.join(os.environ['NVMEINFO_INSTALL_PATH'],'resources','nvmecmd')

    FIO          = "/opt/nvmeinfo/fio"
    FIO_ASYNC_IO = "libaio"
    DEFAULT_VOLUME = '/'

#--------------------------------------------------------------------------------------------------------------------
# Start and end a test
#--------------------------------------------------------------------------------------------------------------------
def start_test(test_number, test_name, test_dir):

    test = {}
    test["number"]    = test_number
    test["name"]      = test_name
    test["errors"]    = 0
    test["start"]     = time.perf_counter() 
    test['step']      = 0

    now = datetime.now() 

    if test_dir == "":   
        test_dir = os.path.join( '.', f"Test{test_number}-{test_name}", now.strftime("%Y%m%d_%H%M%S"))
        test["directory"] = test_dir
    else:
        test["directory"] = os.path.abspath( os.path.join(f"{test_dir}",f"Test{test_number}-{test_name}" ))

    test["logfile"]  = os.path.join(f"{test_dir}","summary.log")
    logger.info(f" +--------------------------------------------------------------------------------------------------------------------------+ ")
    logger.info(f" | Test {test_number:2} : {test_name:110} |")
    logger.info(f" +--------------------------------------------------------------------------------------------------------------------------+ ")
    return test

def end_test(test):
    if (test["errors"] != 0):  
        logger.info("      **********************************************************************")
        logger.info(f"      ******************         Test {test['number']:2} : FAILED         ******************")
        logger.info("      **********************************************************************")
        return 1
    else:    
        logger.info("      +--------------------------------------------------------------------+")
        logger.info(f"      |                         Test {test['number']:2} : PASS                             |")
        logger.info("      +--------------------------------------------------------------------+")
        return 0
#--------------------------------------------------------------------------------------------------------------------
# Start and end a test step
#--------------------------------------------------------------------------------------------------------------------
def start_step(step_name, test):
    test['step']      = test['step'] + 1

    step = {}
    step['directory'] = os.path.abspath(os.path.join(f"{test['directory']}",f"Step{test['step']}-{step_name}"))
    step['name']      = step_name
    step['logfile']   = test['logfile']
    step['start']     = time.perf_counter() 
    step['code']      = 0

    logger.info(f"      Step {test['step']} : {step_name}")
    logger.info(" ")
    logger.info(f"\t Start:      {time.ctime()}")
    logger.info(f"\t Logs:       {step['directory']}")
    logger.info(" ")

    try:
        os.makedirs(step['directory'])
    except FileExistsError:
        pass
    except:
        logger.error(f">>>> FATAL ERROR:  Failed to make directory {step['directory']}")
        os._exit(TEST_CASE_EXCEPTION)

    return step 

def end_step(step):

    run_time = time.perf_counter() - step['start'] 
    logger.info(f"\t End:        {time.ctime()}  ( {run_time:.3f} seconds )")
    
    if (step["code"] == 0):
        logger.info(f"\t Result:     Passed ")
        logger.info(" ")
        return 0
    else:
        logger.info(f"\t Result:     ********  FAILED  ********  ( Code : {step['code']} )")
        logger.info(" ")
        return 1
#--------------------------------------------------------------------------------------------------------------------
# run, start and verify process
#--------------------------------------------------------------------------------------------------------------------
def run_step_process(args,cwd,timeout=None):

    try: 
        logger.debug(" ")
        for index,arg in enumerate(args): 
            if (index == 0): logger.debug(f"\t Process:    {arg}")
            else:            logger.debug(f"\t               {arg}")
        
        logger.debug(" ")    
        start_time  = time.perf_counter()
        step_process = subprocess.Popen(args, cwd=cwd, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        step_process.wait(timeout)
 
        run_time = time.perf_counter() - start_time 
        logger.debug(f"\t Run Time:      {run_time:.3f} seconds")
        logger.debug(f"\t Return Code:   {step_process.returncode}")
        if (step_process.returncode != 0):
            logger.debug(f"\t Result:        Process failed because returned code {step_process.returncode}")
        else:
            logger.debug(f"\t Result:        PASSED")

        logger.debug(" ")
        return step_process.returncode

    except subprocess.TimeoutExpired:
        os.kill(step_process.pid,signal.SIGKILL)
 
        run_time = time.perf_counter() - start_time 
        logger.debug(f"\t Run Time:      {run_time:.3f} seconds")
        logger.debug(f"\t Result:        Process timed out and was terminated.  Timeout value {timeout} seconds")
        logger.debug(" ")

    else:
        logger.exception('ERROR:  run_step_process had unhandled exception:')

    return 1

def start_step_process(args,cwd):

    try: 
        for index,arg in enumerate(args): 
            if (index == 0): logger.debug(f"\t Process:  {arg}")
            else:            logger.debug(f"\t           {arg}")
        
        logger.debug(" ")   
        start_time = time.perf_counter() 
        return subprocess.Popen(args, cwd=cwd, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL),start_time

    except:
        logger.exception(f"Unhandled exception starting process {args[0]}")
        return None,start_time

def verify_process(running_process,start_time,timeout=None):
 
    try: 
        running_process.wait(timeout)
        run_time = time.perf_counter() - start_time 
        logger.debug(f"\t Run Time:      {run_time:.3f} seconds")
        logger.debug(f"\t Return Code:   {running_process.returncode}")
        if (running_process.returncode != 0):
            logger.debug(f"\t Result:        Process failed because returned code {running_process.returncode}")
        else:
            logger.debug(f"\t Result:        PASSED")

        return running_process.returncode

    except subprocess.TimeoutExpired:
        run_time = time.perf_counter() - start_time 
        logger.debug(f"\t Run Time:      {run_time:.3f} seconds")
        logger.debug(f"\t Result:        Process timed out and was terminated.  Timeout value {timeout} seconds")
    else:
        logger.exception('ERROR:  verify_process had unhandled exception:')

    return 1
#--------------------------------------------------------------------------------------------------------------------
#  Simple function that parses fio data
#--------------------------------------------------------------------------------------------------------------------
def parse_fio_data(fio_file_paths,temp_fio_target_file):

    try:
 
        total_fio_data_read = 0
        total_fio_data_written = 0
        total_fio_run_time = 0

        for file in fio_file_paths:
            ref_file = open(file) 
            json_fio = json.load(ref_file) 
            ref_file.close() 

            fio_data_read = 0
            fio_data_written = 0
            read_bw = 0
            write_bw = 0
          
            for job in range(len(json_fio['jobs'])):

                job_data_read    =  float(json_fio['jobs'][job]['read']['io_bytes'])/BYTES_IN_GB  
                job_data_written =  float(json_fio['jobs'][job]['write']['io_bytes'])/BYTES_IN_GB

                fio_data_read += job_data_read    
                fio_data_written +=  job_data_written 

                if int(json_fio['jobs'][job]['read']['runtime']) != 0:
                    read_bw += job_data_read / (int(json_fio['jobs'][job]['read']['runtime']) / MS_IN_SEC)

                if int(json_fio['jobs'][job]['write']['runtime']) != 0:
                    write_bw += job_data_written/ (int(json_fio['jobs'][job]['write']['runtime']) /MS_IN_SEC)
                       
            width = 40

            logger.info("")
            logger.info(f"\t FIO file : {file}")
            logger.info("")
            logger.info(f"\t {'   Data Read':{width}} {fio_data_read:.3f} GB  ({read_bw:.3f} GB/s)")
            logger.info(f"\t {'   Data Written':{width}} {fio_data_written:.3f} GB  ({write_bw:.3f} GB/s)")  
            logger.info(f"\t {'   Run Time':{width}} {int(json_fio['jobs'][0]['job options']['runtime'])} seconds")

            total_fio_data_read += fio_data_read
            total_fio_data_written += fio_data_written
            total_fio_run_time += int(json_fio['jobs'][0]['job options']['runtime'])

        logger.info("")
        logger.info(f"\t FIO Total :")
        logger.info("")
        logger.info(f"\t {'   Data Read':{width}} {total_fio_data_read:.3f} GB ")
        logger.info(f"\t {'   Data Written':{width}} {total_fio_data_written:.3f} GB")
        logger.info(f"\t {'   Run Time':{width}} {total_fio_run_time} seconds  ({(total_fio_run_time/60.0):.3f} Min)")
        logger.info("")

        return 0
    except:
        return 1


#--------------------------------------------------------------------------------------------------------------------
#  Simple function that stops nvmecmd and displays the SMART data change
#--------------------------------------------------------------------------------------------------------------------
def signal_handler(sig, frame):
    pass

def stop_monitor(monitor_directory,nvmecmd_process):

    error_count = 0
    try:
        
        # nvmecmd must still be running, if not report an error but still try and parse the file
        # ... if still running, as expected, send ctrl-c

        exit_code = nvmecmd_process.poll()
 
        if  exit_code != None: 
            error_count = 1
            logger.error(f"nvmecmd was not running when monitor was stopped.  nvmecmd returned code {exit_code}")
        else:
            signal.signal(signal.SIGINT, signal_handler)
            logger.debug("sending ctrl-c to nvmecmd")
            os.kill(nvmecmd_process.pid,signal.CTRL_C_EVENT)
            logger.debug("waiting for nvmecmd to exit")
            return_code = nvmecmd_process.wait(10)
            logger.debug(f"nvmecmd returned code {return_code}")
        #-------------------------------------------------------------------
        # Create csv monitor file  
        #-------------------------------------------------------------------  
        ref_file = open(os.path.join(monitor_directory,"read.summary.json")) 
        monitor_data = json.load(ref_file) 
        ref_file.close() 
  
        last_sample = len(monitor_data['read details']['sample']) - 1

        sample_rate_sec = float(monitor_data['_settings']['read']['interval in ms']) / MS_IN_SEC

        max_temp = int(monitor_data['read details']['sample'][0]["Composite Temperature"].split()[0].replace(',',''))
 
        tmt1 = int(monitor_data['read details']['sample'][0]["Thermal Management Temperature 1 Time"].split()[0].replace(',',''))
        tmt2 = int(monitor_data['read details']['sample'][0]["Thermal Management Temperature 2 Time"].split()[0].replace(',',''))
        wt   = int(monitor_data['read details']['sample'][0]["Warning Composite Temperature Time"].split()[0].replace(',',''))
        ct   = int(monitor_data['read details']['sample'][0]["Critical Composite Temperature Time"].split()[0].replace(',',''))
        dw   = float(monitor_data['read details']['sample'][0]["Data Written"].split()[0].replace(',',''))
        dr   = float(monitor_data['read details']['sample'][0]["Data Read"].split()[0].replace(',',''))
        bt   = int(monitor_data['read details']['sample'][0]["Controller Busy Time"].split()[0].replace(',',''))

        total_tmt1_delta = int(monitor_data['read details']['sample'][last_sample]["Thermal Management Temperature 1 Time"].split()[0].replace(',','')) - tmt1
        total_tmt2_delta = int(monitor_data['read details']['sample'][last_sample]["Thermal Management Temperature 2 Time"].split()[0].replace(',','')) - tmt2
        total_wt_delta = int(monitor_data['read details']['sample'][last_sample]["Warning Composite Temperature Time"].split()[0].replace(',','')) - wt
        total_ct_delta = int(monitor_data['read details']['sample'][last_sample]["Critical Composite Temperature Time"].split()[0].replace(',','')) - ct
        total_bt_delta = int(monitor_data['read details']['sample'][last_sample]["Controller Busy Time"].split()[0].replace(',','')) - bt

        total_dr_delta = float(monitor_data['read details']['sample'][last_sample]["Data Read"].split()[0].replace(',','')) - dr
        total_dw_delta = float(monitor_data['read details']['sample'][last_sample]["Data Written"].split()[0].replace(',','')) - dw


        with open(os.path.join(monitor_directory,"monitor.csv"), mode='w', newline='') as monitor_csv_file:
            csv_writer = csv.writer(monitor_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            csv_writer.writerow(['Timestamp','Temp(C)','DeltaRead(GB/sec)','DeltaWritten(GB/sec)','DeltaTMT1(Sec)','DeltaTMT2(Sec)',
                                'DataRead(GB)','DataWritten(GB)','TMT1(Sec)','TMT2(Sec)','WarningThrottle(Min)','CriticalThrottle(Min)','BusyTime(Min)'])

            for sample in monitor_data['read details']['sample']: 

                if (max_temp < int(sample["Composite Temperature"].split()[0].replace(',',''))):
                    max_temp = int(sample["Composite Temperature"].split()[0].replace(',',''))

                delta_dr = (float(sample["Data Read"].split()[0].replace(',','')) - dr)/sample_rate_sec
                delta_dw = (float(sample["Data Written"].split()[0].replace(',','')) - dw)/sample_rate_sec
                delta_tmt1 = float(sample["Thermal Management Temperature 1 Time"].split()[0].replace(',','')) - tmt1
                delta_tmt2 = float(sample["Thermal Management Temperature 2 Time"].split()[0].replace(',','')) - tmt2

                tmt1 = int(sample["Thermal Management Temperature 1 Time"].split()[0].replace(',',''))
                tmt2 = int(sample["Thermal Management Temperature 2 Time"].split()[0].replace(',',''))
                wt   = int(sample["Warning Composite Temperature Time"].split()[0].replace(',',''))
                ct   = int(sample["Critical Composite Temperature Time"].split()[0].replace(',',''))
                dw   = float(sample["Data Written"].split()[0].replace(',',''))
                dr   = float(sample["Data Read"].split()[0].replace(',',''))
                bt   = int(sample["Controller Busy Time"].split()[0].replace(',',''))

                csv_writer.writerow([sample["timestamp"],sample["Composite Temperature"].split()[0],
                                    f"{delta_dr:.3f}",f"{delta_dw:.3f}",f"{delta_tmt1}",f"{delta_tmt2}",
                                    f"{dr:.3f}",f"{dw:.3f}",f"{tmt1}",f"{tmt2}",f"{wt}",f"{ct}",f"{bt}"])
        
        logger.info("")
        logger.info("\t   The maximum temperature was :    " + str(max_temp) + " C")
        logger.info("")
        logger.info("\t   The TMT1 throttle time was :     " + str(total_tmt1_delta) + " sec")
        logger.info("\t   The TMT2 throttle time was :     " + str(total_tmt2_delta) + " sec")
        logger.info("\t   The warning throttle time was  : " + str(total_wt_delta) + " min")
        logger.info("\t   The critical throttle time was : " + str(total_ct_delta) + " min")
        logger.info("")
        logger.info(f"\t   The total data read was :        {total_dr_delta:.3f} GB")
        logger.info(f"\t   The total data written was :     {total_dw_delta:.3f} GB")
        logger.info("")
        logger.info(f"\t   The controller busy time was :   {total_bt_delta} Min")
        logger.info("")
        signal.signal(signal.SIGINT, signal.default_int_handler)

        return 0
    except:
        return 1

#--------------------------------------------------------------------------------------------------------------------
#  Simple function that parses read summary file to get info on admin commands
#--------------------------------------------------------------------------------------------------------------------
def parse_admin_commands(file_path, csv_path, skip = 0,prefix="",verbose = False):
  
    try:
        ref_file = open(file_path) 
        summary_data = json.load(ref_file) 
        ref_file.close() 

        each_command = {}
        all_commands = []
        error_count  = 0 
        total = 0
       
        with open(csv_path, mode='w', newline='') as times_csv_file:
                csv_writer = csv.writer(times_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

                csv_writer.writerow(['Timestamp','Command','Time(mS)','ReturnCode','Bytes'])
                count = 0
                for entry in summary_data['command times']: 
                    if count >= skip:
                        all_commands.append(entry['time in ms'])
                        if entry['admin command'] not in each_command: each_command[entry['admin command']] = []  
                        each_command[entry['admin command']].append(entry['time in ms'])
                        if int(entry['return code']) != 0: 
                            error_count += 1

                        csv_writer.writerow([entry['timestamp'],entry['admin command'],entry['time in ms'],entry['return code'],entry['bytes returned']])
                    count = count + 1

        for command in each_command:
            average = sum(each_command[command])/len(each_command[command])
            total += average
            logger.info(f"\t   {prefix} {command:35} Avg: {average:6.2f}mS    Min: {min(each_command[command]):6.2f}mS    Max: {max(each_command[command]):6.2f}mS      Count: {len(each_command[command]):6}    ")
        
        if len(each_command) > 1:
            average = sum(all_commands)/len(all_commands) 
            logger.info(" ")
            logger.info(f"\t   {prefix} {'All Commands':35} Avg: {average:6.2f}mS    Min: {min(all_commands):6.2f}mS    Max: {max(all_commands):6.2f}mS      Count: {len(all_commands):6}    ")

        if error_count != 0:
            logger.info(" ")
            logger.info(f"\t   {error_count} admin commands completed with errors! ")

        if verbose:
            prior_timestamp = None
            timestamp_deltas = []
            run_times_ms = []
            for sample in summary_data['read details']['sample']: 
                if prior_timestamp != None: 
                    timestamp_deltas.append( (datetime.strptime(sample['timestamp'], "%Y-%m-%d %H:%M:%S.%f") - prior_timestamp).total_seconds() )
                prior_timestamp = datetime.strptime(sample['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
                run_times_ms.append(float(sample['run time'].split()[0]))

            logger.info(" ")
            logger.info("\t Timestamp Deltas:")
            logger.info(" ")
            average = sum(timestamp_deltas)/len(timestamp_deltas)
            logger.info(f"\t   Max: {max(timestamp_deltas):6.3f}sec   Min: {min(timestamp_deltas):6.3f}sec    Count: {len(timestamp_deltas):6}    Avg: {average:6.3f}sec")
                
            logger.info(" ")
            logger.info("\t Run Times (Read, Verify, Compare, Log):")
            logger.info(" ")
            average = sum(run_times_ms)/len(run_times_ms)
            logger.info(f"\t   Max: {max(run_times_ms):6.2f}mS   Min: {min(run_times_ms):6.2f}mS    Count: {len(run_times_ms):6}    Avg: {average:6.2f}mS")  
        
        logger.info("")    
        return 0
    except Exception as e:
        logger.error('Parse admin commands failed with exception: '+ str(e))
        return 1
        
#--------------------------------------------------------------------------------------------------------------------
#  Simple function that parses read summary file to get info on admin commands
#--------------------------------------------------------------------------------------------------------------------
def get_admin_command(name, file_path, csv_path, skip = 0):
  
    try:
        ref_file = open(file_path) 
        summary_data = json.load(ref_file) 
        ref_file.close() 
         
        each_command = {}
        error_count  = 0 
       
        with open(csv_path, mode='w', newline='') as times_csv_file:
            csv_writer = csv.writer(times_csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(['Timestamp','Command','Time(mS)','ReturnCode','Bytes'])
            count = 0
            for entry in summary_data['command times']: 
                if count >= skip:
                    if entry['admin command'] not in each_command: each_command[entry['admin command']] = []  
                    each_command[entry['admin command']].append(entry['time in ms'])

                    csv_writer.writerow([entry['timestamp'],entry['admin command'],entry['time in ms'],entry['return code'],entry['bytes returned']])
                count = count + 1

        average = sum(each_command[name])/len(each_command[name])
        return average, min(each_command[name]), max(each_command[name]), len(each_command[name])

    except Exception as e:
        logger.error('Failed to get admn command with exception: '+ str(e))
        return 0,0,0,0


#--------------------------------------------------------------------------------------------------------------------
#  Simple function that compares host and drive timestamps and power on hours
#
#  The host timestamp will always be available but the drive timestamp may not.  If available the timestamp can be a 
#  calendar date/time of time since controller reset.  The drive timestamp can also be stopped in some conditions.   
#  Drive power on hours are always available but have low resolution.
#
#  Suspect the timestamp is used in the persistent event log so would be important to be accurate for devices that
#  have the persistent log
#--------------------------------------------------------------------------------------------------------------------
def compare_time(ref_info_file, last_info_file):

    try:
        ref_file = open(ref_info_file)                  
        ref_data = json.load(ref_file) 
        ref_file.close() 

        ref_file = open(last_info_file) 
        last_data = json.load(ref_file) 
        ref_file.close() 

        logger.info(f"\t {'Host Start':35} {ref_data['nvme']['parameters']['Host Timestamp Decoded']['value']}")
        logger.info(f"\t {'Host End':35} {last_data['nvme']['parameters']['Host Timestamp Decoded']['value']}")
        logger.info("")

        host_start = int(ref_data['nvme']['parameters']['Host Timestamp']['value'].split()[0].replace(',',''))
        host_end   = int(last_data['nvme']['parameters']['Host Timestamp']['value'].split()[0].replace(',',''))
        host_time_ms =  host_end - host_start

        poh_start = int(ref_data['nvme']['parameters']["Power On Hours"]["value"].replace(',',''))
        poh_end = int(last_data['nvme']['parameters']["Power On Hours"]["value"].replace(',',''))
        poh_time_hrs = poh_end - poh_start
    
        # check if drive supports timestamp feature, if so use it

        if "Timestamp Feature" in ref_data['nvme']['parameters'] and ref_data['nvme']['parameters']["Timestamp Feature"]["value"] == "Supported":
 
            # If timestamp was from host the decoded value is the calendar date/time

            if ref_data['nvme']['parameters']["Timestamp Origin"]["value"] == "Host Programmed" and last_data['nvme']['parameters']["Timestamp Origin"]["value"] == "Host Programmed":
                
                drive_start = int(ref_data['nvme']['parameters']["Timestamp"]["value"].split()[0].replace(',',''))
                drive_end   = int(last_data['nvme']['parameters']["Timestamp"]["value"].split()[0].replace(',',''))

                drive_time_ms =  drive_end - drive_start
                host_delta_ms = host_time_ms - drive_time_ms
                host_start_delta = drive_start - host_start
                host_end_delta = drive_end - host_end

                logger.info(f"\t {'Drive Start':35} {ref_data['nvme']['parameters']['Timestamp Decoded']['value']}   (Host Delta: {host_start_delta/MS_IN_HR:,.3f} hours {host_start_delta/MS_IN_SEC:,.3f} sec)")   
                logger.info(f"\t {'Drive End':35} {last_data['nvme']['parameters']['Timestamp Decoded']['value']}   (Host Delta: {host_end_delta/MS_IN_HR:,.3f} hours {host_end_delta/MS_IN_SEC:,.3f} sec))")     
                logger.info(" ")
                logger.info(f"\t {'Host Timestamp Change':35} {host_time_ms/MS_IN_HR:.1f} hours  {host_time_ms/MS_IN_SEC:,.3f} sec")
                logger.info(f"\t {'Drive Timestamp Change':35} {drive_time_ms/MS_IN_HR:.1f} hours  {drive_time_ms/MS_IN_SEC:,.3f} sec   (Host Delta: {host_delta_ms:,} mS)")
                logger.info(f"\t {'Drive Timestamp Stopped':35} {last_data['nvme']['parameters']['Timestamp Stopped']['value']}")
                logger.info(f"\t {'Drive Power On Hours Change':35} {poh_time_hrs} hours")
                logger.info("")

            # if timestamp was from reset then decoded value is time since reset

            elif ref_data['nvme']['parameters']["Timestamp Origin"]["value"] != "Host Programmed" and last_data['nvme']['parameters']["Timestamp Origin"]["value"] != "Host Programmed":

                drive_start = int(ref_data['nvme']['parameters']["Timestamp"]["value"].split()[0].replace(',',''))
                drive_end   = int(last_data['nvme']['parameters']["Timestamp"]["value"].split()[0].replace(',',''))
                drive_time_ms =  drive_end - drive_start
                host_delta_ms = host_time_ms - drive_time_ms
 
                logger.info(f"\t {'Drive Start':35} {ref_data['nvme']['parameters']['Timestamp Decoded']['value']}   (Time since controller reset)")   
                logger.info(f"\t {'Drive End':35} {last_data['nvme']['parameters']['Timestamp Decoded']['value']}   (Time since controller reset)")
                logger.info(" ")
                logger.info(f"\t {'Host Timestamp Change':35} {host_time_ms/MS_IN_HR:.1f} hours  {host_time_ms/MS_IN_SEC:,.3f} sec")
                logger.info(f"\t {'Drive Timestamp Change':35} {drive_time_ms/MS_IN_HR:.1f} hours  {drive_time_ms/MS_IN_SEC:,.3f} sec   (Host Delta: {host_delta_ms:,} mS)")
                logger.info(f"\t {'Drive Timestamp Stopped':35} {last_data['nvme']['parameters']['Timestamp Stopped']['value']}")
                logger.info(f"\t {'Drive Power On Hours Change':35} {poh_time_hrs} hours")
                logger.info("")

            # Origin changed between ref and last info so can't get the delta

            else:
                logger.info(" ")
                logger.info(f"\t {'Host Timestamp Change':35} {host_time_ms/MS_IN_HR:.1f} hours  {host_time_ms/MS_IN_SEC:,.3f} sec")
                logger.info(f"\t {'Drive Timestamp Change':35} Not available because timestamp origin changed between start and end")
                logger.info(f"\t {'Drive Timestamp Stopped':35} {last_data['nvme']['parameters']['Timestamp Stopped']['value']}")
                logger.info(f"\t {'Drive Power On Hours Change':35} {poh_time_hrs} hours")                
                logger.info("")

        else:
            logger.info(f"\t {'Host Timestamp Change':35} {host_time_ms/MS_IN_HR:.1f} hours  {host_time_ms/MS_IN_SEC:,.3f} sec")
            logger.info(f"\t {'Drive Power On Hours Change':35} {poh_time_hrs} hours")
            logger.info("")

        return 0

    except:
        logger.exception('Compare Time failed with exception')
        return 1

#--------------------------------------------------------------------------------------------------------------------
#  Simple function that displays a summary of the drive features
#
#  Reads the nvme.info.json file and displays a report.  The content and format can be easily adjusted to meet user
#  specific needs
#--------------------------------------------------------------------------------------------------------------------
def log_report(ref_info_file, nvme, standalone):

    try:            
        ref_file = open(ref_info_file)                  # Read in the info from json file
        source_info = json.load(ref_file) 
        ref_file.close() 

        kwidth = 55                                     # Width of first field for display and log file
        indent = 10
        parameters = source_info['nvme']['parameters']  # short hand for readability
        
        if standalone:
            indent = 1
            logger.info(f"{' ':{indent}} -------------------------------------------------------------------------------------------")
            logger.info(f"{' ':{indent}}  NVME DRIVE {nvme}")
            logger.info(f"{' ':{indent}} -------------------------------------------------------------------------------------------")   
 
        logger.info(f"{' ':{indent}}{'    Vendor':{kwidth}} {parameters['Subsystem Vendor']['value']}")
        logger.info(f"{' ':{indent}}{'    Model':{kwidth}} {parameters['Model Number (MN)']['value']}")
        logger.info(f"{' ':{indent}}{'    Serial Number':{kwidth}} {parameters['Serial Number (SN)']['value']}")
        logger.info(f"{' ':{indent}}{'    IEEE OUI Identifier':{kwidth}} {parameters['IEEE OUI Identifier (IEEE)']['value']}")      
        logger.info(f"{' ':{indent}}{'    Namespace 1 EUID':{kwidth}} {parameters['Namespace 1 IEEE Extended Unique Identifier (EUI64)']['value']}")   
        logger.info(f"{' ':{indent}}{'    Namespace 1 NGUID':{kwidth}} {parameters['Namespace 1 Globally Unique Identifier (NGUID)']['value']}")   
        logger.info(f"{' ':{indent}}{'    Firmware':{kwidth}} {parameters['Firmware Revision (FR)']['value']}")  
        logger.info(f"{' ':{indent}}{'    Size':{kwidth}} {parameters['Size']['value']}")  
        logger.info(f"{' ':{indent}}{'    NVMe Version':{kwidth}} {parameters['Version (VER)']['value']}")  

        logger.info("")
        logger.info(f"{' ':{indent}}{'    Percentage Used':{kwidth}} {parameters['Percentage Used']['value']}")
        logger.info(f"{' ':{indent}}{'    Data Read':{kwidth}} {parameters['Data Read']['value']}")
        logger.info(f"{' ':{indent}}{'    Data Written':{kwidth}} {parameters['Data Written']['value']}")    
        logger.info(f"{' ':{indent}}{'    Power-On Hours':{kwidth}} {parameters['Power On Hours']['value']}")
        logger.info(f"{' ':{indent}}{'    Power Cycles':{kwidth}} {parameters['Power Cycles']['value']}")
        logger.info(f"{' ':{indent}}{'    Available Spare':{kwidth}} {parameters['Available Spare']['value']}")

        logger.info("")
        logger.info(f"{' ':{indent}}{'    Composite Temperature':{kwidth}} {parameters['Composite Temperature']['value']}")
        logger.info(f"{' ':{indent}}{'    Thermal Management Temperature 1 (TMT1)':{kwidth}} {parameters['Thermal Management Temperature 1 (TMT1)']['value']}")
        logger.info(f"{' ':{indent}}{'    Thermal Management Temperature 2 (TMT2)':{kwidth}} {parameters['Thermal Management Temperature 2 (TMT2)']['value']}")
        logger.info(f"{' ':{indent}}{'    Warning Composite Temperature Threshold (WCTEMP)':{kwidth}} {parameters['Warning Composite Temperature Threshold (WCTEMP)']['value']}")
        logger.info(f"{' ':{indent}}{'    Critical Composite Temperature Threshold (CCTEMP)':{kwidth}} {parameters['Critical Composite Temperature Threshold (CCTEMP)']['value']}")
        logger.info(f"{' ':{indent}}{'    Thermal Management Temperature 1 Time':{kwidth}} {parameters['Thermal Management Temperature 1 Time']['value']}")
        logger.info(f"{' ':{indent}}{'    Thermal Management Temperature 2 Time':{kwidth}} {parameters['Thermal Management Temperature 2 Time']['value']}")
        logger.info(f"{' ':{indent}}{'    Warning Composite Temperature Time':{kwidth}} {parameters['Warning Composite Temperature Time']['value']}")
        logger.info(f"{' ':{indent}}{'    Critical Composite Temperature Time':{kwidth}} {parameters['Critical Composite Temperature Time']['value']}")

        logger.info("")
        logger.info(f"{' ':{indent}}{'    Critical Warnings':{kwidth}} {parameters['Critical Warnings']['value']}")
        logger.info(f"{' ':{indent}}{'    Media and Data Integrity Errors':{kwidth}} {parameters['Media and Data Integrity Errors']['value']}")
        logger.info(f"{' ':{indent}}{'    Number Of Failed Self-Tests':{kwidth}} {parameters['Number Of Failed Self-Tests']['value']}")
        logger.info("")

        # Create a table with power information, Windows doesn't support APST, it uses a power plan to define when to change power states

        if ("Windows" == platform.system()):

            logger.info(f"{' ':{indent}}{'    Windows Power Plan':{kwidth}} {parameters['Windows Power Plan']['value']}")
            # Check if on battery or not because power plan is different

            if parameters['Host Power Source'] == "Battery":
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Timeout 1':{kwidth}} {parameters['Windows Power NVMe Timeout 1 (DC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Timeout 2':{kwidth}} {parameters['Windows Power NVMe Timeout 2 (DC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Latency Limit 1':{kwidth}} {parameters['Windows Power NVMe Latency 1 (DC)']['value']}.  After timeout #1, change to lowest power state with entry+exit latency less than this")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Latency Limit 2':{kwidth}} {parameters['Windows Power NVMe Latency 2 (DC)']['value']}.  After timeout #2, change to lowest power state with entry+exit latency less than this")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan PCIe ASPM':{kwidth}} {parameters['Windows Power ASPM (DC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan NOPPME':{kwidth}} {parameters['Windows Power NOPPME (DC)']['value']}")
             
            else:
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Timeout 1':{kwidth}} {parameters['Windows Power NVMe Timeout 1 (AC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Timeout 2':{kwidth}} {parameters['Windows Power NVMe Timeout 2 (AC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Latency Limit 1':{kwidth}} {parameters['Windows Power NVMe Latency 1 (AC)']['value']}.  After timeout 1, change to lowest power state with entry+exit latency less than this")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan Latency Limit 2':{kwidth}} {parameters['Windows Power NVMe Latency 2 (AC)']['value']}.  After timeout 2, change to lowest power state with entry+exit latency less than this")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan PCIe ASPM':{kwidth}} {parameters['Windows Power ASPM (AC)']['value']}")
                logger.info(f"{' ':{indent}}{'    Windows Power Plan NOPPME':{kwidth}} {parameters['Windows Power NOPPME (AC)']['value']}")
         
            logger.info("")
              
        # Linux uses APST as far as I can tell
 
        try:
            if parameters['Autonomous Power State Transition']['value'] == "Supported":
                logger.info(f"{' ':{indent}}{'    Autonomous Power State Transitions':{kwidth}} {parameters['Autonomous Power State Transition']['value']} and {parameters['Autonomous Power State Transition Enable (APSTE)']['value']}")
            else:
                logger.info(f"{' ':{indent}}{'    Autonomous Power State Transitions':{kwidth}} {parameters['Autonomous Power State Transition']['value']}")
        except:
                logger.info(f"{' ':{indent}}{'    Autonomous Power State Transitions':{kwidth}} Not Supported")

        try:
            if parameters['Non-Operational Power State Permissive Mode']['value'] == "Supported":
                logger.info(f"{' ':{indent}}{'    Non-Operational Power State Permissive Mode':{kwidth}} {parameters['Non-Operational Power State Permissive Mode']['value']} and {parameters['Non-Operational Power State Permissive Mode Enable (NOPPME)']['value']}")
            else:
                logger.info(f"{' ':{indent}}{'    Non-Operational Power State Permissive Mode':{kwidth}} {parameters['Non-Operational Power State Permissive Mode']['value']}")
        except:
            logger.info(f"{' ':{indent}}{'    Non-Operational Power State Permissive Mode':{kwidth}} Not Supported")
        
        logger.info("")
        logger.info(f"{' ':{indent}}    -------------------------------------------------------------------------------------------------------------------------------------")
        logger.info(f"{' ':{indent}}    State   NOP    Max        Active     Idle       Entry Latency   Exit Latency    ITPT          ITPS     RWL   RWT   RRL   RRT")
        logger.info(f"{' ':{indent}}    -------------------------------------------------------------------------------------------------------------------------------------")
        for state in range(int(parameters['Number of Power States Support (NPSS)']['value'])):
            power_state = f"{' ':{indent}}    {state:<8}"

            if (parameters[f"Power State {state} Non-Operational State (NOPS)"]['value'] == "True"): 
                power_state += f"{'Yes':7}"
            else: 
                power_state += f"{' ':7}"

            if (parameters[f"Power State {state} Maximum Power (MP)"]['value'] == "Not Reported"): 
                power_state += f"{' ':11}"
            else: 
                power_state += f"{parameters[f'Power State {state} Maximum Power (MP)']['value'].split()[0]+' W':11}"

            if (parameters[f"Power State {state} Active Power (ACTP)"]['value'] == "Not Reported"): 
                power_state += f"{' ':11}"
            else: 
                power_state += f"{parameters[f'Power State {state} Active Power (ACTP)']['value'].split()[0]+' W':11}"

            if (parameters[f"Power State {state} Idle Power (IDLP)"]['value'] == "Not Reported"): 
                power_state += f"{' ':11}"
            else: 
                power_state += f"{parameters[f'Power State {state} Idle Power (IDLP)']['value'].split()[0]+' W':11}"

            if (parameters[f"Power State {state} Entry Latency (ENLAT)"]['value'] == "Not Reported"): 
                power_state += f"{' ':16}"
            else: 
                power_state += f"{parameters[f'Power State {state} Entry Latency (ENLAT)']['value'].split('(')[0]:16}"

            if (parameters[f"Power State {state} Exit Latency (EXLAT)"]['value'] == "Not Reported"): 
                power_state += f"{' ':16}"
            else: 
                power_state += f"{parameters[f'Power State {state} Exit Latency (EXLAT)']['value'].split('(')[0]:16}"

            if f"Power State {state} Idle Time Prior to Transition (ITPT)" in parameters:
                power_state += f"{parameters[f'Power State {state} Idle Time Prior to Transition (ITPT)']['value'].split('(')[0]:14}"
            else: 
                power_state += f"{' ':14}"

            if f"Power State {state} Idle Transition Power State (ITPS)" in  parameters:
                power_state += f"{parameters[f'Power State {state} Idle Transition Power State (ITPS)']['value'].split('(')[0]:9}"
            else: 
                power_state += f"{' ':9}"

            power_state += f"{parameters[f'Power State {state} Relative Write Latency (RWL)']['value']:6}"  
            power_state += f"{parameters[f'Power State {state} Relative Write Throughput (RWT)']['value']:6}"  
            power_state += f"{parameters[f'Power State {state} Relative Read Latency (RRL)']['value']:6}"  
            power_state += f"{parameters[f'Power State {state} Relative Read Throughput (RRT)']['value']:6}"  

            logger.info(power_state)

        # Create a table with PCI information

        logger.info("")
        logger.info(f"{' ':{indent}}    -------------------------------------------------------------------------------------------------------------------------------------")
        logger.info(f"{' ':{indent}}    PCI        Vendor       Vendor ID    Device ID    Width             Speed                                 Location")
        logger.info(f"{' ':{indent}}    -------------------------------------------------------------------------------------------------------------------------------------")
        logger.info(f"{' ':{indent}}{'    Endpoint':{15}}{parameters['Controller Vendor']['value']:13}" + 
                    f"{parameters['PCI Vendor ID (VID)']['value']:13}" +
                    f"{parameters['PCI Device ID']['value']:13}" + 
                    f"{parameters['PCI Width']['value']} (Rated: {parameters['PCI Rated Width']['value']})    " +
                    f"{parameters['PCI Speed']['value']} (Rated: {parameters['PCI Rated Speed']['value']})    " +
                    f"{parameters['PCI Location']['value']} ")

        logger.info(f"{' ':{indent}}{'    Root':{15}}{' ':13}{parameters['Root PCI Vendor ID']['value']:13}" +
                    f"{parameters['Root PCI Device ID']['value']:13}{' ':56}" +
                    f"{parameters['Root PCI Location']['value']} ")

        logger.info("")
        return 0

    except:
        logger.exception('Failed to log report with exception')
        return 1
 
