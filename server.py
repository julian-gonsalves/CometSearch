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
def check_db(words,current_session,conn,qid):
    if get_results(current_session.id,conn,qid):
        return True
    #Get all word ids from lexicon
    word_ids = get_word_id(words,conn)
    if word_ids == -1:
        return False
    # Get all info from hitlist where word in word ids
    docs = get_document_info(word_ids,conn)
    if not docs:
        return False
    # Calculate relevance ranking
    maxrr,doc_relevance = relevance_ranking(docs,word_ids)
    maxqr,doc_quality = get_document_rankings(conn,docs.keys())
    # Calculate total rankings, normalize and sort
    for i in range(len(doc_quality)):
        xx = 0.1*(doc_quality[i][4]/max([maxqr,1])) + 0.9*(doc_relevance[doc_quality[i][0]]/max([maxrr,1]))
        doc_quality[i] = (doc_quality[i][0],doc_quality[i][1],doc_quality[i][2],doc_quality[i][3],xx)
    
    documentsinfo = sorted(doc_quality, key=lambda x: x[4],reverse=True)
    
    # Now store somewhere relative to the session
    pickledInfo = pickle.dumps(documentsinfo)
    return store_results(pickledInfo, current_session.id, len(documentsinfo),conn,qid)

# gets the word id from lexicon
def get_word_id(words,conn):
    c = conn.cursor()
    try:
        sql='''select id,word from lexicon  WHERE word IN (%s)''' 
        in_p=', '.join(map(lambda x: '%s', words))
        sql = sql % in_p
       # print sql, words
        c.execute(sql, words)
        if not c.rowcount:
            # no word found
            print "ERROR: word not found"
            return -1
        results = c.fetchall()
        return [result[0] for result in results]
    except MySQLdb.Error as e:
        print "An error occurred: ", e.args
        print "ERROR: Unable to get word id for: ", words
        return -1
# get relevant hitlist
def get_document_info(wordids,conn):
    c = conn.cursor()
    try:
        docs = {}
        sql='''select docid,wordid,importance from hitlist WHERE wordid IN (%s)''' 
        in_p=', '.join(map(lambda x: '%s', wordids))
        sql = sql % in_p
        #print sql, docids
        c.execute(sql, wordids)
        if not c.rowcount:
            # no documentinfo found
            print "ERROR: document information not found"
            return None
        results = c.fetchall()
        for result in results:
            doc_id = result[0]
            word_id = result[1]
            importance = result[2]
            if doc_id not in docs:
                docs[doc_id] = {}
            if word_id not in docs[doc_id]:
                docs[doc_id][word_id] = list()
            docs[doc_id][word_id].append(importance)
        return docs
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to get doc infos"
        return None

# get page rankings
def get_document_rankings(conn, docids):
    c = conn.cursor()
    try:
        docs = []
        sql='''select id,url,title,description,rank from documentIndex left join pagerank on id=docid  WHERE id IN (%s)''' 
        in_p=', '.join(map(lambda x: '%s', docids))
        sql = sql % in_p
        #print sql, docids
        c.execute(sql, docids)
        if not c.rowcount:
            # no documentinfo found
            print "ERROR: document information not found"
            return None
        results = c.fetchall()
        maxqr = 0
        for result in results:
            doc_id = result[0]
            url = result[1]
            title = result[2]
            description = result[3]
            rank = 0 if result[4] == None else float(result[4])
            docs.append((doc_id,url,title,description,rank))
            if rank > maxqr:
                maxqr = rank
        return maxqr,docs
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Unable to get doc infos"
        return None

# Store pickled search results
def store_results(results, sessionkey,totalNum,conn,qid):
    c = conn.cursor()
    try:
        c.execute('''select sessionID from searchResults where sessionID = %s''', (qid,))
        if c.rowcount:
            c.execute('''update searchResults set searchResult = %s, totalNum = %s  where sessionID = %s''', (results,totalNum,qid,))
        else:
            c.execute('''insert into searchResults(sessionID, searchResult,totalNum) values(%s,%s,%s) ''', (qid,results,totalNum))
        conn.commit()
        return True
    except MySQLdb.Error as e:
        print "An error occurred:", e.args
        print "ERROR: Could not save search results"
        return False

