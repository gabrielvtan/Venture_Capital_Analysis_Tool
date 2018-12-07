#!/usr/bin/env python
import os
from json import dumps
from flask import Flask, g, Response, request
from pprint import pprint

from neo4j.v1 import GraphDatabase, basic_auth

app = Flask(__name__, static_url_path='/static/')

password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver('bolt://localhost',auth=basic_auth("neo4j", password))

def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'neo4j_db'):
        g.neo4j_db.close()

@app.route("/")
def get_index():
    return app.send_static_file('index.html')

def serialize_company(company):
    return {
        'uuid': company['uuid'],
        'name': company['name'],
        'image': company['image'],
        'description': company['description'],
        'primary_role': company['primary_role'],
        'founded_on': company['founded_on'],
        'stock_symbol': company['stock_symbol'],
        'total_funding_usd': company['total_funding_usd'],
        'number_of_investments': company['number_of_investments'],
        'homepage_url': company['homepage_url'],
        'categories': company['categories'],
        'went_public_on': company['went_public_on'],
        'opening_valuation_usd': company['opening_valuation_usd'],
        'city': company['city'],
        'country': company['country']

    }

def serialize_fundingRound(fundingRound):
    return {
        'uuid': fundingRound['uuid'],
        'type': fundingRound['type'],
        'money_raised_usd': fundingRound['money_raised_usd'],
        'announced_on': fundingRound['announced_on']
    }

@app.route("/graph")
def get_graph():
    db = get_db()
    results = db.run("""MATCH(c:Company)<-[f:FUNDED]-(fr:FundingRounds)<-[:INVESTED_IN]-(o:Company)
            WHERE c.name = 'Facebook'
            WITH c, fr, {investor:o.name} AS o_investors
            WITH c, {rounds: fr,  investors: collect(o_investors)} as fr_rounds
            WITH {name:c.name, rounds: collect(fr_rounds)} as c_company
            RETURN{company: collect(c_company)}""")
    nodes = []
    rels = []
    i = 0
    
    for record in results:
        nodes.append({"name": record[0]['company'][0]['name'], 
            "label": "company"})
        target = i
        i += 1
        z = 0

        for fundingRound in record[0]['company'][z]['rounds']:
            rounds = {
                "uuid": fundingRound['rounds']["uuid"], 
                "type": fundingRound['rounds']["type"], 
                "label": "rounds"}
            try:
                source = nodes.index(rounds)
            except ValueError:
                nodes.append(rounds)
                source = i
                target_1 = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "FUNDED"})
            j = 0
            for investor in fundingRound['investors']:
                investors = {"name": investor['investor'], "label": "investor"}
                try:
                    source = nodes.index(investors)
                except ValueError:
                    nodes.append(investors)
                    source = i
                    i += 1
                    z += 1
                    j += 1
                rels.append({"source": source, "target": target_1, "action": "INVESTED_IN"})
    return Response(dumps({"nodes": nodes, "links": rels}),
                    mimetype="application/json")


@app.route("/search")
def get_search():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = get_db()
        results = db.run("MATCH (c:Company) "
                 "WHERE c.name =~ {name} "
                 "RETURN c", {"name": "(?i).*" + q + ".*"}
        )
        return Response(dumps([serialize_company(record['company']) for record in results]),
                        mimetype="application/json")


@app.route("/company/<title>")
def get_movie(title):
    db = get_db()
    results = db.run("MATCH (c:Company {name:{name}}) "
             "OPTIONAL MATCH (c)<-[r]-(fr:FundingRound) "
             "RETURN company.name as name"
             "LIMIT 1", {"name": name})

    result = results.single();
    return Response(dumps({"name": result['name'],
                           "rounds": [serialize_fundingRound(member)
                                    for member in result['rounds']]}),
                    mimetype="application/json")


if __name__ == '__main__':
    app.run(port=8080)
