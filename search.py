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


    """

    def __init__(self,all_path,stopwords_path):
        self.all = all_path
        self.bm25_file = 'BM25Weights.json'
        self.porter = porter.PorterStemmer()
        self.stopwords = self._read_stopwords(stopwords_path)
        # the doc kv
        self.docdict = {}
        self.idfs = {}
        self.BM25 = {}
        self.k = 1
        self.b = 0.75

        # judge that if here is the BM25Weightfile:
        if os.path.exists(self.bm25_file):
            #load the BM25Weights
            print("Loading BM25 index from file, please wait. ")
            self.load_bm25()
        else:
            print("BM25 index is not exists")
            print("Generateing BM25 index....")
            self.calculate_bm25()
            self.save_bm25()

    def _read_stopwords(self,stopwords_path):
        stopwords = set()
        with open(stopwords_path) as f:
            whole = f.read()
        stopwords= set(filter(None,whole.split('\n')))
        return stopwords

    def _read_file(self):
        """
        read the file from the spacific file name
        :return: None
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

        :param type: different type means different txt
        :return: None
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
        prase every doc to get it's doc id and doc content
        :param doc:
        :return:
        """
        doc = doc.split('\n')
        docid = int(doc[0].split('Document')[1])
        doccontent = ''.join(doc[1:]).lower()
        doccontent = self._content_preprocess(doccontent)
        doclen,tfs = self._content_stemming(doccontent)
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
        :return:
        """
        doccontent = re.sub(r"[.(),?$%^*:\"\'/-]|[+——！，。？、~@#￥%……&*（）]"," ",doccontent)
        doccontent = re.sub(r"\s+"," ",doccontent)
        doccontent = doccontent.split(" ")

        if doccontent[-1] == '':
            doccontent.pop()

        return doccontent

    def _content_stemming(self,doccontent):
        doclen = 0
        tfs = {}
        for everyterm in doccontent:
            everyterm = self.porter.stem(everyterm)

            if everyterm not in self.stopwords:
                doclen +=1
                if everyterm in tfs:
                    tfs[everyterm] +=1
                else:
                    if everyterm in self.idfs:
                        self.idfs[everyterm] +=1
                    else :
                        self.idfs[everyterm] =1
                    tfs[everyterm] = 1

        return doclen,tfs

    def _close_file(self):
        """
        close the file if it isn't colseed
        :return:
        """
        pass
    def _close_all_file(self):
        """
        close all the file
        :return:
        """
        pass

    def calculate_bm25(self):
        alldoclen,totaldocsize = self._process_file()

        average_doclen = alldoclen / totaldocsize

        for docid,doc in self.docdict.items():
            doclen = doc['len']
            tfs = doc['tfs']

            value = {}
            for term, freq in tfs.items():

                # calcualte the value of the BM25

                result = freq * (1 + self.k) / (freq + self.k * ((1-self.b)+self.b * doclen/average_doclen))

                result = result * math.log((totaldocsize - self.idfs[term] +0.5)/(self.idfs[term]+0.5), 2)
                value[term] = result
            self.BM25[docid] = value
        # print(self.BM25)
    def save_bm25(self):
        with open(self.bm25_file,'w') as f:
            json.dump(self.BM25,f)

    def load_bm25(self):
        with open(self.bm25_file,'r') as f:
            self.BM25 = json.load(f)
    def get_BM25(self):
        return self.BM25

    def get_stopwords(self):
        return self.stopwords

