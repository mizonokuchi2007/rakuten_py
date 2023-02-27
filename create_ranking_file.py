import pandas as pd
import os,re,json,datetime,requests,openpyxl,time
from config import CLIENT_ME
import get_genreId

REQ_URL = 'https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20170628'
PATH_GENRE = r'.\rakutenichiba_genre.json'
PATH_OUTPUT = '.\output'
RE_PATTRN_CHACK_NAME = r'(:|\\|\?|\[|\]|\/|\*)'
WANT_ITEMS = [
    'genreId','rank','itemCode',
    'itemName','itemPrice','catchcopy',
    'itemCaption','reviewAverage','reviewCount',
    'shopCode','shopName','itemUrl','shopUrl'
]

sta_time = datetime.datetime.today()
this_date = format(sta_time,'%Y%m%d')
path_output_dir = f'.\output\{this_date}'
req_params = {
    'applicationId':CLIENT_ME['APPLICATION_ID'],
    'affiliateId': CLIENT_ME['AFF_ID'],
    'format':'json',
    'formatVersion':'2',
    'genreId':'',
    'page':'1'
}

def main():
    
    ###必要ファイル用意
    ##指定名のjsonファイルがない場合は生成
    if not os.path.isfile(PATH_GENRE):
        print("#####ジャンル取得を行います#####")
        get_genreId.get_genreId()
    
    with open(PATH_GENRE,encoding='utf-8',mode='r') as f:
        dict_genre = json.load(f)

    if not os.path.isdir(PATH_OUTPUT):
        os.mkdir(PATH_OUTPUT)
    
    if not os.path.isdir(path_output_dir):
        os.mkdir(path_output_dir)

    ##シート名に使用できない文字を一致させる正規表現
    re_check_name = re.compile(RE_PATTRN_CHACK_NAME)

    for p_genre_id,p_genre_info in dict_genre.items():
        
        print(f'#####\n親ジャンルID --> {p_genre_id}')
        print(f"親ジャンル名 --> {p_genre_info['genre_name']}\n#####")

        #ランキングファイル作成
        path_output_file = f"{path_output_dir}\{p_genre_id}_{p_genre_info['genre_name']}.xlsx"
        wb = openpyxl.Workbook()
        wb.save(path_output_file)        

        #各種ランキング情報取得
        for c_genre_id,c_genre_info in p_genre_info['children'].items():
            
            print(f"子ジャンルID --> {c_genre_id}")
            print(f"子ジャンル情報 --> {c_genre_info}")
            
            req_params['genreId'] = c_genre_id

            # エラーかレコードが取得できなくなるまで、最大100件取得する
            page = 1
            retrieved = 0
            max_rows = 100
            while retrieved < max_rows:
                req_params['page'] = page
                time.sleep(1) #1つのapplication_idにつき、1秒に1回以下のリクエストとしてください。
                res = requests.get(REQ_URL,params=req_params)
                #エラーで打ち切り
                if res.status_code != 200:
                    print(f"error --> status_code={res.status_code}, response={res.text}")
                    break
                #空レスポンスで打ち切り
                res_json = json.loads(res.text)
                if not res_json['Items']:
                    if retrieved == 0:
                        print(f"error --> response is empty, response={res.text}")
                        df = pd.DataFrame({'エラー':['ランキングが空です'],
                                          '詳細': res.text})
                        retrieved = len(df)
                    break
                #レスポンスをdf化
                if retrieved == 0:
                    df = pd.DataFrame(res_json['Items'])
                else:
                    df = pd.concat([df, pd.DataFrame(res_json['Items'])])
                retrieved = len(df)
                page = page + 1

            if retrieved > 0:
                # max_rows以降は切り捨て
                df = df.head(max_rows)
                # ランキング対象ジャンルを追加
                if 'rank' in df.columns:
                    df['genreOfRank'] = c_genre_id
                # ランキング取得日時を追加
                df['retrieved'] = datetime.datetime.now()
                # mediumImageUrlsを展開
                if 'mediumImageUrls' in df.columns:
                    mediumImageUrls = df['mediumImageUrls']
                    df['mediumImageUrl0'] = mediumImageUrls.transform(lambda x : x[0] if len(x) > 0 else '')
                    df['mediumImageUrl1'] = mediumImageUrls.transform(lambda x : x[1] if len(x) > 1 else '')
                # smallImageUrlsを展開
                if 'smallImageUrls' in df.columns:
                    smallImageUrls = df['smallImageUrls']
                    df['smallImageUrl0'] = smallImageUrls.transform(lambda x : x[0] if len(x) > 0 else '')
                    df['smallImageUrl1'] = smallImageUrls.transform(lambda x : x[1] if len(x) > 1 else '')
                #dfをシートへ出力
                tmp_genre = is_suitble_sheet_name(re_check_name,c_genre_info['genre_name'])
                with pd.ExcelWriter(path_output_file, mode='a') as writer:
                    df.to_excel(writer, sheet_name=tmp_genre,index=False)
        
        #初期シート削除
        wb = openpyxl.load_workbook(path_output_file)
        ws = wb.worksheets[0]
        if len(wb.worksheets) != 1:
            wb.remove(ws)
        else:
            ws.title = '取得失敗'
            ws['A1'] = '取得失敗'
        wb.save(path_output_file)

    fin_time = datetime.datetime.today()
    p_time = fin_time - sta_time
    print(f"処理時間 --> {p_time}")

##シート名に不適切な文字が含まれるまたは不適切な文字列の場合、編集する関数
def is_suitble_sheet_name(arg_re,arg_genre):
    
    #文字判定(不適切文字はアンダーバーに置き換え)
    match_result = arg_re.findall(arg_genre)
    if match_result:            
        arg_genre = arg_re.sub('_',arg_genre)
    
    #文字数判定
    if len(arg_genre) >= 31:
        arg_genre = arg_genre[0:31]
    
    return arg_genre
                                    
if __name__ == '__main__':
    print("#####\n処理を開始します\n#####")
    main()
    print("#####\n処理を終了します\n#####")