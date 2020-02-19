from __future__ import absolute_import, unicode_literals

import codecs

from celery import task

from utils.otherUtils import send_mail_employee


@task
def add_batch_users(filename):
    with open(filename, 'r') as upload_file:
        # fields = csvr?eader.next() 
        data = upload_file.read()

        print(data)
    
