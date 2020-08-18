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

#---TWITTER ID---

def get_last_id():
    mydb.execute('SELECT * FROM mention_id')
    fetch = mydb.fetchall()
    last_id = [list(i) for i in fetch]
    return last_id

def set_last_id(last_id):
    mydb.execute("DELETE FROM mention_id")
    mydb.execute("INSERT INTO mention_id VALUES('" + str(last_id[0][0]) + "')")
    db.commit() 

#---END OF TWITTER ID----

#---INDO CHECK---

def get_check():
    mydb.execute('SELECT * FROM check_case')
    fetch = mydb.fetchall()
    case_date = [list(i) for i in fetch]
    return case_date

def set_check_indo(bool_check):
    mydb.execute('UPDATE check_case SET indo_case=' + str(bool_check))
    db.commit()

def set_check_prov(bool_check):
    mydb.execute('UPDATE check_case SET prov_case=' + str(bool_check))
    db.commit()

#---END OF INDO CHECK---

#---INDO CASE---

def check_indo_case():
    result = requests.get('https://data.covid19.go.id/public/api/update.json')
    src = result.json()

    final_twit = []
    twit = []

    check = get_check()
    date = datetime.now().strftime('%Y-%m-%d')
    if date in src['update']['penambahan']['created']:
        if check[0][0]:
            pass
        else:
            positive = src['update']['total']['jumlah_positif']
            cured = src['update']['total']['jumlah_sembuh']
            death = src['update']['total']['jumlah_meninggal']
            today_positive = src['update']['penambahan']['jumlah_positif']
            today_cured = src['update']['penambahan']['jumlah_sembuh']
            today_death = src['update']['penambahan']['jumlah_meninggal']
            today_case = [today_positive, today_cured, today_death]

            twit.append("#UPDATE\nInformasi kasus COVID-19 terbaru:\n\n")
            twit.append("Positif: {:,}".format(positive).replace(',','.'))
            twit.append(" (+{:,})\n".format(today_positive).replace(',','.'))
            twit.append("Sembuh: {:,}".format(cured).replace(',','.'))
            twit.append(" (+{:,})\n".format(today_cured).replace(',','.'))
            twit.append("Meninggal: {:,}".format(death).replace(',','.'))
            twit.append(" (+{:,})\n".format(today_death).replace(',','.'))
            twit.append('\nSumber: https://covid19.go.id/')
            
            indo_case_graph(today_case)
            separator = ''
            final_twit = separator.join(twit)

            set_check_indo(1)
    else:
        if not check[0][0]:
            pass
        else:
            set_check_indo(0)

    return final_twit

def indo_case_graph(today_case):
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

#---END OF INDO CASE---

#---PROV CASE---

def check_prov_case():
    result = requests.get('https://data.covid19.go.id/public/api/prov.json')
    src = result.json()

    final_twit = ""

    check = get_check()
    date = datetime.now().strftime('%Y-%m-%d')
    if date == src['last_date']:
        if check[0][1]:
            pass
        else:
            final_twit = "#UPDATE\nKasus per provinsi. Untuk melihat detail per-provinsi, mention akun ini dengan hashtag #kasusprov + nama provinsi (Cth: #kasusprov DKI Jakarta)\n\nSumber: https://covid19.go.id/"
            prov_case_graph(src)
            set_check_prov(1)
    else:
        if not check[0][1]:
            pass
        else:
            set_check_prov(0)
    
    return final_twit

def prov_case_graph(src):
    date = src['last_date']
    
    positif, sembuh, meninggal, nama_provinsi = [], [], [], []
    for data in src['list_data']:
        positif.append(data['jumlah_kasus'])
        sembuh.append(data['jumlah_sembuh'])
        meninggal.append(data['jumlah_meninggal'])
        nama_provinsi.append(data['key'])

    pyplot.figure(num=None, figsize=(15, 8), dpi=80)
    elements = pyplot.barh(nama_provinsi, positif)
    pyplot.barh(nama_provinsi, sembuh)
    pyplot.barh(nama_provinsi, meninggal)
    pyplot.subplots_adjust(left=0.16)
    pyplot.title("Kasus per Provinsi (" + date + ")")
    pyplot.legend(["Positif", "Sembuh", "Meninggal"], prop={'size': 14})
    pyplot.grid(True, axis='x')
    pyplot.gca().invert_yaxis()
    for elem in elements:
        pyplot.text(elem.get_width() + 13,  elem.get_y() + 0.8, "{:.1f}".format(elem.get_width()/src['update']['total']['jumlah_positif'] * 100) + "%", fontsize=12)
    pyplot.savefig('img/graph4.png', bbox_inches='tight')

