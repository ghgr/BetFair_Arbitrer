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
import sys
sys.dont_write_bytecode=True
import math
import scipy.optimize
import numpy as np

def safeDivision(n,d):
	return np.divide(n,d)

def getValueFromDict(d,v):
        try:
                d[v]
                return d[v]
        except:
                for lim in range(1,100):
                        num_found=0
                        for k in d.keys():
                                if k[:lim]==v[:lim]:
                                        num_found+=1
                                        val = d[k]
                        if num_found==1:
                                return val

        if v.find("/")==-1:
                raise Exception("Unable to find key / Key not unique: "+str(v))
        # If we are here it may be that there are two teams (e.g.: 'Steaua Buch./Pandurii'      

        homeTeam_indice, awayTeam_indice = v.split("/")
        for lim in range(1,100):
                num_found=0
                for k in d.keys():
                        homeTeam_key, awayTeam_key = k.split("/")
                        if homeTeam_key[:lim]==homeTeam_indice[:lim] and awayTeam_key[:lim]==awayTeam_indice[:lim]:
                                num_found+=1
                                val = d[k]
                if num_found==1:
                        return val
        raise Exception("Unable to find key / Key not unique: "+str(v)+" not even after checking for /")


def poisson(l,k):
	return np.power(l,k)*np.exp(-l)*safeDivision(1.0,math.factorial(k))

def getOdds(lambda_home,lambda_away):
	prob_home=0
	prob_away=0
	
	for home_goals in range(200):
		if poisson(lambda_home,home_goals)<1e-15 and home_goals>lambda_home:
			break	
		for away_goals in range(home_goals):
			if poisson(lambda_away,away_goals)<1e-15 and away_goals>lambda_away:
				break
			prob_home += poisson(lambda_home,home_goals)*poisson(lambda_away,away_goals)
	for home_goals in range(200):
		if poisson(lambda_home,home_goals)<1e-15 and home_goals>lambda_home:
			break	
		for away_goals in range(home_goals+1,20):
			if poisson(lambda_away,away_goals)<1e-15 and away_goals>lambda_away:
				break
			prob_away += poisson(lambda_home,home_goals)*poisson(lambda_away,away_goals)

	prob_home = max(prob_home,1e-9)
	prob_away = max(prob_away,1e-9)
	odds_home = np.divide(1.0,prob_home)
	odds_away = np.divide(1.0,prob_away)
	return [odds_home,odds_away]

def getLayBack(odds):
        odds = np.vstack(odds)
        backs = odds[odds[:,1]>0][:,0]
        lays = odds[odds[:,1]<0][:,0]
        return max(backs),min(lays)

def getError(odds_back,odds_lay,odds):
        if odds_back<=odds<=odds_lay:
                return 0.0
        return min(abs(safeDivision(1.0,odds_back)-safeDivision(1.0,odds)),abs(safeDivision(1.0,odds_lay)-safeDivision(1.0,odds)))

