import json
import re
import math
import porter
import os
import getopt
import sys


class BM25(object):
    """Summary of BM 25 here
    this Class is to handle the BM25 Model , process the file and apply the content for search
    process the lisa.all.txt and store in the BM25Weights.json
    the main process is :
    parse the lisa.all.txt into the dict like this (k:docid,v:content)
    parse the content in the content with re module and porter module
    for every words in content calculate the tf and the idf that is the base step for the BM25 Model
    when get the tf and the idf using the formula to calculate the BM25 weights and store it in the file
    """

    def __init__(self,all_path,stopwords_path):

        # specific path for file to parse
        self.all = all_path
        # the file name of the BMWeights
        self.bm25_file = 'BM25Weights.json'
        # the porter to stem the words
        self.porter = porter.PorterStemmer()
        # the stopwords which is read from the stopwords_path
        self.stopwords = self._read_stopwords(stopwords_path)
        # the doc k:docid v:{k:len,v:doclen,k:tfs,v:tfs} tfs is a dict with k:term v: a number of the frequency
        self.docdict = {}
        # the idfs k:term v: a number of the over all frequency
        self.idfs = {}
        # the BM25 value dict k:docid v:{k:term,v:score}
        self.BM25 = {}
        # the k of the formula
        self.k = 1
        # the b of the formula
        self.b = 0.75

        # judge that if here is the BM25Weightfile:
        if os.path.exists(self.bm25_file):
            #load the BM25Weights
            print("Loading BM25 index from file, please wait. \n")
            self.load_bm25()
        else:
            # calcualte the bm25 score and store
            print("BM25 index is not exists")
            print("Generateing BM25 index....")
            self.calculate_bm25()
            self.save_bm25()

    def _read_stopwords(self,stopwords_path):
        """
        read the stopwords to the memory and split it into the list
        :param stopwords_path: the path of the stopwords file
        :return: a list of the stopwords
        """
        stopwords = set()
        with open(stopwords_path) as f:
            whole = f.read()
        stopwords= set(filter(None,whole.split('\n')))
        return stopwords

    def _read_file(self):
        """
        read the doc info from the self.all file
        and split it into the list everydoc
        :return: a list of the doc info
        """
        # open the file to get the content of all files
        with open(self.all) as f:
            file_all = f.read()
            # a spacific file is look list this

            # Document    2
            # THE LINGERING FRAGRANCE: PROCEEDINGS OF THE XXIV ALL INDIA LIBRARY CONFERENCE,
            # BANGALORE.
            #
            # PAPERS AND PROCEEDINGS FROM THE CONFERENCE, WITH A SUMMARY BY N.D. BAGARI, AND
            # TRANSCRIPTS OF THE INAUGURAL SPEECH, INTRODUCTORY PAPERS, AND MAIN
            # PRESENTATIONS. THE CONFERENCE WAS HELD FROM 29 JAN TO 1 FEB 78.
            # ********************************************

            # split the all file with the ********************************************
            everydoc = file_all.split('********************************************\n')

            if everydoc[-1] == "":
                everydoc.pop()
        return everydoc

    def _process_file(self):
        """
        process the file to get the document length and all the terms length
        :return: a int of the all document terms length , a int of the document length
        """
        alldoclen = 0
        everydoc = self._read_file()
        # to extract the docid and preprocess
        for doc in everydoc:
            doclen = self._prase_doc(doc)
            alldoclen += doclen

        return alldoclen,len(everydoc)

    def _prase_doc(self,doc):
        """
        prase a specific document to get it's doc id and doc content
        :param doc: a specific document
        :return: a int of the document length
        """
        doc = doc.split('\n')

        # get the id
        docid = int(doc[0].split('Document')[1])
        # get the content and change to lower
        doccontent = ''.join(doc[1:]).lower()
        # preprocess the content
        doccontent = self._content_preprocess(doccontent)
        # steming the content
        doclen,tfs = self._content_stemming(doccontent)
        # add it the self.docdict k:docid ,v :{k:'len',v:doclen,k:'tfs',v:tfs}
        self.docdict[docid] = {'len':doclen,'tfs':tfs}
        return doclen

        #print("doclen: {}".format(doclen))
        # print(doccontent)

    def _content_preprocess(self,doccontent):
        """
        Strategy: for every doccontent remove the all the punctuation
        like : . , ' ? ! () $ % ^ * " / - :
        remove the multi blank blocks from the content
        :param doccontent:
        :return: the parsed content of the document
        """
        # remove the specific punctuation to space
        doccontent = re.sub(r"[.(),?$%^*:\"\'/-]|[+——！，。？、~@#￥%……&*（）]"," ",doccontent)
        # remove the continuous space
        doccontent = re.sub(r"\s+"," ",doccontent)
        # split the content to list
        doccontent = filter(None,doccontent.split(" "))

        # if doccontent[-1] == '':
        #     doccontent.pop()

        return doccontent

    def _content_stemming(self,doccontent):
        """
        stemming the content to get the tfs
        :param doccontent: a specific doc list of to stem
        :return: the doclen and the its tfs
        """
        doclen = 0
        tfs = {}
        # visit every term of the content list
        for everyterm in doccontent:
            # stem it
            everyterm = self.porter.stem(everyterm)

            # parse if it is not the stop words
            if everyterm not in self.stopwords:
                # add the length
                doclen +=1
                # set the tfs
                # if it already in the tfs add the count else set it to 1
                if everyterm in tfs:
                    tfs[everyterm] +=1
                else:
                    if everyterm in self.idfs:
                        self.idfs[everyterm] +=1
                    else :
                        self.idfs[everyterm] =1
                    tfs[everyterm] = 1

        return doclen,tfs

    def calculate_bm25(self):
        """
        the main function to calculate the bm25 vlaue
        :return: None
        """

        # get the all terms length and the munber of the doc
        alldoclen,totaldocsize = self._process_file()

        # calculate the average doc terms length
        average_doclen = alldoclen / totaldocsize

        # get every doc in the docdict
        for docid,doc in self.docdict.items():
            # get its length
            doclen = doc['len']
            # geth its tfs
            tfs = doc['tfs']

            # a dict to tore the score k:term,v:score
            value = {}
            for term, freq in tfs.items():

                # calcualte the value of the BM25

                result = freq * (1 + self.k) / (freq + self.k * ((1-self.b)+self.b * doclen/average_doclen))

                result = result * math.log((totaldocsize - self.idfs[term] +0.5)/(self.idfs[term]+0.5), 2)
                # add to value dict
                value[term] = result
            # add to BM25 dict with its docid
            self.BM25[docid] = value
        # print(self.BM25)
    def save_bm25(self):
        """
        save the self.BM25 model to the json file
        :return: None
        """
        with open(self.bm25_file,'w') as f:
            json.dump(self.BM25,f)

    def load_bm25(self):
        """
        load the self.BM25 model from the json file
        :return: None
        """
        with open(self.bm25_file,'r') as f:
            self.BM25 = json.load(f)

    def get_BM25(self):
        """
        a get function to others to visit the BM25 dict
        :return: the BM25 dict
        """
        return self.BM25

    def get_stopwords(self):
        """
        a get function for others to visit the stopwords
        :return: self.stopwords
        """
        return self.stopwords

