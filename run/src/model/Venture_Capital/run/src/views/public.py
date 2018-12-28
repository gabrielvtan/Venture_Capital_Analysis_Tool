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
        return render_template('dashboard.html')


@controller.route('/sample', methods =['GET', 'POST'])
def sample():
    if request.method == 'GET':
        return render_template('sample.html')


### COMPANY ###########################################################
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
                 "RETURN c", {"name": "^(?i)" + q + "$"}
        )
        return Response(json.dumps([model.serialize_company(record[0]) for record in results]),
                        mimetype="application/json") 


@controller.route("/graph/<name>")
def get_company_graph(name):
    db = model.get_db()
    results = db.run("MATCH(c:Company)<-[f:FUNDED]-(fr:FundingRounds)<-[:INVESTED_IN]-(o:Company) "
        "WHERE c.name =~ {name} "
        "WITH c, fr, {investor:o.name} AS o_investors "
        "WITH c, {rounds:fr, investors:collect(o_investors)} as fr_rounds "
        "WITH {name:c.name, rounds:collect(fr_rounds)} as c_company "
        "RETURN{company:collect(c_company)}", {"name": name})
    founders = db.run("MATCH(p:Person)-[:FOUNDED]->(c:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(p.permalink) as founders", {"name": name})
    board = db.run("MATCH (p:Person)-[:BOARDMEMBER]->(c:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(p.permalink) as board", {"name": name})
    acquired = db.run ("MATCH (c:Company)-[:ACQUIRED]-(a:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(a.name) as acquisition", {"name": name})
    return model.get_company_graph(results, founders, board, acquired)


@controller.route("/company/<name>")
def get_company_details(name):
    db = model.get_db()
    results = db.run(" MATCH (c:Company)<-[r]-(fr:FundingRounds) "
            "WHERE c.name =~ {name} "
            "WITH DISTINCT c, fr, fr.announced_on as date ORDER BY date DESC "
            "RETURN c AS company, collect([fr.announced_on, fr.type, fr.money_raised_usd]) as rounds "
            "LIMIT 1", {"name": name})
    result = results.single();
    _competitors = db.run("MATCH (c:Company)-[:CATEGORY]->(cat:Category)<-[:CATEGORY]-(o:Company), "
            "(o)<-[:FUNDED]-(fr:FundingRounds) "
            "WHERE c.name =~ {name} "
            "WITH o, sum(fr.money_raised_usd) as money_raised ORDER BY money_raised DESC LIMIT 5 "
            "RETURN collect([o.name, o.categories]) AS competitors", {"name": name})
    competitors = _competitors.single();
    _acquisitions = db.run ("MATCH (c:Company)-[ac:ACQUIRED]-(a:Company) "
        "WHERE c.name =~ {name} "
        "RETURN collect([a.name, ac.type, ac.announced_on, a.categories]) as acquisitions", {"name": name})
    acquisitions = _acquisitions.single();
    return Response(json.dumps({"rounds": [model.serialize_fundingRound(member)
                                    for member in result['rounds']],
                                "competitors": [model.serialize_competitors(competitor)
                                    for competitor in competitors['competitors']],
                                "acquisitions" : [model.serialize_acquisitions(acquisition)
                                    for acquisition in acquisitions['acquisitions']]}),
                    mimetype="application/json")


### INVESTMENT COMPANY ###
@controller.route('/investmentcompany', methods =['GET', 'POST'])
def get_investment_company_index():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('investment_company.html', message = message)


@controller.route('/investmentcompanysearch')
def get_investmentcompany():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = model.get_db()
        results = db.run("MATCH (c:Company) "
                 "WHERE c.name =~ {name} "
                 "RETURN c", {"name": "^(?i)" + q + "$"})
        return Response(json.dumps([model.serialize_company(record[0]) for record in results]),
                        mimetype="application/json") 


