# coding=utf-8
# python query-based_baseline.py directory_of_threads/ queries_for_useful_threadids.txt viva_queries.postselection.baseline.out

import sys
import os
import xml.etree.ElementTree as ET
import re
from scipy.linalg import norm
import operator

thread_dir = sys.argv[1]
query_file = sys.argv[2]
outfile = sys.argv[3]

def tokenize(t):
    text = t.lower()
    text = re.sub("\n"," ",text)
    text = re.sub('[^a-zèéeêëûüùôöòóœøîïíàáâäæãåA-Z0-9- \']', "", text)
    wrds = text.split()
    return wrds

def fast_cosine_sim(a, b):
    #print (a)
    if len(b) < len(a):
        a, b = b, a
    up = 0
    a_value_array = []
    b_value_array = []
    for key in a:
        a_value = a[key]
        b_value = b[key]
        a_value_array.append(a_value)
        b_value_array.append(b_value)
        up += a_value * b_value
    if up == 0:
        return 0
    return up / norm(a_value_array) / norm(b_value_array)


def find_most_relevant_unit(selected_units,unselected_units,termvectors,queryvector,labda):
    #print ("Selected units:",selected_units)
    #for uid in termvectors:
    #    print (uid)
    most_relevant_unit = ""
    max_score = 0
    #print ("find most relevant unit")
    for unit_id in unselected_units: # walk through all unselected units
        unitvector = termvectors[unit_id] # get the term vector
        #print (unit_id,unitvector)
        max_sim_to_previously_selected = 0
        for sel_unit_id in selected_units: # walk through all previously selected units
            selected_unitvector = termvectors[sel_unit_id] # get the term vector
            selsim = fast_cosine_sim(selected_unitvector,unitvector) # calculate similarity between unit and prev selected unit
            if selsim > max_sim_to_previously_selected:
                max_sim_to_previously_selected = selsim # save the maximum similarity score

        querysim = fast_cosine_sim(unitvector,queryvector) # calculate similarity between unit and query
        score = labda*querysim-(1-labda)*max_sim_to_previously_selected # calculate score
        if score > max_score:
            max_score = score
            most_relevant_unit = unit_id # keep the highest scoring unit (MMR)

    return most_relevant_unit,max_score

def MMR (termvectors,queryvector,labda):
    unselected_units = list()
    for unit_id in termvectors:
        unselected_units.append(unit_id)

    units_with_MMR_scores = dict() # selected_units has postid as key and score as value

    while len(unselected_units) > 0:
        #print ("Selected units with MMR scores:",units_with_MMR_scores)
        #print (len(unselected_units),"units left")
        most_relevant_unit,score = find_most_relevant_unit(units_with_MMR_scores,unselected_units,termvectors,queryvector,labda)
        if score > 0:
            #print ("most relevant unit:",most_relevant_unit)
            units_with_MMR_scores[most_relevant_unit] = score
            unselected_units.remove(most_relevant_unit)
        else:
            return units_with_MMR_scores
    return units_with_MMR_scores


'''
MAIN
'''

queries_per_threadid = dict()

with open(queryfile,'r') as queries:
    for line in queries:
        line = line.rstrip()
        columns = line.split("\t")
        query = columns[0]
        threadid = columns[2]
        queriesforthisthreadid = dict() # we use a dict because there are duplicate queries
        if threadid in queries_per_threadid:
            queriesforthisthreadid = queries_per_threadid[threadid]
        queriesforthisthreadid[query] = 1
        queries_per_threadid[threadid] = queriesforthisthreadid

labda = 0.5

out = open(outfile,'w')

for fn in os.listdir(thread_dir):
    if ".xml" in fn:
        xmlfile = fn

        tree = ET.parse(thread_dir+"/"+xmlfile)
        root = tree.getroot()
        list_of_posts = list()

        # for each thread
        # read thread file

        for thread in root:
            threadid = thread.get('id')
            termvectors = dict() # key is postid, value is vector of posts
            termvectorforthread = dict() # term vector over all posts, determines the dimensions of the vector space


            for posts in thread.findall('posts'):
                postcount = 0
                for post in posts.findall('post'):
                    postcount += 1
                    if postcount > 50:
                        break
                    list_of_posts.append(post)
                    postid = post.get('id')

                    author = post.find('author').text
                    timestamp = post.find('timestamp').text

                    # get content of posts:

                    bodyofpost = post.find('body').text

                    if bodyofpost is None:
                        bodyofpost = ""
                    if re.match(".*http://[^ ]+\n[^ ]+.*",bodyofpost):
                        #print bodyofpost
                        bodyofpost = re.sub("(http://[^ ]+)\n([^ ]+)",r"\1\2",bodyofpost)
                        #print bodyofpost

                    bodyofpost = re.sub("\"","&#34;",bodyofpost)
                    #bodyofpost = re.sub("\'","&#39;",bodyofpost)
                    #bodyofpost = re.sub("\'","\\\'",bodyofpost)
                    bodyofpost = re.sub("\n *\n","<br>\n",bodyofpost)
                    #print currentpostid, bodyofpost
                    #if " schreef op " in bodyofpost:
                        #print currentpostid
                    #    bodyofpost = replace_quote(bodyofpost)

                    bodyofpost = re.sub("\n"," ",bodyofpost)

                    if "smileys" in bodyofpost:
                        bodyofpost = re.sub(r'\((http://forum.viva.nl/global/(www/)?smileys/.*.gif)\)','',bodyofpost)
                        #print bodyofpost
                    #print author, timestamp, bodyofpost

############################

                    words = tokenize(bodyofpost)

                    # vectorize:
                    for word in words:
                        #print (word, nrofsyllables(word))

                        worddict = dict()
                        if postid in termvectors:
                            worddict = termvectors[postid]
                        if word in worddict:
                            worddict[word] += 1
                        else:
                            worddict[word] = 1
                        termvectors[postid] = worddict

                        if word in termvectorforthread:  # dictionary over all posts
                           termvectorforthread[word] += 1
                        else:
                           termvectorforthread[word] = 1


                    #abspositions[(threadid,postid)] = postid
                #print wordcounts

            # for each post, add zeroes for terms that are not in the post vector:
            for postid in termvectors:
                worddictforpost = termvectors[postid]
                for word in termvectorforthread:
                    if word not in worddictforpost:
                        worddictforpost[word] = 0
                termvectors[postid] = worddictforpost
                #print ("post:",postid,len(termvectors[postid]))

            # add queries for this thread to the same vectorspace

            queriesforthisthreadid = queries_per_threadid[threadid]
            for query in queriesforthisthreadid:
                querywords = tokenize(query)
                termvectorforquery = dict()

                for qw in querywords:
                    if qw in termvectorforquery:
                        termvectorforquery[qw] += 1
                    else:
                        termvectorforquery[qw] = 1

                # add zeroes for terms that are not in the query vector:
                for word in termvectorforthread:
                    if word not in termvectorforquery:
                        termvectorforquery[word] = 0
                print ("thread:",threadid,"; query:",query)
                units_with_MMR_scores = MMR(termvectors,termvectorforquery,labda)

                for postid in termvectors:
                    if postid not in units_with_MMR_scores:
                        units_with_MMR_scores[postid] = 0
                #print ("posts with scores:",units_with_MMR_scores)

                for postid in termvectors:
                    out.write(threadid+"\t"+query+"\t"+postid+"\t"+str(units_with_MMR_scores[postid])+"\n")


out.close()