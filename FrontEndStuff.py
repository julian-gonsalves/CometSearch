from bottle import route, run, get, post, request, template
import re

@route('/')
def hello():
	if (request.query):
                result = lookAtText()
		return result
	else:
		return '<form action="/" method="GET"> <input type="text" name="keywords" /> <br> <input type="submit" value="Submit"/></form>'

def lookAtText():
	inputText = request.query.getall('keywords')
	
	data = calculate(inputText[0])

	#return '<html><table border = "1" id = results><th colspan="2">Word</th><th colspan="2">Count</th><tr><td colspan="2">penis</td><td colspan = "2">more penises</td></tr></table> </html>'	
	return template('<p>{{data}}</p>', data=data)
	
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

run(host='localhost', port=8080, debug=True)
