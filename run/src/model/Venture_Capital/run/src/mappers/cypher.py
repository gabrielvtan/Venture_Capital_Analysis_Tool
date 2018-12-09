#!/usr/bin/env python3

def get_graph(company):
    return ("MATCH(c:Company)<-[f:FUNDED]-(fr:FundingRounds)<-[:INVESTED_IN]-(o:Company) "
            "WHERE c.name =~ {company} "
            "WITH c, fr, {investor:o.name} AS o_investors "
            "WITH c, {rounds:fr, investors:collect(o_investors)} as fr_rounds "
            "WITH {name:c.name, rounds:collect(fr_rounds)} as c_company "
            "RETURN{company:collect(c_company)}", {"company": company})