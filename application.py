from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import numpy as np
import json 
import mysql
import requests
from itertools import islice
from contextlib import closing
import csv
import codecs
from itertools import islice
from dateutil.parser import parse
import time  
from time import gmtime, strftime
from azure.storage.blob.baseblobservice import BaseBlobService
from azure.storage.blob import BlobPermissions
from datetime import datetime, timedelta




app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'


import mysql.connector
from mysql.connector import Error





@app.route("/", methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM userdetails WHERE userName = %s AND password = %s ;', (username, password))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            # session['Name'] = account['Name']
            session['username'] = account[0]
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute('SELECT count(Username)-1 FROM userdetails')
        # Fetch one record and return result
        client= cursor.fetchone()
        clients = client[0]

        account = session['username']

        cursor.execute('SELECT count(distinct ProjectName) as a FROM datacatlogentry;')
        # Fetch one record and return result
        Projects = cursor.fetchone()
        Project = Projects[0]
        cursor.execute('SELECT count(distinct JobOwner) FROM datacatlogentry')
        # Fetch one record and return result
        Owners = cursor.fetchone()
        Owner = Owners[0]
        #active runs
        cursor.execute(" select ProjectName, JobName , StartTime ,Status  from audittable WHERE UserName=%s AND Status=%s order by EntryID desc limit 5;",(account,'Running'))
        data = cursor.fetchall() 
        df = pd.DataFrame(data, columns=['Project Name','Job Name', 'Start Time','Status'])
        #past runs
        cursor.execute(" select *  from audittable   WHERE  UserName=%s AND Status!=%s order by EntryID desc limit 5; ",(account,'Running'))
        data1 = cursor.fetchall() 
        df2 = pd.DataFrame(data1, columns=[ 'EntryID','Job Name', 'Project Name', 'Start Time', 'End Time', 'UserName', 'Total Rows', 'Ingested Rows', 'Duplicate Rows', 'DQ Check Failed','Business Rules Check Failed','Custom Rules Check Failed','Rejected Rows', 'Status', 'Error/Reject Log'])
        #df2 = pd.DataFrame(data1, columns=['JobName','RunID' ,'StartTime' ,'EndTime','UserName' ,'TotalRows' ,'DuplicateRows','DuplicatePrimaryKey','DQCheckFailed','Status','RelativeFilePath','ProjectName'])
        df3=  df2.drop(['UserName','EntryID'], axis = 1)
        columns_order=[ 'Project Name','Job Name', 'Start Time', 'End Time', 'Total Rows', 'Ingested Rows', 'Duplicate Rows', 'DQ Check Failed','Business Rules Check Failed','Custom Rules Check Failed','Rejected Rows', 'Status', 'Error/Reject Log']
        df4 = df3.reindex(columns=columns_order)
        # Show the profile page with account info
        return render_template('home.html',column_names=df.columns.values, row_data=list(df.values.tolist()), zip=zip,column_names1=df4.columns.values, row_data1=list(df4.values.tolist()), zip1=zip, account=account, clients = clients, Project = Project,Owner = Owner)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def homeSearch():
    if request.method == "POST":
        details = request.form
        search = details['search']
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute('SELECT count(Username)-1 FROM userdetails')
        # Fetch one record and return result
        client= cursor.fetchone()
        clients = client[0]

        account = session['username']

        cursor.execute('SELECT count(distinct ProjectName) FROM datacatlogentry')
        # Fetch one record and return result
        Projects = cursor.fetchone()
        Project = Projects[0]
        cursor.execute('SELECT count(distinct JobOwner) FROM datacatlogentry')
        # Fetch one record and return result
        Owners = cursor.fetchone()
        Owner = Owners[0]  # projectname like needs to updated
        cursor.execute(" select ProjectName, JobName , StartTime ,Status from audittable WHERE  ProjectName LIKE %s AND UserName=%s AND Status='Running' order by EntryID desc limit 5;",(search,account))
        data = cursor.fetchall() 
        df = pd.DataFrame(data, columns=[ 'Projec tName','Job Name', 'Start Time','Status'])
        #df = pd.DataFrame(data, columns=['JobName','RunID' ,'StartTime' ,'EndTime','UserName' ,'TotalRows' ,'DuplicateRows','DuplicatePrimaryKey','DQCheckFailed','Status','RelativeFilePath','ProjectName'])
        #df1=  df.drop(['UserName'], axis = 1)

        cursor.execute(" select *  from audittable   WHERE  ProjectName LIKE %s AND UserName=%s AND Status!='Running' order by EntryID desc limit 5;",(search,account))
        data1 = cursor.fetchall() 
        df2 = pd.DataFrame(data1, columns=[ 'EntryID','Job Name', 'Project Name', 'Start Time', 'End Time', 'UserName', 'Total Rows', 'Ingested Rows', 'Duplicate Rows', 'DQ Check Failed','Business Rules Check Failed','Custom Rules Check Failed','Rejected Rows', 'Status', 'Error/Reject Log'])
        #df2 = pd.DataFrame(data1, columns=['JobName','RunID' ,'StartTime' ,'EndTime','UserName' ,'TotalRows' ,'DuplicateRows','DuplicatePrimaryKey','DQCheckFailed','Status','RelativeFilePath','ProjectName'])
        df3=  df2.drop(['UserName','EntryID'], axis = 1)
        columns_order=[ 'Project Name','Job Name', 'Start Time', 'End Time', 'Total Rows', 'Ingested Rows', 'Duplicate Rows', 'DQ Check Failed','Business Rules Check Failed','Custom Rules Check Failed','Rejected Rows', 'Status', 'Error/Reject Log']
        df4 = df3.reindex(columns=columns_order)
       
        mydb.commit()
        cursor.close()
        return render_template("home.html", column_names=df.columns.values, row_data=list(df.values.tolist()), zip=zip,column_names1=df4.columns.values, row_data1=list(df4.values.tolist()), zip1=zip,account=account, clients = clients, Project = Project,Owner = Owner)
    return redirect(url_for('home'))


@app.route('/overview')
def overview():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        account = session['username']
        return render_template('setup.html', account=account, username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/pythonlogin/overview', methods=['GET', 'POST'])
def overviewform():                    # setup page user input will be recorder here and 
    if request.method == "POST":       # inserted into database tables and some sesion variables used across other functions
        details = request.form
        session['hostname']=details['hostname']
        session['user']=details['User']
        session['password']=details['password']
        session['database name' ]= details['database name']
        session['source query']=details['sql source query']
        project = details['Project Name']
        UserName = session['username']
        DataCategory = details['Project Category']
        Owner = details['Job Owner']
        FileName = details['Job Name']
        session['source location type'] = details['source location type']
        TargetType = details['Target Location Type']
        Target_Applicationid = details['Target_Applicationid']
        target_ApplicationCredential = details['target_ApplicationCredential']
        Target_Directoryid = details['Target_Directoryid']
        Target_Adlaccount = details['Target_Adlaccount']
        sql_source_query = details['sql source query']
        hive_source_query = details['hive source query']
        Target_filetype = details['Target filetype']
        Target_file_delimiter = details['Delimiter1']
        Server_Name = details['Server Name']
        Hive_Database_Name = details['Hive Database Name']
        Hive_USER_ID = details['Hive USER ID']
        Hive_PASSWORD = details['Hive PASSWORD']
        google_drive_link=details['Public Sharable Link']
        session['onedrive link']=details['Public Downloadable Link']
        session['Delimiter of onedrive']=details['Delimiter of onedrive']
        session['delimiter']=details['Type of Delimiter']
        session['account_name']=details['account_name']
        session['account_key']=details['account_key']
        session['ContainerName']=details['ContainerName']
        session['Blob Name']=details['Blob Name']
        session['azure file format']=details['azure file format']
        session['azure file delimiter']=details['azure file delimiter']
        if session['source location type']=='Google Drive':
            session['file_id'] = google_drive_link.split('/')[-2]
        target_parameter_dictioary = {"ApplicationID":Target_Applicationid,"ApplicationCredential":target_ApplicationCredential,"DirectoryID":Target_Directoryid,"adlAccountName":Target_Adlaccount}
        target_parameter_dictioary_string = str(target_parameter_dictioary)
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        today_date_o=time.strftime("  %Y-%m-%d", time.gmtime())
        today_date= str(today_date_o)
        cursor.execute(" SELECT * FROM datacatlogentry   WHERE  ProjectName=%s AND `JobName`=%s AND date(CreateTime)=%s  order by EntryID desc limit 1  ;",(project,FileName,today_date))
        account1 = cursor.fetchone()
        if account1:
            session['file exists'] = 'YES'
            session['existing file Entry ID']=account1[0]
        else:
            session['file exists'] = 'NO'
        cursor.execute("INSERT INTO datacatlogentry (ProjectName,UserName, ProjectCategory,JobOwner,JobName,SourceType,TargetType) VALUES (%s,%s,%s, %s,%s,%s,%s) ;",(project, UserName, DataCategory,Owner,FileName,session['source location type'],TargetType))
        mydb.commit()
        cursor.close()
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute(" SELECT EntryID FROM datacatlogentry  WHERE UserName=%s AND `JobOwner`=%s ORDER BY EntryID DESC LIMIT 1 ;",(UserName,Owner))
        data=cursor.fetchone()
        df = pd.DataFrame(data)
        session['EntryID']=int(df.iat[0,0])
        if session['source location type'] == 'MySql':
            sql_parameter_dictionary={"jdbcHostname":session['hostname'],"jdbcUserName":session['user'],"jdbcPassword":session['password'],"jdbcDatabasename":session['database name' ]}
            sql_parameter_dictionary_string = str(sql_parameter_dictionary)
            cursor.execute(" INSERT INTO parameter (EntryId, SourceType, SourceParameter,SourceQuery, TargetType, TargetParameter,TargetFileType,TargetFileDelimiter) VALUES(%s,%s, %s, %s,%s, %s,%s, %s) ;",(session['EntryID'],session['source location type'],sql_parameter_dictionary_string,sql_source_query,TargetType,target_parameter_dictioary_string,Target_filetype,Target_file_delimiter))
        elif session['source location type'] == 'Google Drive':
            gdrive_parameter_dictionary={"FileId":session['file_id'],"Delimiter":session['delimiter']}
            gdrive_parameter_dictionary_string = str(gdrive_parameter_dictionary)
            cursor.execute(" INSERT INTO parameter (EntryId, SourceType, SourceParameter, TargetType, TargetParameter,TargetFileType,TargetFileDelimiter) VALUES(%s,%s,%s, %s,%s,%s,%s) ;",(session['EntryID'],session['source location type'],gdrive_parameter_dictionary_string,TargetType,target_parameter_dictioary_string,Target_filetype,Target_file_delimiter))
        elif session['source location type'] == 'AzureBlob':   
            azureblob_parameter_dictionary={"StorageAccountAccessKey":session['account_key'],"StorageAccountName":session['account_name'],"ContainerName":session['ContainerName'],"Path":session['Blob Name'],"Format":session['azure file format'],"Delimiter":session['azure file delimiter']}
            azureblob_parameter_dictionary_string = str(azureblob_parameter_dictionary)
            cursor.execute(" INSERT INTO parameter (EntryId, SourceType, SourceParameter, TargetType, TargetParameter,TargetFileType,TargetFileDelimiter) VALUES(%s,%s,%s, %s,%s,%s,%s) ;",(session['EntryID'],session['source location type'],azureblob_parameter_dictionary_string,TargetType,target_parameter_dictioary_string,Target_filetype,Target_file_delimiter))
        elif session['source location type'] == 'One Drive':
            onedrive_parameter_dictionary={"Link":session['onedrive link'],"Delimiter":session['Delimiter of onedrive']}
            onedrive_parameter_dictionary_string = str(onedrive_parameter_dictionary)
            cursor.execute(" INSERT INTO parameter (EntryId, SourceType, SourceParameter, TargetType, TargetParameter,TargetFileType,TargetFileDelimiter) VALUES(%s,%s,%s, %s,%s,%s, %s) ;",(session['EntryID'],session['source location type'],onedrive_parameter_dictionary_string,TargetType,target_parameter_dictioary_string,Target_filetype,Target_file_delimiter))
        elif session['source location type'] == 'Hive':
            hive_parameter_dictionary={"odbcHostname":Server_Name,"odbcUserName":Hive_USER_ID,"odbcPassword":Hive_PASSWORD,"odbcDatabasename":Hive_Database_Name}
            hive_parameter_dictionary_string= str(hive_parameter_dictionary)
            cursor.execute(" INSERT INTO parameter (EntryId, SourceType, SourceParameter,SourceQuery,TargetType,TargetParameter,TargetFileType,TargetFileDelimiter) VALUES(%s,%s,%s, %s,%s,%s,%s, %s) ;",(session['EntryID'],session['source location type'], hive_parameter_dictionary_string,hive_source_query,TargetType,target_parameter_dictioary_string,Target_filetype,Target_file_delimiter))
        mydb.commit()
        cursor.close()
        if session['source location type'] == 'Hive':
            return redirect(url_for('hive_metadata_1'))
        else:
            return redirect(url_for('index'))
    return render_template('setup.html')


@app.route("/hive_metadata_1", methods=['GET', 'POST'])    #series for hive metadata capture  
def hive_metadata_1():     # for azure hd insight clusterhive metadata 
                           # there is small notebook which would extract metadata and send back to flask api
                           # this is due to unable to install pyodbc driver inside azure app service                           
    headers = {'Authorization': 'Bearer dapi042eca35a8dd2f707b2562849e33f013'}
    data = '{ "job_id" : 12, "notebook_params": { "entryid":  ' +str(session['EntryID'])+ ' } }'
    response = requests.post('https://adb-6971132450799346.6.azuredatabricks.net/api/2.0/jobs/run-now', headers=headers, data=data)
    a = eval(response.text)
    b=a['run_id']
    session['b']=b
    time.sleep(8.0)
    return redirect(url_for('hive_metadata_2'))   




@app.route("/hive_metadata_2", methods=['GET', 'POST']) 
def hive_metadata_2():
    b = session['b']
    headers = {'Authorization': 'Bearer dapi042eca35a8dd2f707b2562849e33f013'}
    response1 = requests.get('https://adb-6971132450799346.6.azuredatabricks.net/api/2.0/jobs/runs/get-output?run_id='+str(b)+'',headers=headers)
    c = response1.text
    session['c']=c
    return redirect(url_for('hive_metadata_3'))


@app.route("/hive_metadata_3", methods=['GET', 'POST'])  # metadata retrieval directly from databricks notebook
def hive_metadata_3():
    c = session['c']
    res = json.loads(c)
    if res['metadata']['state']['life_cycle_state']=='TERMINATED':
        if res['metadata']['state']['result_state']=="SUCCESS":
            d=res['notebook_output']['result']
            e=eval(d)
            df2 = pd.DataFrame(e, columns =['Column Name', 'Data Type'])
            df2['Column Name']=df2['Column Name'].map(lambda x: x.split(".",1)[1])
            df3 = df2.assign(ColumnNumber=[i+1 for i in range(len(df2))])[['ColumnNumber'] + df2.columns.tolist()]
            df3['Column Number']= df3['ColumnNumber']
            df4 = df3.drop(['ColumnNumber'], axis = 1)
            columns_order=['Column Number','Column Name','Data Type']
            df5 = df4.reindex(columns=columns_order)
            value = session['file exists']
            account = session['username']
            return render_template("metadata.html", column_names=df5.columns.values, row_data=list(df5.values.tolist()), zip=zip, value=value,account=account)
        else:
            print("Job Failed")
    else:
        time.sleep(1.5)
        return redirect(url_for('hive_metadata_2'))
        

@app.route('/ingest', methods=['GET', 'POST'])
def index():                                     # for flat file and mysql metadata
    SourceType = session['source location type']
    if SourceType == 'MySql':
        mydb = mysql.connector.connect(host=session['hostname'],user=session['user'],passwd=session['password'],database = session['database name'])
        cursor = mydb.cursor()
        cursor.execute("DROP VIEW IF EXISTS temp")
        cursor.execute("CREATE VIEW temp AS "+session['source query']+" LIMIT 1 ")
        cursor.execute("DESCRIBE temp")
        data = cursor.fetchall() 
        df = pd.DataFrame(data, columns=['Column Name' ,'Data Type' ,'Nullable' ,'Primary Key' ,'Default' ,'Description'])
        df = df.assign(ColumnNumber=[i+1 for i in range(len(df))])[['ColumnNumber'] + df.columns.tolist()]
        df4=  df.drop(['Primary Key','Nullable','Description','Default'], axis = 1)
        df4['Column Number']= df4['ColumnNumber']
        df5 = df4.drop(['ColumnNumber'], axis = 1)
        df5['Description'] = df5["Column Name"].map(lambda row: Business_Description(row)) 
        cursor.execute(session['source query']+" LIMIT 100 ")
        data2= cursor.fetchall()
        df_temp = pd.DataFrame(data2,columns=df5["Column Name"].tolist())
        adict = {}
        for col in df_temp.columns.tolist():
            df_temp[col] = df_temp[col].map(lambda ele:pii(ele))
            x = df_temp[col].value_counts().idxmax()
            adict[col]= x
        df5["PII Type"] = df5["Column Name"].map(lambda ele :adict[ele])
        df5["PII"] = df5["PII Type"].map(lambda ele:"No" if ele  =="None"  else "Yes" )
        columns_order=['Column Number','Column Name','Data Type','Description',"PII","PII Type"]
        df6 = df5.reindex(columns=columns_order)
        cursor.execute(" DROP VIEW temp ")
        mydb.commit()
        cursor.close()
        value = session['file exists']
        account = session['username']
        return render_template("metadata.html", column_names=df6.columns.values, row_data=list(df6.values.tolist()), zip=zip, value=value,account = account)
    elif SourceType == 'Google Drive':
        URL = 'https://docs.google.com/uc?export=download'
        session1 = requests.Session()
        file_id = session['file_id']
        response = session1.get(URL, params = { 'id' : file_id }, stream = True)
        token = get_confirm_token(response)
        if token:
            params = { 'id' : file_id, 'confirm' : token }
            response = session1.get(URL, params = params, stream = True)
        a = session['delimiter']
        with closing(response) as r:
            reader = csv.reader(codecs.iterdecode(r.iter_lines(), 'utf-8'), delimiter=a , quotechar='"',quoting=csv.QUOTE_MINIMAL )
            lst = []
            a=[]
            for row in islice(reader,0,10):
                for cell in row:
                    y=conv2(cell)
                    a.append(y)
                lst.append(a)
                a=[]
        df = pd.DataFrame(lst[1:],columns=lst[0])
        df2=pd.DataFrame(df.dtypes,index=None,columns='data_type'.split())
        df3 = pd.DataFrame(df.columns,columns=['Column Name'])
        df4=df2.replace(['int64','float64','datetime64[ns]','object'],['int','float','datetime','string'])
        df4.index = df3.index
        df3['Data Type']=df4['data_type']
        df3 = df3.assign(ColumnNumber=[i+1 for i in range(len(df3))])[['ColumnNumber'] + df3.columns.tolist()]
        df3['Column Number']= df3['ColumnNumber']
        df4 = df3.drop(['ColumnNumber'], axis = 1)
        df4['Description'] = df4["Column Name"].map(lambda row: Business_Description(row))  
        adict = {}
        for col in df.columns.tolist():
            df[col] = df[col].map(lambda ele:pii(ele))
            x = df[col].value_counts().idxmax()
            adict[col]= x
        df4["PII Type"] = df4["Column Name"].map(lambda ele :adict[ele])
        df4["PII"] = df4["PII Type"].map(lambda ele:"No" if ele  =="None"  else "Yes" )
        columns_order=['Column Number','Column Name','Data Type','Description',"PII","PII Type"]
        df5 = df4.reindex(columns=columns_order)
        value = session['file exists']
        account = session['username']
        return render_template("metadata.html", column_names=df5.columns.values, row_data=list(df5.values.tolist()), zip=zip, value=value,account = account)
    elif SourceType == 'AzureBlob':
        account_name = session['account_name']
        account_key = session['account_key']
        container_name = session['ContainerName']
        blob_name = session['Blob Name']
        url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        service = BaseBlobService(account_name=account_name, account_key=account_key)
        token = service.generate_blob_shared_access_signature(container_name, blob_name, permission=BlobPermissions.READ, expiry=datetime.utcnow() + timedelta(hours=1),)
        #print(url)
        session1 = requests.Session()
        response = session1.get(f"{url}?{token}", stream = True)
        a = session['azure file delimiter'] #variable
        with closing(response) as r:
            reader = csv.reader(codecs.iterdecode(r.iter_lines(), 'latin-1'), delimiter=a , quotechar='"',quoting=csv.QUOTE_MINIMAL )
            #print(reader)
            lst = []
            a=[]
            for row in islice(reader,0,5):
                #print(row)
                
                for cell in row:
                    y=conv2(cell)
                    a.append(y)
                lst.append(a)
                a=[]
        df = pd.DataFrame(lst[1:],columns=lst[0])
        df2=pd.DataFrame(df.dtypes,index=None,columns='data_type'.split())
        df3 = pd.DataFrame(df.columns,columns=['Column Name'])
        df4=df2.replace(['int64','float64','datetime64[ns]','object'],['int','float','datetime','string'])
        df4.index = df3.index
        df3['Data Type']=df4['data_type']
        df3 = df3.assign(ColumnNumber=[i+1 for i in range(len(df3))])[['ColumnNumber'] + df3.columns.tolist()]
        df3['Column Number']= df3['ColumnNumber']
        df4 = df3.drop(['ColumnNumber'], axis = 1)
        df4['Description'] = df4["Column Name"].map(lambda row: Business_Description(row))  
        adict = {}
        for col in df.columns.tolist():
            df[col] = df[col].map(lambda ele:pii(ele))
            x = df[col].value_counts().idxmax()
            adict[col]= x
        df4["PII Type"] = df4["Column Name"].map(lambda ele :adict[ele])
        df4["PII"] = df4["PII Type"].map(lambda ele:"No" if ele  =="None"  else "Yes" )
        columns_order=['Column Number','Column Name','Data Type','Description',"PII","PII Type"]
        df5 = df4.reindex(columns=columns_order)
        value = session['file exists']
        account = session['username']
        return render_template("metadata.html", column_names=df5.columns.values, row_data=list(df5.values.tolist()), zip=zip, value=value,account = account)
    elif SourceType == 'One Drive':           #session['onedrive link'],session['Delimiter of onedrive'],
        session1 = requests.Session()
        dwn_url = session['onedrive link']
        response = session1.get(dwn_url, stream = True)
        token = get_confirm_token(response)
        if token:
            params = { 'confirm' : token }
            response = session1.get(dwn_url, params = params, stream = True)
        a = session['Delimiter of onedrive']
        with closing(response) as r:
            reader = csv.reader(codecs.iterdecode(r.iter_lines(), 'utf-8'), delimiter=a , quotechar='"',quoting=csv.QUOTE_MINIMAL )
            lst = []
            a=[]
            for row in islice(reader,0,10):
                for cell in row:
                    y=conv2(cell)
                    a.append(y)
                lst.append(a)
                a=[]
        df = pd.DataFrame(lst[1:],columns=lst[0])
        df2=pd.DataFrame(df.dtypes,index=None,columns='data_type'.split())
        df3 = pd.DataFrame(df.columns,columns=['Column Name'])
        df4=df2.replace(['int64','float64','datetime64[ns]','object'],['int','float','datetime','string'])
        df4.index = df3.index
        df3['Data Type']=df4['data_type']
        df3 = df3.assign(ColumnNumber=[i+1 for i in range(len(df3))])[['ColumnNumber'] + df3.columns.tolist()]
        df3['Column Number']= df3['ColumnNumber']
        df4 = df3.drop(['ColumnNumber'], axis = 1)
        df4['Description'] = df4["Column Name"].map(lambda row: Business_Description(row))  
        adict = {}
        for col in df.columns.tolist():
            df[col] = df[col].map(lambda ele:pii(ele))
            x = df[col].value_counts().idxmax()
            adict[col]= x
        df4["PII Type"] = df4["Column Name"].map(lambda ele :adict[ele])
        df4["PII"] = df4["PII Type"].map(lambda ele:"No" if ele  =="None"  else "Yes" )
        columns_order=['Column Number','Column Name','Data Type','Description',"PII","PII Type"]
        df5 = df4.reindex(columns=columns_order)
        value = session['file exists']
        account = session['username']
        return render_template("metadata.html", column_names=df5.columns.values, row_data=list(df5.values.tolist()), zip=zip, value=value,account = account)


def conv2(s):      # used for determing datatypes of flat file
    try:
        val = int(s)
        return val
    except ValueError:
        try:
            val = float(s)
            return val
        except ValueError:
            try:
                s=parse(s)
            except ValueError:
                pass    
    return s

def get_confirm_token(response):
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    return value
            return None


def Business_Description(instr):
    shdict = {'%': 'Percentage','rev':'Revenue','cat':'Category','num': 'Number','#': 'Number','no': 'Number','Sl': 'Serial','ph': 'Phone', 'idx': 'Index','dob': 'Date of Birth','perc':'Percentage','cust':'Customer'}
    instr = str(instr)
    import re
    tempstr = instr.replace("_"," ")
    tempstr = tempstr.replace("."," ")
    tempstr = re.sub(r'([a-z](?=[A-Z])|[A-Z](?=[A-Z][a-z]))', r'\1 ',tempstr)
    tempstr = tempstr.lower()
    for word in tempstr.split():
        try:
            tempstr = tempstr.replace(word,shdict[word])
        except:
            tempstr
    if(instr.isupper()):
        tempstr = tempstr.upper() 
    else:
        tempstr = tempstr.title()
    return tempstr

def pii(instr):
    import re
    if (bool(re.match(r'^(?!000|.+0{4})(?:\d{9}|\d{3}-\d{2}-\d{4})$',str(instr)))):
        return "Social Security Number"
    elif(bool(re.match(r'^(?:\d{10}|\d{3}-\d{3}-\d{4})$',str(instr)))):
        return "Phone Number"
    elif(bool(re.match(r'\b[A-Z0-9.@_%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',str(instr),re.I))):
        return "Email ID"
    elif(bool(re.match(r'^([456][0-9]{3})-?([0-9]{4})-?([0-9]{4})-?([0-9]{4})$',str(instr)))):
        return "Credit Card Number"
    else:
        return "None"



@app.route('/Rollbackmetadata', methods=['GET', 'POST'])
def Rollbackmetadata():
    mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM metadata WHERE EntryID = %s ;"%(session['EntryID']))
    cursor.execute(" DROP TABLE "+session['temp_table_name']+"  ;")
    mydb.commit()
    cursor.close()
    if session['source location type'] == 'Hive':
        return redirect(url_for('hive_metadata_3'))
    else:
        return redirect(url_for('index'))    



@app.route('/metadata', methods=['GET', 'POST'])   # after validate metadata to insert into database and 
def index1():                                 # to show back in html page 
    if request.method == "POST":
        session['rule exists']="No"
        newform = request.form.getlist
        # EntryID = newform('EntryID')
        ColumnNumber = newform('Column Number')
        ColumnName = newform('Column Name')
        ColumnName = [x.replace(" ","") for x in ColumnName]
        print(ColumnName)
        DataType = newform('Data Type')
        print(DataType)
        Nullable = newform('Nullable')
        PrimaryKey = newform('PrimaryKey')
        Default = newform('Default')
        Column_description = newform('Description')
        DQ_Check = newform('DQ Check')
        Date_Format = newform('Date Format')
        PII = newform("PII")
        PIIType = newform("PII Type")
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        df_temp = pd.DataFrame(list(zip(DataType)), columns =['Data Type'])
        df_temp_columnname = pd.DataFrame(list(zip(ColumnName)), columns =['ColumnName'])
        df_temp_columnname['ColumnName'] = df_temp_columnname.apply(lambda x: ("`"+x['ColumnName']+"`"),axis=1)
        df_temp_datatype =df_temp.replace(['datetime','string'],['TIMESTAMP','VARCHAR(50)'])
        print(df_temp_datatype,df_temp_columnname)
        df_temp_columnname.index = df_temp_datatype.index
        df_temp_columnname['DataType']=df_temp_datatype['Data Type']
        print(df_temp_columnname)
        records = df_temp_columnname.to_records(index=False)
        table_schema = list(records)
        print(table_schema)
        session['temp_table_name']='temp_'+str(session['EntryID'])
        DDL = ','.join(('{name} {type}'.format(name=col_name, type=col_type) for (col_name, col_type) in table_schema))
        print(DDL)
        sql_create_table_statement='CREATE TABLE '+session['temp_table_name']+' ('+DDL+');'
        print(sql_create_table_statement)
        cursor.execute(sql_create_table_statement)
        df4 = pd.DataFrame(list(zip(ColumnNumber,ColumnName,DataType,PrimaryKey,Nullable,DQ_Check,Default,Date_Format,Column_description,PII,PIIType)), columns =['ColumnNumber','ColumnName','DataType','PrimaryKey','Nullable','DQCheck','Default','Format','Description','PII','PIIType'])
        df8 = pd.DataFrame(list(zip(ColumnNumber,ColumnName,DataType,PrimaryKey,Nullable,DQ_Check,Default,Date_Format,Column_description,PII,PIIType)), columns =['Column Number','Column Name','Data Type','Primary Key','Nullable','DQ Check','Default','Date Format','Description','PII','PII Type'])
        df1 = df4.assign(EntryID=session['EntryID'])[['EntryID'] + df4.columns.tolist()]
        cols = "`,`".join([str(i) for i in df1.columns.tolist()])
        for i,row in df1.iterrows():
            sql = "INSERT INTO `metadata` (`" +cols + "`) VALUES (" + "%s,"*(len(row)-1) + "%s)"
            cursor.execute(sql, tuple(row))
        df5 = df1['DataType']
        mydb.commit()
        cursor.close()
        if session['file exists']=='YES' :
            mydb1 = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
            cursor1 = mydb1.cursor()
            cursor1.execute(' SELECT DataType FROM metadata Where EntryID = %s ;'%(session['existing file Entry ID']))
            data1 = cursor1.fetchall()
            df6 = pd.DataFrame(data1, columns='DataType'.split())
            df7 = df6['DataType']
            mydb.commit()
            cursor.close()
            if df5.equals(df7) :
                value = session['file exists']
                account = session['username']
                return render_template("metadata2.html", column_names=df8.columns.values, row_data=list(df8.values.tolist()), zip=zip, value=value,account = account )
            else :
                session['file exists'] = 'YES, But Metadata is not matching'
                value = session['file exists']
                account = session['username']
                return render_template("metadata2.html", column_names=df8.columns.values, row_data=list(df8.values.tolist()), zip=zip, value=value,account=account)
            
        else:
            value = session['file exists']
            account = session['username']
            return render_template("metadata2.html", column_names=df8.columns.values, row_data=list(df8.values.tolist()), zip=zip, value=value,account = account)
    return render_template("metadata.html",account = account)

@app.route('/rules', methods=['GET', 'POST'])  # for rules html page (metadata3.html)
def rules():
    mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
    cursor = mydb.cursor()
    cursor.execute("SELECT concat(ColumnName,'`~`',Description) as x FROM metadata WHERE EntryID = %s ;"%(session['EntryID']))
    data = cursor.fetchall()
    data1= list(data)
    cursor.execute("SELECT Name as x FROM centralrulerepo")
    data2 = cursor.fetchall()
    data3= list(data2)
    
    #print(data1)
    out = [item for t in data1 for item in t] 
    out1 = [item for t in data3 for item in t]
    print(out)
    print(data1)
    # printing output 
    #print(out) 
    mydb.commit()
    cursor.close()
    value = session['file exists']
    account = session['username']
    if session['rule exists']=="Yes":
        msg="Rule Name already Taken!"
    elif session['rule exists']=="Inserted":
        msg="New Rule "+session['RuleName']+" Added"
    elif session['rule exists']=="No":
        msg=""
    return render_template("metadata3.html", data = out,data1=out1,account = account,value=value,msg=msg)

@app.route('/rules01', methods=['GET', 'POST'])  # for custom rule input form in (rules page metadata3.html)
def rules01():
    if request.method == "POST":
        details = request.form
        Rulename='custom_rule_'+details['Rule Name']
        RuleName = Rulename.replace(" ","")
        session['RuleName']=RuleName
        RuleDefinition='case when '+details['Rule Definition']+' then 1 else 0 end '
        RuleCreator=details['Rule Creator']
        RuleApprover=details['Rule Approver']
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute('SELECT * FROM CentralRuleRepo WHERE `Name` = %s And UserName=%s ',(RuleName,session['username']))
        account = cursor.fetchone()
        mydb.commit()
        cursor.close()
        if account:
            session['rule exists']="Yes"
            return redirect(url_for('rules'))
        else:
            try:
                connection = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
                mySql_select_Query = ("select *,"+RuleDefinition+" AS "+RuleName+" from temp_"+str(session['EntryID']))
                print(mySql_select_Query)
                cursor = connection.cursor(buffered=True)
                cursor.execute(mySql_select_Query)
                record = cursor.fetchone()
                print(record)
                cursor.execute('INSERT INTO CentralRuleRepo (`Name`,UserName,`Definition`,Creator,Approver) VALUES(%s,%s,%s,%s,%s) ',(RuleName,session['username'],RuleDefinition,RuleCreator,RuleApprover))
                connection.commit()
                cursor.close()
                session['rule exists']="Inserted"
                return redirect(url_for('rules'))

                

            except mysql.connector.Error as error:
                print("Error is", error)
                session['rule exists']="Invalid SQL Syntax Error is: "+error
                return redirect(url_for('rules'))


            # cursor.execute('INSERT INTO CentralRuleRepo (`Name`,UserName,`Definition`,Creator,Approver) VALUES(%s,%s,%s,%s,%s) ',(RuleName,session['username'],RuleDefinition,RuleCreator,RuleApprover))
            # mydb.commit()
            # cursor.close()
            # session['rule exists']="Inserted"
            # return redirect(url_for('rules'))



@app.route('/rules1', methods=['GET', 'POST']) # after submit of rules page ( metadata3.html)
def rules1():
    if request.method == "POST":
        newform = request.form.getlist
        ColumnName = newform('ColumnName_1')
        RuleName = newform('RuleName_1')
        Parameters = newform('Parameters_1')
        details = request.form
        ColumnName2=details['ColumnName2']
        ColumnName3=details['ColumnName3']
        ColumnName4=details['ColumnName4']
        lookup_column_origin_file=(ColumnName2.split("`~`",1)[0])
        df4 = pd.DataFrame(list(zip(ColumnName,RuleName,Parameters)), columns =['Column Name','RuleName','RuleParameters'])
        df4['ColumnName']=df4['Column Name'].map(lambda x: x.split("`~`",1)[0])
        df4['Description']=df4['Column Name'].map(lambda x: x.split("`~`",1)[1])
        df5=df4.drop(['Column Name'], axis = 1)
        columns_order=['ColumnName','Description','RuleName','RuleParameters']
 
        df6 = df5.reindex(columns=columns_order)
 
        df1 = df6.assign(EntryID=session['EntryID'])[['EntryID'] + df6.columns.tolist()]
        rslt_df = df1[df1['RuleName'].astype(str).str.contains('custom',case=False)]
        df1 = df1[~df1['RuleName'].astype(str).str.contains('custom',case=False)]
        rules = rslt_df['RuleName'].values.tolist()
        mystring = ','.join(rules)
        df1['RuleName']=df1['RuleName'].map(lambda x: x.replace(" ",""))
        
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute(" SELECT  `Key` FROM userdetails WHERE `UserName`=%s AND `Status`=%s ; ",(session['username'],1))
        data = cursor.fetchone()
        a=data[0]
        df1.loc[df1.RuleName == 'Encrypt', 'RuleParameters'] = a
        update_lookup_parameter=''
        if any(df1.RuleName == "Lookup")==True:
            existing_string = (lookup_column_origin_file+','+ColumnName3+','+ColumnName4)
            print(existing_string)
            df1.loc[df1.RuleName == 'Lookup', 'RuleParameters'] = (existing_string)
            update_lookup_parameter=(existing_string+','+session['azureblob_parameter_dictionary_string'])
            print(update_lookup_parameter)
            # df1.loc[df1.RuleName == 'Lookup', 'RuleParameters'] = (existing_string+','+azureblob_parameter_dictionary_string)
        cols = "`,`".join([str(i) for i in df1.columns.tolist()])
        for i,row in df1.iterrows():
            sql = "replace INTO `business_rule_metadata` (`" +cols + "`) VALUES (" + "%s,"*(len(row)-1) + "%s)"
            cursor.execute(sql, tuple(row))
        cursor.execute('replace INTO `custom_rule_metadata` (`EntryId`,`Custom_rule`) VALUES(%s,%s) ',(session['EntryID'],mystring))
        cursor = mydb.cursor()
        statement = 'select a.`ColumnName`,a.`DataType`,a.`PrimaryKey`,a.`Nullable`,a.`DQCheck`,a.`Default`,a.`Format`,a.`Description`,a.`PII`,a.`PIIType`,b.`Rules` from (select * from `deaccelator`.`metadata` where `EntryID` = %s) as a left join (select `ColumnName`, group_concat(`RuleName`," - " ,`RuleParameters`) as `Rules` from `deaccelator`.`business_rule_metadata` where `EntryID` =%s group by `ColumnName`) as b on a.`ColumnName` = b.`ColumnName` union select a.`ColumnName`,a.`DataType`,a.`PrimaryKey`,a.`Nullable`,a.`DQCheck`,a.`Default`,a.`Format`,a.`Description`,a.`PII`,a.`PIIType`,b.`Rules` from (select * from `deaccelator`.`metadata` where `EntryID` = %s) as a right join (select `ColumnName`, group_concat(`RuleName`," - " ,`RuleParameters`) as `Rules` from `deaccelator`.`business_rule_metadata` where `EntryID` =%s group by `ColumnName`) as b on a.`ColumnName` = b.`ColumnName`;'%(session['EntryID'],session['EntryID'],session['EntryID'],session['EntryID'])
        cursor.execute(statement)
        data1 = cursor.fetchall()
        if any(df1.RuleName == "Lookup")==True:
            cursor.execute('update business_rule_metadata  set RuleParameters=%s where EntryID=%s and RuleName=%s;',(update_lookup_parameter,session['EntryID'],'Lookup'))
        columnlist = ['Column Name','Data Type','Primary Key','Nullable','DQ Check','Default','Format','Description','PII','PII Type','Rules']
        df8 = pd.DataFrame(data1,columns = columnlist)
        cursor.execute('DROP TABLE IF EXISTS temp_'+str(session['EntryID'])+' ;')
        mydb.commit()
        cursor.close()
        account = session['username']
        mystring1 = mystring.replace(",","  ")
        return render_template("metadata4.html", column_names=df8.columns.values, row_data=list(df8.values.tolist()), zip=zip,value=session['file exists'],lengthrow=len(list(df8.values.tolist())), mystring = mystring1,account = account )


@app.route('/rules2', methods=['GET', 'POST'])  # for lookup file column names and connection string capture
def rules2():                                   # in rules page (metadata3.html)
    if request.method == "POST":
        details = request.form
        session['account_name']=details['account_name']
        session['account_key']=details['account_key']
        session['ContainerName']=details['ContainerName']
        session['Blob Name']=details['Blob Name']
        session['azure file format']=details['azure file format']
        session['azure file delimiter']=details['azure file delimiter']
        azureblob_parameter_dictionary={"StorageAccountAccessKey":session['account_key'],"StorageAccountName":session['account_name'],"ContainerName":session['ContainerName'],"Path":session['Blob Name'],"Format":session['azure file format'],"Delimiter":session['azure file delimiter']}
        session['azureblob_parameter_dictionary_string'] = str(azureblob_parameter_dictionary)
        print(session['azureblob_parameter_dictionary_string'])
        account_name = session['account_name']
        account_key = session['account_key']
        container_name = session['ContainerName']
        blob_name = session['Blob Name']
        url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"
        service = BaseBlobService(account_name=account_name, account_key=account_key)
        token = service.generate_blob_shared_access_signature(container_name, blob_name, permission=BlobPermissions.READ, expiry=datetime.utcnow() + timedelta(hours=1),)
        #print(url)
        session1 = requests.Session()
        response = session1.get(f"{url}?{token}", stream = True)
        a = session['azure file delimiter'] #variable
        with closing(response) as r:
            reader = csv.reader(codecs.iterdecode(r.iter_lines(), 'latin-1'), delimiter=a , quotechar='"',quoting=csv.QUOTE_MINIMAL )
            #print(reader)
            lst = []
            a=[]
            for row in islice(reader,0,5):
                #print(row)
                
                for cell in row:
                    y=conv2(cell)
                    a.append(y)
                lst.append(a)
                a=[]
        df = pd.DataFrame(lst[1:],columns=lst[0])
        lookup_data = list(df.columns)
        mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
        cursor = mydb.cursor()
        cursor.execute("SELECT concat(ColumnName,'`~`',Description) as x FROM metadata WHERE EntryID = %s ;"%(session['EntryID']))
        data = cursor.fetchall()
        data1= list(data)
        cursor.execute("SELECT Name as x FROM centralrulerepo")
        data2 = cursor.fetchall()
        data3= list(data2)
    
        #   print(data1)
        out = [item for t in data1 for item in t] 
        out1 = [item for t in data3 for item in t]
        # printing output 
        #print(out) 
        mydb.commit()
        cursor.close()
        value = session['file exists']
        account = session['username']
        if session['rule exists']=="Yes":
            msg="Rule Name already Taken!"
        elif session['rule exists']=="Inserted":
            msg="New Rule "+session['RuleName']+" Added"
        elif session['rule exists']=="No":
            msg=""
        
        return render_template("metadata3.html", data3 = lookup_data,data = out,data1=out1,account = account,value=value,msg=msg)

@app.route('/Rollbackbusinessmetadata', methods=['GET', 'POST'])
def Rollbackbusinessmetadata():
    mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
    cursor = mydb.cursor()
    cursor.execute("DELETE FROM business_rule_metadata WHERE EntryID = %s ;"%(session['EntryID']))
    mydb.commit()
    cursor.close()
    return redirect(url_for('rules'))
    
import requests,json

@app.route('/pythonlogin/metadata4', methods=['GET', 'POST'])  # direct ingest button when file already exists is no
def index2():
    headers = {'Authorization': 'Bearer dapi9aca1f5a0ec7def2d231632c4a8373f7'}
    data = '{ "job_id" : 17 , "notebook_params": { "EntryId": ' +str(session['EntryID'])+ ' } }'
    response = requests.post('https://adb-6971132450799346.6.azuredatabricks.net/api/2.0/jobs/run-now', headers=headers, data=data)
    print(response)
    return redirect(url_for('home')) 


@app.route('/pythonlogin/metadata5', methods=['GET', 'POST']) # Append ingest button when file already exists is YES and metadata is matching
def append():
    mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
    cursor = mydb.cursor()
    cursor.execute(" UPDATE datacatlogentry Set Operation = %s Where entryid = %s ;",('Append',int(session['EntryID'])))
    mydb.commit()
    cursor.close()
    headers = {'Authorization': 'Bearer dapi9aca1f5a0ec7def2d231632c4a8373f7'}
    data = '{ "job_id" : 17 , "notebook_params": { "EntryId": ' +str(session['EntryID'])+ ' } }'
    response = requests.post('https://adb-6971132450799346.6.azuredatabricks.net/api/2.0/jobs/run-now', headers=headers, data=data)
    print(response)
    return redirect(url_for('home')) 

@app.route('/pythonlogin/metadata6', methods=['GET', 'POST'])
def replace():    # Replace ingest button when file already exists is YES and metadata is not matching
    mydb = mysql.connector.connect(host="demetadata.mysql.database.azure.com",user="DEadmin@demetadata",passwd="Tredence@123",database = "deaccelator")
    cursor = mydb.cursor()
    cursor.execute(' UPDATE datacatlogentry Set Operation = %s Where EntryID = %s ; ',('Overwrite',int(session['EntryID'])))
    mydb.commit()
    cursor.close()
    headers = {'Authorization': 'Bearer dapi9aca1f5a0ec7def2d231632c4a8373f7'}
    data = '{ "job_id" : 17 , "notebook_params": { "EntryId": ' +str(session['EntryID'])+ ' } }'
    response = requests.post('https://adb-6971132450799346.6.azuredatabricks.net/api/2.0/jobs/run-now', headers=headers, data=data)
    print(response)
    return redirect(url_for('home')) 




if __name__=="__main__":
    app.run(debug=True)

