# -*- coding: utf-8 -*-
"""FinalProject

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GypFetYFYt2oVCvxknfKuIArCrRBEdqs

# "Foundations of Computer Science" course (1819-1-F9101Q001)
## Final Project

**Alessandro Vaccarino - 811751**


---

The current project refers to [this provided guideline](https://gdv.github.io/foundationsCS-2018/)

0.   **Common part**
"""

import pandas as pd
import numpy as np
import re
import seaborn as sns

googleplaystore_url = 'https://raw.githubusercontent.com/gdv/foundationsCS-2018/master/ex-data/project/googleplaystore.csv'
googleplaystore_user_reviews_url = 'https://raw.githubusercontent.com/gdv/foundationsCS-2018/master/ex-data/project/googleplaystore_user_reviews.csv'

googleplaystore_import = pd.read_csv(googleplaystore_url)
googleplaystore_import.head(2)

googleplaystore_import.dtypes

googleplaystore_user_reviews_import = pd.read_csv(googleplaystore_user_reviews_url)
googleplaystore_user_reviews_import.head(2)

googleplaystore_user_reviews_import.dtypes

"""With reference to [this](https://elearning.unimib.it/mod/forum/discuss.php?d=72986) eLearning topic, there are Apps duplicated with different attributes (e.g. "Reviews").

I'm assuming "Reviews" column can be a good candidate to detect "golden" row: an higher reviews counter can be associated to a more recent scraping activity.

So, for each "App" column value (assiming App name could be a good primary key candidate), I keep the row with the highest "Reviews" value

Referring to this [link text](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.duplicated.html) Pandas documentation page, "duplicated" method by default is set as True except for the first occurrence. 

So, let's use it descending sorting dataframe "Reviews", to have  "False" on the row with the highest value and "True" on the others
"""

googleplaystore_import['Duplicated'] = googleplaystore_import.sort_values(by=['Reviews'], ascending=[False]).duplicated(['App'])

"""Have a check on 2 examples:

1 - "Farm Heroes Saga"

2 - "Facebook"
"""

googleplaystore_import.loc[googleplaystore_import['App'] == 'Farm Heroes Saga']

googleplaystore_import.loc[googleplaystore_import['App'] == 'Facebook']

"""Ok, test is successful: now I can remove rows with "Duplicated" = True"""

googleplaystore = googleplaystore_import.loc[googleplaystore_import['Duplicated'] == False].drop(['Duplicated'], axis=1)
googleplaystore_dup = googleplaystore_import.loc[googleplaystore_import['Duplicated'] == True].drop(['Duplicated'], axis=1)

"""Ok, now "googleplaystore" seems good

Before starting, give a look to googleplaystore_user_reviews_import
"""

googleplaystore_user_reviews_import.head()

"""This table appears to have no primary key (I could have the same review for the same App).

So, we've only to clean table removing "NaN" reviews, focusing on "Translated_Review" column
"""

googleplaystore_user_reviews = googleplaystore_user_reviews_import[~googleplaystore_user_reviews_import['Translated_Review'].isnull()]
googleplaystore_user_reviews_null = googleplaystore_user_reviews_import[googleplaystore_user_reviews_import['Translated_Review'].isnull()]

"""1.   **Convert the app sizes to a number**

First of all, check values for column "Size", to get a quick data profiling
"""

googleplaystore.groupby('Size').size().reset_index(name='counts')

"""Size = '1,000+' and 'Varies with device'? Maybe there is an issue... Let's give a deeper check:"""

googleplaystore.loc[googleplaystore['Size'] == '1,000+']

issuedRowPandasIndex = int(googleplaystore.loc[googleplaystore['Size'] == '1,000+'].index[0])
# "+1" to get effective row number in file
issuedRowNumber = issuedRowPandasIndex + 1

"""Let's give a check on the original file, to be sure the issue is not caused by a bad file read:"""

import urllib.request

googleplaystore_file = urllib.request.urlopen(googleplaystore_url)
for i, line in enumerate(googleplaystore_file):
  if i == issuedRowNumber:
    print(line)
  elif i > issuedRowNumber:
    break
googleplaystore_file.close()

"""...Ok, CSV file is completely missing a column (neither a double delimiter ",,")...
It's a single case, so try to fix it manually
"""

