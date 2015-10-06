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

import betapi
import traceback, operator
from betapi import BetApi
reload(betapi)
import numpy as np
import estimator
reload(estimator)
import sys
sys.dont_write_bytecode=True
import kelly
reload(kelly)
import logmanager
from operator import itemgetter

def getLimOrderValue(odds, volume):
        """ Calculate max price matched (to lay) and min (to back) in order to place a limit order """
        if volume>0: #BACK
                odds_back = odds[odds[:,1]>0]
                odds_back = odds_back[odds_back[:,0].argsort()]
                odds_back = odds_back[::-1]
                odds_back[:,1] = odds_back[:,1].cumsum(axis=0)
                pos = odds_back[:,1]>volume
                lim_value = odds_back[pos][0][0]
        else: # LAY
                odds_lay = odds[odds[:,1]<0]
                odds_lay = odds_lay[odds_lay[:,0].argsort()]
                odds_lay[:,1] = odds_lay[:,1].cumsum(axis=0)
                pos = odds_lay[:,1]<volume
                lim_value = odds_lay[pos][0][0]

        return lim_value

def printCSVLineFromBestBets(best_bets):
	csv_lines=[]
        for best_bet in best_bets:
                event_date = best_bet[0]
                event_name = best_bet[1]
                event_id = str(best_bet[2])
                market_name = str(best_bet[3])
                r_expected = "%.5f" % best_bet[4]
                bet = ""
                for k,v in best_bet[5].iteritems():
                        if abs(v)>0.01:
                                odds = np.array(best_bet[6]['odds_actual'][k])
                                volume = v
                                bet+=k+": "+"%.2f"%volume
                                bet+= " @ %.2f (LIM)" % getLimOrderValue(odds,volume)
                calculated_relevant_odds = ""
                for k,v in best_bet[6]['odds_calculated'].iteritems():
                        calculated_relevant_odds+=k+": "+"%.2f"%v+", "
		actual_odds = str(best_bet[6]['odds_actual']).replace("\n","").replace(" ","")
                market_id = best_bet[6]['market_id']
		money = str(best_bet[7])

        	csv_lines.append(event_date+";"+event_id+";"+event_name+";"+market_id+";"+market_name+";"+bet+";"+calculated_relevant_odds+";"+r_expected+";"+actual_odds+";;;"+money)
	return csv_lines




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

def getDictFromVectors(data,indices):
        res = {}
        for d,i in zip(data,indices):
                res[i]=d
        return res



