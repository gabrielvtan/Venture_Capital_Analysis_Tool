#!/usr/bin/env python3
import os
from json import dumps
from flask import Blueprint, render_template, request, session, Flask, redirect, g, Response


from flask import Flask, render_template, request, session

from datetime import datetime
from neo4j.v1 import GraphDatabase, basic_auth
from src.mappers import cypher

password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver('bolt://localhost',auth=basic_auth("neo4j", password))


def get_db():
    if not hasattr(g, 'neo4j_db'):
        g.neo4j_db = driver.session()
    return g.neo4j_db

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
        'money_raised_usd': company['money_raised_usd'],
        'city': company['city'],
        'country': company['country']
    }

def serialize_person(person):
    return {
        'permalink': person['permalink'],
        'first_name': person['first_name'],
        'last_name': person['last_name'],
        'image': person['image'],
        'gender': person['gender'],
        'born_on': person['born_on'],
        'bio': person['bio']
    }

def serialize_fundingRound(fundingRound):
    return {
        'announced_on' : fundingRound[0],
        'type': fundingRound[1],
        'money_raised_usd': fundingRound[2]
    }

def serialize_competitors(competitor):
    return {
        'competitor': competitor[0],
        'categories': competitor[1]
    }

def serialize_acquisitions(acquisition):
    return {
        'name': acquisition[0],
        'type': acquisition[1],
        'announced_on': acquisition[2],
        'categories': acquisition[3]
    }

def serialize_education(education):
    return {
        'school': education[0],
        'started_on': education[1],
        'degree_type_name': education[2],
        'degree_subject': education[3],
        'completed_on': education [4]
    }

def serialize_jobs(jobs):
    return {
        'title': jobs[0],
        'started_on': jobs[1],
        'company_name': jobs [2],
        'is_current': jobs[3],
        'ended_on': jobs[4]
    }

def get_company_graph(results, founders, board, acquired):
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
            for investor in fundingRound['investors']:
                investors = {"name": investor['investor'], "label": "investor"}
                try:
                    source = nodes.index(investors)
                except ValueError:
                    nodes.append(investors)
                    source = i
                    i += 1
                    z += 1
                rels.append({"source": source, "target": target_1, "action": "INVESTED_IN"})
    
    fd = []
    for record in founders:
        for founder in record['founders']:
            founders = {"permalink": founder, "label": "founders"}
            fd.append(founder)
            try:
                source = nodes.index(founders)
            except ValueError:
                nodes.append(founders)
                source = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "FOUNDED"})

    for record in board:
        for member in record['board']:
            if member in fd:
                pass
            else:
                members = {"permalink": member, "label": "boardMembers"}
                try:
                    source = nodes.index(members)
                except ValueError:
                    nodes.append(members)
                    source = i
                    i += 1
                rels.append({"source": source, "target": target, "action" : "BOARDMEMBER"})
    
    for record in acquired:
        for acquisition in record['acquisition']:
            acquisitions = {"name": acquisition, "label": "acquisitions"}
            try:
                source = nodes.index(acquisitions)
            except ValueError:
                nodes.append(acquisitions)
                source = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "ACQUIRED"})

    return Response(dumps({"nodes": nodes, "links": rels, "label": "hide"}),
                    mimetype="application/json")


def get_person_graph(investments):
    nodes = []
    rels = []
    i = 0
    for record in investments:
        nodes.append({"name": record[0]['person'][0]['permalink'], 
            "label": "person"})
        source = i
        i += 1
        z = 0
        for fundingRound in record[0]['person'][z]['rounds']:
            rounds = {
                "uuid": fundingRound['rounds']["uuid"], 
                "type": fundingRound['rounds']["type"], 
                "label": "rounds"}
            try:
                target = nodes.index(rounds)
            except ValueError:
                nodes.append(rounds)
                target = i
                source_1 = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "FUNDED"})
            for investment in fundingRound['investments']:
                investments = {"name": investment['investment'], "label": "investment"}
                try:
                    target = nodes.index(investments)
                except ValueError:
                    nodes.append(investments)
                    target = i
                    i += 1
                    z += 1
                rels.append({"source": source_1, "target": target, "action": "INVESTED_IN"})

    return Response(dumps({"nodes": nodes, "links": rels, "label": "hide"}),
                    mimetype="application/json")

def get_investor_graph(investments, partner_investments):
    nodes = []
    rels = []
    i = 0
    for record in investments:
        nodes.append({"name": record[0]['person'][0]['permalink'], 
            "label": "person"})
        source = i
        i += 1
        z = 0
        for fundingRound in record[0]['person'][z]['rounds']:
            rounds = {
                "uuid": fundingRound['rounds']["uuid"], 
                "type": fundingRound['rounds']["type"], 
                "label": "rounds"}
            try:
                target = nodes.index(rounds)
            except ValueError:
                nodes.append(rounds)
                target = i
                source_1 = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "FUNDED"})
            for investment in fundingRound['investments']:
                investments = {"name": investment['investment'], "label": "investment"}
                try:
                    target = nodes.index(investments)
                except ValueError:
                    nodes.append(investments)
                    target = i
                    i += 1
                    z += 1
                rels.append({"source": source_1, "target": target, "action": "INVESTED_IN"})

    for record in partner_investments:
        source = 0
        z = 0
        for fundingRound in record[0]['person'][z]['partner_rounds']:
            rounds = {
                "uuid": fundingRound['partner_rounds']["uuid"], 
                "type": fundingRound['partner_rounds']["type"], 
                "label": "partner_rounds"}
            try:
                target = nodes.index(rounds)
            except ValueError:
                nodes.append(rounds)
                target = i
                source_1 = i
                i += 1
            rels.append({"source": source, "target": target, "action" : "PARTNER_FUNDED"})
            for investment in fundingRound['investments']:
                investments = {"name": investment['investment'], "label": "partner_investment"}
                try:
                    target = nodes.index(investments)
                except ValueError:
                    nodes.append(investments)
                    target = i
                    i += 1
                    z += 1
                rels.append({"source": source_1, "target": target, "action": "INVESTED_IN"})

    return Response(dumps({"nodes": nodes, "links": rels, "label": "hide"}),
                    mimetype="application/json")