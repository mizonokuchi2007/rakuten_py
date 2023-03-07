#!/usr/bin/env python3
# coding: utf-8
import datetime
import requests
import time
import json
import os
from config import CLIENT_ME
#config.py:
#CLIENT_ME = {
#    'APPLICATION_ID':'',
#    'APPLICATION_SECRET':'',
#    'AFF_ID':''
#}

req_url = 'https://app.rakuten.co.jp/services/api/IchibaGenre/Search/20140222'
genre_params = {
    'applicationId':CLIENT_ME['APPLICATION_ID'],
    'format':'json',
    'formatVersion':'2',
    'genreId':''
}
sta_time = datetime.datetime.today()

def get_genreId():

    print("ジャンル取得中...")

    cnt_p = 0
    cnt_c = 0
    
    ##親ジャンル取得
    genre_params['genreId'] = '0'
    res = requests.get(req_url,params=genre_params)
    p_items = json.loads(res.text)
    time.sleep(0.01)
    
    dict_p_genre = {}
    for p_genre in p_items['children']:
        
        ##子ジャンル取得
        print(f"子ジャンル取得中({p_genre['genreId']}_{p_genre['genreName']})...")

        genre_params['genreId'] = p_genre['genreId']        
        res = requests.get(req_url,params=genre_params)
        c_items = json.loads(res.text)
        time.sleep(0.01)
        
        ##キー：子ジャンルID, 値:子ジャンル名・階層となる子ジャンル辞書作成        
        dict_c_genre = {}
        for c_genre in c_items['children']:
            
            dict_c_info = {
                'genre_name':c_genre['genreName'],
                'genre_level':c_genre['genreLevel']
            }

            dict_c_genre[c_genre['genreId']] = dict_c_info
            cnt_c += 1

        ##キー：親ジャンルID,値:親ジャンル名・階層・子ジャンル辞書となる親ジャンル辞書作成
        dict_p_info = {
            'genre_name':p_genre['genreName'],
            'genre_level':p_genre['genreLevel'],
            'children':dict_c_genre
        }

        dict_p_genre[p_genre['genreId']] = dict_p_info
        cnt_p += 1
    
    ##json形式で本ファイルの直下に保存
    path = os.path.join(os.path.dirname(__file__), r'rakutenichiba_genre.json')
    with open(path,encoding='utf-8',mode='w') as f:
        json.dump(dict_p_genre,f,ensure_ascii=False,indent=2)
    
    fin_time = datetime.datetime.today()
    p_time = fin_time - sta_time
    print(f"処理時間 --> {p_time}")
    print(f"親ジャンル総数 --> {cnt_p}")
    print(f"子ジャンル総数 --> {cnt_c}")

        
if __name__ == '__main__':
    get_genreId()