#  NightWalk

夜間の徒歩移動において、過去の犯罪発生地点を可視化し、
より安全なルート選択を支援するデモ用Webアプリケーションです。

## ⚠ 実行環境に関する注意

本アプリは **Streamlit Cloud（無料プラン）** 上で動作しています。

そのため、以下のような制約があります。

- 初回アクセス時や一定時間アクセスがない場合  
  → サーバーの **コールドスタート** により表示まで時間がかかることがあります
- ルート探索・地図描画などの処理は計算量が大きいため  
  → ボタン押下後、**数分の待ち時間** が発生する場合があります
- 同時アクセスが集中した場合  
  → 一時的にエラー画面が表示されることがあります

これらは **Streamlit Cloudのリソース制限によるものであり、
アプリケーションロジック自体の不具合ではありません。**

デモ用途・課題提出用途としては
**事前計算・キャッシュ化により可能な限り負荷を軽減**しています。



---

##  概要

- 過去の犯罪発生地点を **ヒートマップ** として地図上に表示
- 徒歩ルートを地図上で可視化
- 夜道の安全性を直感的に理解できるUIを提供
- ユーザ同士が暗かった場所等の共有ができるよう掲示板機能を提供

※ 本アプリは **課題提出・デモ用途** を想定しており、
安定動作を優先した構成になっています。

※ Streamlit Cloud 上で動作しているため、
  ボタンを押してから地図が表示されるまで
  少し時間がかかる場合があります。
  処理中はそのままお待ちください。


---

##  使用技術

- Python 3
- Streamlit
- Folium
- OSMnx
- NetworkX
- Pandas
- OverpassAPI
- pyproj
- SQLite
- bcrypt

---

##  データ構成

- `data/crime_geocoded.csv`  
  → 事前にジオコーディング済みの犯罪発生地点データ  
  （起動時の負荷軽減のため、アプリ内でのジオコーディングは行いません）

- `data/walk.graphml`  
  → 徒歩ネットワークグラフ（事前生成）

---

##  起動方法（ローカル）

```bash
pip install -r requirements.txt
streamlit run app.py



## ⚡ 高速化版のデータ取得

ルート検索のたびにOverpass APIへアクセスすると、街灯・コンビニ・交番の取得で数十秒〜数分かかる場合があります。
この版では、POIを事前取得して `data/osm_poi.db` に保存し、検索時はSQLiteからルート周辺だけを取得します。

また、道路ネットワークも初回取得時に `data/graphs/` へGraphMLとして保存し、2回目以降は再利用します。
犯罪データは `data/crime_geocoded.csv` を作っておけば、検索時のジオコーディングも不要になります。

### 初回セットアップ

```bash
# 1. POI（街灯・コンビニ・交番）を一度だけ取得
python prepare_poi_data.py --place "さいたま市, 埼玉, Japan"

# 2. 徒歩道路ネットワークを一度だけ取得
python prepare_graph.py --place "さいたま市, 埼玉, Japan"

# 3. 犯罪データの住所を一度だけジオコーディング
python prepare_crime_data.py

# 4. 起動
streamlit run app.py
```

### 重要

- `prepare_poi_data.py` と `prepare_graph.py` は、最初の1回だけ時間がかかります。
- アプリの通常検索ではOverpass APIへアクセスしません。
- `data/osm_poi.db`、`data/graphs/*.graphml`、`data/crime_geocoded.csv` は生成物なので、同じPCでデモする場合は残しておきます。
- 対象地域を変更した場合は、その地域用のGraphML/POIを追加で作成してください。


## PBF方式（Overpass不使用）
初回だけ Geofabrik の `kanto-latest.osm.pbf` をダウンロードし、Pyosmium (`osmium`) でローカル解析して `data/osm_poi.db` を作成します。

```bash
pip install -r requirements.txt
python prepare_pbf_data.py --download
streamlit run app.py
```

アプリのルート検索時はSQLiteのbbox検索だけを行います。
