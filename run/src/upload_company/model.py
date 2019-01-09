#!/usr/bin/env python3

import os
import json
import csv
import re
import shutil

from wrapper import Crunchbase
import queries_company as q

from py2neo import Graph
graph = Graph()


### CREATE DATABASE ################################################################################

# Create list of organizations from csv
def create_list_from_csv(file):
    permalink_list = []
    with open(file, 'r') as csvfile:
        rows = csv.DictReader(csvfile, delimiter=',')
        for row in rows:
            permalink_list.append(row['permalink'])
    return permalink_list

# itemlist takes a list of api endpoints - companies
def write_json_company(file, error):
    permalink_list = create_list_from_csv(file)
    with open(error, 'r') as errorfile:
        error = json.load(errorfile)
        for end in permalink_list:
            with Crunchbase() as cb:
                jsondata = cb.company(end)
                if jsondata != error:
                    name = (re.search("(?<=\/organizations\/).*", end)).group(0)
                    print(name)
                    filename = name + '.json'
                    with open(filename, 'w') as outfile:
                        json.dump(jsondata, outfile)
                else:
                    print("Error creating json file")
                    return

# Get all json files
def file_list():
    # get to current path
    json_folder_path = os.path.dirname(os.path.realpath(__file__))
    # get all json files
    json_files = [ x for x in os.listdir(json_folder_path) if x.endswith("json") ]
    return (json_files)

# Add Cypher queries to database
def write_to_db(query, output):
    with open(output, 'r') as jsonfile:
        d = json.load(jsonfile)
        graph.cypher.execute(query, json=d)
        print('EXECUTED CYPHER')

# Add constraint to database
def add_constraint(query):
    graph.cypher.execute(query)
    print('CONSTRAINT ADDED')

# Add index to database
def add_index(query):
    graph.cypher.execute(query)
    print('INDEX ADDED')

# The constraints only needed to be added once
def constraint_to_neo():
    add_constraint(q.const_comp())
    add_constraint(q.const_fr())
    add_constraint(q.const_pers())
    add_constraint(q.const_in())
    add_constraint(q.const_head())
    add_constraint(q.const_cat())
    add_constraint(q.const_ipo())

# Setting an index allows for quicker searches for queries
def index_to_neo():
    add_index(q.ind_comp())
    add_index(q.ind_pers())
    add_index(q.ind_cat())
    add_index(q.ind_fr())

# Add the following queries for each json file passed 
def company_to_neo(output):
    write_to_db(q.comp_prop(),output)
    write_to_db(q.fr_prop(),output)
    write_to_db(q.fr_f_comp(),output)
    write_to_db(q.investComp_prop(),output)
    write_to_db(q.investComp_i_fr(),output)
    write_to_db(q.found_prop(),output)
    write_to_db(q.found_f_comp(),output)
    write_to_db(q.board_prop(),output)
    write_to_db(q.board_b_comp(),output)
    write_to_db(q.acquiree_prop(),output)
    write_to_db(q.comp_a_acquiree(),output)
    write_to_db(q.head_prop(),output)
    write_to_db(q.comp_h_head(),output)
    write_to_db(q.cat_prop(),output)
    write_to_db(q.comp_c_cat(),output)
    write_to_db(q.ipo_prop(),output)
    write_to_db(q.comp_i_ipo(),output)
    write_to_db(q.investment_fr_prop(),output)
    write_to_db(q.comp_i_in_fr(),output)
    write_to_db(q.funded_org_prop(),output)
    write_to_db(q.fr_i_ic(),output)

# Once a json file has been written to the database then it is moved to the completed folder
def list_of_company_to_neo():
    json_list = file_list()
    for json in json_list:
        print(json)
        company_to_neo(json)
        move_file(json)
        print("FILED MOVED")

def move_file(export):
    source = "ENTER_CURRENT_FOUNDER_PATH/run/src/upload_company"
    destination = "ENTER_CURRENT_FOUNDER_PATH/run/src/completed_companies"
    shutil.move(os.path.join(source, export), os.path.join(destination, export))
