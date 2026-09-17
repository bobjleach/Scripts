# Get_SA_Log.py
# How to execute:
# on windows: py Get_SA_Log.py -u root -p calvin -i 10.0.0.190
# on Linux: python Get_SA_Log.py.py -u root -p calvin -i 10.0.0.190


import warnings
import logging
import Rest_wrapper
import sys
import re
import atexit
from pathlib import Path
#import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed 
#import io
import argparse
import time


parser = argparse.ArgumentParser(description='Python script using Redfish API DMTF to get server storage inventory')
parser.add_argument('-u', help='iDRAC Username', required=True)
parser.add_argument('-p', help='iDRAC Password.', required=True)
parser.add_argument('-i', help='hostname', required=True)
 

args=vars(parser.parse_args())


User = args['u']
Password = args['p']
Host_Name = args['i']
 

warnings.filterwarnings("ignore")
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)


# Debug
''' 
User= "root"
Password = "Ihatehp2!"
Host_Name = "10.0.0.191" 
'''

# SA Selector values to collect data
# DebugLogs, HWData, OSAppData, TTYLogs, TelemetryReports, GPULogs
# Data_Selector = ['HWData','TTYLogs']
Data_Selector = ['HWData']

 

def Get_Token(My_idrac, HostName, User, Password):
    Results = {}

    URL = f"https://{HostName}/redfish/v1/SessionService/Sessions"
    headers = {'content-type' : 'application/json'}
    User_Info = { 'User' : User, 'Password' : Password }
    Basic_Auth = False
    Valid_Return_Code = [201]
    Body = {'UserName' : User,
		  	'Password' : Password }
 
    
    Results = My_idrac.Post(URL, Valid_Return_Code, headers, Body, Basic_Auth, User_Info)
    if Results['SUCCESS']:
          
        # got valid token
        Array_Items = re.split("/", Results['SESSION_RESULTS'].headers['Location'])
        Session_ID = Array_Items[5]
        Valid_Token = Results['SESSION_RESULTS'].headers['X-Auth-Token']
        Results['Success'] = True
        Results['Array_Items'] = Array_Items
        Results['Session_ID'] = Session_ID
        Results['Token'] = Valid_Token
        return Results
    else:

        # No token
        Results['Success'] = False
        Results['Array_Items'] = 'NONE'
        Results['Session_ID'] = 'NONE'
        Results['Token'] = 'NONE'
        return Results

