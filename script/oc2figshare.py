#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2017, Aureliu Mocanu <opyus@yahoo.it> and Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

import hashlib
import json
import os
import argparse #added later
import time  
from time import strftime
import sys

import glob
import requests
from requests.exceptions import HTTPError
import requests.packages.urllib3

class OC2Figshare(object):
    def __init__(self, token, conf, dump, material):
        self.token = token
        self.conf = conf
        self.dump = dump
        self.material = material
        self.fg_api = 'https://api.figshare.com/v2/{endpoint}'
        self.chick_size = 1048576
        self.processed_documents_path = self.dump + os.sep + "processed_documents.json"
        if os.path.exists(self.processed_documents_path):
            with open(self.processed_documents_path) as f:
                self.processed_documents = json.load(f)
        else:
            self.processed_documents = {}

    def raw_issue_request(self, method, url, data=None, binary=False):
        headers = {'Authorization': 'token ' + self.token}
        if data is not None and not binary:
            data = json.dumps(data)

        # To disable "SSL InsecurePlatform error"
        requests.packages.urllib3.disable_warnings()
        response = requests.request(method, url, headers=headers, data=data)
        try:
            response.raise_for_status()
            try:
                data = json.loads(response.content)
            except ValueError:
                data = response.content
        except HTTPError as error:
            print 'Caught an HTTPError: {}'.format(error.message)
            print 'Body:\n', response.content
            raise

        return data


    def issue_request(self, method, endpoint, *args, **kwargs):
        return self.raw_issue_request(method, self.fg_api.format(endpoint=endpoint), *args, **kwargs)


    def list_articles(self):
        result = self.issue_request('GET', 'account/articles')
        print 'Listing current articles:'
        if result:
            for item in result:
                print u'  {url} - {title}'.format(**item)
        else:
            print '  No articles.'
        print

    def get_description(self, file_name):
        with open(file_name) as fin:
             description = fin.read()
             description = description.replace("\n", "<br>")
             fin.close()
             return description

    def get_category(self, CATEGORIES):
        xlist = []
        list_categories = self.issue_request('GET', 'categories')
        for index, item in enumerate(list_categories):
            for key, value in enumerate(CATEGORIES):
                if item['title'] == value:
                   xlist.append(item['id'])
        return xlist


    def get_license(self, LICENSE):
        list_licenses = self.issue_request('GET', 'licenses') #account/licenses
        for index, item in enumerate(list_licenses):
            if item['name'] == LICENSE:
               return item['value']


    def create_article(self, title, desc, cat, keywords, lic, references):
        description = self.get_description(desc)
        categories = self.get_category(cat)
        license = self.get_license(lic)

        data = {
            'title' : title,  # You may add any other information about the article here as you wish.
            'description' : description,
            'categories' : categories,
            'tags' : keywords,
            'license' : license,
            'references' : references
        }

        result = self.issue_request('POST', 'account/articles', data=data)


        print 'Created article:', result['location'], '\n'

        result = self.raw_issue_request('GET', result['location'])

        return result['id']


    def list_files_of_article(self, article_id):
        result = self.issue_request('GET', 'account/articles/{}/files'.format(article_id))
        print 'Listing files for article {}:'.format(article_id)
        if result:
            for item in result:
                print '  {id} - {name}'.format(**item)
        else:
            print '  No files.'

        print


    def get_file_check_data(self, file_name):
        with open(file_name, 'rb') as fin:
            md5 = hashlib.md5()
            size = 0
            data = fin.read(self.chick_size)
            while data:
                size += len(data)
                md5.update(data)
                data = fin.read(self.chick_size)
            return md5.hexdigest(), size


    def initiate_new_upload(self, article_id, file_name):
        endpoint = 'account/articles/{}/files'
        endpoint = endpoint.format(article_id)

        md5, size = self.get_file_check_data(file_name)
        data = {'name': os.path.basename(file_name),
                'md5': md5,
                'size': size}

        result = self.issue_request('POST', endpoint, data=data)
        print 'Initiated file upload:', result['location'], '\n'

        result = self.raw_issue_request('GET', result['location'])

        return result


    def complete_upload(self, article_id, file_id):
        self.issue_request('POST', 'account/articles/{}/files/{}'.format(article_id, file_id))


    def upload_parts(self, file_info, FILE_NAME):
        url = '{upload_url}'.format(**file_info)
        result = self.raw_issue_request('GET', url)

        print 'Uploading parts:'
        with open(FILE_NAME, 'rb') as fin:
            for part in result['parts']:
                self.upload_part(file_info, fin, part)
        print



    def upload_part(self, file_info, stream, part):
        udata = file_info.copy()
        udata.update(part)
        url = '{upload_url}/{partNo}'.format(**udata)

        stream.seek(part['startOffset'])
        data = stream.read(part['endOffset'] - part['startOffset'] + 1)

        self.raw_issue_request('PUT', url, data=data, binary=True)
        print '  Uploaded part {partNo} from {startOffset} to {endOffset}'.format(**part)



    def upload_a_list(self, TITLE, FILE_PATH_README, FILE_PATH_CORPUS, CATEGORIES, KEYWORDS,
                      LICENSE_TYPE, REFERENCES, FILE_PATH_INFO):
        # We first create the article
        self.list_articles()
        article_id = self.create_article(TITLE, FILE_PATH_README, CATEGORIES, KEYWORDS, LICENSE_TYPE, REFERENCES)
        self.list_articles()
        self.list_files_of_article(article_id)


        # Then we upload the license.
        FILE_PATH_LICENSE = self.material + os.sep + "LICENSE.txt"
        file_info = self.initiate_new_upload(article_id, FILE_PATH_LICENSE)
        # Until here we used the figshare API; following lines use the figshare upload service API.
        self.upload_parts(file_info, FILE_PATH_LICENSE)
        # We return to the figshare API to complete the file upload process.
        self.complete_upload(article_id, file_info['id'])
        self.list_files_of_article(article_id)


        # Then we upload the readme.
        file_info = self.initiate_new_upload(article_id, FILE_PATH_README)
        self.upload_parts(file_info, FILE_PATH_README)
        self.complete_upload(article_id, file_info['id'])
        self.list_files_of_article(article_id)


        # Then we upload the archive.
        file_info = self.initiate_new_upload(article_id, FILE_PATH_CORPUS)
        self.upload_parts(file_info, FILE_PATH_CORPUS)
        self.complete_upload(article_id, file_info['id'])
        self.list_files_of_article(article_id)


        # Then we upload the information file.
        file_info = self.initiate_new_upload(article_id, FILE_PATH_INFO)
        self.upload_parts(file_info, FILE_PATH_INFO)
        self.complete_upload(article_id, file_info['id'])
        self.list_files_of_article(article_id)

        doi = self.issue_request('POST', 'account/articles/{}/reserve_doi'.format(article_id))

        #pub = issue_request('POST', 'account/articles/{}/publish'.format(article_id)) #publish the article

        return doi['doi']

    def get_info(self, info_file_path):
        with open(info_file_path) as f:
            text = f.read()
            text = text.replace("\n", "")
            f.close()
            vector = text.split('* ')
            return vector

    def create_html_file(self, BASE_PATH, DOI_SET, DATE, DATE_NAME, INFO_FILE_PATH):
        statistics = self.get_info(INFO_FILE_PATH)
        html_str = """<html>
        <head></head>
        <body>
             <h4>"""+DATE_NAME+""" Dump</h4>
             <p>Dump created on """+DATE+""". This dump includes information on:</p>
             <ul>"""
        for cur_stat in statistics[1:]:
            html_str += """
                <li><p>""" + cur_stat + """</p></li>"""
        html_str +="""
             </ul>
             <div class="table-responsive">
                 <table class="table">
                     <tr><th>Type</th><th>Archive</th></tr>
                     <tr><td>agent roles (ar)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_ar'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_ar_prov'])+"""">provenance</a></td></tr>
                     <tr><td>bibliographic entries (be)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_be'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_be_prov'])+"""">provenance</a></td></tr>
                     <tr><td>bibliographic resources (br)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_br'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_br_prov'])+"""">provenance</a></td></tr>
                     <tr><td>identifiers (id)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_id'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_id_prov'])+"""">provenance</a></td></tr>
                     <tr><td>responsible agents (ra)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_ra'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_ra_prov'])+"""">provenance</a></td></tr>
                     <tr><td>resource embodiment (re)</td><td><a href="https://doi.org/"""+str(DOI_SET['corpus_re'])+"""">data</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_re_prov'])+"""">provenance</a></td></tr>
                     <tr><td>corpus</td><td><a href="https://doi.org/"""+str(DOI_SET['triplestore'])+"""">triplestore</a>, <a href="https://doi.org/"""+str(DOI_SET['corpus_prov'])+"""">provenance</a></td></tr>
                 </table>
             </div>
        </body>
    </html>
    """
        html_file_path = BASE_PATH + os.sep + DATE + '.html'
        html_file = open(html_file_path, 'w')
        html_file.write(html_str)
        html_file.close()
        print "HTML file '%s' stored." % html_file_path


    def store_processed_documents(self):
        with open(self.processed_documents_path, "w") as f:
            json.dump(self.processed_documents, f)