googleplaystore.loc[issuedRowPandasIndex,'Android Ver'] = googleplaystore.loc[issuedRowPandasIndex]['Current Ver']
googleplaystore.loc[issuedRowPandasIndex,'Current Ver'] = googleplaystore.loc[issuedRowPandasIndex]['Last Updated']
googleplaystore.loc[issuedRowPandasIndex,'Last Updated'] = googleplaystore.loc[issuedRowPandasIndex]['Genres']
googleplaystore.loc[issuedRowPandasIndex,'Genres'] = googleplaystore.loc[issuedRowPandasIndex]['Content Rating']
googleplaystore.loc[issuedRowPandasIndex,'Content Rating'] = googleplaystore.loc[issuedRowPandasIndex]['Price']
googleplaystore.loc[issuedRowPandasIndex,'Price'] = googleplaystore.loc[issuedRowPandasIndex]['Type']
googleplaystore.loc[issuedRowPandasIndex,'Type'] = googleplaystore.loc[issuedRowPandasIndex]['Installs']
googleplaystore.loc[issuedRowPandasIndex,'Installs'] = googleplaystore.loc[issuedRowPandasIndex]['Size']
googleplaystore.loc[issuedRowPandasIndex,'Size'] = googleplaystore.loc[issuedRowPandasIndex]['Reviews']
googleplaystore.loc[issuedRowPandasIndex,'Reviews'] = googleplaystore.loc[issuedRowPandasIndex]['Rating']
googleplaystore.loc[issuedRowPandasIndex,'Rating'] = googleplaystore.loc[issuedRowPandasIndex]['Category']
googleplaystore.loc[issuedRowPandasIndex,'Category'] = np.NaN

googleplaystore.loc[issuedRowPandasIndex]

googleplaystore.groupby('Size').size().reset_index(name='counts')

googleplaystore.loc[googleplaystore['Size'] == 'Varies with device']

"""'Varies with device' seems to be actually part of the dataset. I've to deal with it later, during conversion phase

Ok, the issue should be fixed (we'll test is later. Now we can cast *Size* value as a numbert (warning: "Varies with device" value needs to be handled)
"""

size_regex = re.compile(r'(\d+(?:\.\d+)?)\s*([kmgtp])', re.IGNORECASE)

def unitConverter(unit):
    unit = unit.upper()
    if unit in ['K','KB']:
        return 1000
    if unit in ['M','MB']:
        return 1000000
    if unit in ['G','GB']:
        return 1000000000
    if unit in ['T','TB']:
        return 1000000000000
    return 1

def sizeConverter(size):
    m = size_regex.search(size)
    if m == None:
      return np.NaN
    else:
      value = float(m[1])
      unit = int(unitConverter(m[2]))
      return int(value*unit)

"""Use defined function to create a **new column** with converted size. We're using a new column, to keep original one to make some tests"""

googleplaystore['SizeNew'] = googleplaystore['Size'].apply(sizeConverter)

googleplaystore.head()

"""Check for "NaN" values (here we should have "Varies with devices" observations, because regex'll not detect the common expected format)"""

googleplaystore[googleplaystore['SizeNew'].isnull()].head()

googleplaystore[googleplaystore['SizeNew'].isnull()]['Size'].unique()

"""Good, the only **Size** column not converted is *''Varies with device'*, as expected. Now we can replace *Size* column with *SizeNew*"""

googleplaystore['Size'] = googleplaystore['SizeNew']
googleplaystore = googleplaystore.drop(columns='SizeNew')
googleplaystore.head(2)

"""2.   **Convert the number of installs to a number**

First of all, check values for column "Installs", to get a quick data profiling
"""

googleplaystore.groupby('Installs').size().reset_index(name='counts')

"""Quite simple, compared to "Size" column. No need to create a dedicated regex, it just need to replace "+" and ",""""

def installsConverter(installs):
  return int(installs.replace('+','').replace(',',''))

googleplaystore['Installs'] = googleplaystore['Installs'].apply(installsConverter)

googleplaystore.head()

"""Check for "NaN" values (0 awaited, looking to data profile)"""

googleplaystore[googleplaystore['Installs'].isnull()].head()

"""Ok, 0 rows affected. Conversion succesfull

3.   **Transform “Varies with device” into a missing value**
"""

