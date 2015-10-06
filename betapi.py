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

import urllib, urllib2
import json
import datetime
import sys
import sys
import datetime
sys.dont_write_bytecode=True

def getSESSIONToken(username, password):

        login_data = urllib.urlencode({
                                        'username' : username,
                                        'password' : password,
                                        'product' : 'exchange',
                                        'url' : 'https://www.betfair.com/Fexchange/login/success/rurl/https://www.betfair.com/Fexchange'
                                        })
        url = "https://identitysso.betfair.com/api/login"
        req = urllib2.Request(url, login_data)
        response = urllib2.urlopen(req)
        the_page = response.read()
        cookie = response.info()['set-cookie']
        idx = cookie.find("ssoid=")+6
        SESSION_TOKEN = cookie[idx:].split(";")[0]

        return SESSION_TOKEN


def getTeamsNamesFromMarketList(market_list):
	for market in market_list:
		if market['marketName']=="Match Odds":
			return [v['runnerName'] for v in market['runners']]
	raise Exception("Team names not found")
class BetApi:

	def __init__(self,username, password, key):
		self.key=key
		self.username = username
		self.password = password
		self.session_token = getSESSIONToken(username, password) 
		self.headers = {'X-Application': key, 'X-Authentication': self.session_token, 'content-type': 'application/json'}
		self.url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
		self.url_account = "https://api.betfair.com/exchange/account/json-rpc/v1"
		self.cache = {}

	def setLog(self,log):
		self.log = log

	def flushCache(self):
		self.cache={}

	def getAccountFunds(self):
                req = {  u'id'          : 1,
                        u'jsonrpc'      : u'2.0',
                        u'method'       : u'AccountAPING/v1.0/getAccountFunds',
                        }

                response = self.callAccountApiNG(req)
		money = float(response['availableToBetBalance'])
		return money

	def executeBet(self, market_id, runner_id, volume, lim_price, system_username):
		order_side = "BACK"
		if volume<0:
			order_side="LAY"
		volume = abs(volume)
		volume = round(volume,2)
		w=open("/home/"+system_username+"/adabet/actual_bets.txt","a")
		if abs(volume)>2:
			w.write("MOCK, EXECUTING BET: "+str(volume)+"@"+str(lim_price)+" (LIM) to "+str(market_id)+" "+str(runner_id)+"\n")
			req = {
				"jsonrpc": "2.0",
				"method": "SportsAPING/v1.0/placeOrders",
				"params": {
				    "marketId": str(market_id),
				    "instructions": [
					{
					    "selectionId": str(runner_id),
					    "side": order_side,
					    "orderType": "LIMIT",
					    "limitOrder": {
						"size": str(volume),
						"price": str(lim_price),
						"persistenceType": "LAPSE"
					    }
					}
				    ]
				},
				"id": 1
			    }
			result = self.callApiNG(req)
			w.write("\nRequest: "+str(req)+"\n----------------------\n")
			w.write("\nResult: "+str(result)+"\n----------------\n")

		else:
			w.write("BET TOO SMALL <2 pounds): "+str(volume)+"@"+str(lim_price)+" (LIM) to "+str(market_id)+" "+str(runner_id)+"\n")
		return False
		
	def listEvents(self, hours):
		event_list = self.getListOfEvents(hours)  
		events_ids = [v['event']['id'] for v in event_list]
		events_names = [v['event']['name'] for v in event_list]
		events_dates = [v['event']['openDate'] for v in event_list]
		return zip(events_ids,events_names,events_dates)
		
	def selectEvent(self,event_id):
		self.flushCache()
		self.event_id = event_id 
		market_list = self.getMarketsForEvent(event_id)
		self.homeTeam, self.awayTeam , self.drawTeam= getTeamsNamesFromMarketList(market_list)
		self.homeTeam=self.homeTeam
		self.awayTeam=self.awayTeam
		self.markets_name_to_id = {}
		self.runners_id_to_name = {}
		self.market_runner_name_to_id = {}
		for elem in market_list:
			self.markets_name_to_id[elem['marketName']]=elem['marketId']
			self.market_runner_name_to_id[elem['marketName']]={} 
			for runner in elem['runners']:
				self.runners_id_to_name[runner['selectionId']]=runner['runnerName']
				self.market_runner_name_to_id[elem['marketName']][runner['runnerName']]=runner['selectionId']
		return self.homeTeam, self.awayTeam
	
	def marketRunnerNameToId(self,market_name,runner_name):
		return self.market_runner_name_to_id[market_name][runner_name]

	def marketRunnerNameToId(self, market_name, runner_name):
		return self.market_runner_name_to_id[market_name][runner_name]

        def market_main(self):
		cache_key = 'market_main'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Match Odds'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Match Odds']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id
        def market_Full_Time(self):
		cache_key = 'market_Full_Time'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Match Odds'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Match Odds']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Half_Time(self):
		cache_key = 'market_Half_Time'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Half Time'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Half Time']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_CorrectScore(self):
		cache_key = 'market_CorrectScore'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Correct Score'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Correct Score']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_0_5(self):
		cache_key = 'market_Over_Under_0_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 0.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 0.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_1_5(self):
		cache_key = 'market_Over_Under_1_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 1.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 1.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_2_5(self):
		cache_key = 'market_Over_Under_2_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 2.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 2.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_3_5(self):
		cache_key = 'market_Over_Under_3_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 3.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 3.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_4_5(self):
		cache_key = 'market_Over_Under_4_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 4.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 4.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_5_5(self):
		cache_key = 'market_Over_Under_5_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 5.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 5.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_6_5(self):
		cache_key = 'market_Over_Under_6_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 6.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 6.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_7_5(self):
		cache_key = 'market_Over_Under_7_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 7.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 7.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Over_Under_8_5(self):
		cache_key = 'market_Over_Under_8_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Over/Under 8.5 Goals'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Over/Under 8.5 Goals']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Half_Time_Over_Under_0_5(self):
		cache_key = 'market_Half_Time_Over_Under_0_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['First Half Goals 0.5'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['First Half Goals 0.5']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Half_Time_Over_Under_1_5(self):
		cache_key = 'market_Half_Time_Over_Under_1_5'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['First Half Goals 1.5'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['First Half Goals 1.5']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_HT_FT(self):
		cache_key = 'market_HT_FT'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Half Time/Full Time'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Half Time/Full Time']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Half_Time_Score(self):
		cache_key = 'market_Half_Time_Score'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Half Time Score'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Half Time Score']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_CorrectScore2Home(self):
		cache_key = 'market_CorrectScore2Home'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Correct Score 2 Home'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Correct Score 2 Home']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_CorrectScore2Away(self):
		cache_key = 'market_CorrectScore2Away'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Correct Score 2 Away'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Correct Score 2 Away']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_BothTeamsToScore(self):
		cache_key = 'market_BothTeamsToScore'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Both teams to Score?'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Both teams to Score?']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_First_Goal(self):
		cache_key = 'market_First_Goal'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['Next Goal'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['Next Goal']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
        def market_Draw_No_Bet(self):
		cache_key = 'market_Draw_No_Bet'
		if cache_key in self.cache:
			return self.cache[cache_key]
		odds_raw = self.getOddsForMarket(self.markets_name_to_id['DRAW NO BET'])
		odds = self.parseOddsFromDict(odds_raw,self.runners_id_to_name)
		market_id=self.markets_name_to_id['DRAW NO BET']
		self.cache[cache_key]=(odds, market_id)
		return odds, market_id 
	def getOddsForMarket(self,market_id):
		req = {  u'id'          : 1,
			u'jsonrpc'      : u'2.0',
			u'method'       : u'SportsAPING/v1.0/listMarketBook',
			u'params'       : {
						u'marketIds': [market_id],
						u'priceProjection' : {
									u'priceData':[u'EX_BEST_OFFERS']
									}
					}
			}

		return self.callApiNG(req)

	def getListOfEvents(self, hours):
		now = datetime.datetime.utcnow()
		endtime = now + datetime.timedelta(hours=hours)
		now = now.strftime('%Y-%m-%dT%H:%M:%SZ')
		endtime = endtime.strftime('%Y-%m-%dT%H:%M:%SZ')
		req = { u'id'          : 1,
			u'jsonrpc'      : u'2.0',
			u'method'       : u'SportsAPING/v1.0/listEvents',
			u'params'       : {
						u'filter':
						{
							u'eventTypeIds': [u'1'],
							u'inplay': False,
							u'marketStartTime':{
									'from':  now,
									'to':  endtime,
									   }
						},
					}
			}

		return self.callApiNG(req)

	def getMarketsForEvent(self,events_id):
		req =  { u'id'          : 1,
			u'jsonrpc'      : u'2.0',
			u'method'       : u'SportsAPING/v1.0/listMarketCatalogue',
			u'params'       : {
				u'filter':
				{
					u'eventTypeIds': [u'1'],
					u'eventIds' : [events_id]
				},
					u'maxResults'   : u'1000',
					u'marketProjection': [u'RUNNER_METADATA'],
				}
			}
		return self.callApiNG(req)

	def callApiNG(self,req_dict):
		encoder = json.JSONEncoder()
		jsonrpc_req = encoder.encode(req_dict)
		req = urllib2.Request(self.url, jsonrpc_req, self.headers)
		response = urllib2.urlopen(req).read()
		response_loads = json.loads(response)
		try:
			results = response_loads['result']
			return results
		except:
			raise Exception( 'Exception from API-NG '+str(response_loads))

	def callAccountApiNG(self,req_dict):
		encoder = json.JSONEncoder()
		jsonrpc_req = encoder.encode(req_dict)
		req = urllib2.Request(self.url_account, jsonrpc_req, self.headers)
		response = urllib2.urlopen(req).read()
		response_loads = json.loads(response)
		try:
			results = response_loads['result']
			return results
		except:
			raise Exception( 'Exception from API-NG '+str(response_loads))

	def parseOddsFromDict(self,data,runners_id_to_name):
		parsed = []
		data = [v for v in data[0]['runners']]
		odds = {}
		for d in data:
			odds[d['selectionId']]=[]
			for back,lay in zip(d['ex']['availableToBack'],d['ex']['availableToLay']):
				odds[d['selectionId']].append((back['price'],back['size']))
				odds[d['selectionId']].append((lay['price'],-lay['size']))
		odds_keys = odds.keys()
		for k in odds_keys:
			odds[runners_id_to_name[k]] = odds.pop(k)
		return odds



