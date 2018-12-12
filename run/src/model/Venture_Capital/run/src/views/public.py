#!/usr/bin/env python3
import os
import json
from flask import Blueprint, render_template, request, session, Flask, redirect, g, Response, jsonify, Markup

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
def get_company_index():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('company.html', message = message)


@controller.route('/companysearch')
def get_company():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = model.get_db()
        results = db.run("MATCH (c:Company) "
                 "WHERE c.name =~ {name} "
                 "RETURN c", {"name": "(?i).*" + q + ".*"}
        )
        return Response(json.dumps([model.serialize_company(record[0]) for record in results]),
                        mimetype="application/json")    


@controller.route("/graph/<name>")
def get_graph(name):
    db = model.get_db()
    results = db.run("MATCH(c:Company)<-[f:FUNDED]-(fr:FundingRounds)<-[:INVESTED_IN]-(o:Company) "
        "WHERE c.name =~ {name} "
        "WITH c, fr, {investor:o.name} AS o_investors "
        "WITH c, {rounds:fr, investors:collect(o_investors)} as fr_rounds "
        "WITH {name:c.name, rounds:collect(fr_rounds)} as c_company "
        "RETURN{company:collect(c_company)}", {"name": name})
    return model.get_graph(results)


@controller.route("/company/<name>")
def get_rounds(name):
    db = model.get_db()
    results = db.run(" MATCH (c:Company)<-[r]-(fr:FundingRounds) "
            "WHERE c.name =~ {name} "
            "RETURN c AS company, collect([fr.announced_on, fr.type, fr.money_raised_usd]) as rounds "
            "LIMIT 1", {"name": name})
    result = results.single();
    return Response(json.dumps({"name": result['company']['name'],
                           "image": result['company']['image'],
                           "rounds": [model.serialize_fundingRound(member)
                                    for member in result['rounds']]}),
                    mimetype="application/json")





   
