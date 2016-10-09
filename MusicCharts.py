import requests
import bs4
import datetime
import re
import random
import webbrowser
import time
import os
import random
import sqlite3 as lite
import wikipedia

YOUTUBELINK="YouTubeLink"
DATABASE='C:\\Users\\Scotts Main\\Google Drive\\BUSINESS WORK STUFF\\PYTHON\\Chart Scraper\\charts.db'
def chartsDB_connect():
    con = None
    con = lite.connect(DATABASE)
    con.row_factory=lite.Row
    return con


def chartsDB_get_charts_by_date(dt,chart_type='S'):
    items=[]
    con=chartsDB_connect()
    cur=con.cursor()
    query="select date('"+dt+"','-7 days')" #add 7 days to the first date
    cur.execute(query)
    d=cur.fetchone()
    if d:
        dt2=d[0]
    if chart_type == 'S': #year, searchstrings, weeksonchart, highestposition, successscore,youtubelink  from singles
        query="select singles.year,singles.searchstrings,position, singles.highestposition, singles.successscore, singles.youtubelink,singles.weeksonchart,chartdate, artists.wikiplink " \
              "from singlecharts, singles,songs, artists where singlecharts.trackid=singles.trackid AND singles.artistid=artists.artistid and singles.songid=songs.songid and singlecharts.chartdate > '"+dt2+"' and singlecharts.chartdate <= '"+dt+"'"
        print (query)
        return chartsDB_run_query(query)
        cur.execute("select position, singles.year,singles.searchstrings,singles.weeksonchart, singles.highestposition, singles.successscore, singles.youtubelink,chartdate, songs.wikiplink "
                    "from singlecharts, singles,songs, artists where singlecharts.trackid=singles.trackid AND "
                    "singles.artistid=artists.artistid and singles.songid=songs.songid and singlecharts.chartdate >= ? and singlecharts.chartdate < ?",(dt,dt2))
        header=[]
        header = [description[0] for description in cur.description]
        items+=[header]
        col_count=len(header)
        rows=cur.fetchall()
        for row in rows:
            item = []
            for i in range(col_count):
                item+=[row[i]]
            items+=[item]

    return items

def chartsDB_fill_out_youtube_link():
    count=1
    con = chartsDB_connect()
    # con.row_factory=lite.Row #so we can refer to
    cur = con.cursor()
    cur2 = con.cursor()
    cur.execute("select searchstrings from singles where youtubelink is null")
    while True:
        row=cur.fetchone()
        if row==None:
            break
        yt = get_youtube_link(row[0])
        cur2.execute("update singles set YouTubeLink=? where SearchStrings=?",(yt,row[0]))
        print (str(count)+": "+row[0]+" "+yt)
        count+=1
        con.commit()

def chartsDB_fill_out_wikipedia_link():
    count=1
    con=chartsDB_connect()
    cur=con.cursor()
    cur2=con.cursor()
    cur.execute("select name from artists where wikiplink is null")
    while True:
        row=cur.fetchone()
        if row==None:
            break
        artist_name=row[0]
        try:
            x=wikipedia.page(artist_name)
            if x:
                cur2.execute("update artists set wikiplink=?, wikiPageId=? where name=?",(x.url,x.pageid,artist_name))
                print(str(count)+": "+artist_name+" "+x.url,x.pageid)
                count+=1
                con.commit()
        except Exception:
            pass

