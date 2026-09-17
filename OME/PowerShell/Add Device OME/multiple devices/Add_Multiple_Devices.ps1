#  
# This script adds a list of idracs to a discovery range within OME. It
# prompts the user for various information along with global
# variables to perfrom this task. The Input file defines the list
# of IP address to be added to OME and comments are defined by starting 
# line in th efile with a # character.
# 
#
# to execute from shell
# pwsh Add_Device.ps1
#



# Global variables
$OME_Server = "10.0.0.61"
$OME_Admin_User = "admin"
$Default_Input_file = "Idrac_IPs.txt" # Input file name

function Get-UserInputs {
    $Return_results = @{}
try{

    # Get script location and move there
    $Script_Path = $PsScriptroot
    Set-Location -Path $Script_Path
    
    $Idrac_User = Read-Host "Please enter iDRAC user admin account name"
    $Idrac_Password = Read-Host -AsSecureString "Please enter iDRAC User password"

    $Input_File_found = $false

    while ( $Input_File_found -eq $false){
        $Idrac_IP_File = Read-Host "Please enter file name for list of iDRAC IP Addresses (default = $Default_Input_file)"
        if ( $Idrac_IP_File.Length -eq 0 ){
            # Use default input string
            $Idrac_IP_File = $Default_Input_file

        } 
        
        # Check existance of file
        if( (test-path -path $Idrac_IP_File ) -eq $true ){
            Write-Host "The input file: '$Default_Input_file' is being used."
            $Input_File_found = $true
        }
        else{
            write-host "The input file name: '$Idrac_IP_File' could not be found, please try again."

        }
    }


    $OME_Password = Read-host -AsSecureString "Please enter OME admin password"
    
    # return results
    $Return_results['IDRAC_USER'] = $Idrac_User
    $Return_results['IDRAC_SECURE_PASSWORD'] = $Idrac_Password
    $Return_results['IDRAC_IP_FILE'] = $Idrac_IP_File
    $Return_results['OME_PASSWORD'] = $OME_Password
    return $Return_results
}

catch{
    # runtime error 
    write-host "runtime error occured in function Get-UserInputs"
    write-host "Error was " + $_.Exception.message
    write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
    exit 1
}

}


