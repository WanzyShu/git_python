#!/usr/bin/env python



def check(f):
	def wrapper(*args,**kwargs):
		result = f(*args,**kwargs)
		if 'error' in result:
			print    'SB'
		else:
			print  result
	return wrapper


@check
def test(a,b):
	if a == 1:
		return {'error':False}
	else:
		return {'data':a+b}

if __name__ == '__main__':
	test(13,2)