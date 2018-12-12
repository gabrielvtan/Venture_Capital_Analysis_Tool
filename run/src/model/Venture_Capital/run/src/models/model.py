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
        'city': company['city'],
        'country': company['country']
    }

def serialize_fundingRound(fundingRound):
    return {
        'announced_on' : fundingRound[0],
        'type': fundingRound[1],
        'money_raised_usd': fundingRound[2]
    }

def get_graph(results):
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
                rels.append({"source": source, "target": target_1, "action": "INVESTED_IN"})
    return Response(dumps({"nodes": nodes, "links": rels}),
                    mimetype="application/json")