@controller.route("/investmentcompany/<name>")
def get_investmentcompany_details(name):
    db = model.get_db()
    _competitors = db.run("MATCH (c:Company)-[:CATEGORY]->(cat:Category)<-[:CATEGORY]-(o:Company) "
            "WHERE c.name =~ {name} "
            "WITH DISTINCT o, o.number_of_investments as investments ORDER BY investments DESC LIMIT 10 "
            "RETURN collect([o.name, investments, o.categories]) AS competitors", {"name": name})
    competitors = _competitors.single();
    _acquisitions = db.run ("MATCH (c:Company)-[ac:ACQUIRED]-(a:Company) "
        "WHERE c.name =~ {name} "
        "RETURN collect([a.name, ac.type, ac.announced_on, a.categories]) as acquisitions", {"name": name})
    acquisitions = _acquisitions.single();
    _investments = db.run("MATCH(c:Company)-[:INVESTED_IN]->(fr:FundingRounds)-[f:FUNDED]->(o:Company) "
                    "WHERE c.name =~ {name} "
                    "AND fr.announced_on > '2018-01-01' "
                    "WITH o, fr, sum(fr.money_raised_usd) as money ORDER BY money DESC LIMIT 20 "
                    "WITH o, fr, money, fr.announced_on as date ORDER BY date DESC "
                    "RETURN collect([o.name, date, money]) as investments", {"name": name})
    investments = _investments.single(); 
    return Response(json.dumps({"competitors": [model.serialize_investment_competitors(competitor)
                                    for competitor in competitors['competitors']],
                                "acquisitions" : [model.serialize_acquisitions(acquisition)
                                    for acquisition in acquisitions['acquisitions']],
                                "investments" : [model.serialize_investments(investment)
                                    for investment in investments['investments']]}),
                    mimetype="application/json")


@controller.route("/investmentcompanygraph/<name>")
def get_investment_company_graph(name):
    db = model.get_db()
    results = db.run("MATCH(c:Company)-[:INVESTED_IN]->(fr:FundingRounds)-[f:FUNDED]->(o:Company)  "
        "WHERE c.name =~ {name} "
        "AND fr.announced_on > '2018-01-01' "
        "WITH c, fr, {investor:o.name} AS o_investors "
        "WITH c, {rounds:fr, investors:collect(o_investors)} as fr_rounds "
        "WITH {name:c.name, rounds:collect(fr_rounds)} as c_company "
        "RETURN{company:collect(c_company)}", {"name": name})
    founders = db.run("MATCH(p:Person)-[:FOUNDED]->(c:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(p.permalink) as founders", {"name": name})
    board = db.run("MATCH (p:Person)-[:BOARDMEMBER]->(c:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(p.permalink) as board", {"name": name})
    acquired = db.run ("MATCH (c:Company)-[:ACQUIRED]-(a:Company) "
        "WHERE c.name =~ {name} "
        "RETURN c.name as company, collect(a.name) as acquisition", {"name": name})
    return model.get_investment_company_graph(results, founders, board, acquired)


### INVESTORS ###
@controller.route('/investor', methods =['GET', 'POST'])
def get_investor_index():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('investor.html', message = message)


@controller.route('/investorsearch')
def get_investor():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = model.get_db()
        results = db.run("MATCH (p:Person) "
                 "WHERE p.permalink =~ {permalink} "
                 "RETURN p", {"permalink": "^(?i)" + q + "$"}
        )
        return Response(json.dumps([model.serialize_person(record[0]) for record in results]),
                        mimetype="application/json") 


