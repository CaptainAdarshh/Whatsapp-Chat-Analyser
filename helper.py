import re
import emoji
import pickle
import base64
import stemmer
import pandas as pd
import streamlit as st
from pathlib import Path
from collections import Counter
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer

model = pickle.load(open("model/semtimental_analysis_model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

# Helper Functions
def local_css(file_name):
  with open(file_name) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def showError(message):
  st.error(message)
  st.stop()

def img_to_bytes(img_path):
  img_bytes = Path(img_path).read_bytes()
  encoded = base64.b64encode(img_bytes).decode()
  return encoded

def remove_emojis(data):
  return emoji.demojize(data)

def seperate(x, seperator):
  if seperator == 'removed':
    if x.find(seperator) != -1:
      return x.split(seperator)[1]
    else:
      return x.split('left')[0]
  else:
    if x.find(seperator) != -1:
      return x.split(seperator)[1]
    else:
      return x.split('joined')[0]

# Main functions
def fetch_stats(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  num_messages = df.shape[0]
  diff_days = (df.Date.iloc[len(df)-1] - df.Date.iloc[0]).days
  words = []
  for message in df['Message']:
    words.extend(message.split())

  num_media_messages = df[df['Message'] == '<Media omitted>\n'].shape[0]
  return num_messages, len(words), num_media_messages, diff_days

def removed_left(df):
  df = df[df['User']=='group_notification']
  df = df[df['Message'].str.contains('changed|deleted|encrypted|created') == False]
  removedLeft = df[df['Message'].str.contains('removed|left') ==  True]
  addedJoined = df[df['Message'].str.contains('added|joined') == True]
  removedLeft['Status'] = 0
  addedJoined['Status'] = 1
  removedLeft['User'] = removedLeft.Message.apply(lambda x: seperate(x, 'removed'))
  addedJoined['User'] = addedJoined.Message.apply(lambda x: seperate(x, 'added'))
  new_df = pd.concat([removedLeft, addedJoined])
  new_df.drop(columns=['Date','Time', 'Message', 'Year', 'Month', 'MonthNum', 'DayOfWeek', 'WeekNum', 'Day', 'Hour', 'DayName', 'Minute'], inplace=True, axis=1)
  new_df['User'] = new_df['User'].str.lower()
  new_df['User'] = new_df['User'].str.split(', ')
  new_df = new_df.explode('User')
  new_df['User'] = new_df['User'].str.split(' and ')
  new_df = new_df.explode('User')
  new_df['User'] = new_df['User'].str.strip()
  new_df = new_df.groupby('User')['Status'].count().reset_index()
  new_df['Status'] = new_df.Status.apply(lambda x: x%2 == 0)
  return len(new_df[new_df.Status==True])

def chat_from(selected_user, df):
  print("Called chat from")
  print("*"*20)
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  else:
    selected_user = 'You'
  unique_years = df['Year'].unique()
  start_year = unique_years[0]
  msg_count = df.groupby(['Date']).count()['Message']
  avg_msg = round(msg_count.mean(),2)
  return start_year, avg_msg, selected_user

def most_talkative(df):
  df = df[df['User'] != 'group_notification']
  user = df['User'].value_counts()
  username = user.index[0]
  avg_msg = round(user[username]/len(df)*100, 2)
  return username, avg_msg

def get_urls(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  df = df[df['User'] != 'group_notification']
  urls_list = []
  url = []
  for i in df['Message']:
    o = re.findall('(https://.*)|(http://.*)',i)
    if len(o) != 0:
      urls_list.append(o[0][0].split(' ')[0])
  if len(urls_list) != 0:
    for i in urls_list:
      o = re.search('.*[.](com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)',i)
      if o != None:
        url.append(o.group())
    url_df = pd.DataFrame(Counter(url).most_common(len(Counter(url))), columns=['Urls', 'Count'])
    return url_df
  else:
    return pd.DataFrame()

def get_emojis(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  emojis = []
  description = []
  for message in df['Message']:
    all_emoji = emoji.distinct_emoji_list(message)
    emojis.extend([emoji.emojize(is_emoji) for is_emoji in all_emoji])
  emoji_df = pd.DataFrame(Counter(emojis).most_common(len(Counter(emojis))), columns=['Emoji', 'Count'])
  for i in emoji_df['Emoji']:
    description.append(emoji.demojize(i))
  emoji_df['Description'] = description
  emoji_df['Description'] = emoji_df['Description'].apply(lambda x: x.strip(':'))
  emoji_df['EmojiDescription'] = emoji_df['Emoji'] + ' - ' + emoji_df['Description']
  return emoji_df

def influencer(df):
  df = df[df['User'] != 'group_notification']
  new_df = df.groupby(['User'])
  inf_dict = {}
  for name, group in new_df:
    count = 0
    for i in group['Message']:
      if '<Media omitted>' in i:
        count += 1
    inf_dict[name]=count
  name = max(inf_dict, key=inf_dict.get)
  name_df = df[df['User']==name]
  percent = (inf_dict[name]/name_df.shape[0])*100
  return name, round(percent,2), inf_dict[name]

def long_winded(df):
  df = df[df['User'] != 'group_notification']
  msg_len = []
  for i in df['Message']:
    msg_len.append(len(i))
  df['Message_len'] = msg_len
  new_df = df.sort_values(by=['Message_len'],ascending=False)
  name = new_df.iloc[0]['User']
  user_df = df[df['User']==name]
  avg_msg_len = int(user_df['Message_len'].mean())
  mean_character = user_df[user_df['Message_len'] > avg_msg_len]
  percentage = round((mean_character.shape[0] / user_df.shape[0])*100, 2)
  return name, avg_msg_len, percentage

def early_bird(df, format):
  new_df = df[df['User']!='group_notification']
  if format == '12 Hour':
    new_df = new_df[((new_df['Meridian'] == 'AM') & (pd.to_numeric(new_df['Hour']) > 7)) | (new_df['Meridian'] == 'PM')]
  elif format == '24 Hour':
    new_df = df[pd.to_numeric(df['Hour']) > 7]
  user = new_df['User'].value_counts()
  username = user.index[0]
  avg_msg = round(user[username]/len(new_df)*100, 2)
  return username, avg_msg

def professor(df):
  pass

def emoji_lover(df):
  df=df[df['User']!='group_notification']
  emoji_user = {}
  new_df = df.groupby(['User'])
  for i in df['User'].unique():
    count = 0
    group = new_df.get_group(i)
    for j in group['Message']:
      for k in j:
        if emoji.is_emoji(k):
          count += 1
    emoji_user[i]=count   
  name = max(emoji_user, key=emoji_user.get)
  total = emoji_user.values()
  percent = round((emoji_user[name]/sum(total))*100, 2)
  return name, percent

def night_owl(df, format):
  new_df = df[df['User']!='group_notification']
  if format == '12 Hour':
    new_df = new_df[((new_df['Meridian'] == 'AM') & (pd.to_numeric(new_df['Hour']) < 7)) | (new_df['Meridian'] == 'PM')]
  elif format == '24 Hour':
    new_df = new_df[(pd.to_numeric(new_df['Hour']) < 6) | (pd.to_numeric(new_df['Hour']) > 11)]
  user = new_df['User'].value_counts()
  username = user.index[0]
  avg_msg = round(user[username]/len(new_df)*100, 2)
  return username, avg_msg

def hourly_timeline(selected_user, df, format):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  
  new_df['Message'] = [1] * new_df.shape[0]
  if format == '12 Hour':
    new_df['Hour'] = new_df['Hour'].apply(lambda x: ('0'+str(x)) if (len(x)<2) else x )
    new_df['Hour'] = new_df['Meridian'].astype(str) + ' ' + new_df['Hour'].astype(str) 
    new_df = new_df.groupby('Hour').sum().reset_index()
  else:
    new_df = new_df.groupby('Hour').sum().reset_index()
  return new_df

def daily_timeline(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  new_df = new_df.groupby('Date')['Message'].count().reset_index()
  return new_df

def weekly_timeline(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  new_df  = df.groupby(['Year','Month','WeekNum'], sort=False)['Message'].count().reset_index()
  week = []
  for i in range(len(new_df)):
    week.append(str(new_df['WeekNum'][i]) + " - " + new_df['Month'][i] + " - " + str(new_df['Year'][i]))
  new_df['Week'] = week
  new_df['Week'] = new_df[['WeekNum', 'Week']].apply(lambda x: "Week 0"+x['Week'] if x['WeekNum']<10 else "Week "+x['Week'], axis=1)
  new_df.sort_values(['WeekNum', 'Month', 'Year'], inplace=True)
  return new_df

def monthly_timeline(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  new_df  = df.groupby(['Year','Month','MonthNum'], sort=False)['Message'].count().reset_index()
  month = []
  for i in range(new_df.shape[0]):
    month.append(str(new_df['MonthNum'][i]) + " - " + new_df['Month'][i] + " - " + str(new_df['Year'][i]))
  new_df['Months'] = month
  new_df['Months'] = new_df[['MonthNum', 'Months']].apply(lambda x: "Month 0"+x['Months'] if x['MonthNum']<10 else "Month "+x['Months'], axis=1)
  new_df.sort_values(['MonthNum', 'Year'], inplace=True)
  return new_df

def most_busy_day(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  
  new_df = new_df.groupby(['DayName', 'DayOfWeek'], sort=False)['Message'].count().reset_index()
  new_df.sort_values('DayOfWeek', inplace=True)
  new_df['Days'] = new_df['DayOfWeek'].astype(str) + " - " + new_df['DayName']
  return new_df

def most_busy_month(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  
  new_df = new_df.groupby(['MonthNum', 'Month'], sort=False)['Message'].count().reset_index()
  new_df.sort_values('MonthNum', inplace=True)
  new_df['Months'] = new_df['MonthNum'].astype(str) + " - " + new_df['Month']
  new_df['Months'] = new_df[['MonthNum', 'Months']].apply(lambda x: "Month 0"+x['Months'] if x['MonthNum']<10 else "Month "+x['Months'], axis=1)
  return new_df

def most_common_words(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  new_df = new_df[new_df['Message'] != '<Media omitted>\n']
  new_df = new_df[new_df['Message'] != 'This message was deleted\n']

  f = open('stop_hinglish.txt')
  stop_words = f.read()

  words = []

  for message in new_df['Message']:
    message = re.sub('[^A-Za-z\s]','',message)
    if message == '':
      pass
    else:
      for word in message.lower().split():
        if word not in stop_words:
          words.append(word)
  
  most_common_df = pd.DataFrame(Counter(words).most_common(50), columns=['Message', 'Count'])
  most_common_df.sort_values('Count')
  return most_common_df

def user_chat_percentage(df):
  df = df[df['User'] != 'group_notification']
  user = df['User'].value_counts()
  new_df = pd.DataFrame ({ 'User': user.index, 'Message': user})
  new_df['Percentage'] = new_df['Message'].apply(lambda x: round(x/len(df)*100, 2))
  new_df['User'] = new_df['Percentage'].astype(str) + "% - " + new_df['User']
  new_df.drop('Message', axis=1, inplace=True)
  new_df.reset_index(drop=True,inplace=True)
  return new_df

def create_wordcloud(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['User'] != 'group_notification']
  new_df = new_df[new_df['Message'] != '<Media omitted>\n']
  new_df = new_df[new_df['Message'] != 'This message was deleted\n']
  
  f = open('stop_hinglish.txt')
  stop_words = f.read()

  def remove_stop_words(message):
    y = []
    for word in message.lower().split():
      if word not in stop_words:
        y.append(word)
    return " ".join(y)

  wc = WordCloud(width=400, height=400, min_font_size=10)
  new_df['Message'] = new_df['Message'].apply(remove_stop_words)
  df_wc = wc.generate(new_df['Message'].str.cat(sep=" "))
  return df_wc

def text_transformation(words_list):
  corpus = []
  myStemmer = stemmer.Stemmer()
  for item in words_list:
    new_item = item.lower()
    new_item = re.sub('[^a-z]',' ', str(new_item))
    if ('https://' or 'http://') in new_item:
      pass
    else:
      new_item = new_item.split()
      for i in new_item:
        i = myStemmer.stemWord(i)
        if len(i)>1:
          corpus.append(re.sub('[^a-z]','', i))
  return list(set(corpus))

def sentimental_analysis(selected_user, df):
  if selected_user != 'Overall':
    df = df[df['User'] == selected_user]
  new_df = df[df['Message']!='<Media omitted>\n']
  new_df = new_df[new_df['Message']!='This message was deleted\n']
  new_df['Message'] = new_df['Message'].apply(remove_emojis)
  words = text_transformation(new_df['Message'])
  prediction = model.predict(vectorizer.transform(words)).tolist()
  total = len(prediction)
  negative = total - prediction.count(1.0)
  positive = total - negative
  negative_per = round(negative / total * 100, 2)
  positive_per = round(positive / total * 100, 2)
  return negative_per, positive_per