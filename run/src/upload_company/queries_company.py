## Test - for Investment companies and schools 
"""
WITH "https://api.crunchbase.com/v3.1/organizations/tiger-global?data=key_set_url?relationships=funding_rounds,founders,board_members_and_advisors,investments,acquisitions,acquired_by,ipo,funds,category,current_team&user_key=cf5494206fc66e0d489c8e3762a8ffd3" AS url
CALL apoc.load.json(url) YIELD value
UNWIND value.data AS o
UNWIND o.relationships.current_team.items as currentTeam
WITH DISTINCT currentTeam

"""

## Test - Get info from DB
def test_query():
    return("""
        MATCH(c)
        RETURN count(c) AS NodeCount
    """)

        

# CONSTRAINTS
def const_comp():
    return("CREATE CONSTRAINT ON (c:Company) ASSERT c.uuid IS UNIQUE;")

def const_fr():
    return("CREATE CONSTRAINT ON (fr:FundingRounds) ASSERT fr.uuid IS UNIQUE;")

def const_pers():
    return("CREATE CONSTRAINT ON (p:Person) ASSERT p.uuid IS UNIQUE;")

def const_in():
    return ("CREATE CONSTRAINT ON (in:INVESTED_IN) ASSERT in.uuid IS UNIQUE;")

def const_head():
    return("CREATE CONSTRAINT ON (h:Headquarters) ASSERT h.city IS UNIQUE;") 

def const_cat():
    return("CREATE CONSTRAINT ON (c:Category) ASSERT c.uuid IS UNIQUE;") 

def const_ipo():
    return("CREATE CONSTRAINT ON (i:Ipo) ASSERT i.uuid IS UNIQUE;") 


# INDEXES
def ind_comp():
    return ("CREATE INDEX ON :Company(name);")

def ind_pers():
    return("CREATE INDEX ON :Person(permalink);")

def ind_cat():
    return("CREATE INDEX ON :Category(name);")

def ind_fr():
    return("CREATE INDEX ON :FundingRounds(type);")



# MERGE Company Properties 
def comp_prop():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        WITH DISTINCT o

        MERGE (company:Company {uuid:o.uuid}) 
        SET company.type = o.type, 
            company.name = o.properties.name,
            company.image = o.properties.profile_image_url, 
            company.description = o.properties.description,
            company.primary_role = o.properties.primary_role,
            company.founded_on = o.properties.founded_on,
            company.stock_symbol = o.properties.stock_symbol,
            company.total_funding_usd = o.properties.total_funding_usd,
            company.number_of_investments = o.properties.number_of_investments,
            company.homepage_url = o.properties.homepage_url,
            company.categories = reduce(categories = [], cat IN o.relationships.categories.items | categories + cat.properties.name),
            company.went_public_on = COALESCE(o.relationships.ipo.item.properties.went_public_on, []),
            company.opening_valuation_usd = COALESCE(o.relationships.ipo.item.properties.opening_valuation_usd, []),
            company.money_raised_usd = COALESCE(o.relationships.ipo.item.properties.money_raised_usd, []),
            company.city = COALESCE(o.relationships.headquarters.item.properties.city, []),
            company.region = COALESCE(o.relationships.headquarters.item.properties.region, []),
            company.country = COALESCE(o.relationships.headquarters.item.properties.country, [])
        """)


# MERGE funding round properties
def fr_prop():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.funding_rounds.items AS fundingRound
        WITH DISTINCT fundingRound

        MERGE (funding_round:FundingRounds{uuid:fundingRound.uuid})
            SET funding_round.type= fundingRound.properties.funding_type,
            funding_round.announced_on = fundingRound.properties.announced_on,
            funding_round.money_raised_currency_code = fundingRound.properties.money_raised_currency_code,
            funding_round.money_raised_usd = fundingRound.properties.money_raised_usd,
            funding_round.pre_money_valuation = fundingRound.properties.pre_money_valuation;
        """)


# MATCH AND MERGE (funding_round)-[:FUNDED]->(company)
def fr_f_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.funding_rounds.items AS fundingRound

        MATCH (company:Company {uuid:o.uuid})
        MATCH (funding_round:FundingRounds{uuid:fundingRound.uuid})
        MERGE (funding_round)-[funded:FUNDED]->(company);
        """)



# MERGE investment company properties
def investComp_prop():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.funding_rounds.items AS fundingRound
        UNWIND fundingRound.relationships.investments AS investment
        UNWIND investment.relationships.investors AS investmentCompany
        WITH DISTINCT investmentCompany

        MERGE (investment_company:Company {uuid:investmentCompany.uuid})
            SET investment_company.name = investmentCompany.properties.name,
            investment_company.description = investmentCompany.properties.description,
            investment_company.primary_role = investmentCompany.properties.primary_role,
            investment_company.founded_on = investmentCompany.properties.founded_on,
            investment_company.number_of_investments = investmentCompany.properties.number_of_investments;
        """)



