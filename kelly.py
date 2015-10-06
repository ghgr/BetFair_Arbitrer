"""
The MIT License (MIT)

Copyright (c) 2015 Eduardo Pena Vina

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import numpy as np
import copy
from operator import itemgetter

def int_o_db(odds,bet):
	odds = filter(lambda x: np.sign(x[1])==np.sign(bet), odds)
	
	amIBacking = (bet>0)
	odds =  sorted(odds, key=itemgetter(0), reverse=amIBacking)


	result=0
	rest_bet=abs(bet)
	for o,v in odds:
		v=abs(v)
		result+=o*min(v,rest_bet)
		rest_bet-=v
		if rest_bet<=0:
			break
	if rest_bet>0 and bet<0:
		return -999999
	return result*np.sign(bet)

def r_func(bets,odds,money,probs,fee,previous_E):
	E=[]
	for i in range(len(bets)):
		E.append(1.0/money * int_o_db(odds[i],bets[i]) - sum(bets)*1.0/money)	
	E=np.array(E)+np.array(previous_E)
	new_E = copy.copy(E) 
	E[E>0]*=(1.0-fee)
	E+=1
	p=np.array(probs)
	r =np.prod(E**p)
	if np.isnan(r):
		r=-9999999
	return [r,new_E]
	
def kelly(odds,money,probs,fee,previous_E):
	import scipy.optimize
	func1 = lambda bets,odds,money,probs,fee,previous_E: -r_func(bets,odds,money,probs,fee,previous_E)[0]
	x0 = np.zeros(len(odds))
	return scipy.optimize.fmin(func1,x0,args=(odds,money,probs,fee,previous_E),disp=False)


if __name__=="__main__":
	oh = [
		(8.4,85),
		(8.2,70),
		(7.6,26),
		(8.8,-14),
		(9.2,-79),
		(9.4,-19),
	      ]
	oa = [
		(1.38,286),
		(1.37,568),
		(1.36,329),
		(1.39,-84),
		(1.4,-357),
		(1.41,-582),
	      ]
	od = [
		(5.8,37),
		(5.9,63),
		(6,87),
		(6.4,-52),
		(6.6,-19),
		(6.8,-177),
	      ]

	ph = 0.73
	pa = 0.12
	pd = 0.15
	money = 1
	fee = 0.05

	odds = [oh,od,oa]
	probs = [ph,pd,pa]

	last_E=np.zeros(len(odds))
	sumv = np.zeros(3)
	for _ in range(20):
		bet_vector=kelly(odds,money,probs,fee,last_E)
		sumv+=bet_vector
		r,last_E=r_func(bet_vector,odds,money,probs,fee,last_E)
		print r,last_E, bet_vector, r_func(sumv,odds,money,probs,fee,[0,0,0])[0]