# get pickled search results
def get_results(sessionkey,conn,qid):
    c = conn.cursor()
    try:
        c.execute('''select searchResult,totalNum from searchResults where sessionID = %s''', (qid,))
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
    qid = pickle.dumps(sorted(words))
    current_session['qid'] = qid


    # get word count
    word_count = calculate(phrase)

    if check_db(list(words),current_session,conn,qid):
        results = paginate_search_results(1,current_session,conn,qid)
    else:
        results = None

    
    return (top_words, recent_queries, insertion_order_list, word_count, results)

def relevance_ranking(docs,wordids):
    # create time frequency, tf
    maxrr = 0
    tf = {docid:{wordid:0 for wordid in wordids} for docid in docs.keys()}
    for docid in docs.keys():
        for wordid in docs[docid]:
            tf[docid][wordid]=math.sqrt(len(docs[docid][wordid]))
    #create docfreq
    docfreq = {wordid:0 for wordid in wordids}
    for wordid in wordids:
        for doc_id in docs:
            if wordid in docs[doc_id]:
                docfreq[wordid] += 1
    #calculate inverse document function
    idf = {wordid:0 for wordid in wordids}
    for wordid in wordids:
        idf[wordid]=1 + math.log10(float(len(docs))/(docfreq[wordid] +1))
    #Calculate query normalizations
    queryNorm = 1/math.sqrt(sum([idf[wordid]**2 for wordid in list(idf.keys())]))
    #Calculate query coordination factor
    coordf={doc_id:float(len(docs[doc_id]))/len(wordids) for doc_id in docs.keys()}
    #Calculate fieldNorm[doc_id][wordid]
    fieldNorm = {docid:{wordid:0 for wordid in wordids} for docid in docs.keys()}
    maxfieldNorm = 0
    for docid in docs.keys():
        for wordid in docs[docid]:
            fieldNorm[docid][wordid] = sum(docs[docid][wordid])
            if fieldNorm[docid][wordid] > maxfieldNorm:
                maxfieldNorm = fieldNorm[docid][wordid] 
	#Normalize by dividing with max
    for docid in docs.keys():
        for wordid in docs[docid]:
            fieldNorm[docid][wordid] = float(fieldNorm[docid][wordid])/float(maxfieldNorm)
    #Calculate relevance ranking
    r_s={}
    for doc_id in docs:
        total_weight = 0
        for wordid in wordids:
            total_weight += tf[doc_id][wordid]*idf[wordid]*fieldNorm[doc_id][wordid]
        r_s[doc_id] = queryNorm * coordf[doc_id] * total_weight
        if r_s[doc_id] > maxrr:
            maxrr = r_s[doc_id]
    return maxrr,r_s

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
def paginate_search_results(page,current_session,conn,qid=0):
    if not qid:
        qid = current_session['qid']
    N = 5 #number of links per page
    page = int(page)
    pickled_results,total_num = get_results(current_session.id,conn,qid)
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
        conn = get_connection()
        top_words, recent_queries,insertion_order_list,calculated,rs = handle_search_words(search_query[0],current_session,conn)
        conn.close()
	listOfWords = re.sub("[^\w]"," ",search_query[0].lower()).split()
        spellChecker = []
	for the_word in listOfWords:
            spellChecker.append(SpellCheck(the_word))
		
        return template('results', 
            insertion_order_list = insertion_order_list, 
            calculated = calculated,
            top_words=top_words,
            recent_queries = recent_queries,
            search_query=search_query[0],
            userData = current_session['user'],
            results = rs,
	    spellChecked = spellChecker

        )
    
    elif bool(request.query.page):
        page_num = search_query = request.query.getall("page")
        conn = get_connection()
        results = paginate_search_results(page_num[0],current_session,conn,qid)
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
run(app, host='localhost', port=80, server=PasteServer)
# ******************** END Application Server Run **********************
