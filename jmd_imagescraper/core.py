# AUTOGENERATED! DO NOT EDIT! File to edit: 00_core.ipynb (unless otherwise specified).

__all__ = ['ImgSize', 'ImgLayout', 'ImgType', 'ImgColor', 'duckduckgo_scrape_urls', 'rmtree', 'download_urls',
           'duckduckgo_search', 'save_urls_to_csv', 'download_images_from_csv']

# Cell

# scraping
from pathlib import Path
from typing import Union
from enum import Enum
import re
import requests
import json
import time
from bs4 import BeautifulSoup

# other
from PIL import Image as PImage
from IPython.display import display
import pandas as pd
from fastprogress.fastprogress import progress_bar

# Cell
class ImgSize(Enum):
  Cached=""
  Small="Small"
  Medium="Medium"
  Large="Large"
  Wallpaper="Wallpaper"

# Cell
class ImgLayout(Enum):
  All=""
  Square="Square"
  Tall="Tall"
  Wide="Wide"

# Cell
class ImgType(Enum):
  All=""
  Photo="photo"
  Clipart="clipart"
  Gif="gif"
  Transparent="transparent"

# Cell
class ImgColor(Enum):
  All=""
  Color="color"
  Monochrome="Monochrome"
  Red="Red"
  Orange="Orange"
  Yellow="Yellow"
  Green="Green"
  Blue="Blue"
  Purple="Purple"
  Pink="Pink"
  Brown="Brown"
  Black="Black"
  Gray="Gray"
  Teal="Teal"
  White="White"

# Cell
def duckduckgo_scrape_urls(keywords: str, max_results: int,
                           img_size: ImgSize=ImgSize.Cached,
                           img_type: ImgType=ImgType.Photo,
                           img_layout: ImgLayout=ImgLayout.Square,
                           img_color: ImgColor=ImgColor.All) -> list:
  '''Scrapes URLs from DuckDuckGo image search. Returns list of URLs.'''
  BASE_URL = 'https://duckduckgo.com/'
  params = {
    'q': keywords
  };
  results = 0
  links = []

  resp = requests.post(BASE_URL, data=params)
  match = re.search(r'vqd=([\d-]+)\&', resp.text, re.M|re.I)
  assert match is not None, "Failed to obtain search token"

  HEADERS = {
      'authority': 'duckduckgo.com',
      'accept': 'application/json, text/javascript, */*; q=0.01',
      'sec-fetch-dest': 'empty',
      'x-requested-with': 'XMLHttpRequest',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-mode': 'cors',
      'referer': 'https://duckduckgo.com/',
      'accept-language': 'en-US,en;q=0.9',
  }

  filters = ""
  if(img_size != ImgSize.Cached): filters +=  "size:" + img_size.name
  filters += ","
  if(img_type != ImgType.All): filters +=  "type:" + img_type.name
  filters += ","
  if(img_layout != ImgLayout.All): filters +=  "layout:" + img_layout.name
  filters += ","
  if(img_color != ImgColor.All): filters +=  "color:" + img_color.name

  PARAMS = (
      ('l', 'us-en'),
      ('o', 'json'),
      ('q', keywords),
      ('vqd', match.group(1)),
      ('f', filters),
      ('p', '1'),
      ('v7exp', 'a'),
  )

  requestUrl = BASE_URL + "i.js"

  while True:
      while True:
          try:
              resp = requests.get(requestUrl, headers=HEADERS, params=PARAMS)
              data = json.loads(resp.text)
              break
          except ValueError as e:
              print("Hit request throttle, sleeping and retrying")
              time.sleep(5)
              continue

      #result["thumbnail"] is normally big enough for most purposes
      #result["width"], result["height"] are for the full size img in result["image"]
      #result["image"] url to full size img on orig site (so may be less reliable)
      #result["url"], result["title"].encode('utf-8') from the page the img came from

      for result in data["results"]:
        if(img_size == ImgSize.Cached): links.append(result["thumbnail"])
        else:                           links.append(result["image"])

        if(max_results is not None):
          if(len(links) >= max_results) : return links

      if "next" not in data:
          #no next page, all done
          return links

      requestUrl = BASE_URL + data["next"]

