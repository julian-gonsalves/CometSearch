from nltk.metrics import edit_distance
import sys
import enchant

def SpellCheck(word):
	dict_name = 'en_GB'
	max_dist = 3
	spell = enchant.Dict(dict_name)
	
	if spell.check(word):
		return word
	
	suggestion = spell.suggest(word)
	print suggestion
	
	if len(suggestion) > 0 and edit_distance(word, suggestion[0]) <= max_dist:
		return suggestion[0]
	else:
		return word

def autoComplete(sequence):
	dict_name = 'en_GB'
	max_dist = 3
	spell = enchant.Dict(dict_name)
	print dir(spell)
	print spell
	
	"""for word in spell:
		if word.find(sequence)!= -1:
			return word"""
	
if __name__ == "__main__":
	print SpellCheck(sys.argv[1])
	print autoComplete(sys.argv[1])
