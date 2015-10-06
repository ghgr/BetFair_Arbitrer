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

import pyodds
reload(pyodds)
import sys
sys.dont_write_bytecode=True
import numpy as np
import pprint

class Estimator:

	def __init__(self,odds_dict, homeTeam, awayTeam,log):

		self.odds = odds_dict

		self.log=log
		self.homeTeam = homeTeam
		self.awayTeam = awayTeam

		# estimate_params
		self.lambda_home_ft, self.lambda_away_ft = pyodds.getLambdas(self.odds, self.homeTeam, self.awayTeam, self.log)
		self.log.log("estimator","Home lambda (FT):", self.lambda_home_ft)
		self.log.log("estimator","Away lambda (FT):", self.lambda_away_ft)

		self.lambda_home_ht = 0.5 * self.lambda_home_ft
		self.lambda_away_ht = 0.5 * self.lambda_away_ft

	def market_Full_Time(self):
		return pyodds.market_Full_Time(self.lambda_home_ft,self.lambda_away_ft, self.homeTeam, self.awayTeam, self.log)
	def market_CorrectScore(self):
		return pyodds.market_CorrectScore(self.lambda_home_ft,self.lambda_away_ft, self.log)
	def market_Over_Under_0_5(self):
		return pyodds.market_Over_Under_0_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_1_5(self):
		return pyodds.market_Over_Under_1_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_2_5(self):
		return pyodds.market_Over_Under_2_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_3_5(self):
		return pyodds.market_Over_Under_3_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_4_5(self):
		return pyodds.market_Over_Under_4_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_5_5(self):
		return pyodds.market_Over_Under_5_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_6_5(self):
		return pyodds.market_Over_Under_6_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_7_5(self):
		return pyodds.market_Over_Under_7_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Over_Under_8_5(self):
		return pyodds.market_Over_Under_8_5(self.lambda_home_ft,self.lambda_away_ft,self.log)
	def market_Half_Time_Over_Under_0_5(self):
		return pyodds.market_Half_Time_Over_Under_0_5(self.lambda_home_ht,self.lambda_away_ht,self.log)
	def market_Half_Time_Over_Under_1_5(self):
		return pyodds.market_Half_Time_Over_Under_1_5(self.lambda_home_ht,self.lambda_away_ht,self.log)
	def market_Half_Time(self):
		return pyodds.market_Half_Time(self.lambda_home_ht,self.lambda_away_ht, self.homeTeam, self.awayTeam, self.log)
	def market_HT_FT(self):
		return pyodds.market_HT_FT(self.lambda_home_ht,self.lambda_away_ht, self.homeTeam, self.awayTeam,self.log)
	def market_Half_Time_Score(self):
		return pyodds.market_Half_Time_Score(self.lambda_home_ht,self.lambda_away_ht, self.log)
	def market_CorrectScore2Home(self):
		return pyodds.market_CorrectScore2Home(self.lambda_home_ft, self.lambda_away_ft, self.log)
	def market_CorrectScore2Away(self):
		return pyodds.market_CorrectScore2Away(self.lambda_home_ft, self.lambda_away_ft, self.log)
	def market_BothTeamsToScore(self):
		return pyodds.market_BothTeamsToScore(self.lambda_home_ft, self.lambda_away_ft, self.log)
	def market_First_Goal(self):
		return pyodds.market_First_Goal(self.lambda_home_ft, self.lambda_away_ft, self.homeTeam, self.awayTeam,self.log)
	def market_Draw_No_Bet(self):
		return pyodds.market_draw_no_bet(self.lambda_home_ft, self.lambda_away_ft, self.homeTeam, self.awayTeam,self.log)
 

if __name__=="__main__":
		m = Estimator("Madrid","Barca",4.4,1.59,6.6,4.6,1.60,7.0)
