from bottle import route, run, static_file,view, get,post, template, request

# store words searched and frequency in dictionary
words_searched = {}

def handleSearchWords(phrase):
    if isinstance(phrase,str):
        words = phrase.split(" ")
        for word in words:
            if word not in words_searched.keys():
                words_searched[word] = 1
            else:
                words_searched[word] += 1
    

# handle search page request
@route('/')
def show_index():
    """ Returns the index search page """
    if bool(request.query):
        my_dict = request.query.getall('keywords')
        return template('results', my_dict)
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