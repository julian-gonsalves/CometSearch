import operator, re, httplib2, time, math, pickle
from bottle import route, run, static_file,view, get,post, template, request, redirect, app, PasteServer, error
from oauth2client.client import OAuth2WebServerFlow,flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from beaker.middleware import SessionMiddleware
from query_comprehension import query_comprehension, evaluate
from spellcheck import SpellCheck

import MySQLdb
import redis


# *********************** START Redis DB *******************************
db = redis.Redis(host='localhost')

# add element to db set with score update
def update_db(table, value, score, increment = False):
    if(increment):
        # get current score and increase by score
        # if it doesn't exist, create it 
        db.zincrby(table,value,score)

    else:
        # simply update score for value in table 
        # if it doesn't exist, create it
        db.zadd(table,value,score)

# get list of elements from db
def get_db_data(table, limit, desc=False, include_score=False):
    if desc:
       val = db.zrevrange(table,0,limit,withscores=include_score)
    else:
       val = db.zrange(table,0,limit,withscores=include_score)
    return val
# ************************ END Redis DB ********************************


# ******************** START Session Config ****************************
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': './data',
    'session.auto': True
}
app = SessionMiddleware(app(), session_opts)
# ********************* END Session Config *****************************


# ************************* START MySQL DB *****************************
# Setup database connection
def get_connection():
    return MySQLdb.connect(host = "comet-mysql-east1.cxtfibfzhdya.us-east-1.rds.amazonaws.com",
                    user = "cometDev", passwd= "mycometdev", db = "cometDev", port=3306)

# Control word search
def check_db(word,current_session,conn):
    word_id = get_word_id(word,conn)
    if word_id == -1:
        return False
    doc_ids = lookup_invereted_index(word_id,conn)
    if not doc_ids:
        return False
    documentsinfo = get_document(doc_ids,conn)
    if not documentsinfo:
        return False
    # Now store somewhere relative to the session
    pickledInfo = pickle.dumps(documentsinfo)
    return store_results(pickledInfo, current_session.id, len(documentsinfo),conn)

# gets the word id from lexicon
def get_word_id(word,conn):
    c = conn.cursor()
    try:
        c.execute('''select id from lexicon where word=%s''', (word,))
        if not c.rowcount:
            # no word found
            print "ERROR: The word {0} doesn't exist in the lexicon".format(word)
            return -1
        result = c.fetchone()
        return result[0]
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to get word id for {0}".format(word)
        return -1

# gets all docids from inverted index given a word
def lookup_invereted_index(wordid,conn):
    c = conn.cursor()
    try:
        c.execute('''select distinct docid from invertedIndex where wordid=%s''', (wordid,))
        if not c.rowcount:
            # no docids found
            print "ERROR: The wordid {0} doesn't exist in invereted index".format(wordid)
            return None
        results = c.fetchall()
        return [int(result[0]) for result in results]
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to get doc ids for {0}".format(wordid)
        return None

def get_document(docids,conn):
    c = conn.cursor()
    try:
        sql='''select docid, url, title, description, rank from documentIndex right join pagerank on id=docid  WHERE id IN (%s) order by rank desc''' 
        in_p=', '.join(map(lambda x: '%s', docids))
        sql = sql % in_p
        print sql, docids
        c.execute(sql, docids)
        if not c.rowcount:
            # no documentinfo found
            print "ERROR: document information not found"
            return None
        results = c.fetchall()
        return [(result[0],result[1],result[2],result[3],result[4]) for result in results]
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to resolve docids"
        return None

# Store pickled search results
def store_results(results, sessionkey,totalNum,conn):
    c = conn.cursor()
    try:
        c.execute('''select sessionID from searchResults where sessionID = %s''', (sessionkey,))
        if c.rowcount:
            c.execute('''update searchResults set searchResult = %s, totalNum = %s  where sessionID = %s''', (results,totalNum,sessionkey,))
        else:
            c.execute('''insert into searchResults(sessionID, searchResult,totalNum) values(%s,%s,%s) ''', (sessionkey,results,totalNum))
        conn.commit()
        return True
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Could not save search results"
        return False