function Add-Device{
param(
    [string]$Idrac_USer,
    [securestring]$Idrac_Password,
    [string]$Idrac_IP,
    [securestring]$OME_Password

)
try{
    $ReturnResults = @{}
    
        $Idrac_IP = $Idrac_IP.Trim()
                  
        # Define Json data structure
        $Payload = '{
        
        "DiscoveryConfigGroupName": "Discovery-2017033110553636",
        "DiscoveryConfigModels": [
            {
                
                "DiscoveryConfigTargets": [
                    {
                        
                        "NetworkAddressDetail": "10.0.0.77"
                        
                    }
                ],
                "ConnectionProfile": "{\n  \"profileName\" : \"\",\n  \"profileDescription\" : \"\",\n  \"type\" : \"DISCOVERY\",\n  \"updatedBy\" : null,\n  \"updateTime\" : 1580413699634,\n  \"credentials\" : [ {\n    \"type\" : \"WSMAN\",\n    \"authType\" : \"Basic\",\n    \"modified\" : false,\n    \"credentials\" : {\n      \"username\" : \"root\",\n      \"password\" : \"calvin\",\n      \"domain\" : null,\n      \"caCheck\" : false,\n      \"cnCheck\" : false,\n      \"certificateData\" : null,\n      \"certificateDetail\" : null,\n      \"port\" : 443,\n      \"retries\" : 3,\n      \"timeout\" : 60,\n      \"isHttp\" : false,\n      \"keepAlive\" : false\n    }\n  }\n]\n}",
                "DeviceType": [
                    1000
                ]
            }
        ],
        "Schedule": {
            "RunNow": true,
            "Cron": "startnow"
            
        },
        "CreateGroup": false,
        "TrapDestination": false,
        "CommunityString": false
    }'
     
    # Add input data
    $Payload_obj = $Payload | ConvertFrom-Json
    
    # Add description, IP addess
    $DateTime = Get-Date -format s
    $DateTime_Formatted = $DateTime.Replace(":","-")
    $Stg = $Idrac_IP+":"+$DateTime_Formatted
    $Payload_obj.DiscoveryConfigGroupName = $Stg
    $OME_discovery_Name =  $Stg
    
    # Add idrac IP
    $Payload_obj.DiscoveryConfigModels[0].DiscoveryConfigTargets[0].NetworkAddressDetail = $Idrac_IP
    

    # Set IDRAC Password (is a string in object)
    $Pass_txt = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Idrac_Password)) 
    $Stg = $Payload_obj.DiscoveryConfigModels[0].ConnectionProfile
    $New_stg = $Stg.Replace("calvin",$Pass_txt)
    $Payload_obj.DiscoveryConfigModels[0].ConnectionProfile = $New_stg
     

    # Set IDRAC user ( is a string object )
    $Stg = $Payload_obj.DiscoveryConfigModels[0].ConnectionProfile
    $New_stg = $Stg.Replace("root",$Idrac_USer)
    $Payload_obj.DiscoveryConfigModels[0].ConnectionProfile = $New_stg

   
    $Payload_json = $Payload_obj | ConvertTo-Json -Depth 12

    $URL  = "https://$OME_Server/api/DiscoveryConfigService/DiscoveryConfigGroups"
    $Credentials = New-Object System.Management.Automation.PSCredential( $OME_Admin_User, $OME_Password)
    $Type = 'application/json'
    
    try{
        $Session_Info = Invoke-WebRequest -Uri $URL `
            -Method POST -Body $Payload_json -Credential $Credentials -ContentType $Type `
            -SkipCertificateCheck
        #throw
    }
    catch{
        # Error with Invoke-WebRequest
        $ReturnResults['RETURN_CODE']  = $false
        $MSG = "Error occured while communicating with OME, Try again!"
        $ReturnResults['JOBID'] = $MSG
        $ReturnResults['OME_DISCOVERY_NAME'] = "NONE"
        return $ReturnResults

    }
    
    if( $Session_Info.StatusCode -eq 201){
        # Success, get Job id
        $Report_data = $Session_Info.Content | ConvertFrom-Json
        $Results = Get-JobId $Report_data.DiscoveryConfigGroupId $OME_Password
        if( $Results['RETURN_CODE'] -eq $true) {
            $ReturnResults['RETURN_CODE'] = $true
            $ReturnResults['JOBID'] = $Results['JOBID']
            $ReturnResults['OME_DISCOVERY_NAME'] = $OME_discovery_Name
            return $ReturnResults
        }
        else{
            $ReturnResults['RETURN_CODE'] = $false
            $ReturnResults['JOBID'] = "NONE"
            $ReturnResults['OME_DISCOVERY_NAME'] = $OME_discovery_Name
            return $ReturnResults
        }
    }
    else{
        # Bad return code
        $MSG = "Bad return code = "+$Session_Info.StatusCode
        $ReturnResults['RETURN_CODE'] = $false
        $ReturnResults['JOBID'] = $MSG
        $ReturnResults['OME_DISCOVERY_NAME'] = "NONE"
        return $ReturnResults
    }
}
catch{
        # runtime error 
        write-host "runtime error occured in function Get-UserInputs"
        write-host "Error was " + $_.Exception.message
        write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
        exit 1
    }
     
}

