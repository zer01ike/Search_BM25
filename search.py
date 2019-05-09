import json
import re
import math
import porter
import os


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

                result = result * math.log((totaldocsize - self.idfs[term] +0.5)/(self.idfs[term]+0.5), 10)
                value[term] = result
            self.BM25[docid] = value
        # print(self.BM25)
    def save_bm25(self):
        with open(self.bm25_file,'w') as f:
            json.dump(self.BM25,f)

    def load_bm25(self):
        with open(self.bm25_file,'r') as f:
            self.BM25 = json.load(f)



if __name__ == '__main__':
    bm25 = BM25('./lisa/lisa.all.txt','./stopwords.txt')


