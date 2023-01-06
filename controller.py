import json
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import pytz

def format_timedelta_to_HHMM(td):
    td_in_seconds = td.total_seconds()
    hours, remainder = divmod(td_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    if minutes < 10:
        minutes = "0{}".format(minutes)
    if seconds < 10:
        seconds = "0{}".format(seconds)
    return "{}:{}".format(hours, minutes)

def read_db():
    con = sqlite3.connect("attendance.db")

    attendance_df = pd.read_sql_query("SELECT * from Attendance", con)
    attendance_action_df = pd.read_sql_query("SELECT * from AttendanceActions", con)
    df = attendance_action_df.merge(attendance_df, left_on='AttendanceId', right_on='Id')
    df['ActionTime']= pd.to_datetime(df['ActionTime'])
    df.drop(columns=['Id_x', 'Id_y'],inplace=True)

    con.close()
    return df

def check_attendance(employee,day):
    df = read_db()
    #Run Query to get attendance
    query = f"employee == '{employee}' and day == '{day}' "
    print(query)
    query_df = df.query(query)
    #Drop unwanted columns and reset index
    query_df.drop(columns=['AttendanceId','employee'],inplace=True)
    query_df.reset_index(inplace=True,drop=True)

    if query_df.empty:
        attended = False
    else:
        attended = True

    if attended:
        #Add a row at the end of the day if the employee last Action was CheckIn
        if query_df['Action'][0] == "CheckIn" and query_df.shape[0] %  2 != 0:
            date  = datetime.strptime(query_df['day'][0], '%Y-%m-%d')
            date = timedelta(days=1) + date
            df2 = {'ActionTime': date, 'Action': 'CheckOut', 'day': query_df['day'][0]}
            query_df = query_df.append(df2, ignore_index = True)  
        #Add a row at the start of the day if the employee first Action was CheckOut
        elif query_df['Action'][0] == "CheckOut" and query_df.shape[0] %  2 != 0:
            date  = datetime.strptime(query_df['day'][0], '%Y-%m-%d')
            df2 = pd.DataFrame([{'ActionTime': date, 'Action': 'CheckIn', 'day': query_df['day'][0]}])
            query_df = pd.concat([df2, query_df], ignore_index=True)

        #generate the time delta and format it
        s = pd.Series(query_df['ActionTime'])
        series = s.groupby(s.index // 2).diff()
        series.sum()
        duration = format_timedelta_to_HHMM(series.sum())
    else:
        duration = '00:00'

    return {'attended': attended,'duration': duration}

def check_record(employee):
    df = read_db()
    #create a column for UTC timezone
    cairo = pytz.timezone('Africa/Cairo')
    df['UTCAction'] = df['ActionTime'].dt.tz_localize(cairo).dt.tz_convert(pytz.utc)
    df['UTCDay'] = df['UTCAction'].dt.strftime("%Y-%m-%d")
    df['time'] = df['UTCAction'].dt.strftime('%Y-%m-%dT%H:%M:%S%z')
    #make the query to get the records
    query = f"employee == '{employee}'"
    query_df = df.query(query)
    if query_df.empty:
        return {'Error':'No records for the employee'}
    #create the dict
    dict_data_list = {'days': []}
    for gg, dd in query_df.groupby(['UTCDay']):
        group = {'date': gg}
        ocolumns_list = list()
        for _, data in dd.iterrows():
            data = data.drop(labels=['UTCDay','ActionTime','day','employee','AttendanceId','UTCAction'])
            ocolumns_list.append(data.to_dict())
        group['actions'] = ocolumns_list
        dict_data_list['days'].append(group) 
    
    return dict_data_list