function Get-JobId{
    param(
        [string]$DiscoveryConfigGroupId,
        [securestring]$OME_Password
         
    
    ) 
try{

    $ReturnResults = @{}
    # Look for Job id, first get number of pages
    
    $URL  = "https://$OME_Server/api/DiscoveryConfigService/Jobs"
    $Credentials = New-Object System.Management.Automation.PSCredential( $OME_Admin_User, $OME_Password)
    $Type = 'application/json'
    
    try{
        $Session_Info = Invoke-WebRequest -Uri $URL `
            -Method Get -Credential $Credentials -ContentType $Type `
            -SkipCertificateCheck
        #throw
    }
    catch{

        # Invode request error
        $ReturnResults['RETURN_CODE']  = $false
        $MSG = "Error occured while communicating with OME, Try again!"
        $ReturnResults['JOBID'] = $MSG
        return $ReturnResults

    }
    if ($Session_Info.StatusCode -eq 200){
        # Get number of records
        $Report_data = $Session_Info.Content | ConvertFrom-Json
        $TotalJobs = $Report_data.'@odata.count'

        # pages could be paginated
        # Get all Jobs
        $URL  = "https://$OME_Server/api/DiscoveryConfigService/Jobs?"+'$top'+"=$TotalJobs"
         
        $Credentials = New-Object System.Management.Automation.PSCredential( $OME_Admin_User, $OME_Password)
        $Type = 'application/json'

        try{
            $Session_Info = Invoke-WebRequest -Uri $URL `
                -Method Get -Credential $Credentials -ContentType $Type `
                -SkipCertificateCheck
            #throw
        }
        catch{
            # Invode request error
            $ReturnResults['RETURN_CODE']  = $false
            $MSG = "Error occured while communicating with OME, Try again!"
            $ReturnResults['JOBID'] = $MSG
            return $ReturnResults
        }
        if ($Session_Info.StatusCode -eq 200){
            # Get JobId
            $Report_data = $Session_Info.Content | ConvertFrom-Json
            foreach( $Value in $Report_data.value ){
                 
                if( $Value.DiscoveryConfigGroupId -eq $DiscoveryConfigGroupId){
                    # Return JobID
                    $JobID = $Value.JobId
                    $ReturnResults['RETURN_CODE']  = $true
                    $ReturnResults['JOBID'] = $JobID
                    return $ReturnResults
                     
                }
            }    
            # Could not find JobID
            $ReturnResults['RETURN_CODE']  = $false
            $ReturnResults['JOBID'] = "NONE"
            return $ReturnResults
                        
        }
        else{
            # Bad return code
            $ReturnResults['RETURN_CODE']  = $false
            $MSG = "Bad return code = "+$Session_Info.StatusCode
            $ReturnResults['JOBID'] = $MSG
            return $ReturnResults
        }
         


    }
    else{
        # Bad return code
        $ReturnResults['RETURN_CODE']  = $false
        $MSG = "Bad return code = "+$Session_Info.StatusCode
        $ReturnResults['JOBID'] = $MSG
        return  $ReturnResults
            
    }
     

}
catch{
    # runtime error 
    write-host "runtime error occured in function Get-JobId"
    write-host "Error was " + $_.Exception.message
    write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
    exit 1
}
}

function Main{

try{
    # Get user input
    $Results = Get-UserInputs
    $IDrac_User = $Results['IDRAC_USER']
    $Idrac_Password = $Results['IDRAC_SECURE_PASSWORD']
    $Idrac_IP_File = $Results['IDRAC_IP_FILE']
    $OME_Password = $Results['OME_PASSWORD']   

         
    # process all IP's in file
    $Idrac_Data = Get-Content -Path $Idrac_IP_File
        

    foreach( $Idrac_IP in $Idrac_Data){

        # Check if comment
        if ( -not(( $Idrac_IP.Trim() -match "^#" ) -or ( $Idrac_IP.Trim().Length -eq 0 ))){
            # Run task to add device to OME
            Write-Host "###########################" 
            Run_Tasks $IDrac_User $Idrac_Password $Idrac_IP $OME_Password
        }
         
        
         
    }

}
catch{
    # runtime error 
    write-host "runtime error occured in function main"
    write-host "Error was " + $_.Exception.message
    write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
    exit 1
}

}

function Run_Tasks{
param(
    [string]$Idrac_USer,
    [securestring]$Idrac_Password,
    [string]$Idrac_IP,
    [securestring]$OME_Password
)
try{
    
    # Add device to OME
    $Results = Add-Device $IDrac_User $Idrac_Password $Idrac_IP $OME_Password
    if ($Results['RETURN_CODE'] -eq $True){
        # check status of discovery job
        $Job_Description = $Results['OME_DISCOVERY_NAME']
        $Msg = "Created discovery task in OME: "+$Job_Description
        Write-Host $Msg
        write-host "Checking the status of discovery job." 
        $JobID = $Results['JOBID']
        $Results = Check_Status $JobID $OME_Password
        if ($Results['RETURN_CODE'] -eq $true){
            # Completed fine 
            write-host "`nDiscovery task $Job_Description successfully completed within OME." -ForegroundColor Green

        }
        else{
            # Failed
            Write-Host "`nDiscovery task $Job_Description failed within OME, please try again." -ForegroundColor Red
        }

    }
    else{
        Write-Host "Error occured while creating discovery task for idrac "$Idrac_IP.Trim()" in OME, please try again." -ForegroundColor Red
    }
}
catch{
    # runtime error 
    write-host "runtime error occured in function main"
    write-host "Error was " + $_.Exception.message
    write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
    exit 1
}
}

