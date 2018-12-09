#!/usr/bin/env python3
import os
import json
from flask import Blueprint, render_template, request, session, Flask, redirect, g, Response, jsonify

from src.models import model
from src.mappers import cypher

from neo4j.v1 import GraphDatabase, basic_auth

controller = Blueprint('public',__name__)


@controller.route('/', methods =['GET', 'POST'])
def landingpage():
    if request.method == 'GET':
        return render_template('index.html')


@controller.route('/sample', methods =['GET', 'POST'])
def sample():
    if request.method == 'GET':
        return render_template('sample.html')

@controller.route('/company', methods =['GET', 'POST'])
def get_company():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('company.html', message = message)


@controller.route('/graph', methods =['POST'])
def get_graph():
    if request.method == 'POST':
        db = model.get_db()
        company = request.form['company']
        results = db.run("MATCH(c:Company)<-[f:FUNDED]-(fr:FundingRounds)<-[:INVESTED_IN]-(o:Company) "
            "WHERE c.name =~ {company} "
            "WITH c, fr, {investor:o.name} AS o_investors "
            "WITH c, {rounds:fr, investors:collect(o_investors)} as fr_rounds "
            "WITH {name:c.name, rounds:collect(fr_rounds)} as c_company "
            "RETURN{company:collect(c_company)}", {"company": company})
        json_data = model.get_graph(results).get_json()
        print(type(json_data))
        return render_template('company.html', json_data = json_data, mimetype="application/json")


   
