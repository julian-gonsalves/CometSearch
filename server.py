import operator, re
from bottle import route, run, static_file,view, get,post, template, request

# store words searched and frequency in dictionary
words_searched = {}

def get_top_words():
    """ Sorts the words_searched dictionary and returns the 20 most searched words """
    # Check if words_searched contains anything
    if not bool(words_searched):
        return None
    else:
        most_searched = {}
        #print sorted(words_searched.items(),key=operator.itemgetter(1),reverse=True)
        return [(word,freq) for (word,freq) in sorted(words_searched.items(),key=operator.itemgetter(1), reverse=True)][:20]

def handleSearchWords(phrase):
    """ Adds each word in phrase to a search word cache and outputs top 20 most searched words """
    if isinstance(phrase,str):
        words = phrase.lower().split(" ")
        for word in words:
            if word not in words_searched.keys():
                words_searched[word] = 1
            else:
                words_searched[word] += 1
    return get_top_words()

	
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
	
# handle search page request
@route('/')
def show_index(): 
    """ Returns the index search page """
    if bool(request.query):
        search_query = request.query.getall('keywords')
        top_words = handleSearchWords(search_query[0])
	insertionOrderList = re.sub("[^\w]", " ",  search_query[0]).split()
	theList = []
        for word in insertionOrderList:
            if word not in theList:
        	    theList.append(word)
        calculated = calculate(search_query[0])
        return template('results', insertionOrderList = theList, calculated = calculated,top_words=top_words,search_query=search_query[0])
    else:
        return template('index')
	
		
# handle static file requests
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


# return test pages for crawler
@route('/test')
def test():
    """ Returns static index page with links to all other test pages """
    return static_file('index.html', root='public/test_html/')

@route('/test/<filepath:re:.*\.html>')
def pages(filepath):
    """ Returns static html test pages """
    return static_file(filepath, root='public/test_html/')


# run
run(host='localhost',port=8080,debug=True)