def chartsDB_get_wikiinfo(trackid,artistid,searchstrings,artist):
    wikiinfo=""
    con=chartsDB_connect()
    cur=con.cursor()
    if trackid:
        cur.execute("select wikipageid from singles where trackid=?",(trackid,))
        wikiinfo=chartsDB_get_wikiinfo_from_db_row(cur.fetchone())
        if wikiinfo == "": #we dont have a wiki page link on the song level - try the artist
            cur.execute("select artistid from singles where trackid=?",(trackid,))
            wikiinfo=chartsDB_get_wikiinfo(artistid=cur.fetchone()[0])
    elif artistid:
        cur.execute("select wikipageid from artists where artistid=?",(artistid,))
        wikiinfo=chartsDB_get_wikiinfo_from_db_row(cur.fetchone())
    elif searchstrings:
        cur.execute("select trackid from singles where searchstrings=?", (searchstrings,))
        wikiinfo = chartsDB_get_wikiinfo(trackid=cur.fetchone()[0])
    elif artist:
        cur.execute("select wikipageid from artists where name=?", (artist,))
        wikiinfo = chartsDB_get_wikiinfo_from_db_row(cur.fetchone())

    return wikiinfo

def chartsDB_get_wikiinfo_from_db_row(row):
    wikiinfo = ""
    if row:
        wikipageid=row[0]
        if wikipageid:
            wikiinfo=wikipedia.page(pageid=wikipageid).summary
    return wikiinfo

def chartsDB_update_track_statistics(trackid):

    con = chartsDB_connect()
    # con.row_factory=lite.Row #so we can refer to
    cur = con.cursor()
    cur2=con.cursor()
    cur.execute("select * from SingleCharts where trackid=?", (trackid,))
    songs = cur2.fetchall()
    weeks_in_chart = len(songs)
    success_score = 0
    best_position = 100
    year = 2016
    for song in songs:
        cur_year = int(song[4][:4])
        if cur_year < year:
            year = cur_year
        pos = int(song[3])
        if pos < best_position:
            best_position = pos
        if pos == 1:
            success_score += 250
        elif pos < 11:
            success_score += (11 - pos) * 10 + 110
        elif pos < 41:
            success_score += (41 - pos) + 70
        else:
            success_score += (101 - pos)
    cur2.execute("update Singles set weeksonchart=?, year=?,highestposition=?,successscore= ? where trackid=?",
                 (weeks_in_chart, year, best_position, success_score, trackid))
    con.commit()

