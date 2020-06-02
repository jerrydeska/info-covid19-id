import covid19cases as covid19
import tweepy
import time
import os
from os import environ

CONSUMER_KEY = environ['CONSUMER_KEY']
CONSUMER_SECRET = environ['CONSUMER_SECRET']
ACCESS_KEY = environ['ACCESS_KEY']
ACCESS_SECRET = environ['ACCESS_SECRET']

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

file_name_id = 'id.txt'
file_name_data = 'data.txt'

def retrieve_last_id(file_name_id):
    read = open(file_name_id, 'r')
    last_id = int(read.read())
    read.close()
    return last_id

def store_last_id(last_id, file_name_id):
    write = open(file_name_id, 'w')
    write.write(str(last_id))
    write.close()
    return

def retrieve_old_data(file_name_data):
    read = open(file_name_data, 'r')
    old_data = read.read().splitlines()
    read.close()
    return old_data

def store_old_data(data, file_name_data):
    with open(file_name_data, 'w') as write:
        for item in data:
            write.write("%s\n" % item)
        write.close()

def reply():
    print('Mengambil data...')
    data = covid19.get_country_cases("Indonesia")
    confirmed = data['TotalCases']
    deaths = data['TotalDeaths']
    recovered = data['TotalRecovered']

    new_data = [confirmed, deaths, recovered]
    old_data = retrieve_old_data(file_name_data)

    if new_data[0] != old_data[0] or new_data[1] != old_data[1] or new_data[2] != old_data[2]:
        old_data = [new_data[0], new_data[1], new_data[2]]
        store_old_data(old_data, file_name_data)
        api.update_status('#UPDATE\n\nInformasi kasus COVID-19 terbaru:\n\nJumlah Positif: ' + str(confirmed) + '\nMeninggal: ' + str(deaths) + '\nSembuh: ' + str(recovered) + '\n\nSumber: https://www.worldometers.info/coronavirus/country/indonesia/')
        
    last_id = retrieve_last_id(file_name_id)
    mentions = api.mentions_timeline(last_id, tweet_mode='extended')
    for mention in reversed(mentions):
        last_id = mention.id
        store_last_id(last_id, file_name_id)
        if '#kasus' in mention.full_text.lower():
            print("mendapatkan twit \"" + mention.full_text + " - " + str(mention.id) + "\"")
            api.update_status('@' + mention.user.screen_name + ' Informasi kasus COVID-19 terbaru:\n\nJumlah Positif: ' + str(confirmed) + '\nMeninggal: ' + str(deaths) + "\nSembuh: " + str(recovered) + "\n\nSumber: https://www.worldometers.info/coronavirus/country/indonesia/", mention.id)
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

while True:
    reply()
    time.sleep(15)
    