if __name__ == '__main__':
    if __name__ == "__main__":
        arg_parser = argparse.ArgumentParser("oc2figshare.py",
                                             description="An application for storing data and metadata related "
                                                         "to OpenCitations Corpus to Figshare.com. Example of usage:"
                                                         "\n\n"
                                                         "python oc2fighshare.py -t XXX -c conf_oc2fig.json "
                                                         "-d 2017-03-24 -m corpus/dump -dt 2017-03-24")
        arg_parser.add_argument("-t", "--token", dest="token", required=True,
                                help="The token to use to call the Figshare APIs.")
        arg_parser.add_argument("-c", "--conf", dest="conf", required=True,
                                help="The configuration file to use.")
        arg_parser.add_argument("-d", "--dump_dir", dest="dump", required=True,
                                help="The directory containing the dump of the OCC.")
        arg_parser.add_argument("-m", "--material_dir", dest="material", required=True,
                                help="The directory containing the other material for the metadata of the OCC dumps.")
        arg_parser.add_argument("-dt", "--date", dest="date", required=True,
                                help="The date of the dump, in YYYY-MM-DD format.")
        args = arg_parser.parse_args()

        date = ''
        date_name = ''

        print "\n\n\n# Start new process"

        with open(args.conf) as f:
            conf = json.load(f)
            oc2fig = OC2Figshare(args.token, conf, args.dump, args.material)
            date = args.date
            date_i = time.strptime(date, '%Y-%m-%d')  # control if the format is YYYY-MM-DD
            date_name = strftime("%d %B %Y", date_i)
            file_path_info = oc2fig.material + os.sep + date + '-info.txt'
            try:
                for index, item in enumerate(conf):  # item is the key of object json and value is conf[item]
                    if item not in oc2fig.processed_documents:
                        print "\n\n### Processing item '%s'\n" % item
                        zip_file = glob.glob(oc2fig.dump + os.sep + '*' + item + '.zip')
                        if len(zip_file):
                            title = conf[item]['title'] + ', archived on ' + date
                            description = oc2fig.material + os.sep + conf[item]['desc_file']
                            categories = conf[item]['categories']
                            keywords = conf[item]['keywords']
                            license_type = conf[item]['license']
                            references = conf[item]['references']
                            cur_doi = oc2fig.upload_a_list(title, description, zip_file[0], categories,
                                                                 keywords, license_type, references, file_path_info)
                            oc2fig.processed_documents[item] = cur_doi
                            time.sleep(5)  # after each upload need 5 sec of pause
                        else:
                            print "No ZIP file has been found for item '%s'" % item
            except Exception as e:
                print "\nAn error has occurred:", e.message
                print sys.exc_info()

            oc2fig.store_processed_documents()

            oc2fig.create_html_file(args.dump, oc2fig.processed_documents, date, date_name, file_path_info)

        print "\n# Process finished"