# get pickled search results
def get_results(sessionkey,conn):
    c = conn.cursor()
    try:
        c.execute('''select searchResult,totalNum from searchResults where sessionID = %s''', (sessionkey,))
        if not c.rowcount:
            # no searchResults found
            print "ERROR: document information not found"
            return None
        result = c.fetchone()
        return result[0], result[1]
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to get search Results"
        return None
# ************************** END MySQL DB ******************************


# ******************* START Helper Functions ***************************
def handle_search_words(phrase, current_session,conn):
    """ 
    returns multiple lists and dictionary
    top_words: top 20 most searched words as a list
    insertion_order_list: words in current search phrase as a list
    calculated: distinct words in current phrase with frequency as dictionary
    """
    # Error Checking: Valid Phrase
    if not isinstance(phrase,str):
        print "Error: Invalid search phrase"
        return False
    
    #initialize empty top words  and recent queries list
    top_words = []
    recent_queries = []

    # split search query into list of words
    words = re.sub("[^\w]"," ",phrase.lower()).split()
    
    # Modify User session cache if user is logged in
    if current_session['user']:
        # add query to user's query cache
        table = '{0}:{1}'.format('query_cache',current_session['user']['email'])        
        update_db(table=table,value=phrase,score=float(time.time()))
        
        # get user's recent queries
        recent_queries = get_recent_queries(current_session)

        # add words to user's word cache
        table = '{0}:{1}'.format('word_cache',current_session['user']['email'])
        for word in words:
            update_db(table=table,value=word,score=1,increment=True)
        
        # get user's most searched words
        top_words = get_top_words(current_session)
        
    # get current query word list in order
    insertion_order_list = get_word_list(words)

    # get word count
    word_count = calculate(phrase)

    if check_db(words[0],current_session,conn):
        results = paginate_search_results(1,current_session,conn)
    else:
        results = None

    
    return (top_words, recent_queries, insertion_order_list, word_count, results)


def get_recent_queries(current_session):
    """ Sorts the user's query cache db and returns the 10 most recent searches """
    table = '{0}:{1}'.format('query_cache',current_session['user']['email'])
    return get_db_data(table = table, limit = 9, desc=True)


def get_top_words(current_session):
    """ Sorts the user's word cache and returns the 10 most searched words """    
    table = '{0}:{1}'.format('word_cache',current_session['user']['email'])
    return get_db_data(table = table, limit = 9, desc=True, include_score=True)


def get_word_list(words):
    l = []
    for word in words:
        word = word.lower()
        if word not in l:
            l.append(word)
    return l


#Returns list of words without whitespace and all lowercase
def calculate(inputText):
    wordList = re.sub("[^\w]", " ",  inputText).split()
    storedData={}
    for word in wordList:
        word = word.lower()
        if word in storedData:
            storedData[word]+= 1
        else:
            storedData[word] = 1
    return storedData


# paginate search results and return at most n results
def paginate_search_results(page,current_session,conn):
    N = 5 #number of links per page
    page = int(page)
    pickled_results,total_num = get_results(current_session.id,conn)
    results = pickle.loads(pickled_results)
    total_pages = int(math.ceil(float(total_num)/N))
    start_index = (page-1)*N
    end_index = (page*N) if (page*N) < total_num else total_num
    return results[start_index:end_index], total_pages, page


def sign_in():
    flow = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri='http://ec2-34-227-189-125.compute-1.amazonaws.com')
    uri = flow.step1_get_authorize_url()
    redirect(str(uri))


def sign_out(current_session):
    current_session.invalidate()
    redirect("/")


def handle_redirect(code, current_session):
    credential = get_credentials(code)

    #Handle error in getting user info
    if credential.invalid:
        print "Error: Invalid Credential"
        return False

    # No Errors with getting user info
    current_session['user'] = retrieve_user_data(credential)
    redirect("/")

def get_credentials(code):
    flow = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri='http://ec2-34-227-189-125.compute-1.amazonaws.com')
    return flow.step2_exchange(code)

def retrieve_user_data(credential):
    http = httplib2.Http()
    http = credential.authorize(http)
    # Get user {email, name, family_name, given_name, picture, id, link, verified_email}
    users_service = build('oauth2', 'v2', http=http)
    user_document = users_service.userinfo().get().execute()
    user_document['link'] = None
    return user_document
