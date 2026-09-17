
# on windows: py DriveEndurance.py -u root -p calvin -o outputfile -i InputHostFile
# on Linux: python DriveEndurance.py -u root -p calvin -o outputfile -i InputHostFile

import warnings
import logging
import Rest_wrapper
import sys
import re
import atexit
from pathlib import Path
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed 
import io
import argparse


parser = argparse.ArgumentParser(description='Python script using Redfish API DMTF to get server storage inventory')
parser.add_argument('-u', help='iDRAC Username', required=True)
parser.add_argument('-p', help='iDRAC Password.', required=True)
parser.add_argument('-o', help='Output file Name.', required=True)
parser.add_argument('-i', help='Input file Name. (hosts)', required=True)

args=vars(parser.parse_args())


User = args['u']
Password = args['p']
Input_File_Name = args['i']
Base_Output_file_name = args['o']

warnings.filterwarnings("ignore")
logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.INFO)

'''
# Debug
Input_File_Name = 'Hosts.txt'
User= "oseadmin"
Password = "***********"
Base_Output_file_name = 'DiskResults'
'''

 

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

def Read_File(Input_File_Name):
    
    # check file existance
    file_path = Path(Input_File_Name)
    
    if file_path.is_file():
        logging.info(f"Found input file: {Input_File_Name}")
        with open(Input_File_Name) as f:
            return f.read().splitlines()   # Read line at a time
    else:
        logging.warning(f"File {Input_File_Name} does not exist")
        empty = []
        return empty

def Flush_Buffer(Msg):
    # lock thread, print buffer, free lock
    #print("in print lock") 
    with print_lock:
        try:
            # Write buffer to file
            file = open(Output_File_Name, 'a')
            #file.write(thread_local.buffer.getvalue())
            file.write(Msg)
             
            # clear buffer
            #thread_local.buffer = io.StringIO()
            file.close()
          
    
        except FileNotFoundError as e:
            logging.warning(f"Could not open filename: {Output_File_Name}, for appending results, Aborting!")
            logging.warning("Details:", e)
            print("file not found")
        
    
        except OSError as e:
            logging.warning(f"Error: An OS error occurred while appending to file {Output_File_Name}, Aborting!")
            logging.warning("Details:", e)
            #sys.stdout.write(thread_local.buffer.getvalue())
            #thread_local.buffer.close()
            #del thread_local.buffer
            print("os error")

def Create_Output_file( Output_file_Name ):
     
    # Create Unique output file name using date time in format FileName-2026-01-07T09:14:34.txt
    # happens befroe threading occures
    dt_string = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    Output_file = Output_file_Name + '-' + dt_string + '.csv'
     
        
    try:
        # Write header to the file
        file = open(Output_file, 'w')
        file.write("Hostname,Server Model,Server Service Tag,idrac Firmware,Controller,Controller Name,Disk Remaining Life Endurance,Available Spare %,Disk Model,Disk Manufacturer,Disk Serial Number,Drive ID,Disk Description,Disk Predictive Failure State\n")
        file.close()
        return Output_file 
    
    except FileNotFoundError as e:
        logging.warning(f"Could not open filename: {Output_file_Name}, Aborting!")
        logging.warning("Details:", e)
        return "NULL"
    
    except OSError as e:
            logging.warning("Error: An OS error occurred while writing the file,Aborting!")
            logging.warning("Details:", e)
            return "NULL"

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

