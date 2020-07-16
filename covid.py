import requests
from bs4 import BeautifulSoup
import tweepy
import time
import csv
import mysql.connector
from os import environ
from datetime import datetime
import pandas
from matplotlib import pyplot

db = mysql.connector.connect(
    host = environ['HOST'],
    user = environ['USER'],
    passwd = environ['PASSWD'],
    database = environ['DATABASE']
)

mydb = db.cursor()

CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET = environ['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

#---ID---

def get_last_id():
    mydb.execute('SELECT * FROM mention_id')
    fetch = mydb.fetchall()
    last_id = [list(i) for i in fetch]
    return last_id

def set_last_id(last_id):
    mydb.execute("DELETE FROM mention_id")
    mydb.execute("INSERT INTO mention_id VALUES('" + str(last_id[0][0]) + "')")
    db.commit() 

#---END OF ID----

#---CASE---

def get_old_case():
    mydb.execute('SELECT * FROM old_case')
    fetch = mydb.fetchall()
    old_case = [list(i) for i in fetch]
    return old_case

def set_old_case(case):
    mydb.execute("DELETE FROM old_case")
    mydb.execute("INSERT INTO old_case VALUES('" + case[0][0] + "','" + case[0][1] + "','" + case[0][2] + "')")
    db.commit()

def scraping_case():
    result = requests.get('https://kemkes.go.id/')
    src = result.content
    soup = BeautifulSoup(src, 'lxml')
    links = soup.find_all("td")
    case = []

    for link in links:
        if "case" in link.attrs['class']:
            case.append(link.text)
            if len(case) == 3:
                break

    new_case = [case]
    return new_case

def twit_case(old_case, new_case):
    print("Mendapatkan kasus baru...")
    twit = []
    today_case = []
    twit.append('#UPDATE\nInformasi kasus COVID-19 terbaru:\n\n')
    for x in range(0,3):
        if x == 0:
            twit.append('Jumlah Positif: ')
        elif x == 1:
            twit.append('Sembuh: ')
        elif x == 2:
            twit.append('Meninggal: ')

        if new_case[0][x] != old_case[0][x]:
            dev = int(new_case[0][x].replace('.', '')) - int(old_case[0][x].replace('.', ''))
            today_case.append(dev)
            old_case[0][x] = new_case[0][x]
            twit.append(new_case[0][x] + ' (+' + str(dev) + ')\n')
        else:
            twit.append(new_case[0][x] + '\n')

    twit.append('\nSumber: https://kemkes.go.id/')
    separator = ''
    final_twit = separator.join(twit)

    daily_case_graph(today_case)
    set_old_case(old_case)
    image = api.media_upload(filename = "img/graph1.png")
    api.update_status(final_twit, media_ids = [image.media_id])
    print("Berhasil twit kasus baru!")

def daily_case_graph(today_case):
    date = datetime.now().strftime('%Y-%m-%d')
    mydb.execute("INSERT INTO daily_case VALUES('" + str(date) + "'," + str(today_case[0]) + "," + str(today_case[1]) + "," + str(today_case[2]) + ")")
    db.commit()

    df = pandas.read_sql("SELECT * FROM daily_case", db)
    df['date'] = pandas.to_datetime(df['date'])
    pyplot.figure(num=None, figsize=(15, 8), dpi=80)
    pyplot.plot(df['date'],df['positive'])
    pyplot.plot(df['date'],df['cured'])
    pyplot.plot(df['date'],df['death'])
    pyplot.title("Kasus per Hari")
    pyplot.grid(True)
    pyplot.legend(["Positif", "Sembuh", "Meninggal"], prop={'size': 14})
    pyplot.savefig('img/graph1.png', bbox_inches='tight')

#---END OF CASE---

#---ARTICLE---

def get_old_article(table):
    mydb.execute('SELECT * FROM ' + table)
    fetch = mydb.fetchall()
    old_article = [list(i) for i in fetch]
    return old_article

def set_old_article(article, table):
    mydb.execute("DELETE FROM " + table)
    mydb.execute("INSERT INTO " + table + " VALUES('" + article[0][0] + "','" + article[0][1] + "')")
    db.commit()

def scraping_article(old_article, table):
    if table == 'hoax':
        result = requests.get('https://covid19.go.id/p/hoax-buster')
    else:
        result = requests.get('https://covid19.go.id/p/berita')
        
    src = result.content
    soup = BeautifulSoup(src, 'html.parser')

    check = False
    i = 0
    new_article = []

    while not check:
        link = soup.find_all("a", class_="text-color-dark")[i]
        if link.attrs['href'] == old_article[0][1]:
            check = True
        else:
            if table == 'berita' and 'infografis' not in link.text.lower() or table == 'hoax':
                article = []
                article.append(link.text)
                article.append(link.attrs['href'])
                new_article.append(article)
        i += 1

    return new_article

#---END OF ARTICLE---

#---HOSPITAL---

def rujukan(mention):
    with open ('daftar_rujukan.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        twit = []

        key = False
        for line in csv_reader:
            if not key:
                if line['provinsi'].lower() in mention:
                    provinsi = line['provinsi'].lower()
                    twit.append("Rujukan " + line['provinsi'] + "\n\n")
                    twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
                    key = True
            else:
                if line['provinsi'].lower() == provinsi:
                    twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
        csv_file.close()
    
    separator = ''
    final_twit = separator.join(twit)
    return final_twit

#---END OF HOSPITAL---

def reply():
    print('Mengambil data...')
    new_case = scraping_case()
    old_case = get_old_case()

    for x in range(0,3):
        if new_case[0][x] != old_case[0][x]:
            twit_case(old_case, new_case)
            break
    
    article_tables = ['hoax', 'berita']
    for table in article_tables:
        old_article = get_old_article(table)
        new_article = scraping_article(old_article, table)
    
        if new_article:
            print("Mendapatkan artikel baru...")
            set_old_article(new_article, table)
            for i in range(0, len(new_article)):
                if table == 'hoax':
                    api.update_status("#HoaxBuster\n" + new_article[i][0] + "\n\nSelengkapnya: " + new_article[i][1])
                    print("Berhasil twit artikel baru!")
                else:
                    api.update_status("#BeritaTerkini\n" + new_article[i][0] + "\n\nSelengkapnya: " + new_article[i][1])
                    print("Berhasil twit berita baru!")

    last_id = get_last_id()
    mentions = api.mentions_timeline(last_id[0][0], tweet_mode='extended')
    for mention in reversed(mentions):
        last_id[0][0] = mention.id
        set_last_id(last_id)
        if '#kasusindo' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            api.update_status('@' + mention.user.screen_name + ' Informasi kasus COVID-19 terbaru:\n\nJumlah Positif: ' + new_case[0][0] + "\nSembuh: " + new_case[0][1] + '\nMeninggal: ' + new_case[0][2] +  "\n\nSumber: https://kemkes.go.id/", mention.id)
            print("Berhasil membalas twit!")
        if '#gejala' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            api.update_status('@' + mention.user.screen_name + ' Gejala umum yang dirasakan:\n1. Demam\n2. Batuk Kering\n3. Sesak Napas\n\nGejala lain yang dapat muncul:\n1. Diare\n2. Sakit Kepala\n3. Mata Merah\n4. Hilangnya kemampuan mengecap rasa atau mencium bau\n5. Ruam di kulit\n\nSumber: https://www.alodokter.com/virus-corona', mention.id)
            print("Berhasil membalas twit!")
        if '#cucitangan' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            image = api.media_upload(filename = "img/Etika-Mencuci-Tangan.png")
            api.update_status(status = '@' + mention.user.screen_name + ' Sumber: Humas Litbangkes', in_reply_to_status_id = mention.id, media_ids = [image.media_id])
            print("Berhasil membalas twit!")
        if '#pencegahan' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            image = api.media_upload(filename = "img/Cara-Cegah-Virus-Corona.jpeg")
            api.update_status(status = '@' + mention.user.screen_name + ' Sumber: Kemkominfo RI', in_reply_to_status_id = mention.id, media_ids = [image.media_id])
            print("Berhasil membalas twit!")
        if '#rujukan' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            final_twit = rujukan(mention.full_text.lower())
            if final_twit:
                api.update_status('@' + mention.user.screen_name + ' ' + final_twit, mention.id)
                print("Berhasil membalas twit!")
            else:
                print("Provinsi tidak ada!")

while True:
    reply()
    time.sleep(10)
    