class evaluation():
    def __init__(self):
        self.sample_query_file = './lisa/lisa.queries.txt'
        self.gt = './lisa/lisa.relevance.txt'
        self.output = 'evaluation_output.txt'
        self.query = {}
        self.relevance ={}
        self.prediction = {}
        # self.process_example_query()

        self.precision={}
        self.recall ={}
        self.precision_at_n ={}
        self.r_precision ={}
        self.average_precision_single_query ={}
        self.map = 0
        self.precision_mean=0
        self.recall_mean=0
        self.precision_at_n_mean=0
        self.r_precision_mean =0

    def calculate_precision_recall(self,queryid,relevances,predictions):
        # using self.relevance and the self.prediction to calculate the precision
        # self.relevance is a dict , k:queryid,v:dict(k:rank,v:docid)
        # self.prediction is a dict to ,k:queryid,v:dict(k:rank,v:docid)

        # precision is the relret / ret
        # for queryid,relevances in self.relevance.items():
        #     predictions = self.prediction[queryid]

        ret = len(predictions)
        rel = len(relevances)
        relret = len(set(relevances.values()).intersection(set(predictions.values())))

        self.precision[queryid] = relret * 1.0 / ret
        self.recall[queryid] = relret * 1.0 / rel
    def claculate_precision_at_n(self,n,queryid,relevances,predictions):
        # for queryid,relevances in self.relevance.items():
        #     predictions = self.prediction[queryid]

        ret = n
        relret = 0
        for i in predictions.values():
            for k, v in relevances.items():
                if i == v:
                    relret+=1
        self.precision_at_n[queryid] = relret /ret

    def calculate_r_precsion(self,r,queryid,relevances,predictions):
        # for queryid,relevances in self.relevance.items():
        #     predictions = self.prediction[queryid]

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
        # for queryid,relevances in self.relevance.items():
        #     predictions = self.prediction[queryid]

        self.map = self.calculate_average(self.average_precision_single_query.values())
        # sum =0
        # for i in self.average_precision_single_query.values():
        #     sum += i
        #
        # self.map = sum/len(self.average_precision_single_query)


    def evaluation_all(self,n,r):

        self.process_prediction_relevance()
        self.process_example_relevance()

        for queryid,relevances in self.relevance.items():
            predictions = self.prediction[queryid]

            self.calculate_precision_recall(queryid,relevances,predictions)
            self.claculate_precision_at_n(n,queryid,relevances,predictions)
            self.calculate_r_precsion(r,queryid,relevances,predictions)
            self.calculate_average_precision_single_query(queryid,relevances,predictions)
        self.calcualte_map()
        self.calculate_all_average()
        self.print_results()



    def calculate_all_average(self):

        self.precision_mean = self.calculate_average(self.precision.values())
        self.recall_mean = self.calculate_average(self.recall.values())
        self.precision_at_n_mean = self.calculate_average(self.precision_at_n.values())
        self.r_precision_mean = self.calculate_average(self.r_precision.values())


    def calculate_average(self,values):
        if len(values) == 0 :return 0
        sum = 0
        for i in values:
            sum +=i
        return sum/len(values)

    def print_results(self):
        print("Evaluation results:")
        print("{0:<21}{1:>5}".format('R-precision at R=0.4:', self.r_precision_mean))
        print("{0:<21}{1:>5}".format('Precision:',self.precision_mean))
        print("{0:<21}{1:>5}".format('Recall:',self.recall_mean))
        print("{0:<21}{1:>5}".format('P@10:',self.precision_at_n_mean))
        print("{0:<21}{1:>5}".format('MAP:',self.map))

    def process_example_query(self):
        with open(self.sample_query_file) as f:

            sample_file = f.read()
            samples = filter(None,sample_file.split('#\n'))
            for i in samples:
                i = i.split('\n')
                id = int(i[0])
                content = ' '.join(i[1:])
                self.query[id] = content
                # print (content)

        sorted_query = sorted(self.query.items(), key=lambda item: item[0])
        # sorted_query = sorted(self.query.keys())
        return sorted_query

    def save_result(self,queryid,sort_simBM25,total = 50):
        rank = 1
        # self.prediction[queryid] = sort_simBM25
        with open(self.output,'a') as f:
            for result in sort_simBM25[:total]:
                f.write("{} {} {}\n".format(queryid,result[0],rank))
                rank +=1

    def calculate_score(self):
        self.prediction = self.process_prediction_relevance()

    def process_prediction_relevance(self):
        with open(self.output) as f:
            result = f.read()

            lines = filter(None,result.split('\n'))
            rank = 1
            queryresult = {}
            for line in lines:
                queryid , docid, queryrank = line.split(' ')
                if rank != int(queryrank):
                    rank = 1
                    self.prediction[int(queryid)-1]=queryresult
                    queryresult = {}
                    queryresult[rank] = int(docid)
                else:
                    queryresult[rank] = int(docid)

                rank +=1
            self.prediction[int(queryid)] = queryresult
        # print(self.prediction)


    def process_example_relevance(self):
        with open(self.gt) as f:
            sample_file = f.read()
            sample_file = sample_file.split()
            print(sample_file)
            # three blocks here
            # the third blocks length is defined by the second blocks
            # the first block is the queryid
            # start at 0 and 1

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
        return self.query



class search():
    def __init__(self):
        self.model = {}
        self.porter = porter.PorterStemmer()

    def search(self,argv):
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
                if arg == 'manual':
                    #load manual function
                    model= BM25('./lisa/lisa.all.txt', './stopwords.txt')
                    self.model = model.get_BM25()
                    self.stopwords = model.get_stopwords()

                    self.query()
                elif arg == 'evaluation':
                    #load evaluation function
                    model = BM25('./lisa/lisa.all.txt', './stopwords.txt')
                    self.model = model.get_BM25()
                    self.stopwords = model.get_stopwords()
                    e = evaluation()
                    if not os.path.exists('evaluation_output.txt'):
                        id_and_words = e.process_example_query()

                        for id,words in id_and_words:
                            sort_simBM25=self._query_result(words)
                            e.save_result(id,sort_simBM25,50)

                    # e.process_prediction_relevance()
                    # e.process_example_relevance()
                    e.evaluation_all(10,0.4)




                else:
                    print("Can't Find the Command you have typed")
                    self._helper_msg()
                    sys.exit(2)

    def query(self):
        query_words = input("Enter query:")
        while query_words != 'QUIT':
            sort_simBM25=self._query_result(query_words)
            self._print_query_result(sort_simBM25,query_words)
            query_words = input("Enter query:")

    def _query_result(self,query_words):
        words = re.sub(r"[.(),?$%^*:\"\'/-]|[+——！，。？、~@#￥%……&*（）]", " ", query_words)
        words = re.sub(r"\s+", " ", words)
        words = words.lower().split(" ")

        temp_word_vector =[]

        for word in words:
            if word not in self.stopwords:
                word = self.porter.stem(word)

                if word in temp_word_vector:
                    continue
                else:
                    temp_word_vector.append(word)

        simBM25={}

        for docid,value in self.model.items():
            score = 0

            for words in temp_word_vector:
                if words in value:
                    score += value[words]

            simBM25[docid] = score
        sort_simBM25 = sorted(simBM25.items(),key=lambda item:item[1],reverse= True)

        return sort_simBM25

    def _print_query_result(self,sort_simBM25,query_words):
        print('Results for query [{}]'.format(query_words))
        rank = 1
        # printed = False
        for result in sort_simBM25[:15]:
            # if result[1] == 0 and not printed:
            #     print("Fllowing is the score 0 for the result")
            #     printed = True
            print("{0:>2} {1:>5} {2:.5f}".format(rank, int(result[0]), float(result[1])))
            # print("{} {} {}".format(rank, int(result[0]), float(result[1])))
            rank +=1


    def _helper_msg(self):
        print("usage:")
        print("search.py -m manual")
        print("serach.py -m evaluation")


if __name__ == '__main__':
    s = search()
    s.search(sys.argv[1:])

    # e  = evaluation()
    # e.process_example_query()


