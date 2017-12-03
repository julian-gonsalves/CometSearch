import ast
import operator as op
import sys
import math
import astor

operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor, ast.USub: op.neg}
ops = {"*", "+", " ", "-", "/", "\'", "\""}
origin = ""

def query_comprehension(input):
	global origin
	origin = input
        input = input.strip()

	if input.find('pi') != -1:
		input = input.replace('pi', str(math.pi))

	if input.find('e') != -1:
		input = input.replace('e', str(math.e))
        if input[0] in ops and input[0] != "-":
            return origin
	try:
		return evaluate(ast.parse(input, mode='eval').body)
	except(SyntaxError, TypeError):
		return origin

def evaluate(expression):
	
	try:
		if isinstance(expression, ast.Num):
			return expression.n
		elif isinstance(expression, ast.Call):			
			temporaryCall = astor.dump(expression.func)
			argument = ""
			if astor.dump(expression.args).find("left") != -1:
				argument = operators[type(expression.args[0].op)](evaluate(expression.args[0].left), evaluate(expression.args[0].right))
			else:
				argument = astor.dump(expression.args)[7:]
				argument = argument[:-2]			
                        print temporaryCall[0]
                        print temporaryCall[temporaryCall.find("cos") - 1]
			if temporaryCall.find("cos") != -1 and (temporaryCall[temporaryCall.find("cos") - 1] in ops or (temporaryCall[temporaryCall.find("cos")] == 0)):
				converted_val = math.cos(float(argument))
				return evaluate(ast.Num(converted_val))
			elif temporaryCall.find("sin") != -1 and (temporaryCall[temporaryCall.find("sin") - 1] in ops or (temporaryCall[temporaryCall.find("sin")] == 0)):
				converted_val = math.sin(float(argument))
				return evaluate(ast.Num(converted_val))
			elif temporaryCall.find("tan") != -1 and (temporaryCall[temporaryCall.find("tan") - 1] in ops or (temporaryCall[temporaryCall.find("tan")] == 0)):
				converted_val = math.tan(float(argument))
				return evaluate(ast.Num(converted_val))
                        elif temporaryCall.find("ln") != -1 and (temporaryCall[temporaryCall.find("ln") - 1] in ops or (temporaryCall[temporaryCall.find("ln")] == 0)):
                                converted_val = math.log(float(argument))
                                return evaluate(ast.Num(converted_val))
                        elif temporaryCall.find("log") != -1 and (temporaryCall[temporaryCall.find("log") - 1] in ops or (temporaryCall[temporaryCall.find("log")] == 0)):
                                converted_val = math.log10(float(argument))
                                return evaluate(ast.Num(converted_val))
                        else:
                            return origin
		elif isinstance(expression, ast.BinOp):
			return operators[type(expression.op)](evaluate(expression.left), evaluate(expression.right))
		elif isinstance(expression, ast.UnaryOp):
			return operators[type(expression.op)](evaluate(expression.operand))

	except(TypeError, ValueError):
		return origin


if __name__ == "__main__":
	result = query_comprehension(str(sys.argv[1]))
	if isinstance(result, str):
		print (0, result)
	else:
		print (1, result)