#---END OF PROV CASE---

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

def scraping_article(old_article, table, href):
    result = requests.get('https://covid19.go.id/p/' + href)
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
            if table == 'berita' and 'infografis' in link.text.lower():
                pass
            else:
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
    
    final_twit = check_indo_case()
    if final_twit:
        graph1 = api.media_upload(filename = "img/graph1.png")
        api.update_status(final_twit, media_ids = [graph1.media_id])
        print("Berhasil twit kasus Indonesia baru!")

    final_twit = check_prov_case()
    if final_twit:
        graph2 = api.media_upload(filename = "img/graph2.png")
        api.update_status(final_twit, media_ids = [graph2.media_id])
        print("Berhasil twit kasus Provinsi baru!")

    articles = [['hoax', '#HoaxBuster\n', 'hoax-buster'], ['berita', '#BeritaTerkini\n', 'berita'], ['protokol', '#Protokol\n', 'protokol']]
    for i in range(0, len(articles)):
        old_article = get_old_article(articles[i][0])
        new_article = scraping_article(old_article, articles[i][0], articles[i][2])
    
        if new_article:
            print("Mendapatkan artikel baru...")
            set_old_article(new_article, articles[i][0])
            for x in range(0, len(new_article)):
                api.update_status(articles[i][1] + new_article[x][0] + "\n\nSelengkapnya: " + new_article[x][1])
                print("Berhasil twit artikel baru!")

    last_id = get_last_id()
    mentions = api.mentions_timeline(last_id[0][0], tweet_mode='extended')
    for mention in reversed(mentions):
        last_id[0][0] = mention.id
        set_last_id(last_id)
        if '#kasusindo' in mention.full_text.lower():
            result = requests.get('https://data.covid19.go.id/public/api/update.json')
            src = result.json()

            positive = "{:,}".format(src['update']['total']['jumlah_positif']).replace(',','.')
            cured = "{:,}".format(src['update']['total']['jumlah_sembuh']).replace(',','.')
            death = "{:,}".format(src['update']['total']['jumlah_meninggal']).replace(',','.')
            today_positive = "{:,}".format(src['update']['penambahan']['jumlah_positif']).replace(',','.')
            today_cured = "{:,}".format(src['update']['penambahan']['jumlah_sembuh']).replace(',','.')
            today_death = "{:,}".format(src['update']['penambahan']['jumlah_meninggal']).replace(',','.')

            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            api.update_status('@' + mention.user.screen_name + ' Informasi kasus COVID-19 terbaru:\n\nPositif: ' + positive + ' (+' + today_positive + ')\nSembuh: ' + cured + ' (+' + today_cured + ')\nMeninggal: ' + death + ' (+' + today_death + ')\n\nSumber: https://covid19.go.id/', mention.id)
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
                print("Provinsi tidak ditemukan!")
        if '#kasusprov' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            result = requests.get('https://data.covid19.go.id/public/api/prov.json')
            src = result.json()

            for data in src['list_data']:
                if data['key'].lower() in mention.full_text.lower():
                    date = src['last_date']
                    positive = "{:,}".format(data['jumlah_kasus']).replace(',','.')
                    cured = "{:,}".format(data['jumlah_sembuh']).replace(',','.')
                    death = "{:,}".format(data['jumlah_meninggal']).replace(',','.')
                    today_positive = "{:,}".format(data['penambahan']['positif']).replace(',','.')
                    today_cured = "{:,}".format(data['penambahan']['sembuh']).replace(',','.')
                    today_death = "{:,}".format(data['penambahan']['meninggal']).replace(',','.')
                    prov_name = data['key']
                    
                    api.update_status('@' + mention.user.screen_name + ' Kasus Provinsi ' + prov_name + ' (' + date + ')\n\nPositif: ' + positive + ' (+' + today_positive + ')\nSembuh: ' + cured + ' (+' + today_cured + ')\nMeninggal: ' + death + ' (+' + today_death + ')\n\nSumber: https://covid19.go.id/', mention.id)
                    print("Berhasil membalas twit!")
                    break
            
while True:
    reply()
    time.sleep(10)
    
