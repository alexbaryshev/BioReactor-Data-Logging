"""
Written By: Kathryn Cogert
For: Winkler Lab/CSE599 Winter Quarter 2016
Purpose: Write and read from a google doc.


Note: Due to this issue:https://github.com/ctberthiaume/gdcp/issues/11, I had
to run python2.7 in a virtual environment for this to work.  UGH!
To Do:
+Visualization Tools
+Combinations with human collected data

"""

import os
import urllib2
import datetime
from xml.etree import ElementTree
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
import time

"""
Define Custom Errors
"""


class BaseError(Exception):
    """Base error for google drive manipulation and navigation errors."""


class InvalidDir(BaseError):
    """Error for specifying a directory ID that doesn't exist"""


class NotMatching(BaseError):
    """Error for specifying a file name that doesn't exist"""


class NoFolders(BaseError):
    """Error for specifying a directory to find folders in that has no folders
    in it"""


class NoSuchReactor(BaseError):
    """Error for specifying a reactor number to find the directory for"""


"""
Authenticate the connection to google drive
Requires correct client_secrets, credentials, and settings files.
"""

gauth = GoogleAuth("settings.yaml")
gauth.CommandLineAuth()
gauth.Authorize()
drive = GoogleDrive(gauth)


def remove_file(filename):
    """
    Determines if a file exists before trying to delete it
    :param filename: str, name of file to delete
    :return: boolean if the filename doesn't exist
    """
    if os.path.exists(filename):
        os.remove(filename)
    else:
        return False
    return


def get_newdata(reactorno):
    """
    Uses HTTP method to query cRIO server for reactor status
    :param reactorno: int, this is the reactor in question
    :return: dataframe, this is a dataframe of requested values
    """
    # Builds the cRIO web server URL where we will make the GET request
    url = 'http://128.208.236.156:8080/cRIOtoWeb/DataTransfer?reactorno=' + \
          str(reactorno)
    # Makes the GET request
    result = urllib2.urlopen(url).read()
    # Result is a labview "cluster" type variable, (like a struct in java)
    # But it is saved here as an XML string and converted to a parseable form
    root = ElementTree.fromstring(result)
    column_names = [Name.text for Name in root[0][1].findall('Name')]
    column_names.insert(0, 'Date')
    # Returns data and data cleans
    data = [Value.text for Value in root[0][1].findall('Value')]
    ts = time.time()
    ts_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    data.insert(0, ts_date)
    df = pd.DataFrame(columns=column_names)
    df.loc[0] = data
    df = df.set_index('Date')
    return df


def get_file_list(directory):
    """
    Returns a file list given the file ID of a directory folder.
    :param directory: str, this is the file ID of the directory of interest
    :return: file_list, list, this is a list of all the files in the directory
    :exceptions: if the specified ID is invalid, raises an exception.
    """
    # List all files
    try:
        file_list = drive.ListFile({'q': "'%s' in parents and trashed=false" %
                                         directory}).GetList()
        return file_list
    except:
        # If directory id is bad, say so.
        raise InvalidDir('Specified directory ' + directory + ' is invalid')


def find_folderid(folder_name, directory):
    """
    Returns the id of a folder of a given name in a given directory
    :param folder_name: str, this is the name of folder of interest
    :param directory: str, this is the folder ID of the directory of interest
    :return: str, this is the folder ID from folder_name
    :exception NotMatching: if no folder of specified name is found, raise
    exception
    :exception NoFolders: if there are no folders in the specified directory,
    raise exception
    """
    # get list of files from our directory of interest
    file_list = get_file_list(directory)
    # We'll use this to decide whether we need to raise an error later
    no_folders_here = True
    for afile in file_list:
        # if file is a folder...
        if afile['mimeType'] == 'application/vnd.google-apps.folder':
            no_folders_here = False  # We won't need to raise the error
            if afile['title'] == folder_name:
                # Look for folder that matches name, and save the folder ID
                fid = afile['id']
                return fid
    # If nothing matched, the name was wrong
    if 'fid' in locals() or 'fid' in globals():
        raise NotMatching('No folder of that name in specified dir')
    # if none of files in the list were folders, then say so.
    if no_folders_here:
        raise NoFolders('There are no folders in specified directory')


def find_reactorfolder(reactorno):
    """
    Finds the directory of a specified reactor. (reactors are numbered 1
    thru 6)
    :param reactorno: int, this is the reactor in question
    :return: str, this is the file ID of the specified reactor's directory
    :exception No Such Reactor: if no directory of the specified reactor
    exists, raise an error.
    """
    # folder will be 'R1', 'R2', etc. So make that string.
    r_folder_name = 'R' + str(reactorno)
    # Navigate through the directories
    wlab_fid = find_folderid('Winkler Lab', 'root')
    rdata_fid = find_folderid('ReactorData', wlab_fid)
    try:  # When we find reactordata directory, look for our reactor's folder
        r_fid = find_folderid(r_folder_name, rdata_fid)
        return r_fid
    except:  # If we can't find it, say so.
        raise NoSuchReactor('There is no reactor with that number')


def return_reactorfilelist(reactorno):
    """
    Return list of correctly named files in specifed reactors directory
    :param reactorno: int, the number of reactor in question
    :return:
    """
    tgt_folder_id = find_reactorfolder(reactorno)
    file_list = get_file_list(tgt_folder_id)  # List all files in that folder
    reactor_file_list = []
    filename_format = 'R' + str(reactorno) + 'data %Y-%m-%d'
    for afile in file_list:
        # If it's not a folder, try to parse the name and get the time stamp
        if afile['mimeType'] != 'application/vnd.google-apps.folder':
            file_title = afile['title']
            try:
                file_ts = datetime.datetime.strptime(file_title,
                                                     filename_format)
            except Exception, e:
                # If can't parse file, let user know their organization sucks
                print 'Warning: ' + str(e)
                continue  # skip this iteration
            reactor_file_list.append(afile)  # Add this file to the list
    return reactor_file_list