def chartsDB_update_charts_table_from_flat_file(file):

    con = chartsDB_connect()
    cur=con.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS charts (key text PRIMARY KEY, dt text, pos INTEGER , song TEXT, artist text);
       """)
    chartsfile = open(file)
    for line in chartsfile.readlines():
        str="INSERT OR IGNORE INTO charts VALUES(?,?,?,?,?)"
        items = line.split(',')
        key = items[0]+":"+items[1]
        cur.execute(str,(key, items[0],items[1],items[2],items[3].strip("\n")))
        #print (items[0],items[1],items[2],items[3])
    con.commit()
    print("Run a query but retieve data 1 row at a time - more managable - each row is a tuple")

    cur.execute("select * from charts")
    while True:
        row = cur.fetchone()
        if row == None:
            break
        print(row)
    con.close()

def chartsDB_get_track_history(trackid):
    wikiinfo=""
    songinfo = ""
    con=chartsDB_connect()
    cur = con.cursor()
    cur.execute("select weeksonchart, year, highestposition, successscore from singles where trackid=?",(trackid,))
    song=cur.fetchone()
    if song:
        songinfo = "<h2>This song entered the charts in "+str(song[1]) + " and lasted "+str(song[0]) +" weeks reaching a high position of number: "+str(song[2])+ ". It has as success score of: "+str(song[3])+"</h2>"
    query = "select chartdate,POSITION from singlecharts where trackid ='" + trackid + "' order by chartdate asc"
    cur.execute("select searchstrings from singles where trackid = ?", (trackid,))
    x = cur.fetchone()
    if x:
        title=x[0]
        youtube=get_youtube_html_embed_link(title)
        header = "<h1>" + title + "</h1></br>"
        wikiinfo=chartsDB_get_wikiinfo(trackid=trackid)
        return header +songinfo+ youtube+chartsDB_run_query(query)+"<p>"+ wikiinfo+ "</p>"
    return "NO RESULTS"

def chartsDB_get_trackid_from_artist_and_song(artist, song):
    songid="#na"
    artistid="#na"
    con = chartsDB_connect()
    cur = con.cursor()
    cur.execute("select songid from songs where title=?",(song,))
    row = cur.fetchone()
    if row:
        songid=row[0]
    cur.execute("select artistid from artists where name=?", (artist,))
    row = cur.fetchone()
    if row:
        artistid = row[0]
    if artistid != "#na" and songid !="#na":
        cur.execute("select trackid from singles where songid=? and artistid=?",(songid,artistid))
        row = cur.fetchone()
        if row:
            trackid = row[0]
            return trackid
    return None

def chartsDB_get_artistIDs_from_artist_name(artist):
    artistids = ""
    con = chartsDB_connect()
    cur = con.cursor()
    if "%" in artist or "*" in artist:
        artist += "%"
        artist = artist.replace(" ", "%")
        artist = artist.replace("*", "%")
        cur.execute("select artistid from artists where name like ?", (artist,))
        rows = cur.fetchall()
        artistids = "("
        for row in rows:
            artistids += str(row[0]) + ","
        if len(artistids) > 1:
            a = list(artistids)
            a[-1] = ")"  # replace the last comma with a )
            artistids = "".join(a)
        else:
            artistids = ""
    else:
        cur.execute("select artistid from artists where upper(name) = upper(?)", (artist,))
        rows = cur.fetchone()
        if rows:
            artistids = "(" + str(rows[0]) + ")"
        else:  # couldnt find an exact match so perform a fuzzy search
            artist = "%" + artist
            return chartsDB_get_artistIDs_from_artist_name(artist)

    return artistids

def chartsDB_get_songIDs_from_song_name(song):
    songids = ""
    con = chartsDB_connect()
    cur = con.cursor()
    if "%" in song or "*" in song:
        song += "%"
        song = song.replace(" ", "%")
        song = song.replace("*", "%")
        cur.execute("select songid from songs where title like ?", (song,))
        rows = cur.fetchall()
        songids = "("
        for row in rows:
            songids += str(row[0]) + ","
        if len(songids) > 1:
            s = list(songids)
            s[-1] = ")"  # replace the last comma with a )
            songids = "".join(s)
        else:
            songids = ""
    else:
        cur.execute("select songid from songs where upper(title) = upper(?)", (song,))
        rows = cur.fetchone()
        if rows:
            songids = "(" + str(rows[0]) + ")"
        else: #couldnt find an exact match so perform a fuzzy search
            song="%"+song
            return chartsDB_get_songIDs_from_song_name(song)

    return songids

def chartsDB_get_artist_and_song_matches(artist,song):
    con=chartsDB_connect()
    cur = con.cursor()
    songids=chartsDB_get_songIDs_from_song_name(song)
    artistids = chartsDB_get_artistIDs_from_artist_name(artist)
    if songids!="" and artistids!="":
        query = "select trackid from singles where artistid in "+artistids+" and songid in "+songids
        cur.execute(query)
        rows=cur.fetchall()
        if len(rows)==1: #we only got a single match so return this songs history with a header
            trackid=rows[0][0]
            return chartsDB_get_track_history(trackid)
        elif len(rows)>1:
            query = "select * from singles where artistid in " + artistids + " and songid in " + songids
            return chartsDB_run_query(query)
    return "<h1>NO RESULTS</h1>"

def process_year_in_string(text_search):
    current_year = datetime.datetime.now().year
    earliest_year = 1954
    years=[]
    year_query=""

    if "50s" in text_search:
        for y in range(earliest_year,1960):
            years+= [y]
        text_search=text_search.replace("50s","")
    if "60s" in text_search:
        for y in range(1960, 1970):
            years += [y]
        text_search = text_search.replace("60s", "")
    if "70s" in text_search:
        for y in range(1970, 1980):
            years += [y]
        text_search = text_search.replace("70s", "")
    if "80s" in text_search:
        for y in range(1980, 1990):
            years += [y]
        text_search = text_search.replace("80s", "")
    if "90s" in text_search:
        for y in range(1990, 2000):
            years += [y]
        text_search = text_search.replace("90s", "")
    if "2000s" in text_search:
        for y in range(2000, 2010):
            years += [y]
        text_search = text_search.replace("2000s", "")
    if "2010s" in text_search:
        if current_year<2020:
            for y in range(2010, current_year+1):
                years += [y]
        else:
            for y in range(2010, 2020):
                years += [y]
        text_search = text_search.replace("2010s", "")
    if "2020s" in text_search:
        if current_year < 2030:
            for y in range(2020, current_year+1):
                years += [y]
        else:
            for y in range(2020, 2030):
                years += [y]
        text_search = text_search.replace("2020s", "")
    year_regex=re.compile("\d\d\d\d-\d\d\d\d")
    year_range=year_regex.search(text_search)
    if year_range:
        from_year=year_range.group()[0:4]
        to_year=year_range.group()[5:9]
        if int(from_year) > current_year:
            from_year=current_year
        if int(to_year) > current_year:
            to_year = current_year
        if int(from_year) < earliest_year:
            from_year = earliest_year
        if int(to_year) < earliest_year:
            to_year = earliest_year
        if int(from_year)>int(to_year):
            temp=from_year
            from_year=to_year
            to_year=temp
        for y in range(int(from_year), int(to_year)):
            years += [y]
            text_search=text_search.replace(year_range.group(),"")
    year_regex=re.compile("\d\d\d\d")
    years_found=year_regex.findall(text_search)
    if years_found:
        for y in years_found:
            #check that it is a valid year
            if int(y) <= current_year and int(y)>earliest_year:
                years+=[y]
                text_search = text_search.replace(y,"") #remove year from the search string
    if years:
        year_query=" year in ("
        for year in years:
            year_query+=str(year)+","
        year_query=year_query[:-1]
        year_query+=")"

    return year_query,text_search

def process_position_in_string(text_search):
    max_position=100
    min_position=1

    position="#\d+"

    return position,text_search



def chartsDB_process_search_string(text_search):

    ret=""
    if "SELECT" in text_search.upper() and "FROM" in text_search.upper():
        ret = chartsDB_run_query(text_search);
    elif re.match("\d\d-\d\d-\d\d\d\d", text_search) != None or re.match("\d\d\d\d-\d\d-\d\d", text_search) != None:
        ret=chartsDB_get_charts_by_date(text_search)
    else:
        year_query,text_search=process_year_in_string(text_search)
        position_query,text_search=process_position_in_string(text_search)
        query = "select year, searchstrings, weeksonchart, highestposition, successscore,youtubelink  from singles "
        text_search=text_search.replace(" ","%")
        text_search = text_search.replace("*", "%")
        if year_query:
            query+=" where "+year_query
        if text_search:
            if year_query:
                query+=" and searchstrings like'%" + text_search + "%'"
            else:
                query += "where searchstrings like'%" + text_search + "%'"
            print(query)
        query+=" order by successscore desc"
        ret = chartsDB_run_query(query)
    return ret


def chartsDB_get_charts_results(raw_query=None,text_search=None,song=None,artist=None,year_from=None,year_to=None,posfrom=None,posto=None,weeks_on_chart=None,order_by=None):

    if raw_query:
        query=raw_query
    else:
        if artist and song:
           return chartsDB_get_artist_and_song_matches(artist,song)
        if re.match("\d\d-\d\d-\d\d\d\d", text_search) != None:
            s=get_chart_song_by_date_string(text_search)
            return "<h1>Number 1 on "+text_search +" was "+ s+ "</h1> " + get_youtube_html_embed_link(s)
        query = "select year, searchstrings, weeksonchart, highestposition, successscore,youtubelink  from singles "
        if text_search:
            query+="where searchstrings like'%" + text_search + "%' "
        else:
            query += "where searchstrings is not null "
        if year_from:
            query+=" and year >= "+year_from
        if year_to:
            query += " and year <= " + year_to
        if posfrom:
            query += " and highestposition >= " + posfrom
        if posto:
            query += " and highestposition <= " + posto
        if weeks_on_chart:
            query += " and weeksonchart >= " + weeks_on_chart
        if order_by:
            if order_by in ["successscore","weeksonchart"]:
                query += " order by "+order_by+" desc"
            else:
                query += " order by " + order_by + " asc"
        else:
            query+=" order by successscore desc"

    print(query)
    return chartsDB_run_query(query)

def chartsDB_run_query(querystring):
    items=[]
    count = 1
    con = chartsDB_connect()
    cur = con.cursor()
    cur.execute(querystring)
    header=[]
    header+=["#"]
    header+=[description[0] for description in cur.description]#first row is column names
    items+=[header]
    col_count=len(header)-1
    rows = cur.fetchall()
    for row in rows:
        item = []
        item += [count]
        count+=1
        for i in range(col_count):
            if header[i+1]==YOUTUBELINK:
                item+=[convert_youtube_link_to_embed(row[i])]
            else:
                item += [row[i]]

        items += [item]
    '''
    for col in columns:
        ret+="<th>"+col+"</th>"
    ret+="</tr></thead><tbody>"
    while True:
        row = cur.fetchone()
        ret+="<tr>"
        if row is None:
            break
        ret += "<td>"+str(count) + "</td>"
        for item in row:
            ret += "<td>"+str(item)+ "</td>"
        ret += '</tr>'
        count += 1
    ret+="</tbody></table>"
    '''
    return items

def get_random_chart_date(year=None,year_to=None):
    official_start = datetime.datetime(1956, 11, 14, 0, 0, 0)  # offical charts start date
    official_end = get_current_chart_date()
    if year:
        start=datetime.datetime(year,1,1,0,0,0)
        if start < official_start: start=official_start
        if start > official_end: start=official_end
        if year_to:
            end = datetime.datetime(year_to, 12, 31, 0, 0, 0)
        else:
            end = datetime.datetime(year, 12, 31, 0, 0, 0)
        if end > official_end: end=official_end
        if start>=end: return official_end
    else:
        start=official_start#offical charts start date
        end=official_end

    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + datetime.timedelta(seconds=random_second)

def get_current_chart_date():
    td = datetime.datetime.now()
    dayofweek = td.weekday()
    diff = 0
    if dayofweek > 4:
        diff = dayofweek - 4
    elif dayofweek < 4:
        diff = dayofweek + 3
    td -= datetime.timedelta(diff)
    return td


######################################################################
###############~~~CHART FUNCTIONS~~~~~~~~~~~~~~~~~~~~~################
######################################################################



def get_user_input_chart_type():
    correct_chart=False
    while correct_chart==False:
        print('Please enter A for Album chart or S for Single chart')
        chart_type = input()
        if (chart_type=='A'):
            correct_chart=True
        if (chart_type=='S'):
            correct_chart=True
    return chart_type

def get_user_input_date():
    correct_date = False
    print('Enter a start date in DD-MM-YYYY format (Note the official single charts started on 14-11-1952, Albums on 22-07-1956')
    while correct_date == False:
        date_entry = input()

        if (re.match("\d\d-\d\d-\d\d\d\d", date_entry) != None):
            day, month, year = map(int, date_entry.split('-'))
            try:
                start_date = datetime.date(year, month, day)
                correct_date = True
            except ValueError:
                correct_Date = False
                print('Please enter a valid date')
        else:
            print('Please enter a valid date in DD-MM-YYYY format')
    return start_date

def chart_scraper_run(max_number=100):
    user_date=get_user_input_date()
    user_chart_type=get_user_input_chart_type()
    create_chart_file(user_date,chart_type=user_chart_type,max_number=max_number)

def create_chart_file(start_date,chart_type='S',max_number=100):
    count = 0
    today = datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)

    chart_database = open('chartdatabase.txt', 'w')  # open chart database file to store this data in

    current_date = start_date

    start_time = time.time()
    prev_time = start_time
    # start getting the data for each date
    while current_date < today:

        tm = str(int(time.time() - start_time)) + '[' + str(int(time.time() - prev_time)) + '] seconds...'

        if chart_type == 'S':
            print('Processing ' + str(current_date) + ' ' + str(count) + ' songs processed so far, ' + tm)
        if chart_type == 'A':
            print('Processing ' + str(current_date) + ' ' + str(count) + ' albums processed so far, ' + tm)
        charts = get_charts_by_date(current_date,chart_type)

        amount=min(max_number,len(charts))

        for i in range(amount):
            chart_database.write(str(current_date) + ',') #date
            chart_database.write(str(i + 1) + ',') #position

            artist = charts[i].select('.title')[0].getText()
            title = charts[i].select('.artist')[0].getText()

            # strip out any dodgy non ascii characters otherwise the write function will fail
            artist = ''.join(a for a in artist if ord(a) < 128)
            title = ''.join(a for a in title if ord(a) < 128)

            chart_database.write(artist.strip("\n") + ',') #artist
            chart_database.write(title.strip("\n") + "\n") #song

            count += 1

        current_date += datetime.timedelta(days=7)
        prev_time = time.time()

    chart_database.close()  # close the file

    # rename the file
    new_name = ''
    if (chart_type == "S"):
        new_name += "Single Chart "
    if (chart_type == "A"):
        new_name += "Album Chart "
    new_name += "Top " + str(amount) + " "
    current_date += datetime.timedelta(days=-7)  # go back to last date
    new_name += 'from ' + str(start_date) + ' to ' + str(current_date) + ' ' + str(count)

    if (chart_type == "S"):
        new_name += " Songs.txt"
    if (chart_type == "A"):
        new_name += " Albums.txt"

    os.rename("chartdatabase.txt", new_name)

#############################################################################
##################### YOUTUBE FUNCTIONS #####################################
#############################################################################

def play_current_number1():
    play_song(get_current_chart_song(chart_position=1))

def download_song(song):
    webbrowser.open(get_youtube_link(song,True))

def play_song(song):
    webbrowser.open(get_youtube_link(song))

def get_youtube_link(song,d=False):
    # look here for info on checking if the video has been removed - http://stackoverflow.com/questions/30190620/how-do-i-check-if-a-youtube-video-is-blocked-restricted-deleted
    song=song.replace(" ","+")
    song = song.replace("&", "%26")
    web_url = "https://www.youtube.com/results?search_query=" + song
    ret=""
    res = requests.get(web_url)
    html = bs4.BeautifulSoup(res.text, "html.parser")  # create an html parser for the webpage
    substring = 'watch'
    # find all links
    for link in html.find_all('a'):
        # find the first one that contains watch
        x = link.get('href')
        if substring in x:
            if d:
                ret= "https://www.ssyoutube.com" + x
                return ret
            else:
                ret= "https://www.youtube.com"+x
                return ret
    #if not len(ret): ret=get_youtube_link("Metallica Master of Puppets",d) #if it cant find anyting return master of puppets
    return ret

def get_youtube_html_embed_link(song, audio_only=False):
    yt=get_youtube_link(song)
    code=yt[len(yt)-11:len(yt)]
    if audio_only:
        return '<iframe width = "0" height = "0" src = "https://www.youtube.com/embed/' + code + '?autoplay=1&rel=0&autohide=0&#8243"frameborder="0" allowfullscreen></iframe>'
    else:
        return '<iframe width = "610" height = "315" src = "https://www.youtube.com/embed/'+code+'?autoplay=1"frameborder="0" allowfullscreen></iframe>'

def convert_youtube_link_to_embed(youtube_link):
    return youtube_link.replace("watch?v=","embed/")


#############################################################################
##################### CHART FUNCTIONS #####################################
#############################################################################

def get_current_chart_song(chart_type='S',chart_position=1):
    return get_chart_song_by_date(get_current_chart_date(),chart_type, chart_position)

def get_random_chart_song(chart_type='S', include_info=False, year=None, year_to=None,max_chart_position=1):
    dt=get_random_chart_date(year,year_to)
    chart_position=random.randint(1,max_chart_position)
    if include_info:
        return get_chart_song_by_date(dt,chart_type,chart_position)+ " [Number: "+ str(chart_position) +" on "+str(dt.day)+"-"+str(dt.month)+"-"+str(dt.year)+"]"
    else:
        return get_chart_song_by_date(dt,chart_type,chart_position)

def get_charts_by_date(dt,chart_type='S'):
    if chart_type=='S':
        if type(dt).__name__ != 'str': #if they pass a date instead of a string then we need to convert it
            dt=convert_date_to_string(dt)
        songs=chartsDB_get_charts_by_date(dt,chart_type)
        if songs:
            ret=songs
        else:
            if type(dt).__name__ == 'str':  # if they pass a string instead of a date then we need to convert it
                dt=convert_string_to_date(dt)
            ret = download_charts_by_date(dt, chart_type)
    return ret

def download_charts_by_date(dt,chart_type='S'):
        y = str(dt.year)

        if dt.month < 10:
            m = '0' + str(dt.month)
        else:
            m = str(dt.month)

        if dt.day < 10:
            d = '0' + str(dt.day)
        else:
            d = str(dt.day)
        if chart_type == 'S':
            web_url = "http://www.officialcharts.com/charts/singles-chart/" + y + m + d + "/7501/"
        if chart_type == 'A':
            web_url = "http://www.officialcharts.com/charts/albums-chart/" + y + m + d + "/7502/"
        else: #if all else fails download singles chart
            web_url = "http://www.officialcharts.com/charts/singles-chart/" + y + m + d + "/7501/"


        res = requests.get(web_url)
        if res.status_code == requests.codes.ok:
            print('Page downloaded ok!')
        else:
            print('Error downloading page...')

        html = bs4.BeautifulSoup(res.text, "html.parser")  # create an html parser for the webpage
        selected_date = html.find_all("option", selected=True)  # finds all values selected in comboboxes

        selected_day = int(selected_date[0]["value"])
        selected_month = int(selected_date[1]["value"])
        selected_year = int(selected_date[2]["value"])

        current_date = datetime.date(selected_year, selected_month, selected_day)

        return html.select('.title-artist')  # get the title/artists part


def get_chart_song_by_date(dt,chart_type='S',chart_position=1):

    charts = get_charts_by_date(dt,chart_type)

    # get the first item in list which should be the number 1
    artist = charts[chart_position-1].select('.artist')[0].getText()
    title = charts[chart_position-1].select('.title')[0].getText()

    return title.strip("\n") + " by " + artist.strip("\n")

def convert_string_to_date(dt):
    if re.match("\d\d-\d\d-\d\d\d\d", dt):
        day, month, year = map(int, dt.split('-'))
        try:
            dt = datetime.date(year, month, day)
            correct_date = True
        except ValueError:
            correct_date = False
            print('Please enter a valid date')
    elif re.match("\d\d\d\d-\d\d-\d\d", dt):
        year,month,day=map(int, dt.split('-'))
        try:
            dt = datetime.date(year, month, day)
            correct_date = True
        except ValueError:
            correct_date = False
            print('Please enter a valid date')
    else:
        print("date format not recognised")
    return dt

def convert_date_to_string(dt):
    y = str(dt.year)

    if dt.month < 10:
        m = '0' + str(dt.month)
    else:
        m = str(dt.month)

    if dt.day < 10:
        d = '0' + str(dt.day)
    else:
        d = str(dt.day)
    return d+"-"+m+"-"+y

def get_chart_song_by_date_string(dt,chart_type='S',chart_position=1):
    return get_chart_song_by_date(convert_string_to_date(dt),chart_type,chart_position)
