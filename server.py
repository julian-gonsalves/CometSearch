import operator, re, httplib2, time
from bottle import route, run, static_file,view, get,post, template, request, redirect, app
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from beaker.middleware import SessionMiddleware
import redis

# *********************** START Redis DB *******************************
db = redis.Redis(host='localhost')
# db.

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
    'session.cookie_expires': 20000,
    'session.data_dir': './data',
    'session.auto': True
}
app = SessionMiddleware(app(), session_opts)
# ********************* END Session Config *****************************


# ******************* START Helper Functions ***************************
def handle_search_words(phrase, current_session):
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
    
    return (top_words, recent_queries, insertion_order_list, word_count)


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


def sign_in():
    flow = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri='http://localhost:8080')
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
    flow = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email', redirect_uri='http://localhost:8080')
    return flow.step2_exchange(code)

def retrieve_user_data(credential):
    http = httplib2.Http()
    http = credential.authorize(http)
    # Get user {email, name, family_name, given_name, picture, id, link, verified_email}
    users_service = build('oauth2', 'v2', http=http)
    user_document = users_service.userinfo().get().execute()
    user_email = user_document['email']
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
        top_words, recent_queries,insertion_order_list,calculated = handle_search_words(search_query[0], current_session=current_session)
        return template('results', 
            insertion_order_list = insertion_order_list, 
            calculated = calculated,
            top_words=top_words,
            recent_queries = recent_queries,
            search_query=search_query[0],
            userData = current_session['user']
        )

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
# ********************** END Crawler Test Routes ***********************


# ******************* START Application Server Run *********************
run(app=app, host='localhost',port=8080,debug=True)
# ******************** END Application Server Run **********************