def find_reactorfile(reactorno, collect_int=30, file_length=14):
    """
    Find latest or make new file in specified reactor's directory
    :param reactorno: int, the number of reactor in question
    :param collect_int: float, this is the number of secs between data pts.
    :param make: boolean, if true (default) than make a new file if needed
    :param file_length: float, this is the number of days in a file.
    :return: our_file, this is the file
    """
    # Get the current date
    what_time_is_it = datetime.datetime.now()
    # Get file id of our reactor's folder
    tgt_folder_id = find_reactorfolder(reactorno)
    file_list = return_reactorfilelist(1)  # List all files in that folder
    no_file = True
    filename_format = 'R' + str(reactorno) + 'data %Y-%m-%d'
    if file_list:
        for afile in file_list:
            # Get each files timestamp
            file_ts = datetime.datetime.strptime(afile['title'],
                                                 filename_format)
            # Take difference of current and file time stamp
            ts_delta = what_time_is_it - file_ts
            # Select out # of days
            days_since_creation = ts_delta.days
            # Look for file made in specified time frame
            if days_since_creation < file_length:
                no_file = False
                our_file = afile  # Return our file of interest
                break
    # If file we asked for doesn't exist, make a new one!
    if no_file:
        # File name format is "R#Data YYYY-MM-DD"
        filename = filename_format.format(what_time_is_it)
        print 'Making new file: ' + filename
        # Create a new file with that name
        our_file = drive.CreateFile({'title': filename,
                                          'mimeType': 'text/csv',
                                          "parents":
                                              [{"kind": "drive#fileLink",
                                                "id": tgt_folder_id}]})
        to_write = get_newdata(reactorno)  # Get first data pt
        to_write.to_csv('temp.csv')  # Convert to CSV
        our_file.SetContentFile('temp.csv')  # Write this to google drive
        remove_file('temp.csv')  # Remove temp file w/ first data pt
        our_file.Upload()  # Upload it
        # Tell user what happened
        print 'Sucessfully created new file ' + filename
        time.sleep(collect_int)  # Wait before collecting another pt
    return our_file


def read_from_reactordrive(reactorno, filename, latest=1):
    """
    Reads the google drive files for reactor data and saves as a csv
    :param reactorno: int, the number of reactor in question
    :param filename: name of the file we want to save as
    :param latest: latest file only if true, else or all files as master csv
    :return:
    """
    # Get the current date
    what_time_is_it = datetime.datetime.now()

    file_list = return_reactorfilelist(reactorno)  # Find files
    sortable_file_list = []  # initialize this sortable list
    idx = 0
    filename_format = 'R' + str(reactorno) + 'data %Y-%m-%d'
    for afile in file_list:
        # Get each files timestamp
        file_ts = datetime.datetime.strptime(afile['title'],
                                             filename_format)
        # Take difference of current and file time stamp
        ts_delta = what_time_is_it - file_ts
        # These are the key params we'll need to sort and select the file
        file_summary = (idx, ts_delta, afile['title'], afile['id'])
        sortable_file_list.append(file_summary)
        idx = +1
    if latest:
        # If we only want the latest file, find the latest file with ts_delta
        tgt_file = min(sortable_file_list, key=lambda t: t[1])
        tgt_file_idx = tgt_file[0]
        # Use index from
        file_list[tgt_file_idx].GetContentFile(filename)
    else:
        # Start filling up a dataframe
        file_list[0].GetContentFile('temp.csv')
        masterdf = pd.read_csv('temp.csv')
        masterdf = masterdf.set_index('Date')
        # Remove temporary file & first entry in list
        remove_file('temp.csv')  # Remove temp file
        del file_list[0]
        # Fill up dataframe with the other files by appending
        idx = 0
        for afile in file_list:
            # Download and convert to dataframe
            file_list[idx].GetContentFile('temp.csv')
            idx += 1
            to_append_df = pd.read_csv('temp.csv')
            to_append_df = to_append_df.set_index('Date')
            remove_file('temp.csv')  # Remove temp file
            masterdf = masterdf.append(to_append_df)
        # Sort from oldest to newest
        masterdf.index = pd.DatetimeIndex(masterdf.index)
        masterdf = masterdf.sort_index(ascending=True)
        masterdf.to_csv(filename)
    return


def write_to_reactordrive(reactorno, collect_int, file_length):
    """
    Writes some latest dataframe to a specified file for a specified reactor
    :param reactorno: int, this is the reactor in question
    :param collect_int: float, this is the number of secs between data pts.
    :param file_length: float, this is the number of days in a data file
    """
    # Get latest data point from the reactor.
    try:
        to_write = get_newdata(reactorno)
        # Find our file we asked for
        file_to_write = find_reactorfile(reactorno, collect_int, file_length)
        # Take all data in drive and convert to dataframe
        file_to_write.GetContentFile('temp.csv')
        old_data = pd.read_csv('temp.csv')
        old_data = old_data.set_index('Date')
        # Append latest data point in local csv file
        new_data = old_data.append(to_write)
        new_data.to_csv('temp.csv')
        # Write to google drive file
        file_to_write.SetContentFile('temp.csv')
        # Delete that local file
        remove_file('temp.csv')
        file_to_write.Upload()  # Upload it
        print 'Reactor #' + str(reactorno)+' Data point saved successfully'
    except Exception, e:
        print str(e)
        ts_str = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
        print 'Due to error, skipped collection at ' + str(ts_str)
    return