@controller.route("/investor/<permalink>")
def get_investor_details(permalink):
    db = model.get_db()
    _education = db.run("MATCH (p:Person)-[s:SCHOOL]-(uni:Company) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN collect([uni.name, s.started_on, s.degree_type_name, s.degree_subject, s.completed_on]) as educations "
            "LIMIT 1", {"permalink": permalink})
    educations = _education.single();
    _jobs = db.run("MATCH (p:Person)-[j:JOB]-(c:Company) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN collect ([j.title, j.started_on, c.name, j.is_current, j.ended_on ]) as jobs", {"permalink": permalink})
    jobs = _jobs.single();
    _location = db.run("MATCH (p:Person)-[pa:PRIMARY_AFFILIATION]-(c:Company), "
            "(p)-[pl:PRIMARY_LOCATION]-(h:Headquarters) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN h.city as City, collect([c.name, pa.title]) as Primary", {"permalink": permalink})
    location = _location.single();
    _investments = db.run("MATCH(p:Person)-[:INVESTED_IN]->(fr:FundingRounds)-[f:FUNDED]->(o:Company) "
                    "WHERE p.permalink =~ {permalink} "
                    "AND fr.announced_on > '2018-01-01' "
                    "WITH o, fr, sum(fr.money_raised_usd) as money ORDER BY money DESC LIMIT 20 "
                    "WITH o, fr, money, fr.announced_on as date ORDER BY date DESC "
                    "RETURN collect([o.name, date, money]) as investments", {"permalink": permalink})
    investments = _investments.single(); 
    return Response(json.dumps({"education": [model.serialize_education(education)
                                    for education in educations['educations']],
                                "jobs": [model.serialize_jobs(job)
                                    for job in jobs['jobs']],
                                "city": location[0],
                                "primary_affiliation": location[1][0][0],
                                "primary_title": location[1][0][1],
                                "investments" : [model.serialize_investments(investment)
                                    for investment in investments['investments']]}),
                    mimetype="application/json")


@controller.route("/investorgraph/<permalink>")
def get_investor_graph(permalink):
    db = model.get_db()
    investments = db.run("MATCH(p:Person)-[i:INVESTED_IN]-(fr:FundingRounds)-[f:FUNDED]-(c:Company) "
        "WHERE p.permalink =~ {permalink} "
        "WITH p, fr, {investment:c.name} AS c_investments "
        "WITH p, {rounds:fr, investments:collect(c_investments)} as fr_rounds "
        "WITH {permalink:p.permalink, rounds:collect(fr_rounds)} as p_person "
        "RETURN {person:collect(p_person)}", {"permalink": permalink})
    partner_investments = db.run("MATCH (p:Person)-[pf:PARTNER_FUNDED]->(fr:FundingRounds)-[i:INVESTED_IN]->(ic:Company) "
        "WHERE p.permalink =~ {permalink} "
        "WITH p, fr, {investment:ic.name} AS ic_investments "
        "WITH p, {partner_rounds:fr, investments:collect(ic_investments)} AS pfr_rounds "
        "WITH {permalink:p.permalink, partner_rounds:collect(pfr_rounds)} as p_person "
        "RETURN {person:collect(p_person)}", {"permalink": permalink})
    
    return model.get_investor_graph(investments, partner_investments)



### PEOPLE ###
@controller.route('/person', methods =['GET', 'POST'])
def get_person_index():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('person.html', message = message)


@controller.route('/personsearch')
def get_person():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = model.get_db()
        results = db.run("MATCH (p:Person) "
                 "WHERE p.permalink =~ {permalink} "
                 "RETURN p", {"permalink": "^(?i)" + q + "$"})
        return Response(json.dumps([model.serialize_person(record[0]) for record in results]),
                        mimetype="application/json") 


@controller.route("/person/<permalink>")
def get_person_details(permalink):
    db = model.get_db()
    _education = db.run("MATCH (p:Person)-[s:SCHOOL]-(uni:Company) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN collect([uni.name, s.started_on, s.degree_type_name, s.degree_subject, s.completed_on]) as educations "
            "LIMIT 1", {"permalink": permalink})
    educations = _education.single();
    _jobs = db.run("MATCH (p:Person)-[j:JOB]-(c:Company) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN collect ([j.title, j.started_on, c.name, j.is_current, j.ended_on ]) as jobs", {"permalink": permalink})
    jobs = _jobs.single();
    _location = db.run("MATCH (p:Person)-[pa:PRIMARY_AFFILIATION]-(c:Company), "
            "(p)-[pl:PRIMARY_LOCATION]-(h:Headquarters) "
            "WHERE p.permalink =~ {permalink} "
            "RETURN h.city as City, collect([c.name, pa.title]) as Primary", {"permalink": permalink})
    location = _location.single();
    return Response(json.dumps({"education": [model.serialize_education(education)
                                    for education in educations['educations']],
                                "jobs": [model.serialize_jobs(job)
                                    for job in jobs['jobs']],
                                "city": location[0],
                                "primary_affiliation": location[1][0][0],
                                "primary_title": location[1][0][1]}),
                    mimetype="application/json")


