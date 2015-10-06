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

import time
import copy
import random
import sys
import datetime
import manager
import cPickle
import pprint
import operator
import traceback
import logmanager
reload(manager)
import sys
sys.dont_write_bytecode=True
import numpy as np
from joblib import Parallel, delayed  
import multiprocessing

def parallelTask(event):
	mt = copy.deepcopy(m)
	try:
		data=mt.getBestBetsForEvent(event)
	except:
		data=False
	return data


if __name__=="__main__":
	
	# Usage: python main.py <logs_folder> <username>

	# Main variables
        username = 'YOUR_USERNAME'
        password = 'YOUR_PASSWORD'
	API_KEY_DELAYED = "API_KEY_DELAYED"
	API_KEY_REALTIME = "API_KEY_REALTIME"
	API_KEY = API_KEY_REALTIME

	min_performance_to_bet = 1.001
	min_accepted_volume = 2
	fee=0.05
	hours_to_find_events = 0.5

	raise Exception("Please read the source code carefully before running it!")

	logs_directory = sys.argv[1]
	log = logmanager.LogManager(logs_directory)

	system_username = sys.argv[2]
	previous_bets_filename = "/home/"+system_username+"/adabet/previous_bets_event_id.pickle"

	m = manager.Manager( 	username = username,
				password = password,
				API_KEY=API_KEY,
				fee = fee,
				min_accepted_volume = min_accepted_volume,
				logs_directory = logs_directory
				)

	num_cores = multiprocessing.cpu_count()

	log.log("main","Simulation started at ",datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),"with username",system_username)
	log.log("main","Listing events...")
	hours = hours_to_find_events
	log.log("main","Starting at",hours,"hours...")
	events_list = m.listEvents(hours)
	while len(events_list)<num_cores:
		hours+=0.5
		log.log("main","There are",num_cores,"cores but only",len(events_list),"events. Incresing the search window to",hours) 
		events_list = m.listEvents(hours)
	log.log("main","Success! There are",len(events_list),"events")
	events_list = random.sample(events_list,num_cores)
	log.log("main","Sampling to",len(events_list),"=min(n_cores, len(events_list))")
	money = m.getCurrentMoney()
	log.log("main","Current money is",money)
	log.log("main","Starting parallel task to find the best of each kind")
	log.flush("main")

	# PARALLEL
	best_bets_each_market_array_dicts_and_info = Parallel(n_jobs=num_cores, verbose=11)(delayed(parallelTask)(i) for i in events_list)
	#########
#	best_bets_each_market_array_dicts_and_info=[]
#	for i in events_list:
#		best_bets_each_market_array_dicts_and_info.append(parallelTask(i))
	
	# Remove all Falses
	best_bets_each_market_array_dicts_and_info = filter(lambda a: a != False, best_bets_each_market_array_dicts_and_info)

	# END PARALLEL
	log.log("main","Done paralell task, now finding the best of the 'best'")
	log.flush("main")

	# Merge_results
	bets_events_dict = {}
	event_name_to_id={}
	event_name_to_date={}
	for bets_events_dict_tmp, event_name_to_id_tmp, event_name_to_date_tmp in best_bets_each_market_array_dicts_and_info:
		if len(bets_events_dict_tmp.keys())>0:
			event_name = bets_events_dict_tmp.keys()[0]
			bets_events_dict[event_name] = bets_events_dict_tmp[event_name]
			event_name_to_id[event_name] = event_name_to_id_tmp[event_name]
			event_name_to_date[event_name] = event_name_to_date_tmp[event_name]

	# Done
	best_bets=[]
	for event_name,v in bets_events_dict.iteritems():
		if len(v)==0:
			log.log("main","Nothing found")
			break
		best = v[0]
		market_name = best[0]
		r = best[1]
		bet = best[2]

		info = best[3]
		event_id = event_name_to_id[event_name]
		event_date = event_name_to_date[event_name]
		best_bets.append([event_date, event_name, event_id, market_name,r,bet,info,money])
	best_bets = sorted(best_bets,key=operator.itemgetter(4),reverse=True)

	log.log("main","DONE! Printing results (last one is the highest)")

	csv_lines = manager.printCSVLineFromBestBets(best_bets)[::-1]
	for line in csv_lines:
		log.log("main",line)

	if len(csv_lines)>0:
		if float(csv_lines[-1].split(";")[7])>=min_performance_to_bet:
			# Check if already bet
			try:
				f=open(previous_bets_filename)
				f.close()
			except:
				a=[]
				w=open(previous_bets_filename,"w")
				cPickle.dump(a,w)
				w.close()
			previous_bets_event_id = cPickle.load(open(previous_bets_filename))
			
			event_id = str(best_bets[0][2])
			if not(event_id in previous_bets_event_id):
				m.executeBet(best_bets[0], system_username)	
				previous_bets_event_id.append(event_id)
				w=open(previous_bets_filename,"w")
				cPickle.dump(previous_bets_event_id[-10:],w)
				w.close()	
				log.log("main","Appending to paperbet_file")
				a=open("/home/"+system_username+"/adabet/paper_bets.csv","a")
				a.write(csv_lines[-1]+"\n")
				a.close()
			else:
				log.log("main","Already bet in event",event_id)
		else:
			log.log("main","No interesting (>=",min_performance_to_bet,") opportunities)")


	log.log("main","Simulation ended at ",datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
	log.close()