def Get_Disk_Info(Host_Name, Output_File_Name):

    logging.info(f"Task Running on host: {Host_Name}")
    # create instance
    My_idrac = Rest_wrapper.REST_wrapper()

     

    # For security, Get Token
     
    Results = Get_Token ( My_idrac, Host_Name, User, Password )
    if Results['SUCCESS']:
        
        Token = Results['Token']
        Session_ID = Results['Session_ID']

        # Set up function to delete token upon exit
        atexit.register(Delete_Token, My_idrac, Host_Name, Token, Session_ID)

        #print(f"Token = {Token}")
        #print(f"Session id = {Session_ID}")

    else: 
        logging.warning(f"could not get valid token from server {Host_Name}, Check logon or password,  Aborting!")
        print("no token")
        return Host_Name

    # Check supported iDRAC
    Results = Get_Model_Service_Tag(My_idrac, Token, Host_Name)
    
    Server_Model = Results['Model']
    Service_Tag = Results['Sevice_Tag']

    #print (Model, Service_Tag)   
    # Get idrac firmware version
    iDRAC_Firmware = Get_iDRAC_Firmware_Version(My_idrac, Token, Host_Name)
         

    # Get storage information information
    URL = f"https://{Host_Name}/redfish/v1/Systems/System.Embedded.1/Storage"
    Basic_Auth = False
    Valid_Return_Code = [200]
    headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
    User_Info = {}
    Body = {}

    Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
    if Results['SUCCESS']:
        Data = Results['SESSION_RESULTS'].json()
        Controller_List = []
        All_Disks = ""
        for i in Data['Members']:
            Controller_List.append(i['@odata.id'].split("/")[-1])
         
        for Controller in Controller_List:
            # Get drives on each controller
            #URL = f"https://{Host_Name}/redfish/v1/Systems/System.Embedded.1/Storage/{Controller}?$select=Drives"
            URL = f"https://{Host_Name}/redfish/v1/Systems/System.Embedded.1/Storage/{Controller}"
            Basic_Auth = False
            Valid_Return_Code = [200]
            headers = {'content-type' : 'application/json',
		        'X-Auth-Token' : Token }
            User_Info = {}
            Body = {}
            
            Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
            if Results['SUCCESS']:
                Drive_Data = Results['SESSION_RESULTS'].json()
                 
            
            if Drive_Data["Drives"] == []:
                # print that no data is aviable for this controller (could be perc and no drives)
                # do nothing and go to next controller in list
                pass 
            else:
                
                 
                # Add controller
                if Drive_Data['Name']:
                    Controller_Name = Drive_Data['Name']
                else:
                    Controller_Name = "Unknown" 
                
                Output = ""
                for i in Drive_Data["Drives"]:
                    for ii in i.items():
                        # Get drives on each controller
                        URL = f"https://{Host_Name}{ii[1]}"
                        Basic_Auth = False
                        Valid_Return_Code = [200]
                        headers = {'content-type' : 'application/json',
		                            'X-Auth-Token' : Token }
                        User_Info = {}
                        Body = {}

                        
                        Results = My_idrac.Get(URL, Valid_Return_Code, headers, Basic_Auth, User_Info)
                        if Results['SUCCESS']:
                            # Get Data
                            Data = Results['SESSION_RESULTS'].json()
                             
                            ID = Data['Id']
                             
                            if Data['PredictedMediaLifeLeftPercent']:
                                LifeRemaining = Data['PredictedMediaLifeLeftPercent']
                            else:
                                LifeRemaining = 'N/A'
                            
                            Failure_predict = Data['FailurePredicted']
                            Description = Data['Description']
                            Model = Data['Model']
                            Serial_Number = Data['SerialNumber']
                            Manufacturer = Data['Manufacturer']
                            if Data['Oem']['Dell']['DellPhysicalDisk']['AvailableSparePercent']:
                                AvailableSparePercentage = Data['Oem']['Dell']['DellPhysicalDisk']['AvailableSparePercent']
                            else:
                                AvailableSparePercentage = 'N/A'
                            
                            Output = (f"{Host_Name},{Server_Model},{Service_Tag},{iDRAC_Firmware},{Controller},{Controller_Name},{LifeRemaining},{AvailableSparePercentage},{Model},{Manufacturer},{Serial_Number},{ID},{Description},{Failure_predict} ") 
                            

                            All_Disks = All_Disks + Output +'\n' 
                            # Buffered_Print(Output)
                            
                        else:
                            # no disk data to get 
                            pass
        
        #print data to file 
        #print("printing read to dump")
        #Flush_Buffer()
    if All_Disks:
        # Only print if data exists
        Flush_Buffer(All_Disks)
        #print("printing read to dump")

    return Host_Name # to send output for futures

'''
def Buffered_Print(Msg):
     
    if not hasattr(thread_local, "buffer"):
        thread_local.buffer = io.StringIO()
    print(Msg, file=thread_local.buffer )
    '''

def Main():
    
    global Output_File_Name
    

    # Get host names from file
    Host_Name_List = Read_File(Input_File_Name)
    if not Host_Name_List:
        logging.info(f"The input file is empty, Aborting!")    
        #sys.exit(1)
        return
    #print(Host_Name_List)
    #print (len(Host_Name_List))
     
         

    # create ouput file and Add header 
    Output_File_Name = Create_Output_file( Base_Output_file_name ) 
    if Output_File_Name == "NULL":
        return
    logging.info(f"Output file name: {Output_File_Name}")

    # multi thread disk info
    Num_Of_Threads =  5
    with ThreadPoolExecutor(max_workers=Num_Of_Threads) as executor:
        #
        #executor.map(Get_Disk_Info, Host_Name_List, Output_File_Name)
          
        futures = [executor.submit(Get_Disk_Info, Item, Output_File_Name) for Item in Host_Name_List]
        for f in as_completed(futures):
            try:
                
                print(f"Task completed for host: {f.result()}")
            except Exception as e:
                print(f"Task Failed for host: {f.result()}")

    print("Done!")


if __name__ == "__main__":
    
    # create print lock, global variables
      
    print_lock = threading.Lock() # create print lock

    Main()
    