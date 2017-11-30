import unittest
from crawler import crawler
import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import copy
import MySQLdb as db
from pagerank import page_rank
import pprint

def reset_db(conn):
    c = conn.cursor()
    try:
        c.execute('''drop table  documentIndex''')
        c.execute('''drop table  hitlist''')
        c.execute('''drop table  invertedIndex''')
        c.execute('''drop table  lexicon''')
        c.execute('''drop table  links''')
        c.execute('''drop table  pagerank''')
        conn.commit()
        return True
    except db.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to reset db"
        return False





##use this to find doc url/name
def get_document(docids,conn):
    c = conn.cursor()
    try:
        sql='''select docid, url, title, description, rank from documentIndex left join pagerank on id=docid  WHERE id IN (%s) order by rank desc''' 
        in_p=', '.join(map(lambda x: '%s', docids))
        sql = sql % in_p
        c.execute(sql, docids)
        if not c.rowcount:
            # no documentinfo found
            print "ERROR: document information not found"
            return None
        results = c.fetchall()
        return [(result[0],result[1],result[2],result[3],result[4]) for result in results]
    except db.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to resolve docids"
        return None

		
		
def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')
PAGE_DESCRIPTION_LENGTH = 15



if __name__ == "__main__":
    # Setup database connection
    conn = db.connect(host = "comet-mysql-east1.cxtfibfzhdya.us-east-1.rds.amazonaws.com",
                    user = "cometDev", passwd= "mycometdev", db = "cometTest", port=3306)
    if not reset_db(conn):
        quit()
    
    c = conn.cursor()

    # Create tables for data structures if they do not exist
    # documentIndex
    c.execute('''CREATE TABLE IF NOT EXISTS documentIndex
             (id int unsigned AUTO_INCREMENT, url varchar(250), title varchar(250), description text, primary key (id), unique (url))''')
    # Lexicon
    c.execute('''CREATE TABLE IF NOT EXISTS lexicon
             (id int unsigned AUTO_INCREMENT, word varchar(250), primary key (id), unique (word))''')
    # Hitlist
    c.execute('''CREATE TABLE IF NOT EXISTS hitlist
             (id int unsigned AUTO_INCREMENT, docid int unsigned, wordid int unsigned, importance int unsigned, primary key (id))''')
    # Index
    c.execute('''CREATE TABLE IF NOT EXISTS invertedIndex
             (id int unsigned AUTO_INCREMENT, docid int unsigned, wordid int unsigned, nhits int unsigned, primary key (id))''')
    # links
    c.execute('''CREATE TABLE IF NOT EXISTS links
             (docidFrom int unsigned, docidTo int unsigned)''')
    # pagerank
    c.execute('''CREATE TABLE IF NOT EXISTS pagerank
             (docid int unsigned, rank float unsigned, primary key (docid))''')
    conn.commit()


    bot = crawler(db_conn=conn, url_file="test_urls2.txt")
    bot.crawl(depth=1)
    bot.build_inverted_index()
    bot.rank_all()
 
	##print docid and ranks
    print "___________________"
    print "___________________"
    pp = pprint.PrettyPrinter(indent = 1)
    zzz = bot._page_rank.items()
    qqq = [pair[0] for pair in zzz]

    bbb = [(info[2],info[4]) for info in get_document(qqq,conn)]
                
    pp.pprint(bbb)
	
    print "___________________"
    conn.close()