def Delete_Token(My_idrac, HostName, Token, Session_ID):
    
    
    URL = f"https://{HostName}/redfish/v1/SessionService/Sessions/{Session_ID}"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
    User_Info = {}
    
    Results = My_idrac.Delete(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
    if Results['SUCCESS']:
		 
		# Deleted token
        #print("Deleted Token")
        Results['Success'] = True
        return Results
		 
    else:
        Results['Success'] = False
        return Results

  
def Check_Supported_iDRACs(My_idrac, Token, Host_Name):
        
    URL = f"https://{Host_Name}/redfish/v1/Systems/System.Embedded.1/Storage"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
    if Results['SUCCESS']:
		 
		# Deleted token
        Results['Success'] = True
        return Results
		 
    else:
        Results['Success'] = False
        return Results
    
     

def Get_Model_Service_Tag(My_idrac, Token, Host_Name):  

    # Get model/Service Tag
    URL = f"https://{Host_Name}/redfish/v1/Systems/System.Embedded.1"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
    if Results['SUCCESS']:
        Server_Info = Results['SESSION_RESULTS'].json()
        # Convert to json
        
        Model = Server_Info['Model']
        Sevice_Tag = Server_Info['Oem']['Dell']['DellSystem']['ChassisServiceTag']
        
        Results['Model'] = Model
        Results['Sevice_Tag'] = Sevice_Tag
        return Results

    else:
        
        Results['Model'] = "Unknown"
        Results['Sevice_Tag'] = "Unknown"
        return Results

def Get_iDRAC_Firmware_Version(My_idrac, Token, Host_Name):
     
         
    URL = f"https://{Host_Name}/redfish/v1/Managers/iDRAC.Embedded.1"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
     
    if Results['SUCCESS']:
        # got data
        Data = Results['SESSION_RESULTS'].json()
        iDRAC_Firmware = Data['FirmwareVersion']
         
    else:
        # Could not get idrac firmware
        iDRAC_Firmware = "UNKOWN"

    return iDRAC_Firmware


def Get_EULA_Status(My_idrac, Host_Name, Token):
       
    Return_Results = {}
    URL = f"https://{Host_Name}/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellLCService/Actions/DellLCService.SupportAssistGetEULAStatus"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		       'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Post(URL, Valid_Return_Code, headers, Body, Basic_Auth, User_Info)
    if Results['SUCCESS']:
        Data = Results['SESSION_RESULTS'].json()
        
        for Messages in Data['@Message.ExtendedInfo']:
            if "(EULA)" in Messages['Message']:
                if "not" in Messages['Message']:
                    return "Not Accepted"
                else:
                    return "Accepted"
                    
    else:
        # Could not get ULA status
        return "Unknown"

def Accept_EULA(My_idrac, Host_Name, Token):
    
    Return_Results = {} 

    #Return_Results = {}
    URL = f"https://{Host_Name}/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellLCService/Actions/DellLCService.SupportAssistAcceptEULA"
    Basic_Auth = False
    Valid_Return_Code = [200,202]
    headers = {'content-type' : 'application/json',
		       'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Post(URL, Valid_Return_Code, headers, Body, Basic_Auth, User_Info)
    
    if Results['SUCCESS']: 
        Return_Results['SUCCESS'] = True
        Return_Results['ERROR_MSG'] = "NONE"
        return Return_Results
        
    else:
        Return_Results['SUCCESS'] = False
        Return_Results['ERROR_MSG'] = f"Error: {Results['ERROR_MSG']}"
        return Return_Results
         
def Run_SA_Log( My_idrac, Host_Name, Token, Data_Selector ):
    
    Return_Results = {}

    URL = f"https://{Host_Name}/redfish/v1/Managers/iDRAC.Embedded.1/Oem/Dell/DellLCService/Actions/DellLCService.SupportAssistCollection"
    Basic_Auth = False
    Valid_Return_Code = [202]
    headers = {'content-type' : 'application/json',
		       'X-Auth-Token' : Token }
    User_Info = {}
    
    Body = {"ShareType":"Local",
            "DataSelectorArrayIn" : Data_Selector }

    Results = My_idrac.Post(URL, Valid_Return_Code, headers, Body, Basic_Auth, User_Info)
    if Results['SUCCESS']:
        Job_ID = Results['SESSION_RESULTS'].headers['Location'].split("/")[-1]
        Return_Results['SUCCESS'] = True
        Return_Results['JOB_ID'] = Job_ID
        return Return_Results
    else:
        Return_Results['SUCCESS'] = False
        Return_Results['JOB_ID'] = "NONE"
        return Return_Results

def Check_Job_status_idrac_9( My_idrac, Host_Name, Job_ID, Token):
       

    Return_Results = {}

    MAX_TIME_IN_LOOP = 45  # minutes
    Sleep_Interval =  15  # seconds  

    Loop_flag = True # loop flag
    Start_time = time.monotonic() 

    Do_running_message = True

	# Loop until job complete/failed or max time reached
    while Loop_flag == True:

        # Sleep for time interval
        time.sleep(Sleep_Interval)

		# Check if time elapsed
        Current_time = time.monotonic()
        Total_time = (Current_time - Start_time) / 60 # Convert to minutes

        #print("Total time =", Total_time)

        if Total_time >= MAX_TIME_IN_LOOP:
			# Job did not complete reached MAX time
            Return_Results['EXIT_CODE'] = False
            Return_Results.headers['LOCATION'] = "NONE"
            Return_Results['STATUS'] =  "MAX TIME REACHED"
            return Return_Results
        
         
        URL = f"https://{Host_Name}/redfish/v1/Managers/iDRAC.Embedded.1/Jobs/{Job_ID}"
        Basic_Auth = False
        Valid_Return_Code = [200, 202 ]
        headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
        User_Info = {}
        Body = {}
            
        Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
        if Results['SUCCESS']:
            
            Data = Results['SESSION_RESULTS'].json()
             
            if "Completed" in Data['JobState'] or "complete" in Data['Message']:
                
                Return_Results['EXIT_CODE'] = True
                Return_Results['LOCATION'] = Results['SESSION_RESULTS'].headers["Location"]
                Return_Results['STATUS'] =  "Completed"
                return Return_Results
            
            elif Data["JobState"] == "CompletedWithErrors":
                Return_Results['EXIT_CODE'] = True
                Return_Results['LOCATION'] = Results['SESSION_RESULTS'].headers["Location"]
                Return_Results['STATUS'] =  "Completed with Errors"
                return Return_Results

            
            elif "Fail" in Data["Message"] or "fail" in Data["Message"] or Data["JobState"] == "Failed" or "error" in Data["Message"] or "Error" in Data["Message"]:
                Return_Results['EXIT_CODE'] = False
                Return_Results['LOCATION'] = "NONE"
                Return_Results['STATUS'] =  "Failed"
                return Return_Results
         
        # Try again  
         
          
def Check_Job_status_idrac_10( My_idrac, Host_Name, Job_ID, Token):
       

    Return_Results = {}

    MAX_TIME_IN_LOOP = 45  # minutes
    Sleep_Interval =  15  # seconds  

    Loop_flag = True # loop flag
    Start_time = time.monotonic() 

    Do_running_message = True

	# Loop until job complete/failed or max time reached
    while Loop_flag == True:

        # Sleep for time interval
        time.sleep(Sleep_Interval)

		# Check if time elapsed
        Current_time = time.monotonic()
        Total_time = (Current_time - Start_time) / 60 # Convert to minutes

        #print("Total time =", Total_time)

        if Total_time >= MAX_TIME_IN_LOOP:
			# Job did not complete reached MAX time
            Return_Results['EXIT_CODE'] = False
            Return_Results.headers['LOCATION'] = "NONE"
            Return_Results['STATUS'] =  "MAX TIME REACHED"
            return Return_Results
        
        
        URL = f"https://{Host_Name}/redfish/v1/TaskService/TaskMonitors/{Job_ID}"
        Basic_Auth = False
        Valid_Return_Code = [ 202, 204 ]
        headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
        User_Info = {}
        Body = {}

        Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
        if Results['SUCCESS']:
            
            Status_code = Results['SESSION_RESULTS'].status_code
            
            if Status_code == 204:
                # Sa ready for download

                if "sacollect.zip" in Results['SESSION_RESULTS'].headers["Location"].lower():
                                 
                    Return_Results['EXIT_CODE'] = True
                    Return_Results['LOCATION'] = Results['SESSION_RESULTS'].headers["Location"]
                    Return_Results['STATUS'] =  "Completed"
                    return Return_Results
                else:

                    Return_Results['EXIT_CODE'] = False
                    Return_Results['LOCATION'] = "NONE"
                    Return_Results['STATUS'] =  "SA collection not found"
                    return Return_Results
                       
            else: # SA running must be return code 202

                Status_code = Results['SESSION_RESULTS'].status_code
                            
                try:
                    Data = Results['SESSION_RESULTS'].json()


                except Exception as DataError:
                     # Data error, skip
                     continue
                              
            
                if "Completed" in Data["Oem"]["Dell"]['JobState'] or "complete" in Data["Oem"]["Dell"]['Message'].lower():
                    # Job completed, wait for 204 before exit
                    continue 
                   
                elif Data["Oem"]["Dell"]["JobState"] == "CompletedWithErrors":
                    
                    Return_Results['EXIT_CODE'] = False
                    Return_Results['LOCATION'] = "NONE"
                    Return_Results['STATUS'] =  "Completed with Errors"
                    return Return_Results

            
                elif "Fail" in Data["Oem"]["Dell"]["Message"] or "fail" in Data["Oem"]["Dell"]["Message"] or Data["Oem"]["Dell"]["JobState"] == "Failed" or "error" in Data["Oem"]["Dell"]["Message"] or "Error" in Data["Oem"]["Dell"]["Message"]:
                    
                    Return_Results['EXIT_CODE'] = False
                    Return_Results['LOCATION'] = "NONE"
                    Return_Results['STATUS'] =  "Failed"
                    return Return_Results
         
            
        


def Get_SA_Log( My_idrac, Host_Name, Location, Token, Service_Tag ):
   
    URL = f"https://{Host_Name}{Location}"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
	           'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}
            
    Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
    if Results['SUCCESS']:
        SA_export_filename = Service_Tag + "_SA_Log.zip"
        logging.info(f"SA Log file name: {SA_export_filename}")
        
        with open(SA_export_filename, "wb") as output:
            output.write(Results['SESSION_RESULTS'].content)    

def Get_Idrac_Generation(My_idrac, Token, Host_Name, Model):
    
    # Please add new or missing models 

    # 14G
    if any(x in Model for x in ["R340", "R440", "R540", "R640", "R740", "R740xd", "R740xd2", "T140", "T340", "T440", "C6420", "C6525"]):
        return "9"
    
    #15G
    if any(x in Model for x in ["R520", "R530", "R450", "R550", "R650", "R650xs", "R6515", "R6525", "R750", "R750xs", "R750xa", "R7515", "R7525", "T150", "T350", "C6520", "C6525", "T550", "MX750c", "XR11", "XR12" ]):
        return "9"
    
    #16G
    if any(x in Model for x in ["R260", "R360", "R660", "R660xs", "R6615", "R6625", "R760", "R760xa", "R760xd2", "R760xs", "R7615", "R7625", "R860", "R960", "T160", "T360", "T560", "C6615", "C6620", "MX760c"]):
        return "9"
    
    #17G
    if any(x in Model for x in ["R470", "R570", "R670", "R6715", "R6725", "R770", "R7715", "R7725"]):
        return "10"
    
    return "UNKOWN"
     
    
if __name__ == "__main__": 
    
    warnings.filterwarnings("ignore")
    logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)
         
    # create instance
    My_idrac = Rest_wrapper.REST_wrapper()
     
    # For security, Get Token
    logging.info("Getting token for idrac")
    Token_Results = Get_Token ( My_idrac, Host_Name, User, Password )
    if Token_Results['SUCCESS']:
        
        Token = Token_Results['Token']
        Session_ID = Token_Results['Session_ID']

        # Set up function to delete token upon exit
        atexit.register(Delete_Token, My_idrac, Host_Name, Token, Session_ID)

        #print(f"Token = {Token}")
        #print(f"Session id = {Session_ID}")

    else: 
        logging.warning(f"could not get valid token from server {Host_Name}, Check logon or password,  Aborting!")
        sys.exit(1) 

    # Get Service Tag Information
    Servie_Tag_Results = Get_Model_Service_Tag(My_idrac, Token, Host_Name)
    Service_Tag = Servie_Tag_Results['Sevice_Tag']
    Model = Servie_Tag_Results['Model']

    #print (f"Service tag = {Service_Tag}")
    #print (f"Model = {Model}")

    logging.info("Determining iDRAc generation")
    Generation = Get_Idrac_Generation(My_idrac, Token, Host_Name, Model)
    if Generation == "UNKOWN":
        logging.warning(f"Could not determine idrac generation, Aborting!") 
        sys.exit (1)   
    
    # Check status of EULA
    logging.info("Checking EULA for iDRAC")
    EULA_Results = Get_EULA_Status(My_idrac, Host_Name, Token)
    
    # Accept EULA if not accepted
    if EULA_Results == "Not Accepted":
        
        EULA_Accept = Accept_EULA(My_idrac, Host_Name, Token)
        if EULA_Accept['SUCCESS'] == False:
           logging.warning(f"Could not accept (EULA) for support assits log, Aborting!") 
           sys.exit(1) 

    elif EULA_Results == "UNKOWN": 
        logging.warning(f"Unkown error occured when looking for (EULA), Aborting!")
        sys.exit(1)
    
    # Start Log in idrac

    logging.info(f"Starting SA Log on iDRAC")
    Log_Started = Run_SA_Log( My_idrac, Host_Name, Token,  Data_Selector )    
    if Log_Started['SUCCESS']:
        Job_ID = Log_Started['JOB_ID']
    else:
        logging.warning(f"Could not start SA log, Please try again. Aborting!")
        sys.exit(1)
    
    logging.info(f"Running SA Job ID: {Job_ID}")
    logging.info("Waiting for Job to complete")
    
    # Get SA log
    if Generation == "9":
        
        Completed = Check_Job_status_idrac_9( My_idrac, Host_Name, Job_ID, Token)

    if Generation == "10":
        
        Completed = Check_Job_status_idrac_10( My_idrac, Host_Name, Job_ID, Token)
        
    if Completed['EXIT_CODE']:
        if "Completed with Errors" in Completed['STATUS']:
            logging.warning("SA collection completed with errors, please check iDRAC Lifecycle Logs for more details")
            sys.exit(1)

        logging.info(f"Job Id: {Job_ID} completed")
    else:
        logging.warning("SA collection Failed or is still running past Maximum time, please check iDRAC Lifecycle Logs for more details. Aborting")
        sys.exit(1)
           
    Location = Completed['LOCATION']
     
    # Get SA log and store on disk
    logging.info("Down loading SA log file")
    SA_LOG = Get_SA_Log( My_idrac, Host_Name, Location, Token, Service_Tag )
    
    