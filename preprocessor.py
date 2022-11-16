import re
import pandas as pd

def seperate_date_time(x):
  date = pd.to_datetime(x.split(', ')[0])
  time = x.split(', ')[1].split(' - ')[0]
  return date, time

def preprocess(data, format):
  pattern = {
    '12 Hour':'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s[APap][mM]\s-\s',
    '24 Hour':'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s-\s',
  }

  user_message = re.split(pattern[format], data)[1:]
  date_time = re.findall(pattern[format], data)

  if (len(user_message) and len(date_time)) == 0:
    return pd.DataFrame(), True

  df = pd.DataFrame({'UserMessage': user_message, 'DateTime': date_time})
  df[['Date','Time']] = df['DateTime'].apply(lambda x: seperate_date_time(x)).to_list()
  
  users = []
  messages = []
  for message in df['UserMessage']:
    entry = re.split('([\w\W]+?):\s', message)
    if entry[1:]:
      users.append(entry[1])
      messages.append(entry[2])
    else:
      users.append('group_notification')
      messages.append(entry[0])

  df['User'] = users
  df['Message'] = messages
  df['Year'] = df['Date'].dt.year
  df['Month'] = df['Date'].dt.month_name()
  df['MonthNum'] = df['Date'].dt.month
  df['Day'] = df['Date'].dt.day
  df['DayName'] = df['Date'].dt.day_name()
  df['DayOfWeek'] = df['Date'].dt.dayofweek
  df['WeekNum'] = df['Date'].dt.week
  # df['date'] = df['date'].dt.date
  df['Hour'] = df['Time'].apply(lambda x: x.split(':')[0])
  df['Minute'] = df['Time'].apply(lambda x: (x.split(':')[1]).split(' ')[0])
  if format == '12 Hour':
    df['Meridian'] = df['Time'].apply(lambda x: (x.split(':')[1]).split(' ')[1]).str.upper()
  df.drop(columns=['UserMessage', 'DateTime'], inplace=True)
  return df, False