# MATCH AND MERGE (investment_company)-[:INVESTED_IN]->(funding_round)
def investComp_i_fr():
    return("""
    WITH {json} as value
    UNWIND value.data AS o
    UNWIND o.relationships.funding_rounds.items AS fundingRound
    UNWIND fundingRound.relationships.investments AS investment
    UNWIND investment.relationships.investors AS investmentCompany
    UNWIND CASE WHEN investment.relationships.partners = []
        THEN [null]
        ELSE investment.relationships.partners END
        AS companyPartner

    MATCH (investment_company:Company {uuid:investmentCompany.uuid})
    MATCH (funding_round:FundingRounds{uuid:fundingRound.uuid})
    MERGE (investment_company)-[invested:INVESTED_IN
        {uuid : investment.uuid,
        money_invested_currency_code : COALESCE(investment.properties.money_invested_currency_code, []),
        money_invested_usd : COALESCE(investment.properties.money_invested_usd, []),
        is_lead_investor : COALESCE(investment.properties.is_lead_investor, []),
        announced_on : investment.properties.announced_on,
        partner_permalink : COALESCE(companyPartner.properties.permalink,[])
        }]->(funding_round);
    """)



# MERGE founder properties
def found_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.founders.items AS founderCompany
        WITH DISTINCT founderCompany

        MERGE (founder:Person{uuid:founderCompany.uuid}) 
        SET founder.permalink = founderCompany.properties.permalink,
            founder.bio = founderCompany.properties.bio,
            founder.gender = founderCompany.properties.gender,
            founder.born_on = founderCompany.properties.born_on;
        """)



# MATCH AND MERGE (founder)-[:FOUNDED]->(company)
def found_f_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.founders.items AS founderCompany

        MATCH (founder:Person{uuid:founderCompany.uuid})
        MATCH (company:Company {uuid:o.uuid})
        MERGE (founder)-[founded:FOUNDED]->(company)
        """)


# MERGE board memeber properties
def board_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.board_members_and_advisors.items AS members
        WITH DISTINCT members

        MERGE(board_member:Person{uuid:members.relationships.person.uuid})
            SET board_member.permalink = members.relationships.person.properties.permalink,
            board_member.bio = members.relationships.person.properties.bio,
            board_member.gender = members.relationships.person.properties.gender,
            board_member.born_on = members.relationships.person.properties.born_on
        """)


# MATCH AND MERGE (board_member)-[:BOARDMEMBER]->(company)
def board_b_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.board_members_and_advisors.items AS members

        MATCH(board_member:Person{uuid:members.relationships.person.uuid})
        MATCH (company:Company {uuid:o.uuid})
        MERGE (board_member)-[boardMember:BOARDMEMBER
            {uuid:members.uuid,
            title:members.properties.title,
            started_on:COALESCE(members.properties.started_on,[])
            }]->(company)
        """)

# MATCH AND MERGE (company)-[:ACQUIRED]->(company)
def comp_a_acquiree():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.acquisitions.items AS acquisitions

        MATCH (company:Company {uuid:o.uuid})
        MATCH (acquisition:Company{uuid:acquisitions.relationships.acquiree.uuid})
        MERGE (company)-[acquired:ACQUIRED
            {uuid:COALESCE(acquisitions.uuid,[]),
            type:COALESCE(acquisitions.properties.acquisition_type,[]),
            announced_on:COALESCE(acquisitions.properties.announced_on,[])
            }]->(acquisition)
        """)



# MERGE headquarters Properties
def head_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.headquarters.item as headquarter
        WITH DISTINCT headquarter

        MERGE(head:Headquarters{city:headquarter.properties.city})
        SET head.region = headquarter.properties.region,
            head.country = headquarter.properties.country
    """)

# MATCH AND MERGE (company)-[:HEADQUARTERS]->(head)
def comp_h_head():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.headquarters.item as headquarter

        MATCH (company:Company {uuid:o.uuid})
        MATCH (head:Headquarters{city:headquarter.properties.city})
        MERGE(company)-[headquartered:HEADQUARTERS
            {street: COALESCE(headquarter.properties.street_1,[]),
            city: COALESCE(headquarter.properties.city,[]),
            region: COALESCE(headquarter.properties.region,[]),
            country: COALESCE(headquarter.properties.country,[]),
            postal_code: COALESCE(headquarter.properties.postal_code,[])
            }]->(head)
        """)

# MERGE categories properties
def cat_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.categories.items as category
        WITH DISTINCT category

        MERGE(cat:Category{uuid:category.uuid})
        SET cat.name = category.properties.name,
            cat.category_groups = category.properties.category_groups
        """)


# MATCH AND MERGE (company)-[:CATEGORY]-(cat)
def comp_c_cat():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.categories.items as category

        MATCH (company:Company {uuid:o.uuid})
        MATCH (cat:Category{uuid:category.uuid})
        MERGE (company)-[:CATEGORY]->(cat)
    """)


# MERGE ipo properties
def ipo_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.ipo.item as ipo
        WITH DISTINCT ipo

        MERGE(i:Ipo{uuid:ipo.uuid})
        SET i.went_public_on = ipo.properties.went_public_on,
            i.type = ipo.type,
            i.opening_valuation_usd = ipo.properties.opening_valuation_usd,
            i.money_raised_usd = ipo.properties.money_raised_usd,
            i.stock_exchange_symbol = ipo.properties.stock_exchange_symbol
    """)

# MATCH and Merge (comp)-[:IPO]->(ipo)
def comp_i_ipo():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.ipo.item as ipo

        MATCH (company:Company {uuid:o.uuid})
        MATCH (i:Ipo{uuid:ipo.uuid})
        MERGE(company)-[:IPO]-(i)
        """)