def columnCleaner(value):
    # Treat only str columns
    if type(value) is str:
      if value.upper().strip() == 'VARIES WITH DEVICE':
        return np.NaN
      else:
        return value
    else:
       return value

"""No specific column in the request. Check on all"""

for column in googleplaystore:
  # We don't need to handle "IntSize" & "IntInstalls" column, already cleaned
  if column not in ['Size','Installs']:
    googleplaystore[column] = googleplaystore[column].apply(columnCleaner)

"""4.   **Convert Current Ver and Android Ver into a dotted number (e.g. 4.0.3 or 4.2)**

First of all, check values for columns "Current Ver" and "Android Ver", to get a quick data profiling
"""

googleplaystore.groupby('Current Ver').size().reset_index(name='counts')

googleplaystore.groupby('Android Ver').size().reset_index(name='counts')

currentVer_regex = re.compile(r'(\d?[.\d]+)', re.IGNORECASE)

def versionConverter(currentVer):
  if currentVer == np.NaN or currentVer == None:
    return np.NaN
  elif type(currentVer) is str:
    m = currentVer_regex.findall(currentVer)
    if m == None:
      return np.NaN
    elif len(m) == 0:
      return np.NaN
    else:
      # In case of multiple version, return the first
      # If the version is something like '.2019', then add a '0' head, to have something like '0.2019'
      if m[0][0]=='.':
        return '0' + m[0][0]
      else:
        return m[0]
  else:
     return np.NaN

"""Use defined function to create a **new column** with converted *'Current Ver'*. We're using a new column, to keep original one to make some tests"""

googleplaystore['Current Ver New'] = googleplaystore['Current Ver'].apply(versionConverter)

googleplaystore.groupby('Current Ver New').size().reset_index(name='counts')

googleplaystore[googleplaystore['Current Ver New'].isnull() & googleplaystore['Current Ver'].notnull()].head()

"""The only remaining rows are related to "non-standard" values ('Final', 'Initial',...) so it's correct to convert them as NaN
We can now replace *'Current Ver'*
"""

googleplaystore['Current Ver'] = googleplaystore['Current Ver New']
googleplaystore = googleplaystore.drop(columns='Current Ver New')
googleplaystore.head(2)

"""Use defined function to create a **new column** with converted *'Android Ver'*. We're using a new column, to keep original one to make some tests"""

googleplaystore['Android Ver New'] = googleplaystore['Android Ver'].apply(versionConverter)

googleplaystore.groupby('Android Ver New').size().reset_index(name='counts')

googleplaystore[googleplaystore['Android Ver New'].isnull() & googleplaystore['Android Ver'].notnull()].head()

"""0 rows are related to unhandled NaN values.
We can now replace *'Andoroid Ver'*
"""

googleplaystore['Android Ver'] = googleplaystore['Android Ver New']
googleplaystore = googleplaystore.drop(columns='Android Ver New')
googleplaystore.head(2)

"""5.   **Remove the duplicates**

First of all, check if there are some duplicates
"""

googleplaystore.groupby(googleplaystore.columns.tolist(),as_index=False).size().reset_index(name='counts')

"""Ok, we have duplicates. Remove them"""

googleplaystore = googleplaystore.drop_duplicates(keep='first')

googleplaystore.groupby(googleplaystore.columns.tolist(),as_index=False).size().reset_index(name='counts')

"""6.   **For each category, compute the number of apps**"""

googleplaystore.groupby(['Category']).size().sort_values(ascending=False).reset_index(name='Numbers of Apps')

sns.countplot(y=googleplaystore['Category']);

"""7.   **For each category, compute the average rating**"""

googleplaystore.groupby('Rating').size().reset_index(name='counts')

sns.distplot(pd.to_numeric(googleplaystore['Rating']).dropna());

"""First of all, convert "Rating" to a float"""

def ratingConverter(rating):
  return float(rating)

googleplaystore['Rating'] = googleplaystore['Rating'].apply(ratingConverter)

googleplaystore.groupby(['Category'])['Rating'].mean().sort_values(ascending=False).reset_index(name='Average Rating')