class evaluation():
    """Summary of evaluation here
    the evaluation class is to evaluate the result of the BM25 model
    using lisa.queries to test and lisa.relevance as the ground truth
    the main process is:
    prase the lisa.queries.txt for BM25 model
    prase the lisa.relevance.txt as ground truth

    run the queries of the BM25 model
    save the result to evaluation_output.txt

    calculate the several formula with the evaluation_output and the relevance
    like the precision,recall...

    """
    def __init__(self):

        # the path of the queries
        self.sample_query_file = './lisa/lisa.queries.txt'
        # the path of the relevance as ground truth
        self.gt = './lisa/lisa.relevance.txt'
        # the paht of the stored evaluation file
        self.output = 'evaluation_output.txt'
        # the query dict k:queryid v:query content list
        self.query = {}
        # the relevance dict k:queryid v:dict{k:rank,v:docid}
        self.relevance ={}
        # the prediction dict k:queryid v:dict{k:rank,v:docid}
        self.prediction = {}
        # the precision dict k:queryid v: precision number
        self.precision={}
        # the recall dict k:queryid v: recall number
        self.recall ={}
        # the precision_at_n dict k:queryid v: precision_at_n number
        self.precision_at_n ={}
        # the r precision dict k:queryid v: r_precision number
        self.r_precision ={}
        # the single average precision dict k:queryid v: single average precision
        self.average_precision_single_query ={}
        # the MAP　value
        self.map = 0
        # the average precision value
        self.precision_mean=0
        # the average recall value
        self.recall_mean=0
        # the average precision at n value
        self.precision_at_n_mean=0
        # the average R precision value
        self.r_precision_mean =0

    def calculate_precision_recall(self,queryid,relevances,predictions):
        """
        calculate the precsions =relret/ret
        calculate the recall = relret/rel
        :param queryid: the specific id of the query
        :param relevances: the specific query's relevance
        :param predictions: the specific query's prediction
        :return: None
        """
        ret = len(predictions)
        rel = len(relevances)
        relret = len(set(relevances.values()).intersection(set(predictions.values())))

        self.precision[queryid] = relret * 1.0 / ret
        self.recall[queryid] = relret * 1.0 / rel
    def claculate_precision_at_n(self,n,queryid,relevances,predictions):
        """
        calculate the precsions_at_n by set the ret to n
        :param n: the n of the formula
        :param queryid: the specific id of the query
        :param relevances: the specific query's relevance
        :param predictions: the specific query's prediction
        :return: None
        """
        ret = n
        relret = 0
        for i in predictions.values():
            for k, v in relevances.items():
                if i == v:
                    relret+=1
        self.precision_at_n[queryid] = relret /ret

    def calculate_r_precsion(self,r,queryid,relevances,predictions):
        """
        calcualte the R recision of by claculate the recall every loop
        :param r: the r of the formula
        :param queryid: the specific id of the query
        :param relevances: the specific query's relevance
        :param predictions: the specific query's prediction
        :return: None
        """
        rel = len(relevances)
        ret = 1
        relret = 0
        for i in predictions.values():
            if i in relevances.values():
                relret+=1

            if (relret / rel > r):
                self.r_precision[queryid] = relret/ret
                break

            ret+=1

    def calculate_average_precision_single_query(self,queryid,relevances,predictions):
        """
        calcualte the average precision of a single query
        :param queryid: the specific id of the query
        :param relevances: the specific query's relevance
        :param predictions: the specific query's prediction
        :return: None
        """
        ret = 1
        relret = 0
        sum = 0
        for i in predictions.values():
            if i in relevances.values():
                relret += 1
                sum += relret / ret
            ret += 1
        self.average_precision_single_query[queryid] = sum / len(predictions)

    def calcualte_map(self):
        """
        using the single average query to get the average of the whole test collections
        :return: None
        """
        self.map = self.calculate_average(self.average_precision_single_query.values())


    def evaluation_all(self,n,r):
        """

        :param n: the n of the formula
        :param r: the r of the formula
        :return: None
        """

        # get the predictions dict
        self.process_prediction_relevance()

        # get the relevance dict
        self.process_example_relevance()

        # using self.relevance and the self.prediction to calculate the precision
        # self.relevance is a dict , k:queryid,v:dict(k:rank,v:docid)
        # self.prediction is a dict to ,k:queryid,v:dict(k:rank,v:docid)
        for queryid,relevances in self.relevance.items():
            predictions = self.prediction[queryid]

            # calcualte the precsion and recall
            self.calculate_precision_recall(queryid,relevances,predictions)
            # calculate the precision at n
            self.claculate_precision_at_n(n,queryid,relevances,predictions)
            # calcualte the R precision
            self.calculate_r_precsion(r,queryid,relevances,predictions)
            # calculate the singe average
            self.calculate_average_precision_single_query(queryid,relevances,predictions)
        # calculate the map
        self.calcualte_map()
        # calculate the all the value to the average across the collection
        self.calculate_all_average()
        # print the result to the screen
        self.print_results()



    def calculate_all_average(self):
        """
        calcualte the average using funciton self.calcualte_average
        :return:
        """

        self.precision_mean = self.calculate_average(self.precision.values())
        self.recall_mean = self.calculate_average(self.recall.values())
        self.precision_at_n_mean = self.calculate_average(self.precision_at_n.values())
        self.r_precision_mean = self.calculate_average(self.r_precision.values())


    def calculate_average(self,values):
        """
        get the average value of a specific list
        :param values: a list of the values
        :return: None
        """
        # incase the error
        if len(values) == 0 :return 0

        # get the sum and divided
        sum = 0
        for i in values:
            sum +=i
        return sum/len(values)

    def print_results(self):
        """
        print the result
        :return: None
        """
        print("Evaluation results:")
        print("{0:<21}{1:>.4f}".format('R-precision at R=0.4:', self.r_precision_mean))
        print("{0:<21}{1:>.4f}".format('Precision:',self.precision_mean))
        print("{0:<21}{1:>.4f}".format('Recall:',self.recall_mean))
        print("{0:<21}{1:>.4f}".format('P@10:',self.precision_at_n_mean))
        print("{0:<21}{1:>.4f}".format('MAP:',self.map))

    def process_example_query(self):
        """
        precess the example query file to add the content to the list
        :return: None
        """
        with open(self.sample_query_file) as f:

            sample_file = f.read()
            # split the file
            samples = filter(None,sample_file.split('#\n'))
            for i in samples:
                i = i.split('\n')
                # get the id
                id = int(i[0])
                # get the content
                content = ' '.join(i[1:])
                # set it the self.query
                self.query[id] = content
                # print (content)
        # sorted make sure the fllow the queryid
        sorted_query = sorted(self.query.items(), key=lambda item: item[0])
        # sorted_query = sorted(self.query.keys())
        return sorted_query

    def save_result(self,queryid,sort_simBM25,total = 50):
        """
        save the evaluation result from the result
        :param queryid: the specific query id
        :param sort_simBM25: the result from the bm25model
        :param total: the save number of the every query
        :return: None
        """
        rank = 1
        # self.prediction[queryid] = sort_simBM25
        with open(self.output,'a') as f:
            for result in sort_simBM25[:total]:
                # wirte it to the file
                f.write("{} {} {}\n".format(queryid,result[0],rank))
                rank +=1

    def process_prediction_relevance(self):
        """
        open the evaluation output file
        process the relevance of the prediction result
        :return: None
        """
        # open file
        with open(self.output) as f:
            result = f.read()

            lines = filter(None,result.split('\n'))
            rank = 1
            # queryresult dict k:rank v: docid
            queryresult = {}

            # read every line
            for line in lines:
                # get the queryid docid and queryrank
                queryid , docid, queryrank = line.split(' ')
                if rank != int(queryrank):
                    rank = 1
                    # add it to the prediction dict
                    self.prediction[int(queryid)-1]=queryresult
                    queryresult = {}
                    queryresult[rank] = int(docid)
                else:
                    queryresult[rank] = int(docid)

                rank +=1

            # add the final queryresult
            self.prediction[int(queryid)] = queryresult
        # print(self.prediction)


    def process_example_relevance(self):
        """
        open the lisa.relevance.txt to set the example relevance
        :return: None
        """
        # open the file
        with open(self.gt) as f:
            sample_file = f.read()
            sample_file = sample_file.split()
            # print(sample_file)
            # three blocks here
            # the third blocks length is defined by the second blocks
            # the first block is the queryid
            # start at 0 and 1
            # prase here like a auto machine
            id_block = True
            num_block = False
            relevance_block = False
            relevance_content = {}
            current_relevance = 0
            count = 0
            id = 0
            i =0
            while i<len(sample_file):
                if id_block:
                    # if not First:
                    #
                    # else:
                    #     First = False
                    id = int(sample_file[i])
                    id_block = False
                    num_block = True

                elif num_block:
                    count = int(sample_file[i])
                    num_block = False
                    relevance_block = True
                elif relevance_block:
                    if count == current_relevance :
                        relevance_block = False
                        current_relevance = 0
                        i -=1
                        # id_block = True
                    else:
                        current_relevance +=1
                        relevance_content[current_relevance]= int(sample_file[i])
                else:
                    self.relevance[id] = relevance_content
                    relevance_content = {}
                    id_block = True
                    i-=1
                i+=1
            self.relevance[id] = relevance_content



    def get_content(self):
        """
        get funciton for self.query
        :return: self.query
        """
        return self.query



