#import warnings
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import logging
import sys 

 

class REST_wrapper:
 	
 	# future use
	# protected data
	#_Read_Timeout = 10 # seconds
	#_Connection_timeout = 10 # seconds
	
	
	# initialize class
	def __init__(self):
	
		# Global variables
		self.Read_Timeout = 20.0        # Time allowed for client to establish
									   # connection to server (seconds).
		self.Connection_timeout = 30.0  # Time it will wait on responce once client
									   # has established connection (seconds).
		self.Max_Retries = 2           # Maximum retries 
		self.BackOff_factor = 1        # used to calculate timout (BackOff_factor)
									   # BackOff_factor * (2 ** ({number_retries} - 1))
	def Get_Global_Parms(self):
		
		''' return Global paramters defined below '''
		 
		Return_Results = {"Read_Timeout" : self.Read_Timeout,
		                  "Connection_timeout" : self.Connection_timeout,
		                  "Max_Retries" : self.Max_Retries,
		                  "BackOff_factor" : self.BackOff_factor}
		
		return Return_Results
	
	def Get( self, Session_URL, Valid_Return_Codes, Headers, Basic_Auth, User_Info =''):
		
		''' GET REST API for idrac and OME '''

		# disable logging  
		logging.getLogger("urllib3").propagate = False
		
		Return_Results = {}  # define return
		
		if not(isinstance(Valid_Return_Codes, list )):
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = 'Input dictionary item "Valid_Return_Codes" must be type "list"'
			return Return_Results
		
		if Basic_Auth:
			# must have user name and password
			if not(isinstance(User_Info, dict )):
				Return_Results['SUCCESS'] = False
				Return_Results['SESSION_RESULTS'] = "NONE"
				Return_Results['ERROR_MSG'] = 'When using basic authentication, the dictionary "User_Info" must be dictionary { User : User, Password: Password}'
				return Return_Results
		 
		 			 
		# set up retry and backoff
		retry_strategy = Retry(
			total = self.Max_Retries, # Max number of retires
			backoff_factor = self.BackOff_factor,
			status_forcelist=[],  
	    )
		
		
		# Create an HTTP adapter with the retry strategy and mount it to session
		adapter = HTTPAdapter(max_retries=retry_strategy)
 
		# Create a new session object
		session = requests.Session()
		session.mount('https://', adapter)

		try:
			if Basic_Auth:

				Session_info = session.get( Session_URL,
											headers = Headers,
											auth = ( User_Info['User'], User_Info['Password'] ),
											verify = False,
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	   
			else:		 	 
				Session_info = session.get( Session_URL,
											headers = Headers,
											verify = False,
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	
			 
			#raise Exception()					
		except requests.exceptions.Timeout:
			#---------------------
			# requests timed out
			#---------------------
			 
			# Tried Max times and failed, return error
			  
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = "Requests Timeout Occured"
			return Return_Results
			
		except requests.exceptions.RequestException as e:
			#----------------------------------
			# an unkown requests error occured
			#----------------------------------
					 
			Error_msg = "Connection Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
		
		except Exception as e:
			# runtime error occured
			 
			Error_msg = "Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
				 		
		if Session_info.status_code in Valid_Return_Codes:
			#----------------------
			# Got Valid Return code
			#----------------------
			   	
			Return_Results['SUCCESS'] = True
			Return_Results['SESSION_RESULTS'] = Session_info
			Return_Results['ERROR_MSG'] = "NONE"
			return Return_Results	
			
		else:
			#--------------------- 
			# Invalid return code  
			#--------------------- 
			 
			# Tried Max times and failed, return error
			Error_msg = "Invalid return code = " + str(Session_info.status_code)
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = Session_info
			#Return_Results['HEADERS'] = Session_info.headers
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results		
				 
	def Post( self, Session_URL, Valid_Return_Codes, Headers, Body, Basic_Auth, User_Info=''):
		
		''' POST REST API for idrac or OME '''

		# disable logging  
		logging.getLogger("urllib3").propagate = False
		
		Return_Results = {}  # define return
		
		if not(isinstance(Valid_Return_Codes, list )):
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = 'Input dictionary item "Valid_Return_Codes" must be type "list"'
			return Return_Results
		
		if Basic_Auth:
			# must have user name and password
			if not(isinstance(User_Info, dict )):
				Return_Results['SUCCESS'] = False
				Return_Results['SESSION_RESULTS'] = "NONE"
				Return_Results['ERROR_MSG'] = 'When using basic authentication, the dictionary "User_Info" must be dictionary { User : User, Password: Password}'
				return Return_Results
		 
		 			 
		# set up retry and backoff
		retry_strategy = Retry(
			total = self.Max_Retries, # Max number of retires
			backoff_factor = self.BackOff_factor,
			status_forcelist=[],  
	    )
		
		
		# Create an HTTP adapter with the retry strategy and mount it to session
		adapter = HTTPAdapter(max_retries=retry_strategy)
 
		# Create a new session object
		session = requests.Session()
		session.mount('https://', adapter)

		try:
			if Basic_Auth:

				Session_info = session.post( Session_URL,
											headers = Headers,
											auth = ( User_Info['User'], User_Info['Password'] ),
											verify = False,
											data = json.dumps(Body),
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	   
			else:		 	 
				Session_info = session.post( Session_URL,
											headers = Headers,
											verify = False,
											data = json.dumps(Body),
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	
			 
			#raise Exception()					
		except requests.exceptions.Timeout:
			#---------------------
			# requests timed out
			#---------------------
			 
			# Tried Max times and failed, return error
			  
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = "Requests Timeout Occured"
			return Return_Results
			
		except requests.exceptions.RequestException as e:
			#----------------------------------
			# an unkown requests error occured
			#----------------------------------
					 
			Error_msg = "Connection Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
		
		except Exception as e:
			# runtime error occured
			 
			Error_msg = "Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
				 		
		if Session_info.status_code in Valid_Return_Codes:
			#----------------------
			# Got Valid Return code
			#----------------------
			 	
			Return_Results['SUCCESS'] = True
			Return_Results['SESSION_RESULTS'] = Session_info
			Return_Results['ERROR_MSG'] = "NONE"
			return Return_Results	
			
		else:
			#--------------------- 
			# Invalid return code  
			#--------------------- 
			 
			# Tried Max times and failed, return error
			Error_msg = "Invalid return code = " + str(Session_info.status_code)
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = Session_info
			#Return_Results['HEADERS'] = Session_info.headers
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results				 
			 		 
		 
	def Patch( self, Session_URL, Valid_Return_Codes, Headers, Body, Basic_Auth, User_Info=''):
		
		''' POST REST API for idrac or OME '''

		# disable logging  
		logging.getLogger("urllib3").propagate = False
		
		Return_Results = {}  # define return
		
		if not(isinstance(Valid_Return_Codes, list )):
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = 'Input dictionary item "Valid_Return_Codes" must be type "list"'
			return Return_Results
		
		if Basic_Auth:
			# must have user name and password
			if not(isinstance(User_Info, dict )):
				Return_Results['SUCCESS'] = False
				Return_Results['SESSION_RESULTS'] = "NONE"
				Return_Results['ERROR_MSG'] = 'When using basic authentication, the dictionary "User_Info" must be dictionary { User : User, Password: Password}'
				return Return_Results
		 
		 			 
		# set up retry and backoff
		retry_strategy = Retry(
			total = self.Max_Retries, # Max number of retires
			backoff_factor = self.BackOff_factor,
			status_forcelist=[],  
	    )
		
		
		# Create an HTTP adapter with the retry strategy and mount it to session
		adapter = HTTPAdapter(max_retries=retry_strategy)
 
		# Create a new session object
		session = requests.Session()
		session.mount('https://', adapter)

		try:
			if Basic_Auth:

				Session_info = session.patch( Session_URL,
											headers = Headers,
											auth = ( User_Info['User'], User_Info['Password'] ),
											verify = False,
											data = json.dumps(Body),
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	   
			else:		 	 
				Session_info = session.patch( Session_URL,
											headers = Headers,
											verify = False,
											data = json.dumps(Body),
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	
			 
			#raise Exception()					
		except requests.exceptions.Timeout:
			#---------------------
			# requests timed out
			#---------------------
			 
			# Tried Max times and failed, return error
			  
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = "Requests Timeout Occured"
			return Return_Results
			
		except requests.exceptions.RequestException as e:
			#----------------------------------
			# an unkown requests error occured
			#----------------------------------
					 
			Error_msg = "Connection Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
		
		except Exception as e:
			# runtime error occured
			 
			Error_msg = "Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
				 		
		if Session_info.status_code in Valid_Return_Codes:
			#----------------------
			# Got Valid Return code
			#----------------------
			 	
			Return_Results['SUCCESS'] = True
			Return_Results['SESSION_RESULTS'] = Session_info
			Return_Results['ERROR_MSG'] = "NONE"
			return Return_Results	
			
		else:
			#--------------------- 
			# Invalid return code  
			#--------------------- 
			 
			# Tried Max times and failed, return error
			Error_msg = "Invalid return code = " + str(Session_info.status_code)
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = Session_info
			#Return_Results['HEADERS'] = Session_info.headers
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results	

	def Delete( self, Session_URL, Valid_Return_Codes, Headers, Basic_Auth, User_Info =''):
		
		''' GET REST API for idrac and OME '''

		# disable logging  
		logging.getLogger("urllib3").propagate = False
		
		Return_Results = {}  # define return
		
		if not(isinstance(Valid_Return_Codes, list )):
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = 'Input dictionary item "Valid_Return_Codes" must be type "list"'
			return Return_Results
		
		if Basic_Auth:
			# must have user name and password
			if not(isinstance(User_Info, dict )):
				Return_Results['SUCCESS'] = False
				Return_Results['SESSION_RESULTS'] = "NONE"
				Return_Results['ERROR_MSG'] = 'When using basic authentication, the dictionary "User_Info" must be dictionary { User : User, Password: Password}'
				return Return_Results
		 
		 			 
		# set up retry and backoff
		retry_strategy = Retry(
			total = self.Max_Retries, # Max number of retires
			backoff_factor = self.BackOff_factor,
			status_forcelist=[],  
	    )
		
		
		# Create an HTTP adapter with the retry strategy and mount it to session
		adapter = HTTPAdapter(max_retries=retry_strategy)
 
		# Create a new session object
		session = requests.Session()
		session.mount('https://', adapter)

		try:
			if Basic_Auth:

				Session_info = session.delete( Session_URL,
											headers = Headers,
											auth = ( User_Info['User'], User_Info['Password'] ),
											verify = False,
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	   
			else:		 	 
				Session_info = session.delete( Session_URL,
											headers = Headers,
											verify = False,
											timeout= (self.Connection_timeout, self.Read_Timeout ) )	
			 
			#raise Exception()					
		except requests.exceptions.Timeout:
			#---------------------
			# requests timed out
			#---------------------
			 
			# Tried Max times and failed, return error
			  
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = "Requests Timeout Occured"
			return Return_Results
			
		except requests.exceptions.RequestException as e:
			#----------------------------------
			# an unkown requests error occured
			#----------------------------------
					 
			Error_msg = "Connection Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
		
		except Exception as e:
			# runtime error occured
			 
			Error_msg = "Error: {0}".format(e) 
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = "NONE"
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results
		
				 		
		if Session_info.status_code in Valid_Return_Codes:
			#----------------------
			# Got Valid Return code
			#----------------------
			   	
			Return_Results['SUCCESS'] = True
			Return_Results['SESSION_RESULTS'] = Session_info
			Return_Results['ERROR_MSG'] = "NONE"
			return Return_Results	
			
		else:
			#--------------------- 
			# Invalid return code  
			#--------------------- 
			 
			# Tried Max times and failed, return error
			Error_msg = "Invalid return code = " + str(Session_info.status_code)
			Return_Results['SUCCESS'] = False
			Return_Results['SESSION_RESULTS'] = Session_info
			#Return_Results['HEADERS'] = Session_info.headers
			Return_Results['ERROR_MSG'] = Error_msg
			return Return_Results

	def Change_Global_Parms( self, Global_Parms=''):
		'''
		Change global values - Read Read_Timeout: float or int
							   Connection_timeout: float or int
							   Max_Retries: int
							   BackOff_factor: int

		Return - dictionary:
		    ['VALUES_SET'] = True or False
		    ['ERROR_MSG'] = NONE or Error message.

		'''     
		# disable logging  
		logging.getLogger("urllib3").propagate = False
		
		Return_Results = {}  # define return
				 
		#--------------------------------		 
		# Check if dictionary passed in 
		if not(isinstance(Global_Parms,  dict)):
			# Not dictionary
			
			Return_Results['VALUES_SET'] = False
			Return_Results['ERROR_MSG'] = "Must pass in a dictionary to set Global paramters. { 'Read_Timeout' : 20.5, 'Connection_timeout' : 30.2, 'Max_Retries' : 5 , 'BackOff_factor' : 3 }"
			return Return_Results
		
		# set flags
		ERROR = False
		ERROR_MSG = "The following Items were not set:"
		
		if 'Read_Timeout' in Global_Parms:
			if isinstance(Global_Parms['Read_Timeout'], (float, int)):
				self.Read_Timeout = float(Global_Parms['Read_Timeout'])
				Read_Timeout_Set = True
			else:
				ERROR_MSG = ERROR_MSG + '\n' +'Dictionary item "Raed_Timeout" must be "int" or "float"'
				ERROR = True
				
		if 'Connection_timeout' in Global_Parms:
			if isinstance(Global_Parms['Connection_timeout'], (float, int)):
				self.Connection_timeout = float(Global_Parms['Connection_timeout'])
				Connectoin_Timeout_Set = True
			else:
				ERROR_MSG = ERROR_MSG + '\n' + 'Dictionary item "Connection_timeout" must be "int" or "float"'
				ERROR = True		
		
		if 'Max_Retries' in Global_Parms:
			if isinstance(Global_Parms['Max_Retries'], (int)):
				self.Max_Retries  = int(Global_Parms['Max_Retries'])
				Max_Retries_Set = True
			else:
				ERROR_MSG = ERROR_MSG + '\n' + 'Dictionary item "Max_Retries" must be "int"'
				ERROR = True	
				
		if 'BackOff_factor' in Global_Parms:
			if isinstance(Global_Parms['BackOff_factor'], (int)):
				self.BackOff_factor  = int(Global_Parms['BackOff_factor'])
				BackOff_factor_Set = True
			else:
				ERROR_MSG = ERROR_MSG + '\n' + 'Dictionary item "BackOff_factor" must be "int"'
				ERROR = True 
	
		if ERROR:
			# error setting some value occured
			Return_Results['VALUES_SET'] = False
			Return_Results['ERROR_MSG'] = ERROR_MSG
			return Return_Results 
		else:
			Return_Results['VALUES_SET'] = True
			Return_Results['ERROR_MSG'] = "NONE"
			return Return_Results
	
		