class Manager:
	def __init__(self,username, password, API_KEY, fee, min_accepted_volume, logs_directory):
		# Setup API
		self.username = username
		self.password = password
		self.API_KEY = API_KEY
		self.fee = fee
		self.min_accepted_volume = min_accepted_volume
		self.logs_directory = logs_directory
		self.betapi = BetApi(self.username, self.password, self.API_KEY)
		self.last_E= { 
			'Full_Time': np.zeros(3),
			'CorrectScore': np.zeros(19),
			'Over_Under_0_5': np.zeros(2),
			'Over_Under_1_5': np.zeros(2),
			'Over_Under_2_5': np.zeros(2),
			'Over_Under_3_5': np.zeros(2),
			'Over_Under_4_5': np.zeros(2),
			'Over_Under_5_5': np.zeros(2),
			'Over_Under_6_5': np.zeros(2),
			'Over_Under_7_5': np.zeros(2),
			'Over_Under_8_5': np.zeros(2),
			'Half_Time_Over_Under_0_5': np.zeros(2),
			'Half_Time_Over_Under_1_5': np.zeros(2),
			'Half_Time': np.zeros(3),
			'HT_FT': np.zeros(9),
			'Half_Time_Score': np.zeros(10),
			'CorrectScore2Home': np.zeros(13),
			'CorrectScore2Away': np.zeros(13),
			'BothTeamsToScore': np.zeros(2),
			'First_Goal': np.zeros(3),
			'Draw_No_Bet': np.zeros(2)
			}
	
	def close(self):
		self.log.close()

	def listEvents(self, hours):
		return self.betapi.listEvents(hours)

	def getCurrentMoney(self):
		return self.betapi.getAccountFunds()

	def selectEvent(self,event_id):
		# Now that we have the event_id, let's create the log manager for this process
		self.log = logmanager.LogManager(self.logs_directory,event_id)
		self.betapi.setLog(self.log)
		self.money = self.betapi.getAccountFunds()

		self.homeTeam, self.awayTeam = self.betapi.selectEvent(event_id)

		self.log.log("manager","Home Team:",self.homeTeam)
		self.log.log("manager","Away Team:",self.awayTeam)
		# Get main odds(to calculate probabilities)
		odds_dict = {}
		try:
			odds_dict['market_Full_Time'] = self.betapi.market_Full_Time()[0]
		except:
			pass
		try:
			odds_dict['market_Half_Time'] = self.betapi.market_Half_Time()[0]
		except:
			pass
		try:
			odds_dict['market_CorrectScore'] = self.betapi.market_CorrectScore()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_0_5'] = self.betapi.market_Over_Under_0_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_1_5'] = self.betapi.market_Over_Under_1_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_2_5'] = self.betapi.market_Over_Under_2_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_3_5'] = self.betapi.market_Over_Under_3_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_4_5'] = self.betapi.market_Over_Under_4_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_5_5'] = self.betapi.market_Over_Under_5_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_6_5'] = self.betapi.market_Over_Under_6_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_7_5'] = self.betapi.market_Over_Under_7_5()[0]
		except:
			pass
		try:
			odds_dict['market_Over_Under_8_5'] = self.betapi.market_Over_Under_8_5()[0]
		except:
			pass
		try:
			odds_dict['market_Half_Time_Over_Under_0_5'] = self.betapi.market_Half_Time_Over_Under_0_5()[0]
		except:
			pass
		try:
			odds_dict['market_Half_Time_Over_Under_1_5'] = self.betapi.market_Half_Time_Over_Under_1_5()[0]
		except:
			pass
		try:
			odds_dict['market_HT_FT'] = self.betapi.market_HT_FT()[0]
		except:
			pass
		try:
			odds_dict['market_Half_Time_Score'] = self.betapi.market_Half_Time_Score()[0]
		except:
			pass
		try:
			odds_dict['market_CorrectScore2Home'] = self.betapi.market_CorrectScore2Home()[0]
		except:
			pass
		try:
			odds_dict['market_CorrectScore2Away'] = self.betapi.market_CorrectScore2Away()[0]
		except:
			pass
		try:
			odds_dict['market_BothTeamsToScore'] = self.betapi.market_BothTeamsToScore()[0]
		except:
			pass
		try:
			odds_dict['market_First_Goal'] = self.betapi.market_First_Goal()[0]
		except:
			pass
		try:
			odds_dict['market_Draw_No_Bet'] = self.betapi.market_Draw_No_Bet()[0]
		except:
			pass



		# Create estimator (calculator of theoretical odds)
		self.estimator = estimator.Estimator(
				odds_dict = odds_dict,
				homeTeam = self.homeTeam,
				awayTeam = self.awayTeam,
				log = self.log
				) 
		self.event_id = event_id

	def executeBet(self, bet, system_username):
		event_date = bet[0]
		event_name = bet[1]
		event_id = str(bet[2])
		market_name = str(bet[3])
		market_id = bet[6]['market_id']
		for k,v in bet[5].iteritems():
			if abs(v)>0.01:
				odds = np.array(bet[6]['odds_actual'][k])
				volume = v
				runner_name = k
				self.betapi.selectEvent(event_id)
				runner_id = self.betapi.marketRunnerNameToId(market_name,runner_name)
				lim_price =  getLimOrderValue(odds,volume)
				self.betapi.executeBet(market_id, runner_id, volume, lim_price, system_username)
		return True

	def getBestBetsForEvent(self,event):

                bets_events_dict={}
		event_name_to_id = {}
		event_name_to_date = {}
                event_id,event_name,event_date = event
		try:
			self.selectEvent(event_id)
			self.log.log("manager","Trying",event_id,"(",event_name,")")
			bets_events_dict[event_name]=self.getBestBetsAcrossAllMarkets()
			event_name_to_id[event_name]=event_id
			event_name_to_date[event_name]=event_date
			self.log.log("manager","DONE")
		except:
			traceback.print_exc()
		# Close all open logs for this event
		self.log.close()
		return bets_events_dict,event_name_to_id,event_name_to_date


	def getBestBetsAcrossAllMarkets(self):
		bets = []
		try:
			optimal_bet, r, info =self.getOptimalBet_Full_Time(pretty_print=True)
			bets.append(['Match Odds',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info = self.getOptimalBet_CorrectScore(pretty_print=True)
			bets.append(['Correct Score',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_7_5(pretty_print=True)
			bets.append(['Over/Under 7.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_8_5(pretty_print=True)
			bets.append(['Over/Under 8.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Half_Time_Over_Under_0_5(pretty_print=True)
			bets.append(['First Half Goals 0.5',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Half_Time_Over_Under_1_5(pretty_print=True)
			bets.append(['First Half Goals 1.5',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Half_Time(pretty_print=True)
			bets.append(['Half Time',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_HT_FT(pretty_print=True)
			bets.append(['Half Time/Full Time',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Half_Time_Score(pretty_print=True)
			bets.append(['Half Time Score',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_CorrectScore2Home(pretty_print=True)
			bets.append(['Correct Score 2 Home',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_CorrectScore2Away(pretty_print=True)
			bets.append(['Correct Score 2 Away',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_BothTeamsToScore(pretty_print=True)
			bets.append(['Both Teams To Score?',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_First_Goal(pretty_print=True)
			bets.append(['Next Goal',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Draw_No_Bet(pretty_print=True)
			bets.append(['DRAW NO BET',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_0_5(pretty_print=True)
			bets.append(['Over/Under 0.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_1_5(pretty_print=True)
			bets.append(['Over/Under 1.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_2_5(pretty_print=True)
			bets.append(['Over/Under 2.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_3_5(pretty_print=True)
			bets.append(['Over/Under 3.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_4_5(pretty_print=True)
			bets.append(['Over/Under 4.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_5_5(pretty_print=True)
			bets.append(['Over/Under 5.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		try:
			optimal_bet, r, info =self.getOptimalBet_Over_Under_6_5(pretty_print=True)
			bets.append(['Over/Under 6.5 Goals',r,optimal_bet,info])
		except:
			self.log.log("manager","\tMarket not found!")
		
		bets = sorted(bets,key=itemgetter(1),reverse=True)
		return bets
	

	

	def _getOptimalBet_generic(self,last_E,estimator_function,betapi_market_function,indices,market_name_human_readable,pretty_print):
		odds_calculated = estimator_function()
		self.log.log("manager","Odds calculated")
		self.log.log("manager",odds_calculated)
		odds_calculated = np.array([ getValueFromDict(odds_calculated, indice) for indice in indices])
			# And get probabilities
		probs_calculated = 1.0/odds_calculated
		self.log.log("manager","Probabilities calculated")
		self.log.log("manager",probs_calculated)

		# Get actual odds for Half Time
		odds_actual, market_id = betapi_market_function()
		self.log.log("manager","Actual odds")
		self.log.log("manager",odds_actual)
		
		odds_actual = np.array([ getValueFromDict(odds_actual, indice) for indice in indices])


		# Apply kelly
		optimal_bet = kelly.kelly(odds_actual, self.money, probs_calculated, self.fee, previous_E=last_E)
		optimal_bet[optimal_bet<self.min_accepted_volume]=0
		r,last_E = kelly.r_func(optimal_bet,odds_actual, self.money, probs_calculated, self.fee, previous_E=last_E)
		optimal_bet_dict = getDictFromVectors(optimal_bet,indices)

		info = { 'odds_calculated' : getDictFromVectors(odds_calculated,indices),
			'odds_actual' : getDictFromVectors(odds_actual,indices),
			'market_id' : market_id }
		if pretty_print:
			self.log.log("manager","Optimal Bet for:",market_name_human_readable)
			for indice,value in zip(indices,optimal_bet):
				self.log.log("manager","\t",indice,":\t$ %.2f"%value)
			self.log.log("manager","Performance: %.3f"%r)
	
		return (optimal_bet_dict,r,info)

	def getOptimalBet_Full_Time(self, pretty_print=True):
		indices = [self.homeTeam,"The Draw",self.awayTeam]
		market_name_human_readable = "Match Odds"
		estimator_function = self.estimator.market_Full_Time
		betapi_market_function = self.betapi.market_Full_Time
		last_E = self.last_E['Match_Odds']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)

	def getOptimalBet_CorrectScore(self, pretty_print=True):
		indices = ['0 - 0','0 - 1','0 - 2','0 - 3','1 - 0','1 - 1','1 - 2','1 - 3','2 - 0','2 - 1','2 - 2','2 - 3','3 - 0','3 - 1','3 - 2','3 - 3',
			'Any Other Away Win', 'Any Other Draw', 'Any Other Home Win']
		market_name_human_readable = "Correct Score"
		estimator_function = self.estimator.market_CorrectScore
		betapi_market_function =  self.betapi.market_CorrectScore 
		last_E = self.last_E['CorrectScore']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)

	def getOptimalBet_Over_Under_0_5(self, pretty_print=True):
		indices = ['Over 0.5 Goals', 'Under 0.5 Goals']
		market_name_human_readable = "Over/Under 0.5 Goals"
		estimator_function = self.estimator.market_Over_Under_0_5
		betapi_market_function =  self.betapi.market_Over_Under_0_5
		last_E = self.last_E['Over_Under_0_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_1_5(self, pretty_print=True):
		indices = ['Over 1.5 Goals', 'Under 1.5 Goals']
		market_name_human_readable = "Over/Under 1.5 Goals"
		estimator_function = self.estimator.market_Over_Under_1_5
		betapi_market_function =  self.betapi.market_Over_Under_1_5
		last_E = self.last_E['Over_Under_1_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_2_5(self, pretty_print=True):
		indices = ['Over 2.5 Goals', 'Under 2.5 Goals']
		market_name_human_readable = "Over/Under 2.5 Goals"
		estimator_function = self.estimator.market_Over_Under_2_5
		betapi_market_function =  self.betapi.market_Over_Under_2_5
		last_E = self.last_E['Over_Under_2_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_3_5(self, pretty_print=True):
		indices = ['Over 3.5 Goals', 'Under 3.5 Goals']
		market_name_human_readable = "Over/Under 3.5 Goals"
		estimator_function = self.estimator.market_Over_Under_3_5
		betapi_market_function =  self.betapi.market_Over_Under_3_5
		last_E = self.last_E['Over_Under_3_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_4_5(self, pretty_print=True):
		indices = ['Over 4.5 Goals', 'Under 4.5 Goals']
		market_name_human_readable = "Over/Under 4.5 Goals"
		estimator_function = self.estimator.market_Over_Under_4_5
		betapi_market_function =  self.betapi.market_Over_Under_4_5
		last_E = self.last_E['Over_Under_4_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_5_5(self, pretty_print=True):
		indices = ['Over 5.5 Goals', 'Under 5.5 Goals']
		market_name_human_readable = "Over/Under 5.5 Goals"
		estimator_function = self.estimator.market_Over_Under_5_5
		betapi_market_function =  self.betapi.market_Over_Under_5_5
		last_E = self.last_E['Over_Under_5_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_6_5(self, pretty_print=True):
		indices = ['Over 6.5 Goals', 'Under 6.5 Goals']
		market_name_human_readable = "Over/Under 6.5 Goals"
		estimator_function = self.estimator.market_Over_Under_6_5
		betapi_market_function =  self.betapi.market_Over_Under_6_5
		last_E = self.last_E['Over_Under_6_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_7_5(self, pretty_print=True):
		indices = ['Over 7.5 Goals', 'Under 7.5 Goals']
		market_name_human_readable = "Over/Under 7.5 Goals"
		estimator_function = self.estimator.market_Over_Under_7_5
		betapi_market_function =  self.betapi.market_Over_Under_7_5
		last_E = self.last_E['Over_Under_7_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Over_Under_8_5(self, pretty_print=True):
		indices = ['Over 8.5 Goals', 'Under 8.5 Goals']
		market_name_human_readable = "Over/Under 8.5 Goals"
		estimator_function = self.estimator.market_Over_Under_8_5
		betapi_market_function =  self.betapi.market_Over_Under_8_5
		last_E = self.last_E['Over_Under_8_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
        def getOptimalBet_Half_Time_Over_Under_0_5(self, pretty_print=True):
		indices = ['Over 0.5 Goals', 'Under 0.5 Goals']
		market_name_human_readable = "First Half Goals 0.5"
		estimator_function = self.estimator.market_Half_Time_Over_Under_0_5
		betapi_market_function =  self.betapi.market_Half_Time_Over_Under_0_5
		last_E = self.last_E['Half_Time_Over_Under_0_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
        def getOptimalBet_Half_Time_Over_Under_1_5(self, pretty_print=True):
		indices = ['Over 1.5 Goals', 'Under 1.5 Goals']
		market_name_human_readable = "First Half Goals 1.5"
		estimator_function = self.estimator.market_Half_Time_Over_Under_1_5
		betapi_market_function =  self.betapi.market_Half_Time_Over_Under_1_5
		last_E = self.last_E['Half_Time_Over_Under_1_5']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Half_Time(self, pretty_print=True):
		indices = [self.homeTeam,"The Draw",self.awayTeam]
		market_name_human_readable = "Half Time Score"
		estimator_function = self.estimator.market_Half_Time
		betapi_market_function = self.betapi.market_Half_Time
		last_E = self.last_E['Half_Time']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_HT_FT(self, pretty_print=True):
		indices = [self.homeTeam+'/'+self.homeTeam,self.homeTeam+'/Draw',self.homeTeam+'/'+self.awayTeam,'Draw/'+self.homeTeam,'Draw/Draw','Draw/'+self.awayTeam,self.awayTeam+'/'+self.homeTeam,self.awayTeam+'/Draw',self.awayTeam+'/'+self.awayTeam]
		market_name_human_readable = "Half Time/Full Time"
		estimator_function = self.estimator.market_HT_FT
		betapi_market_function = self.betapi.market_HT_FT
		last_E = self.last_E['HT_FT']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Half_Time_Score(self, pretty_print=True):
		indices = ['0 - 0','0 - 1','0 - 2','1 - 0','1 - 1','1 - 2','2 - 0','2 - 1','2 - 2','Any Unquoted']
		market_name_human_readable = "Half Time Score"
		estimator_function = self.estimator.market_Half_Time_Score
		betapi_market_function = self.betapi.market_Half_Time_Score
		last_E = self.last_E['Half_Time_Score']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_CorrectScore2Home(self, pretty_print=True):
		indices = ["4 - 0","5 - 0","6 - 0","7 - 0","4 - 1","5 - 1","6 - 1","7 - 1","4 - 2","5 - 2","6 - 2","7 - 2","Any Unquoted"]
		market_name_human_readable = "Correct Score 2 Home"
		estimator_function = self.estimator.market_CorrectScore2Home
		betapi_market_function = self.betapi.market_CorrectScore2Home
		last_E = self.last_E['CorrectScore2Home']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_CorrectScore2Away(self, pretty_print=True):
		indices = ["0 - 4","0 - 5","0 - 6","0 - 7","1 - 4","1 - 5","1 - 6","1 - 7","2 - 4","2 - 5","2 - 6","2 - 7","Any Unquoted"]
		market_name_human_readable = "Correct Score 2 Away"
		estimator_function = self.estimator.market_CorrectScore2Away
		betapi_market_function = self.betapi.market_CorrectScore2Away
		last_E = self.last_E['CorrectScore2Away']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_BothTeamsToScore(self, pretty_print=True):
		indices = ["Yes","No"]
		market_name_human_readable = "Both Teams To Score?"
		estimator_function = self.estimator.market_BothTeamsToScore
		betapi_market_function = self.betapi.market_BothTeamsToScore
		last_E = self.last_E['BothTeamsToScore']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_First_Goal(self, pretty_print=True):
		indices = [self.homeTeam,"No Goal",self.awayTeam]
		market_name_human_readable = "Next Goal"
		estimator_function = self.estimator.market_First_Goal
		betapi_market_function = self.betapi.market_First_Goal
		last_E = self.last_E['First_Goal']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
	def getOptimalBet_Draw_No_Bet(self, pretty_print=True):
		indices = [self.homeTeam,self.awayTeam]
		market_name_human_readable = "DRAW NO BET"
		estimator_function = self.estimator.market_Draw_No_Bet
		betapi_market_function = self.betapi.market_Draw_No_Bet
		last_E = self.last_E['Draw_No_Bet']
		return self._getOptimalBet_generic(last_E, estimator_function,betapi_market_function, indices, market_name_human_readable,pretty_print)