"""8.   **Create two dataframes: one for the genres and one bridging apps and genres. So that, for instance, the app *Pixel Draw - Number Art Coloring Book* appears twice in the bridging table, once for *Art & Design*, once for *Creativity***"""

googleplaystore.groupby('Genres').size().reset_index(name='counts')

"""Looking at the data profiling phase, genres are splitted by ";".
So, first of all, unwind DataFrame for "Genres" values (splitted by ";")
"""

unwindedGenres = pd.DataFrame(googleplaystore.Genres.str.split(';', expand=True).stack().str.strip().reset_index(level=1, drop=True))
unwindedGenres.columns = ['Genres']

distinctGenres = pd.DataFrame(unwindedGenres['Genres'].unique())
distinctGenres.head()

bridgeDataFrame = googleplaystore.drop(['Genres'], axis=1).join(unwindedGenres).reset_index(drop=True)
bridgeDataFrame.head()

"""Check provided example"""

bridgeDataFrame.loc[bridgeDataFrame['App'] == 'Pixel Draw - Number Art Coloring Book']

"""Ok, seems good!

9.   **For each genre, create a new column of the original dataframe. The new columns must have boolean values (True if the app has a given genre)**
"""

pivotted_genres = bridgeDataFrame[['App','Genres']].pivot_table(
    index=['App'],
		columns=['Genres'],
		aggfunc=lambda x: True).fillna(False).reset_index()

"""Check an example with 2 genres"""

bridgeDataFrame.loc[bridgeDataFrame['App'] == 'Pixel Draw - Number Art Coloring Book']

pd.set_option('display.max_columns', None)
pivotted_genres.loc[pivotted_genres['App'] == 'Pixel Draw - Number Art Coloring Book']

"""Seems good!

10.   **For each genre, compute the average rating. What is the genre with highest average?**
"""

bridgeDataFrame.groupby(['Genres'])['Rating'].mean().sort_values(ascending=False).reset_index(name='Average Rating')

"""Answer to the question: **"*Events*" is the genre with the highest rating (*4.435556*)**"""

plotdataset = bridgeDataFrame.groupby(['Genres'])['Rating'].mean().sort_values(ascending=False).reset_index(name='Average Rating')
sns.barplot(y=plotdataset['Genres'],x=plotdataset['Average Rating']);

"""11.   **For each app, compute the approximate income, obtain as a product of number of installs and price.**"""

googleplaystore.groupby('Price').size().reset_index(name='counts')

"""Format "Price" column as a float"""

currentPrice_regex = re.compile(r'(\d?[.\d]+)', re.IGNORECASE)

def priceConverter(currentPrice):
  if currentPrice == np.NaN or currentPrice == None:
    return np.NaN
  elif type(currentPrice) is str:
    m = currentPrice_regex.findall(currentPrice)
    if m == None:
      return np.NaN
    elif len(m) == 0:
      return np.NaN
    else:
      # In case of multiple prices, return the first
      return float(m[0])
  else:
     return np.NaN

"""Use defined function to create a **new column** with converted price. We're using a new column, to keep original one to make some tests"""

googleplaystore['Price New'] = googleplaystore['Price'].apply(priceConverter)

googleplaystore[googleplaystore['Price New'].isnull()]['Price'].unique()

"""0 rows are related to unhandled NaN values.
We can now replace *'Price'*
"""

googleplaystore['Price'] = googleplaystore['Price New']
googleplaystore = googleplaystore.drop(columns='Price New')
googleplaystore.head(2)

googleplaystore['Income'] = googleplaystore['Price'] * googleplaystore['Installs']

# Get some examples
googleplaystore.loc[googleplaystore['Price'] > 0]

"""12.   **For each app, compute its minimum and maximum `Sentiment_polarity`**"""

googleplaystore_user_reviews.groupby('Sentiment_Polarity').size().reset_index(name='counts')

"""We can use *googleplaystore_user_reviews* DataFrame for this analysis, converting *Sentiment_Polarity* in float"""

def sentimentPolarityConverter(sentimentPolarity):
  return float(sentimentPolarity)

googleplaystore_user_reviews['Sentiment_Polarity'] = googleplaystore_user_reviews['Sentiment_Polarity'].apply(sentimentPolarityConverter)

googleplaystore_user_reviews.groupby(['App']).agg({'Sentiment_Polarity': [min, max]})