
# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import copy
import MySQLdb as db
from pagerank import page_rank

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')
PAGE_DESCRIPTION_LENGTH = 15

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        # establish db connection
        self.conn = db_conn

        self._url_queue = [ ]

        # Document Id Cache: Stores all url and their respective document id
        self._doc_id_cache = { }

        # Title Cache: Stores all document ids and their respective titles
        self._title_cache = { }

        # Page Description Cache: Stores all document ids and their respective decriptions
        self._pg_cache = { }
        
        # Lexicon Cache: Stores all words and their respective word id
        self._word_id_cache = { }

        # Forward Index: Links documents to words and their hit list
        self._forward_index = defaultdict(dict)

        # Inverted Index: Links words to every document in which they occur
        self._inverted_index = { }

        # Links cache: a list of how outgoing and incoming urls are connected by using docids
        self._links = []

        # Page Rank: Stores docid and its rank
        self._page_rank = None

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # TODO remove me in real version
        self._mock_next_doc_id = 1
        self._mock_next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None
        self._curr_page_description_count = 0
        self._curr_page_description_flag = False

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass
    
    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1
        return ret_id
    
    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to insert a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1
        return ret_id
    
    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]
        
        # TODO: 1) add the word to the lexicon, if that fails, then the
        #          word is in the lexicon
        #       2) query the lexicon for the id assigned to this word, 
        #          store it in the word id cache, and return the id.
        c = self.conn.cursor()
        word_id = -1
        try:
            # try adding word to lexicon
            c.execute("insert into lexicon(word) values (%s)", (word,))
            self.conn.commit()
            word_id =  c.lastrowid
        except db.IntegrityError:
            # word already exists so get it's id
            c.execute("select id from lexicon where word=%s limit 1", (word,))
            for row in c:
                word_id = row[0]

        #word_id = self._mock_insert_word(word)
        self._word_id_cache[word] = word_id
        return word_id
    
    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        # TODO: just like word id cache, but for documents. if the document
        #       doesn't exist in the db then only insert the url and leave
        #       the rest to their defaults.
        
        c = self.conn.cursor()
        doc_id = -1
        try:
            # try adding word to lexicon
            c.execute("insert into documentIndex(url) values (%s)", (url,))
            self.conn.commit()
            doc_id =  c.lastrowid
        except db.IntegrityError:
            # word already exists so get it's id
            c.execute("select id from documentIndex where url=%s limit 1", (url,))
            for row in c:
                doc_id = row[0]

        #doc_id = self._mock_insert_document(url)
        self._doc_id_cache[url] = doc_id
        return doc_id

    def resolve_word(self, word_id):
        """Get the word given word id"""
        for word in self._word_id_cache:
            if self._word_id_cache[word] == word_id:
                return word
        return ""

    def resolve_document(self, doc_id):
        """Get the url given document id"""
        for url in self._doc_id_cache:
            if self._doc_id_cache[url] == doc_id:
                return url
        return ""
    
    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # TODO
        self._links.append((from_doc_id,to_doc_id))
        try:
            c = self.conn.cursor()
            c.execute("insert into links(docidFrom,docidTo) values(%s,%s)",(from_doc_id,to_doc_id,))
            self.conn.commit()
        except db.Error as e:
            print "An error occurred:", e.args[0]

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print "document title="+ repr(title_text)

        # TODO update document title for document id self._curr_doc_id
        self._title_cache[self._curr_doc_id] = title_text

        try:
            c = self.conn.cursor()
            c.execute("update documentIndex set title = %s where id=%s",(title_text,self._curr_doc_id))
            self.conn.commit()
        except db.Error as e:
            print "An error occurred:", e.args[0]
    
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url
    
    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document
        print "    num words="+ str(len(self._curr_words))

        c = self.conn.cursor()
        for (wordid, importance) in self._curr_words:
            if wordid not in self._forward_index[self._curr_doc_id]:
                self._forward_index[self._curr_doc_id][wordid] = []
            self._forward_index[self._curr_doc_id][wordid].append(importance)
        
            # build hitlist
            try:
                c.execute("insert into hitlist(docid,wordid,importance) values(%s,%s,%s)",(self._curr_doc_id,wordid,importance))
            except db.Error as e:
                print "An error occurred:", e.args[0]
        self.conn.commit()
            


    # def _add_document_to_words(self):
    #     """Update inverted index by linking current document id to every word in current words"""
    #     for (curr_word_id,its_font_size) in self._curr_words:
    #         #if word_id does not exist in inverted index, initialize set
    #         if curr_word_id not in self._inverted_index:
    #             self._inverted_index[curr_word_id] = set()
    #         self._inverted_index[curr_word_id].add(self._curr_doc_id)



    def _increase_font_factor(self, factor):
        """Increase/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))
        
        # Add the word to page description
        if self._curr_doc_id not in self._pg_cache:
            self._pg_cache[self._curr_doc_id] = ''
        if (len(self._pg_cache[self._curr_doc_id]) < PAGE_DESCRIPTION_LENGTH) and (self._curr_page_description_flag):
            self._pg_cache[self._curr_doc_id] += ' ' + ' '.join(word.strip() for word in words)
            self._pg_cache[self._curr_doc_id] = ' '.join(self._pg_cache[self._curr_doc_id].split())
        
    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))
            
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue

                # Start recording page description when we enter the body
                if (tag_name == 'body'):
                    self._curr_page_description_flag = True
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id) # mark this document as haven't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = [ ]
                # Traverse url 
                self._index_document(soup)
                self._add_words_to_document() # build forward index with hit list
                print "    url="+repr(self._curr_url)

                # reset page description recording flag
                self._curr_page_description_flag = False
                # save page description
                try:
                    c = self.conn.cursor()
                    c.execute("update documentIndex set description = %s where id=%s",(self._pg_cache[self._curr_doc_id],self._curr_doc_id))
                    self.conn.commit()
                except:
                    pass

            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()
    def build_inverted_index(self):
        # build index
        try:
            c = self.conn.cursor()
            for wordid in self.get_inverted_index():                
                c.executemany("insert into invertedIndex(docid,wordid) values(%s,{0})".format(wordid),
                    [(docid,) for docid in list(self._inverted_index[wordid])])
                self.conn.commit()
        except db.Error as e:
            print "An error occurred:", e.args[0]

    def rank_all(self):
        self._page_rank = page_rank(links = self._links)
        try:
            c = self.conn.cursor()
            c.executemany("insert into pagerank(docid,rank) values(%s,%s)", self._page_rank.items())
            self.conn.commit()
        except:
            pass

    def get_lexicon(self):
        """returns a mapping of a word with its id as a dict"""
        return sorted(self._word_id_cache)

    def get_document_index(self):
        """returns a mapping of a document id with a tuple of its url and title as a dict"""
        return {doc_id:(doc_url, self._title_cache[doc_id], self._pg_cache[doc_id]) for (doc_url, doc_id) in self._doc_id_cache.items()}

    def get_links(self):
        """returns the relation between incoming and outgoing urls"""
        return self._links

    def get_inverted_index(self):
        """returns the inverted index in a dict()"""
        for docid in self._forward_index:
            for wordid in self._forward_index[docid]:
                if wordid not in self._inverted_index:
                    self._inverted_index[wordid] = set()
                self._inverted_index[wordid].add(docid)
        return self._inverted_index

    def get_resolved_inverted_index(self):
        """returns the inverted index in a dict() where word ids
        are replaced by the word strings, and the document Ids are 
        replaced by URL strings in the inverted index"""
        return  {self.resolve_word(word_id):set([self.resolve_document(doc_id) for doc_id in self._inverted_index[word_id]]) for word_id in self._inverted_index}

    def get_document_info(self, doc_id):
        """returns a page title and page description as a tuple"""
        return (self._title_cache[doc_id],self._pg_cache[doc_id])

    def reset_db(conn):
    c = conn.cursor()
    try:
        c.execute('''drop table  documentIndex''')
        c.execute('''drop table  hitlist''')
        c.execute('''drop table  invertedIndex''')
        c.execute('''drop table  lexicon''')
        c.execute('''drop table  links''')
        c.execute('''drop table  pagerank''')
        c.execute('''drop table  searchResults''')
        conn.commit()
        return True
    except db.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to reset db"
        return False

if __name__ == "__main__":
    # Setup database connection
    conn = db.connect(host = "comet-mysql-east1.cxtfibfzhdya.us-east-1.rds.amazonaws.com",
                    user = "cometDev", passwd= "mycometdev", db = "cometDev", port=3306)
    if not reset_db(conn):
        print "Tables don't exist"
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
    #searchResults
    c.execute('''CREATE TABLE IF NOT EXISTS `searchResults` (
            id int(10) unsigned NOT NULL AUTO_INCREMENT,
            sessionID varchar(250) NOT NULL,
            searchResult text NOT NULL,
            dateAdded timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            totalNum int(10) unsigned NOT NULL DEFAULT '0',
            PRIMARY KEY (`id`)
            )''')
             
    conn.commit()


    bot = crawler(db_conn=conn, url_file="urls.txt")
    bot.crawl(depth=1)
    bot.build_inverted_index()
    bot.rank_all()
    conn.close()