# *********************** END Helper Functions *************************


# ******************** START Index Route Handling **********************
@route('/')
def show_index(): 
    """ Returns the index search page """
    # set up session variable
    current_session = request.environ.get('beaker.session')
    #Initialize user in session if not done already
    if 'user' not in current_session:
        current_session['user'] = None
	
    if bool(request.query.keywords):
        search_query = request.query.getall("keywords")
        result = query_comprehension(search_query[0])
        math_equation = tuple()
        if isinstance(result, str) or result == None:
            math_equation = (0, result)
        else:
            math_equation = (1, result)
        print math_equation
        if math_equation[0] == 1:
            return template('interpretor', 
            userData = current_session['user'],
            math_eq = search_query[0] + ' is ' + str(result),
	    )
	elif math_equation[0] == 0:
            conn = get_connection()
	    top_words, recent_queries,insertion_order_list,calculated,rs = handle_search_words(search_query[0],current_session,conn)
	    conn.close()
		
		#for spell checking
	    listOfWords = re.sub("[^\w]"," ",search_query[0].lower()).split()
	    spellChecker = []
		#spellcheck every word in query
	    for the_word in listOfWords:
	        spellChecker.append(SpellCheck(the_word))
			
		spellCheckedQuery = str(spellChecker[0])
		for i in range (1,len(spellChecker)):
			spellCheckedQuery = str(spellCheckedQuery) + ' ' + str(spellChecker[i])
			
	    return template('results', 
	    	insertion_order_list = insertion_order_list, 
    		calculated = calculated,
                top_words=top_words,
	    	recent_queries = recent_queries,
    		search_query=search_query[0],
                userData = current_session['user'],
	    	results = rs,
		spellChecked = spellCheckedQuery
		)

    elif bool(request.query.page):
        page_num = search_query = request.query.getall("page")
        conn = get_connection()
        results = paginate_search_results(page_num[0],current_session,conn)
        conn.close()
        return template('paginate', results=results)

    elif bool(request.query.signin):
        #redirect to google authorization server
        sign_in()
    
    elif bool(request.query.signout):
        #delete session and return to index page
        sign_out(current_session)

    elif bool(request.query.code):
        #handle redirect and get credentials from google apis
        code = request.query.get('code', '')
        handle_redirect(code, current_session)

    else:
        # Handle all other get scenarios
        return template('index', userData = current_session['user'])
# ********************* END Index Route Handling ***********************


# *********************** START Error Routes ***************************
@error(404)
def error404(error):
    return template('error404')
# ************************* END Error Routes ***************************


# ********************** START Static Routes ***************************
@route('/css/<filepath:path>')
def get_css(filepath):
    """ Returns css files """
    return static_file(filepath, root="public/css/")

@route('/js/<filepath:re:.*\.js>')
def get_js(filepath):
    """ Returns javascript files """
    return static_file(filepath, root="public/js/")

@route('/fonts/<filepath:path>')
def get_font(filepath):
    """ Returns fonts files """
    return static_file(filepath, root="public/fonts/")

@route('/img/<filepath:path>')
@route('/image/<filepath:path>')
@route('/images/<filepath:path>')
def get_img(filepath):
    """ Returns images files """
    return static_file(filepath, root="public/img/")
# *********************** END Static Routes ****************************


# ********************* START Crawler Test Routes **********************
@route('/test')
def test():
    """ Returns static index page with links to all other test pages """
    return static_file('index.html', root='public/test_html/')

@route('/test/<filepath:re:.*\.html>')
def pages(filepath):
    """ Returns static html test pages """
    return static_file(filepath, root='public/test_html/')


@route('/testpage')
def test():
    """ Returns static index page with links to all other test pages """
    return static_file('indexed.html', root='public/test_page/')


@route('/testpage/<filepath:re:.*\.html>')
def pages(filepath):
    """ Returns static html test pages """
    return static_file(filepath, root='public/test_page/')
# ********************** END Crawler Test Routes ***********************


# ******************* START Application Server Run *********************
run(app, host='0.0.0.0', port=80, server=PasteServer)
# ******************** END Application Server Run **********************