@controller.route("/persongraph/<permalink>")
def get_person_graph(permalink):
    db = model.get_db()
    investments = db.run("MATCH(p:Person)-[i:INVESTED_IN]-(fr:FundingRounds)-[f:FUNDED]-(c:Company) "
        "WHERE p.permalink =~ {permalink} "
        "WITH p, fr, {investment:c.name} AS c_investments "
        "WITH p, {rounds:fr, investments:collect(c_investments)} as fr_rounds "
        "WITH {permalink:p.permalink, rounds:collect(fr_rounds)} as p_person "
        "RETURN {person:collect(p_person)}", {"permalink": permalink})
    
    return model.get_person_graph(investments)


### Headquarters ###
@controller.route('/headquarter', methods =['GET', 'POST'])
def get_headquarter_index():
    if request.method == 'GET':
        message = "This is a Test"
        return render_template('headquarter.html', message = message)


@controller.route('/headquartersearch')
def get_headquarter():
    try:
        q = request.args["q"]
    except KeyError:
        return []
    else:
        db = model.get_db()
        results = db.run("MATCH (h:Headquarters) "
                 "WHERE h.city =~ {city} "
                 "RETURN h", {"city": "^(?i)" + q + "$"})
        return Response(json.dumps([model.serialize_headquarter(record[0]) for record in results]),
                        mimetype="application/json") 


@controller.route("/headquarter/<city>")
def get_headquarter_details(city):
    db = model.get_db()
    _company_count = db.run("MATCH(c:Company)-[h:HEADQUARTERS]->(hd:Headquarters) "
                    "WHERE hd.city =~ {city} "
                    "RETURN count(c) as company_count", {"city": city})
    company_count = _company_count.single();
    _total_funding = db.run("MATCH(c:Company)-[h:HEADQUARTERS]->(hd:Headquarters), "
                    "(c)<-[f:FUNDED]-(fr:FundingRounds) "
                    "WHERE hd.city =~ {city} "
                    "AND fr.announced_on > '2018-01-01' "
                    "RETURN sum(fr.money_raised_usd) as total_funding", {"city": city})
    total_funding = _total_funding.single();
    _category_funding = db.run("MATCH(c:Company)-[h:HEADQUARTERS]->(hd:Headquarters), "
                "(c)<-[f:FUNDED]-(fr:FundingRounds), "
                "(c)-[:CATEGORY]->(cat:Category) "
                "WHERE hd.city =~ {city} "
                "WITH cat, sum(fr.money_raised_usd) as money ORDER BY money DESC LIMIT 25 "
                "RETURN collect([cat.name, money]) as category_funding", {"city": city})
    category_funding = _category_funding.single();
    _companies = db.run("MATCH(c:Company)-[h:HEADQUARTERS]->(hd:Headquarters), "
                "(c)<-[f:FUNDED]-(fr:FundingRounds) "
                "WHERE hd.city =~ {city} "
                "AND fr.announced_on > '2018-01-01' "
                "WITH c, sum(fr.money_raised_usd) as money ORDER BY money DESC LIMIT 25 "
                "RETURN collect([c.name,c.categories, money]) as companies", {"city": city})
    companies = _companies.single();
    _ico = db.run("MATCH(c:Company)-[h:HEADQUARTERS]->(hd:Headquarters), "
                "(c)<-[f:FUNDED]-(fr:FundingRounds) "
                "WHERE hd.city =~ {city} "
                "AND fr.announced_on > '2018-01-01' "
                "AND fr.type = 'initial_coin_offering' "
                "WITH c, sum(fr.money_raised_usd) as money ORDER BY money DESC LIMIT 25 "
                "RETURN collect([c.name,c.categories, money]) as companies", {"city": city})
    ico = _ico.single();
    return Response(json.dumps({"total_funding": total_funding[0],
                                "company_count" : company_count[0],
                                "category_funding": [model.serialize_category_funding(category)
                                    for category in category_funding['category_funding']],
                                "companies": [model.serialize_head_companies(city)
                                    for city in companies['companies']],
                                "ico_companies": [model.serialize_head_companies(city)
                                    for city in ico['companies']]}),
                    mimetype="application/json")

   
