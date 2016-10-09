import sqlite3 as lite
import sys
sys.path.append("C:\\Users\\Scotts Main\\Google Drive\\BUSINESS WORK STUFF\\PYTHON\\Chart Scraper\\")
import MusicCharts as x


def filloutyoutubelink():
    count=41455
    con = None
    con = lite.connect('charts.db')
    # con.row_factory=lite.Row #so we can refer to
    cur = con.cursor()
    cur2 = con.cursor()
    cur.execute("select searchstrings from tracks")
    while True:
        row=cur.fetchone()
        if row==None:
            break
        yt = x.get_youtube_link(row[0])
        cur2.execute("update tracks set YouTubeLink=? where SearchStrings=?",(yt,row[0]))
        print (str(count)+": "+row[0]+" "+yt)
        count-=1
    con.commit()
#this script takes the raw charts.db database and distributes the data across all the other areas

def there_can_be_only_one(searchstring):
    ret=""
    #split the search string by spaces
    parts=searchstring.split(" ")
    size=len(parts)
    con = None
    con = lite.connect('charts.db')
    # con.row_factory=lite.Row #so we can refer to
    cur = con.cursor()

# first lets get a list of all artist names that have a partial match

    for artist in parts:
        cur.execute("select * from Artists where upper(Name)=?",(artist.upper(),))
        item=cur.fetchone()
        if item:
            ret=artist

    if ret=="" & size >1:
        for i in range (0,size,2):
            artist=parts[i]+" "+parts[i+1]
            cur.execute("select * from Artists where upper(Name)=?", (artist.upper(),))
            item = cur.fetchone()
            if item:
                ret = artist

    return ret

