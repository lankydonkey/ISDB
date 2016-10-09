import sqlite3
from flask import Flask
from flask import request
from flask import render_template
#import sys
#sys.path.append("C:\\Users\\Scotts Main\\Google Drive\\BUSINESS WORK STUFF\\PYTHON\\Chart Scraper\\")
import MusicCharts as x

app = Flask(__name__)

@app.route('/')
def isdb():
   print("isdb called")
   return render_template("isdb.html")

@app.route('/',methods=['POST'])
def run_query():

   text_search=request.form['textsearch']

   mytable=x.chartsDB_process_search_string(text_search)

   link=""
   if len(mytable)>1:
      for item in mytable[1]:
         if "YOUTUBE" in str(item).upper():
            link=item

   if len(mytable)>1:
      return render_template("queryresults.html",mytable=mytable,link=link)
   else:
      print("no table")
      link = x.convert_youtube_link_to_embed(x.get_youtube_link(text_search))
      return render_template("queryresults.html",mytable=mytable,link=link)


if __name__ == '__main__':
   app.run()