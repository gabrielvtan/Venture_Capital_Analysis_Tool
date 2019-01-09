#!/usr/bin/env python3

import model

file = '<INSERT CSV FILE FROM CRUNCHBASE>'

error = 'error.txt'

def create_json(file, error):
    model.write_json_company(file, error)

def create_db():
    model.constraint_to_neo()
    model.index_to_neo()
    model.list_of_company_to_neo()
 
def test_query():
    model.test_query()

if __name__ == '__main__':
    create_json(file, error)
    create_db()
    test_query()