def funcWrapper(lambdas,actual_odds_dict, homeTeam, awayTeam):
	if min(lambdas)<=0:
		return 100

	lambda_home_ft,lambda_away_ft  = lambdas
	lambda_home_ht = 0.5 * lambda_home_ft
	lambda_away_ht = 0.5 * lambda_away_ft

	calculated_odds_dict = {
                                'market_Full_Time' : market_Full_Time(lambda_home_ft,lambda_away_ft,homeTeam, awayTeam),
                                'market_Half_Time' : market_Half_Time(lambda_home_ht,lambda_away_ht,homeTeam, awayTeam),
                                'market_CorrectScore' : market_CorrectScore(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_0_5' : market_Over_Under_0_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_1_5' : market_Over_Under_1_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_2_5' : market_Over_Under_2_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_3_5' : market_Over_Under_3_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_4_5' : market_Over_Under_4_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_5_5' : market_Over_Under_5_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_6_5' : market_Over_Under_6_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_7_5' : market_Over_Under_7_5(lambda_home_ft,lambda_away_ft),
                                'market_Over_Under_8_5' : market_Over_Under_8_5(lambda_home_ft,lambda_away_ft),
                                'market_Half_Time_Over_Under_0_5' :market_Half_Time_Over_Under_0_5(lambda_home_ht,lambda_away_ht),
                                'market_Half_Time_Over_Under_1_5' : market_Half_Time_Over_Under_1_5(lambda_home_ht,lambda_away_ht),
                                'market_HT_FT' : market_HT_FT(lambda_home_ht,lambda_away_ht, homeTeam, awayTeam),
                                'market_Half_Time_Score' : market_Half_Time_Score(lambda_home_ht,lambda_away_ht),
                                'market_CorrectScore2Home' : market_CorrectScore2Home(lambda_home_ft, lambda_away_ft),
                                'market_CorrectScore2Away' : market_CorrectScore2Away(lambda_home_ft, lambda_away_ft),
                                'market_BothTeamsToScore' : market_BothTeamsToScore(lambda_home_ft, lambda_away_ft),
                                'market_First_Goal' : market_First_Goal(lambda_home_ft, lambda_away_ft, homeTeam, awayTeam),
                                'market_Draw_No_Bet' : market_draw_no_bet(lambda_home_ft, lambda_away_ft, homeTeam, awayTeam),
				}

	errors = []
	for market_name in actual_odds_dict:
		for runner_name in actual_odds_dict[market_name]:
			actual_odds = actual_odds_dict[market_name][runner_name]
			calculated_odds = getValueFromDict(calculated_odds_dict[market_name],runner_name)
			errors.append(getError(actual_odds[0],actual_odds[1],calculated_odds))

	errors = np.array(errors)
	return errors.dot(errors) 

def getLambdas(odds_dict_raw, homeTeam, awayTeam,log):
	import scipy.optimize

	actual_odds_dict = {}
	for market_name, odds_dict in odds_dict_raw.iteritems():
		tmp={}
		for runner_name,odds_list in odds_dict.iteritems():
			if len(odds_list)==0:
				tmp[runner_name] = [1.0,100000.0]
			else:
				tmp[runner_name] = getLayBack(odds_list)
		actual_odds_dict[market_name] = tmp

	xopt = scipy.optimize.fmin(funcWrapper,[3.0,3.0],args=(actual_odds_dict,homeTeam,awayTeam,),disp=False)
	error = funcWrapper(xopt,actual_odds_dict,homeTeam,awayTeam)
	if error<1e-17:
		log.log("pyodds","\n\nThere is no arbitrage (error=0)")
		raise Exception("There is no arbitrage (error=0)")
	else:
		log.log("pyodds","\n\nError is",error,"so let's proceed")
	return xopt

def getOdds_gt(lim,lambda_home,lambda_away):
	prob=0
	for home_goals in range(200):
		if poisson(lambda_home,home_goals)<1e-15 and home_goals>lambda_home:
			break
		for away_goals in range(200):
			if poisson(lambda_away,away_goals)<1e-15 and away_goals>lambda_away:
				break
			if (home_goals+away_goals)>lim:
				prob += poisson(lambda_home,home_goals)*poisson(lambda_away,away_goals)
	odds = safeDivision(1.0,prob)
	return odds 

def getOdds_lt(lim,lambda_home,lambda_away):
	prob=0
	for home_goals in range(200):
		if poisson(lambda_home,home_goals)<1e-15 and home_goals>lambda_home:
			break
		for away_goals in range(200):
			if poisson(lambda_away,away_goals)<1e-15 and away_goals>lambda_away:
				break
			if (home_goals+away_goals)<lim:
				prob += poisson(lambda_home,home_goals)*poisson(lambda_away,away_goals)
	odds = safeDivision(1.0,prob)
	return odds 

def getOdds_exact(h,a,lambda_home,lambda_away):
	home_goals,away_goals = h,a
	prob=poisson(lambda_home,home_goals)*poisson(lambda_away,away_goals)
	odds = safeDivision(1.0,prob)
	return odds 



def market_CorrectScore(lambda_home_ft,lambda_away_ft, log=False):
	odds = {}
	for home_goals in range(4):
		for away_goals in range(4):
			odds[str(home_goals)+" - "+str(away_goals)] = getOdds_exact(home_goals,away_goals,lambda_home_ft,lambda_away_ft)

	prob_other_home=0
	for home_goals in range(4,200):
                if poisson(lambda_home_ft,home_goals)<1e-15 and home_goals>lambda_home_ft:
                        break 
		#log.log("pyodds",prob_other_home)
		for away_goals in range(home_goals):
			prob_other_home+= (poisson(lambda_home_ft,home_goals)*poisson(lambda_away_ft,away_goals))
	odds['Any Other Home Win']=safeDivision(1.0,prob_other_home)

	prob_other_away=0
	for away_goals in range(4,200):
                if poisson(lambda_away_ft,away_goals)<1e-15 and away_goals>lambda_away_ft:
                        break 
		for home_goals in range(away_goals):
			prob_other_away+= (poisson(lambda_home_ft,home_goals)*poisson(lambda_away_ft,away_goals))
	odds['Any Other Away Win']=safeDivision(1.0,prob_other_away)

	prob_other_draw=0
	for goals in range(4,200):
                if poisson(lambda_home_ft,goals)<1e-15 and goals>lambda_home_ft:
                        break 
                if poisson(lambda_away_ft,goals)<1e-15 and goals>lambda_away_ft:
                        break 
		prob_other_draw+= (poisson(lambda_home_ft,goals)*poisson(lambda_away_ft,goals))
	odds['Any Other Draw']=safeDivision(1.0,prob_other_draw)

	if log:
		log.log("pyodds","\n\nCorrect Score")
		for home_goals in range(4):
			for away_goals in range(4):
				idx = str(home_goals)+" - "+str(away_goals)
				log.log("pyodds","\t",idx,"\t%.2f" % odds[idx])
		log.log("pyodds","\tAny Other Home Win\t%.2f" % odds['Any Other Home Win'])
		log.log("pyodds","\tAny Other Away Win\t%.2f" % odds['Any Other Away Win'])
		log.log("pyodds","\tAny Other Draw\t%.2f" % odds['Any Other Draw'])
	return odds

def _market_Over_Under_n(n,lambda_home_ft,lambda_away_ft,log):
	odds = {}
	odds['Over '+str(n)+' Goals'] = getOdds_gt(n,lambda_home_ft,lambda_away_ft)
	odds['Under '+str(n)+' Goals'] = getOdds_lt(n,lambda_home_ft,lambda_away_ft)
	if log:
		log.log("pyodds","\n\nOver/Under "+str(n)+" Goals")
		log.log("pyodds","\tOver "+str(n)+" Goals\t%.2f" % odds['Over '+str(n)+' Goals'])
		log.log("pyodds","\tUnder "+str(n)+" Goals\t%.2f" % odds['Under '+str(n)+' Goals'])
	return odds

def market_Over_Under_0_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(0.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_1_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(1.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_2_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(2.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_3_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(3.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_4_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(4.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_5_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(5.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_6_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(6.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_7_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(7.5,lambda_home_ft,lambda_away_ft,log=log)
def market_Over_Under_8_5(lambda_home_ft,lambda_away_ft,log=False):
	return _market_Over_Under_n(8.5,lambda_home_ft,lambda_away_ft,log=log)

def market_Half_Time_Over_Under_0_5(lambda_home_ht,lambda_away_ht,log=False):
	if log:
		log.log("pyodds","\t HALF - TIME")
        return _market_Over_Under_n(0.5,lambda_home_ht,lambda_away_ht,log=log)

def market_Half_Time_Over_Under_1_5(lambda_home_ht,lambda_away_ht,log=False):
	if log:
		log.log("pyodds","\t HALF - TIME")
        return _market_Over_Under_n(1.5,lambda_home_ht,lambda_away_ht,log=log)

def market_Full_Time(lambda_home_ft,lambda_away_ft, homeTeam,awayTeam,log=False):
	odds={}
	odds[homeTeam],odds[awayTeam] = getOdds(lambda_home_ft,lambda_away_ft)
	odds_draw = safeDivision(1.0,(1.0-safeDivision(1.0,odds[homeTeam]) - safeDivision(1.0,odds[awayTeam])))
	odds['The Draw']=odds_draw
	if log:
		log.log("pyodds","\n\nFull Time")
		log.log("pyodds",homeTeam,"\t%.2f"%odds[homeTeam])
		log.log("pyodds",awayTeam,"\t%.2f"%odds[awayTeam])
		log.log("pyodds","The Draw\t%.2f"%odds_draw)
	return odds

def market_Half_Time(lambda_home_ht,lambda_away_ht, homeTeam,awayTeam,log=False):
	odds={}
	odds[homeTeam],odds[awayTeam] = getOdds(lambda_home_ht,lambda_away_ht)
	odds_draw = safeDivision(1.0,(1.0-safeDivision(1.0,odds[homeTeam]) - safeDivision(1.0,odds[awayTeam])))
	odds['The Draw']=odds_draw
	if log:
		log.log("pyodds","\n\nHalf Time")
		log.log("pyodds",homeTeam,"\t%.2f"%odds[homeTeam])
		log.log("pyodds",awayTeam,"\t%.2f"%odds[awayTeam])
		log.log("pyodds","The Draw\t%.2f"%odds_draw)
	return odds

def market_HT_FT(lambda_home_ht,lambda_away_ht, homeTeam, awayTeam, log=False):
	odds_draw_draw = 0
	odds_draw_home = 0
	odds_draw_away = 0
	odds_home_draw = 0
	odds_home_home = 0
	odds_home_away = 0
	odds_away_draw = 0
	odds_away_home = 0
	odds_away_away = 0

	for ht1_home_goals in range(200):
                if poisson(lambda_home_ht,ht1_home_goals)<1e-8 and ht1_home_goals>lambda_home_ht:
                        break
		for ht1_away_goals in range(200):
			if poisson(lambda_away_ht,ht1_away_goals)<1e-8 and ht1_away_goals>lambda_away_ht:
				break
			probability_to_be_here_ht1 = (poisson(lambda_home_ht,ht1_home_goals)*poisson(lambda_away_ht,ht1_away_goals))
			for ht2_home_goals in range(200):
				if poisson(lambda_home_ht,ht2_home_goals)<1e-8 and ht2_home_goals>lambda_home_ht:
					break
				for ht2_away_goals in range(200):
					if poisson(lambda_away_ht,ht2_away_goals)<1e-8 and ht2_away_goals>lambda_away_ht:
						break
					probability_to_be_here_ht2 = (poisson(lambda_home_ht,ht2_home_goals)*poisson(lambda_away_ht,ht2_away_goals))
					probability_to_be_here_ft = probability_to_be_here_ht1*probability_to_be_here_ht2
					# Now decide which state is
					if ht1_home_goals==ht1_away_goals:
						if (ht1_home_goals+ht2_home_goals) == (ht1_away_goals+ht2_away_goals):
							odds_draw_draw+=probability_to_be_here_ft
						elif (ht1_home_goals+ht2_home_goals) > (ht1_away_goals+ht2_away_goals):
                                                        odds_draw_home+=probability_to_be_here_ft
                                                else: 
                                                        odds_draw_away+=probability_to_be_here_ft
					elif ht1_home_goals>ht1_away_goals:
                                                if (ht1_home_goals+ht2_home_goals) == (ht1_away_goals+ht2_away_goals):
                                                        odds_home_draw+=probability_to_be_here_ft
                                                elif (ht1_home_goals+ht2_home_goals) > (ht1_away_goals+ht2_away_goals):
                                                        odds_home_home+=probability_to_be_here_ft
                                                else:
                                                        odds_home_away+=probability_to_be_here_ft
                                        else:
                                                if (ht1_home_goals+ht2_home_goals) == (ht1_away_goals+ht2_away_goals):
                                                        odds_away_draw+=probability_to_be_here_ft
                                                elif (ht1_home_goals+ht2_home_goals) > (ht1_away_goals+ht2_away_goals):
                                                        odds_away_home+=probability_to_be_here_ft
                                                else:
                                                        odds_away_away+=probability_to_be_here_ft
	odds_draw_draw = safeDivision(1.0,odds_draw_draw)
	odds_draw_home = safeDivision(1.0,odds_draw_home)
	odds_draw_away = safeDivision(1.0,odds_draw_away)
	odds_home_draw = safeDivision(1.0,odds_home_draw)
	odds_home_home = safeDivision(1.0,odds_home_home)
	odds_home_away = safeDivision(1.0,odds_home_away)
	odds_away_draw = safeDivision(1.0,odds_away_draw)
	odds_away_home = safeDivision(1.0,odds_away_home)
	odds_away_away = safeDivision(1.0,odds_away_away)

	odds = {
		str(homeTeam)+'/'+str(homeTeam): odds_home_home,
		str(homeTeam)+'/Draw': odds_home_draw,
		str(homeTeam)+'/'+str(awayTeam) : odds_home_away,
		'Draw/'+str(homeTeam): odds_draw_home,
		'Draw/Draw': odds_draw_draw,
		'Draw/'+str(awayTeam): odds_draw_away,
		str(awayTeam)+'/'+str(homeTeam): odds_away_home,
		str(awayTeam)+'/Draw': odds_away_draw,
		str(awayTeam)+'/'+str(awayTeam): odds_away_away
		}
                                        
	
	if log:	
		log.log("pyodds","\n\nHalf Time / Full Time")
		log.log("pyodds","\t",homeTeam,"/",homeTeam,": %.2f" % odds_home_home)
		log.log("pyodds","\t",homeTeam,"/The Draw: %.2f" % odds_home_draw)
		log.log("pyodds","\t",homeTeam,"/",awayTeam,": %.2f" % odds_home_away)
		log.log("pyodds","\tThe Draw/",homeTeam,": %.2f" % odds_draw_home)
		log.log("pyodds","\tThe Draw/The Draw: %.2f" % odds_draw_draw)
		log.log("pyodds","\tThe Draw/",awayTeam,": %.2f" % odds_draw_away)
		log.log("pyodds","\t",awayTeam,"/",homeTeam,": %.2f" % odds_away_home)
		log.log("pyodds","\t",awayTeam,"/The Draw: %.2f" % odds_away_draw)
		log.log("pyodds","\t",awayTeam,"/",awayTeam,": %.2f" % odds_away_away)

	
	return odds 
					
def market_Half_Time_Score(lambda_home_ht,lambda_away_ht, log=False):
	odds = {}
	for home_goals in range(3):
		for away_goals in range(3):
			idx = str(home_goals)+" - "+str(away_goals)
			odds[idx]=getOdds_exact(home_goals,away_goals,lambda_home_ht,lambda_away_ht)
	prob_unquoted=0
	for home_goals in range(200):
                if poisson(lambda_home_ht,home_goals)<1e-15 and home_goals>lambda_home_ht:
                        break
		for away_goals in range(200):
			if home_goals<3 and away_goals<3:
				continue

			if poisson(lambda_away_ht,away_goals)<1e-15 and away_goals>lambda_away_ht:
				break

			prob_unquoted += (poisson(lambda_home_ht,home_goals)*poisson(lambda_away_ht,away_goals))	
	odds['Any Unquoted']= safeDivision(1.0,prob_unquoted)

	if log:
		log.log("pyodds","\n\nHalf Time Score")
		for home_goals in range(3):
			for away_goals in range(3):
				idx = str(home_goals)+" - "+str(away_goals)
				log.log("pyodds","\t",idx,"\t%.2f" % odds[idx])
				
		log.log("pyodds","\tAny Unquoted\t%.2f"%odds['Any Unquoted'])
	return odds

def market_CorrectScore2Home(lambda_home_ft, lambda_away_ft, log=False):
	odds = {}
	for home_goals in range(4,8):
		for away_goals in range(3):
			idx = str(home_goals)+" - "+str(away_goals)
			odds[idx]=getOdds_exact(home_goals,away_goals,lambda_home_ft,lambda_away_ft)
	prob_unquoted=0
	for home_goals in range(200):
                if poisson(lambda_home_ft,home_goals)<1e-15 and home_goals>lambda_home_ft:
                        break
		for away_goals in range(200):
			if 4<=home_goals<=7 and 0<=away_goals<=2:
				continue

			if poisson(lambda_away_ft,away_goals)<1e-15 and away_goals>lambda_away_ft:
				break

			prob_unquoted += (poisson(lambda_home_ft,home_goals)*poisson(lambda_away_ft,away_goals))	
	odds['Any Unquoted']= safeDivision(1.0,prob_unquoted)

	if log:
		log.log("pyodds","\n\nCorrect Score 2 Home")
		for home_goals in range(4,8):
			for away_goals in range(3):
				idx = str(home_goals)+" - "+str(away_goals)
				log.log("pyodds","\t",idx,"\t%.2f" % odds[idx])
				
		log.log("pyodds","\tAny Unquoted\t%.2f"%odds['Any Unquoted'])
	return odds

def market_CorrectScore2Away(lambda_home_ft, lambda_away_ft, log=False):
	odds = {}
	for home_goals in range(3):
		for away_goals in range(4,8):
			idx = str(home_goals)+" - "+str(away_goals)
			odds[idx]=getOdds_exact(home_goals,away_goals,lambda_home_ft,lambda_away_ft)
	prob_unquoted=0
	for home_goals in range(200):
                if poisson(lambda_home_ft,home_goals)<1e-15 and home_goals>lambda_home_ft:
                        break
		for away_goals in range(200):
			if 0<=home_goals<=2 and 4<=away_goals<=7:
				continue

			if poisson(lambda_away_ft,away_goals)<1e-15 and away_goals>lambda_away_ft:
				break

			prob_unquoted += (poisson(lambda_home_ft,home_goals)*poisson(lambda_away_ft,away_goals))	
	odds['Any Unquoted']= safeDivision(1.0,prob_unquoted)

	if log:
		log.log("pyodds","\n\nCorrect Score 2 Away")
		for home_goals in range(3):
			for away_goals in range(4,8):
				idx = str(home_goals)+" - "+str(away_goals)
				log.log("pyodds","\t",idx,"\t%.2f" % odds[idx])
				
		log.log("pyodds","\tAny Unquoted\t%.2f"%odds['Any Unquoted'])
	return odds
	
def market_BothTeamsToScore(lambda_home_ft, lambda_away_ft, log=False):
	odds = {}
	prob_score_home = 1.0-poisson(lambda_home_ft,0)	
	prob_score_away = 1.0-poisson(lambda_away_ft,0)	
	
	prob_both_score = prob_score_home*prob_score_away
	odds['Yes'] = safeDivision(1.0,prob_both_score)
	odds['No'] = safeDivision(1.0,(1.0-prob_both_score))
	if log:
		log.log("pyodds","\n\nBoth Teams To Score")
		log.log("pyodds","\tYes\t%.2f" % odds['Yes'])
		log.log("pyodds","\tNo\t%.2f" % odds['No'])
	return odds

def market_First_Goal(lambda_home_ft, lambda_away_ft, homeTeam, awayTeam, log=False):
	ratio_prob = lambda_home_ft*safeDivision(1.0,lambda_away_ft)
	p_no_goal = (poisson(lambda_home_ft,0)*poisson(lambda_away_ft,0))
	# The equation is: p_home + p_away + p_draw = 1 AND ratio_prob = p_home/p_away
	p_away = (1.0 - p_no_goal)/(1.0+ratio_prob)
	p_home = 1.0 - p_away - p_no_goal
	odds = {
		homeTeam : safeDivision(1.0,p_home),
		'No Goal' : safeDivision(1.0,p_no_goal),
		awayTeam : safeDivision(1.0,p_away)
		}
	if log:
		log.log("pyodds","\n\nFIRST GOAL (= NEXT GOAL, since they are time independent")
		log.log("pyodds","\033[93mATTENTION, EXPERIMENTAL!\033[0m")
		log.log("pyodds","\t",homeTeam,"\t%.2f" % odds[homeTeam])
		log.log("pyodds","\tNo Goal\t%.2f" % odds['No Goal'])
		log.log("pyodds","\t",awayTeam,"\t%.2f" % odds[awayTeam])
	return odds

def market_draw_no_bet(lambda_home_ft, lambda_away_ft, homeTeam, awayTeam, log=False):
	odds_home_total,odds_away_total = getOdds(lambda_home_ft, lambda_away_ft)
	# Scale odds to make their inverses sum 1
	factor = safeDivision(1.0,odds_home_total)+safeDivision(1.0,odds_away_total)
	odds = {}
	odds[homeTeam] = odds_home_total*factor
	odds[awayTeam] = odds_away_total*factor
	if log:
		log.log("pyodds","\n\nDRAW NO BET (cancel when draw)")
		log.log("pyodds","\t",homeTeam,"\t%.2f" % odds[homeTeam])
		log.log("pyodds","\t",awayTeam,"\t%.2f" % odds[awayTeam])
	return odds
		

if __name__=="__main__":
	pass
