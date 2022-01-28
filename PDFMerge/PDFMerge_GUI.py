import cv2
from pathlib import Path
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
import numpy as np
import fnmatch
from PIL import Image
import datetime

import PySimpleGUI as sg
import os

#────────────────────
# PDFの比較関数
#────────────────────
def Pdf2image(folder_name, pdf_path):

    # poppler/binを環境変数PATHに追加する
    poppler_dir = Path().resolve().parent.absolute() / "poppler/bin"
    os.environ["PATH"] += os.pathsep + str(poppler_dir)

    # 画像フォルダパス
    img_files = r"./image_file/" + folder_name
    pdf_path = Path(pdf_path)
    # PDF -> Image に変換（150dpi）
    print(img_files)
    print(pdf_path)
    pages = convert_from_path(str(pdf_path), 150)

    # 比較項目ごとにフォルダ作成
    if not os.path.exists(img_files):
        os.mkdir(img_files)
    
    # 画像ファイルを１ページずつ保存
    image_dir = Path(img_files)
    for i, page in enumerate(pages):
        file_name = pdf_path.stem + "_{:02d}".format(i + 1) + ".png"
        image_path = image_dir / file_name
        # PNGで保存
        page.save(str(image_path), "png")

    print("変換が完了しました。")

#────────────────────
# PDFの比較関数
#────────────────────
def PDFMerge(folder_name, file_A, file_B):

    #────────────────────
    # パラメータ
    #────────────────────

    # folder_name = "厚生労働省Merge"
    # folder_name_true = "厚生労働省_True"
    # folder_name_false = "厚生労働省_False"

    folder_path = r"./image_file/" + folder_name
    print(folder_path)

    pdf_files = Path(folder_path)
    files = os.listdir(pdf_files)
    # 画像ファイルの数をカウント
    count = len(fnmatch.filter(files, "*.png"))
    miss_array = []

    # フォルダ内末尾数字を一致させながら比較
    for i in range (1, int(count / 2) + 1):
        # 画像A
        # "/content/drive/My Drive/Colab Notebooks/pdf_merge/image_file/厚生労働省Merge/厚生労働省_True_0x.png"
        img_path_A = folder_path + "/" + file_A + "_" +  str(i).zfill(2) + ".png"

        # 画像B
        img_path_B = folder_path + "/" + file_B + "_" +  str(i).zfill(2) + ".png"
        print("比較を開始します。")
        print("------------------------------------------------------------------------------------------------------------------------")
        print("出力結果：" + str(i) + "枚目")

        #────────────────────
        # 画像表示関数
        #────────────────────
        def show(img):
            plt.figure(figsize=(100, 100))
            plt.imshow(img, vmin = 0, vmax = 255)
            plt.show()
            plt.close()

        #────────────────────
        # 画像読み込み
        #────────────────────
        # openCVが日本語パスに対応していないんため、numpyで読み込み → 変換
        n_A = np.fromfile(img_path_A, np.uint8)
        img_A = cv2.imdecode(n_A, cv2.IMREAD_COLOR)
        img_A = cv2.cvtColor(img_A, cv2.COLOR_BGR2RGB)
        n_B = np.fromfile(img_path_B, np.uint8)
        img_B = cv2.imdecode(n_B, cv2.IMREAD_COLOR)
        img_B = cv2.cvtColor(img_B, cv2.COLOR_BGR2RGB)

        #────────────────────
        # 画像の差分
        #────────────────────
        #準備
        fgbg = cv2.createBackgroundSubtractorMOG2(history=2)

        #差分マスクの計算
        fgmask = fgbg.apply(img_A)
        fgmask = fgbg.apply(img_B)
        #差分の数値を取得 0なら一致
        moment = cv2.countNonZero(fgmask)   
        print(moment)
        # show(fgmask)

        #画像１を暗くして差分マスクを重ねる

        img_A[fgmask==255] = (255, 0, 0)
        
        #────────────────────
        # MergeResult画像を保存
        #────────────────────
        # 保存フォルダ「Result」を作成
        result_path = "./Result/" + folder_name
        if not os.path.exists(result_path):
            os.mkdir(result_path)
        # 画像を保存        
        img_Merge = img_A
        #show(img_Merge)
        # cv2.imencode + np.ndarray.tofile に分解して実行する。（日本語対応のため）
        filename = result_path + "/" + folder_name + "_" +  str(i).zfill(2) + ".png"        
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img_Merge)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)

        # 一致しなかったページ情報を取得
        if moment != 0:
            miss_array.append(str(i) + "ページ")

        i += 1

    print("比較が完了しました。")

    if len(miss_array) == 0:
        print("完全一致です。")
    else:
        print("相違があります。")
    print("相違箇所は、")
    print(miss_array)

#────────────────────
# GUI側の処理
#────────────────────

# ステップ1. インポート
# import PySimpleGUI as sg
# import os

# ステップ2. デザインテーマの設定
sg.theme('Dark Blue 3')

# ステップ3. ウィンドウの部品とレイアウト
layout = [
    [sg.Text('比較対象のフォルダを指定してください')],
    [sg.Text('ファイル①', size=(10, 1)), sg.Input(), sg.FileBrowse('ファイル①を選択', key='file_A')],
    [sg.Checkbox('画像出力済み', default=False, key='img_A_flg')],
    [sg.Text('ファイル②', size=(10, 1)), sg.Input(), sg.FileBrowse('ファイル②を選択', key='file_B')],
    [sg.Checkbox('画像出力済み', default=False, key='img_B_flg')],
    [sg.Button('比較', key='merge')],
    [sg.Output(size=(80,20))]
]

# ステップ4. ウィンドウの生成
window = sg.Window('PDF比較ツール', layout)

# ステップ5. イベントループ
while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED: #ウィンドウのXボタンを押したときの処理
        break

    if event == 'merge': #「比較」ボタンが押されたときの処理
        #────────────────────
        # データの元処理
        #────────────────────

        # フォルダ名取得
        folder_name = values['file_A'].split("/")[-2]
        # pdfファイルのフルパス
        pdf_path_A = values['file_A']
        pdf_path_B = values['file_B']

        # 「厚生労働省_True」の形に
        file_A = values['file_A'].split("/")[-1].split(".pdf")[0]
        file_B = values['file_B'].split("/")[-1].split(".pdf")[0]

        # 画像化フラグをチェックして変換
        if values['img_A_flg'] == False:
            Pdf2image(folder_name, pdf_path_A)
        if values['img_B_flg'] == False:
            Pdf2image(folder_name, pdf_path_B)
        
        PDFMerge(folder_name, file_A, file_B)
        '''
        テキストは表示された
        あとは画像をぶち込むことができれば勝ち
        
        追記 09/02
        結果画像を個別のフォルダに保存して、
        新たなビューアーで結果を一覧表示が良さそう
        
        追記 09/04
        画像が青くなるのだけわからないね
        showだと正しいカラーなのに保存すると変わる
        '''

window.close()