class search():
    """Summary of search here
    search class is to handle the interface and other process of this program
    the main process is:
    get the argv of the user input
    if it is manual get into the query and result process
    if it is evaluation get into the evaluation result process
    """
    def __init__(self):

        # the BM25 model
        self.model = {}
        # the poter to stem the input
        self.porter = porter.PorterStemmer()

    def search(self,argv):
        """
        change the process by the user input argv
        :param argv: user input
        :return: None
        """
        # case error
        if not argv:
            self._helper_msg()
            sys.exit(2)
        try:
            opts,args = getopt.getopt(argv,"-h-m:")
        except getopt.GetoptError:
            self._helper_msg()
            sys.exit(2)

        for opt,arg in opts:
            if opt == '-h':
                self._helper_msg()
            elif opt == '-m':
                # change to the manual
                if arg == 'manual':
                    #load manual function
                    model= BM25('./lisa/lisa.all.txt', './stopwords.txt')
                    # set the model
                    self.model = model.get_BM25()
                    # set the stopwords
                    self.stopwords = model.get_stopwords()
                    # start the process to query question
                    self.query()
                # change to the evaluation
                elif arg == 'evaluation':
                    #load evaluation function
                    model = BM25('./lisa/lisa.all.txt', './stopwords.txt')
                    # set the model
                    self.model = model.get_BM25()
                    # set the stopwords
                    self.stopwords = model.get_stopwords()
                    # new the evaluation class
                    e = evaluation()
                    # judge if is need to generate the evaluation_output.txt
                    if not os.path.exists('evaluation_output.txt'):
                        id_and_words = e.process_example_query()

                        for id,words in id_and_words:
                            sort_simBM25=self._query_result(words)
                            e.save_result(id,sort_simBM25,40)
                    # evaluate all
                    e.evaluation_all(10,0.4)
                # others
                else:
                    print("Can't Find the Command you have typed")
                    self._helper_msg()
                    sys.exit(2)

    def query(self):
        """
        the interface of the query info
        :return: None
        """
        # get the input
        query_words = input("Enter query:")

        # continue until get quit
        while query_words != 'QUIT':
            # get the result
            sort_simBM25=self._query_result(query_words)
            # print the result
            self._print_query_result(sort_simBM25,query_words)
            # continue input
            query_words = input("Enter query:")

    def _query_result(self,query_words):
        """
        preprocess the words
        send to BM25 to find the score list
        :param query_words: the words input to he system
        :return:
        """
        words = re.sub(r"[.(),?$%^*:\"\'/-]|[+——！，。？、~@#￥%……&*（）]", " ", query_words)
        words = re.sub(r"\s+", " ", words)
        words = words.lower().split(" ")

        # get the useful word
        temp_word_vector =[]

        for word in words:
            if word not in self.stopwords:
                word = self.porter.stem(word)

                if word in temp_word_vector:
                    continue
                else:
                    temp_word_vector.append(word)
        # the similarity of the BM25
        simBM25={}

        # get all for the model
        for docid,value in self.model.items():
            # set the score to 0
            score = 0

            for words in temp_word_vector:
                # if the words in the model sum the score
                if words in value:
                    score += value[words]
            # add to the simBM25 dict
            simBM25[docid] = score
        # sorted the dict and return the result
        sort_simBM25 = sorted(simBM25.items(),key=lambda item:item[1],reverse= True)

        return sort_simBM25

    def _print_query_result(self,sort_simBM25,query_words):
        """
        the interface to print the result of a search
        :param sort_simBM25: the result
        :param query_words: the words to search
        :return: None
        """
        print('Results for query [{}]'.format(query_words))
        rank = 1
        # printed = False
        for result in sort_simBM25[:15]:
            # if result[1] == 0 and not printed:
            #     print("Fllowing is the score 0 for the result")
            #     printed = True
            print("{0:>2} {1:>5} {2:.5f}".format(rank, int(result[0]), float(result[1])))
            # print("{} {} {}".format(rank, int(result[0]), float(result[1])))
            rank += 1


    def _helper_msg(self):
        """
        the helper messsage for people who want to use this program
        :return:
        """
        print("usage:")
        print("search.py -m manual")
        print("serach.py -m evaluation")


if __name__ == '__main__':
    s = search()
    s.search(sys.argv[1:])