# Cell
def rmtree(path: Union[str, Path]):
    '''Recursively delete a directory tree'''
    path = Path(path); assert path.is_dir()
    for p in reversed(list(path.glob('**/*'))):
        if p.is_file():  p.unlink()
        elif p.is_dir(): p.rmdir()
    path.rmdir()

# Cell
import uuid

def download_urls(path: Union[str, Path], links: list, random_names=False) -> list:
  '''Downloads urls to the given path. Returns a list of Path objects for files downloaded to disc.'''
  if(len(links) == 0):
    print("Nothing to download!"); return

  path = Path(path)
  path.mkdir(parents=True, exist_ok=True)

  print("Downloading results into", path)
  pbar = progress_bar(links)
  pbar.comment = 'Images downloaded'

  i = 1
  mk_uniq = lambda : '_' + str(uuid.uuid4())[:8] if random_names else ''
  mk_fp = lambda x: path/(str(x).zfill(3) + mk_uniq() + ".jpg")

  is_file = lambda x: mk_fp(x).exists()
  while is_file(i): i += 1 # don't overwrite previous searches

  results = []

  #for link in links:
  for link in pbar:
      try:
        resp = requests.get(link)
        fp = mk_fp(i)
        fp.write_bytes(resp.content)

        try:
          img = PImage.open(fp)
          img.verify()
          img.close()
          results.append(Path(fp))
        except Exception as e:
          # print(e)
          print(fp, "is invalid")
          fp.unlink()
      except Exception as e:
        # print(e)
        print("Exception occured while retrieving", link)

      i += 1

  return results

# Cell
def duckduckgo_search(path: Union[str, Path], label: str, keywords: str, max_results: int=100,
                           img_size: ImgSize=ImgSize.Cached,
                           img_type: ImgType=ImgType.Photo,
                           img_layout: ImgLayout=ImgLayout.Square,
                           img_color: ImgColor=ImgColor.All,
                           random_names: bool=False) -> list:
  '''Run a DuckDuckGo search and download the images. Returns a list of Path objects for files downloaded to disc.'''

  print("Duckduckgo search:", keywords)
  links = duckduckgo_scrape_urls(keywords, max_results, img_size, img_type, img_layout, img_color)
  return download_urls(Path(path)/label, links, random_names=random_names)

# Cell
def save_urls_to_csv(path: Union[str, Path], label: str, keywords: str, max_results: int=100,
                       img_size: ImgSize=ImgSize.Cached,
                       img_type: ImgType=ImgType.Photo,
                       img_layout: ImgLayout=ImgLayout.Square,
                       img_color: ImgColor=ImgColor.All) -> None:
  '''Run a search and concat the URLs to a CSV file'''
  path = Path(path)
  if(path.exists() == False):
    df = pd.DataFrame(columns=["URL", "Label"])
    df.to_csv(path, index=False)

  urls = duckduckgo_scrape_urls(keywords, max_results, img_size, img_type, img_layout, img_color)

  rows = []
  for url in urls: rows.append({"URL":url, "Label":label})

  df = pd.concat([pd.read_csv(path), pd.DataFrame(rows)])
  df.to_csv(path, index=False)

# Cell
def download_images_from_csv(path: Union[str, Path], csv: Union[str, Path], url_col: str="URL", label_col: str="Label", random_names=False):
    '''Download the URLs from a CSV file to the given path. Returns a list of Path objects for files downloaded to disc.'''
    path = Path(path); csv = Path(csv);

    df = pd.read_csv(csv)
    labels = df.Label.unique()
    imgs = []

    for label in labels:
        df_label = df.loc[df[label_col] == label]
        urls = df_label[url_col].to_list()
        imgs.extend(download_urls(path/label, urls, random_names=random_names))

    return imgs