function Check_Status{
param(
        [string]$JobID,
        [securestring]$OME_Password
      
    
) 
try{

    # Define job status

    $Failed_Job_Status = @( 2070, 2090, 2100, 2101, 2102, 2103 )
    $Job_status = @{
        "2020" = "Scheduled";
        "2030" = "Queued"
        "2040" = "Starting"
        "2050" = "Running"
        "2060" = "Completed"
        "2070" = "Failed"
        "2080" = "New"
        "2090" = "Warning"
        "2100" = "Aborted"
        "2101" = "Paused"
        "2102" = "Stopped"
        "2103" = "Canceled"
    }

    $Return_results = @{}

    $MAX_TIME_IN_LOOP = 30    ############# Minutes
    $Sleep_interval = 5       ############# seconds
    $Loop_flag = $false
    $Start_time = Get-Date # Start time of processing

    # Convert minutes to seconds
    $MAX_TIME_IN_LOOP_SEC = $MAX_TIME_IN_LOOP * 60

    $Return_results = @{}
     
    
    # Loop until job is done or MAX time reached
    while( $Loop_flag -eq $False ) {
        Write-Host -NoNewline "."
        
        #  Get server information from OME
        $url = "https://$OME_Server/api/JobService/Jobs($JobID)"
        

        $Credentials = New-Object System.Management.Automation.PSCredential( $OME_Admin_User, $OME_Password)
        $Type = 'application/json'
    
        try{
            $Session_Info = Invoke-WebRequest -Uri $URL `
                -Method Get -Credential $Credentials -ContentType $Type `
                -SkipCertificateCheck
            #throw
            #$Session_info =  Invoke-WebRequest -Uri $url -UseBasicParsing -Headers $Headers -Method Get -ContentType $Type
            }
            catch{
                # Could not talk to ome log error and continue, will get stopped by timer if issue persits.
                # do nothing
                $Do_nothing = $true 
           
            }

         
        if ( $Session_info.StatusCode -eq 200 ){
            
            $Job_data = $Session_info.Content | ConvertFrom-Json
            [string]$Job_status = $Job_data.LastRunStatus.Id
              
            if ( $Job_status -eq "2060" ){
                # Job completed successfully
                $Return_results["JOB_CODE"] = $Job_status
                $Return_results["RETURN_CODE"] = $true
                $Return_results["MAX_TIME_REACHED"] = $false
                return $Return_results
            }
            elseif(  $Failed_Job_Status -contains $Job_status ) {
                # Job failed
                if ( $Job_status -eq "2090" ){
                    # Completed with warning
                    $Return_results["JOB_CODE"] = $JOB_status
                    $Return_results["RETURN_CODE"] = $true
                    $Return_results["MAX_TIME_REACHED"] = $false
                    return $Return_results
                }
                else{
                    # Job failed
                    $Return_results["JOB_CODE"] = $JOB_status
                    $Return_results["RETURN_CODE"] = $false
                    $Return_results["MAX_TIME_REACHED"] = $false
                    return $Return_results

                }
            }
        }
        
        # Check if MAX time has expired
        $Current_time = Get-Date
        $Total_time = New-TimeSpan $Start_time $Current_time
        $Total_seconds = ($Total_time.Hours *60 *60 ) + ($Total_time.Minutes * 60) + ($Total_time.Seconds)
        #write-host "Total Seconds = $Total_seconds"
        #write-host "Max time in loop sec = $MAX_TIME_IN_LOOP_SEC"

        if ( $Total_seconds -gt $MAX_TIME_IN_LOOP_SEC ) {
        #if ( $Total_seconds -gt 20 ) {
            # Max time in loop reached stop processing 
            $Return_results["JOB_CODE"] = $Job_status
            $Return_results["RETURN_CODE"] = $false  
            $Return_results["MAX_TIME_REACHED"] = $true
            return $Return_results
            }
        
        Start-Sleep -Seconds $Sleep_interval

    
    }

}
catch{
    # runtime error 
    write-host "runtime error occured in function main"
    write-host "Error was " + $_.Exception.message
    write-host "Error Line Number =" + $_.InvocationInfo.ScriptLineNumber
    exit 1
}

} 

#=========================
# Main
#=========================

main 