import requests
from bs4 import BeautifulSoup
import tweepy
import time
import os
import csv
import mysql.connector
from os import environ

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

def retrieve_last_id():
    mydb.execute('SELECT * FROM mention_id')
    fetch = mydb.fetchall()
    last_id = [list(i) for i in fetch]
    return last_id

def store_last_id(last_id):
    mydb.execute("DELETE FROM mention_id")
    mydb.execute("INSERT INTO mention_id VALUES('" + str(last_id[0][0]) + "')")
    db.commit()

def retrieve_old_data():
    mydb.execute('SELECT * FROM old_data')
    fetch = mydb.fetchall()
    old_data = [list(i) for i in fetch]
    return old_data

def store_old_data(data):
    mydb.execute("DELETE FROM old_data")
    mydb.execute("INSERT INTO old_data VALUES('" + data[0][0] + "','" + data[0][1] + "','" + data[0][2] + "')")
    db.commit()

def scraping_data():
    result = requests.get('https://kemkes.go.id/')
    src = result.content
    soup = BeautifulSoup(src, 'lxml')
    links = soup.find_all("td")
    data = []

    for link in links:
        if "case" in link.attrs['class']:
            data.append(link.text)
            if len(data) == 3:
                break
    
    new_data = [data]
    return new_data

def rujukan(mention):
    with open ('daftar_rujukan.csv', 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=';')
        twit = []

        key = False
        for line in csv_reader:
            if not key:
                if line['provinsi'].lower() in mention:
                    provinsi = line['provinsi'].lower()
                    twit.append("#rujukan " + line['provinsi'] + "\n\n")
                    twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
                    key = True
            else:
                if line['provinsi'].lower() == provinsi and provinsi in mention:
                    if provinsi == 'riau' and 'kepulauan riau' not in mention:
                        twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
                    elif provinsi == 'papua' and 'papua barat' not in mention:
                        twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
                    elif provinsi == 'maluku' and 'maluku utara' not in mention:
                        twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
                    else:
                        twit.append(line['rumah_sakit'].replace("Â", "") + "\n")
        csv_file.close()
    
    separator = ''
    final_twit = separator.join(twit)
    return final_twit

def twit_data(old_data, new_data):
    print("Mendapatkan data baru...")
    twit = []
    twit.append('#UPDATE\nInformasi kasus COVID-19 terbaru:\n\n')
    for x in range(0,3):
        if x == 0:
            twit.append('Jumlah Positif: ')
        if x == 1:
            twit.append('Sembuh: ')
        if x == 2:
            twit.append('Meninggal: ')

        if new_data[0][x] != old_data[0][x]:
            dev = int(new_data[0][x].replace('.', '')) - int(old_data[0][x].replace('.', ''))
            old_data[0][x] = new_data[0][x]
            twit.append(new_data[0][x] + ' (+' + str(dev) + ')\n')
        else:
            twit.append(new_data[0][x] + '\n')

    twit.append('\nSumber: https://kemkes.go.id/')
    separator = ''
    final_twit = separator.join(twit)

    store_old_data(old_data)
    api.update_status(final_twit)
    print("Berhasil twit data baru!")

def scraping_article(old_article):
    result = requests.get('https://covid19.go.id/p/hoax-buster')
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
            article = []
            article.append(link.text)
            article.append(link.attrs['href'])
            new_article.append(article)
        i += 1

    return new_article

def retrieve_old_article():
    mydb.execute('SELECT * FROM hoax_buster WHERE id = 1')
    fetch = mydb.fetchall()
    old_article = [list(i) for i in fetch]
    return old_article

def store_old_article(article):
    mydb.execute("DELETE FROM hoax_buster")
    mydb.execute("ALTER TABLE hoax_buster AUTO_INCREMENT=1;")
    for i in range(0, len(article)):
        mydb.execute("INSERT INTO hoax_buster VALUES('" + article[i][0] + "','" + article[i][1] + "', 0")
        db.commit()

def reply():
    print('Mengambil data...')
    new_data = scraping_data()
    old_data = retrieve_old_data()

    for x in range(0,3):
        if new_data[0][x] != old_data[0][x]:
            twit_data(old_data, new_data)
            break
    
    old_article = retrieve_old_article()
    new_article = scraping_article(old_article)
    
    if new_article:
        print("Mendapatkan artikel baru...")
        store_old_article(new_article)
        for i in range(0, len(new_article)):
            api.update_status("#HoaxBuster\n" + new_article[i][0] + "\n\nSelengkapnya: " + new_article[i][1])
            print("Berhasil twit artikel baru!")
        
    last_id = retrieve_last_id()
    mentions = api.mentions_timeline(last_id[0][0], tweet_mode='extended')
    for mention in reversed(mentions):
        last_id[0][0] = mention.id
        store_last_id(last_id)
        if '#kasus' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            api.update_status('@' + mention.user.screen_name + ' Informasi kasus COVID-19 terbaru:\n\nJumlah Positif: ' + new_data[0][0] + "\nSembuh: " + new_data[0][1] + '\nMeninggal: ' + new_data[0][2] +  "\n\nSumber: https://kemkes.go.id/", mention.id)
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
            api.update_status('@' + mention.user.screen_name + ' ' + final_twit, mention.id)
            print("Berhasil membalas twit!")

while True:
    reply()
    time.sleep(15)
    