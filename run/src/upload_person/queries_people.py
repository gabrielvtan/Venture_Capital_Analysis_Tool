## The following queries are for the Person category

# MERGE People Properties 
def person_prop():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        WITH DISTINCT o

        MERGE (person:Person {uuid:o.uuid}) 
        SET person.type = o.type,
            person.permalink = o.properties.permalink,
            person.image = o.properties.profile_image_url, 
            person.first_name = o.properties.first_name, 
            person.last_name = o.properties.last_name,
            person.gender = o.properties.gender,
            person.bio = o.properties.bio,
            person.born_on = o.properties.born_on
        """)

# MERGE primary affiliation properties 
def comp_prop():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.primary_affiliation.item.relationships.organization AS primaryAff
        WITH DISTINCT primaryAff

        MERGE(primary:Company{uuid:primaryAff.uuid})
        SET primary.name = primaryAff.properties.name
        """)

# MATCH AND MERGE (person)-[:PRIMARY_AFFILIATION]-(company)
def person_pa_comp():
    return ("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.primary_affiliation.item AS primaryAff

        MATCH(person:Person {uuid:o.uuid})
        MATCH(primary:Company{uuid:primaryAff.relationships.organization.uuid})
        MERGE(person)-[prime:PRIMARY_AFFILIATION
            {uuid : primaryAff.uuid,
            title : COALESCE(primaryAff.properties.title, []),
            started_on : COALESCE(primaryAff.properties.started_on, []),
            is_current : COALESCE(primaryAff.properties.is_current,[])
            }]->(primary);
    """)

# MERGE school properties (done already from company upload)
def school_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.degrees.items AS degree

        MERGE(uni:Company{uuid:degree.relationships.school.uuid})
        SET uni.name = degree.relationships.school.properties.name
    """)

# MATCH and MERGE (person) -[:SCHOOL]->(company)
def school_s_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.degrees.items AS degree

        MATCH(person:Person {uuid:o.uuid})
        MATCH(uni:Company{uuid:degree.relationships.school.uuid})
        MERGE(person)-[:SCHOOL
            {uuid : degree.uuid,
            started_on : COALESCE(degree.properties.started_on,[]),
            completed_on : COALESCE(degree.properties.completed_on,[]),
            degree_type_name : COALESCE(degree.properties.degree_type_name,[]),
            degree_subject : COALESCE(degree.properties.degree_subject,[])
            }]->(uni)
    """)

# MERGE job company properties
def job_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.jobs.items AS job
        WITH DISTINCT job

        MERGE (company:Company{uuid:job.relationships.organization.uuid})
        SET company.name = job.relationships.organization.properties.name
    """)

#MATCH and MERGE (person)-[:JOB]->(company)
def person_j_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.jobs.items AS job

        MATCH(person:Person{uuid:o.uuid})
        MATCH(company:Company{uuid:job.relationships.organization.uuid})
        MERGE(person)-[:JOB
        {uuid:job.uuid,
        title:COALESCE(job.properties.title,[]),
        started_on:COALESCE(job.properties.started_on,[]),
        ended_on:COALESCE(job.properties.ended_on,[]),
        is_current:COALESCE(job.properties.is_current,[])
        }]->(company)
    """)

# MERGE funding rounds Properties
def fr_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.investments.items as investment
        WITH DISTINCT investment

        MERGE (fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        SET fundingRound.type = investment.relationships.funding_round.properties.funding_type,
            fundingRound.series =investment.relationships.funding_round.properties.series,
            fundingRound.announced_on = investment.relationships.funding_round.properties.announced_on,
            fundingRound.money_raised_usd = investment.relationships.funding_round.properties.money_raised_usd,
            fundingRound.money_raised_currency_code = investment.relationships.funding_round.properties.money_raised_currency_code,
            fundingRound.pre_money_valuation_usd = investment.relationships.funding_round.properties.pre_money_valuation_usd  
    """)

# MATCH AND MERGE (person)-[:INVESTED_IN]-(fundingRound)
def person_f_fr():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.investments.items as investment

        MATCH(person:Person{uuid:o.uuid})
        MATCH(fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        MERGE(person)-[:INVESTED_IN
            {uuid:investment.uuid,
            money_invested_usd:COALESCE(investment.properties.money_invested_usd,[]),
            is_lead_investor:COALESCE(investment.properties.is_lead_investor,[]),
            announced_on:COALESCE(investment.properties.announced_on,[])
            }]->(fundingRound)
    """)

# MERGE company investment properties
def invest_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.investments.items as investment

        MERGE(ic:Company{uuid:investment.relationships.invested_in.uuid})
        SET ic.name = investment.relationships.invested_in.properties.name
    """)

# MATCH and MERGE (fundingRound)-[:FUNDED]-(company)
def fr_f_comp():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.investments.items as investment
        
        MATCH(fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        MATCH(ic:Company{uuid:investment.relationships.invested_in.uuid})
        MERGE(fundingRound)-[:FUNDED]->(ic)
    """)


# MERGE primary_location properties
def head_prop():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.primary_location.item as headquarter
        WITH DISTINCT headquarter

        MERGE(head:Headquarters{city:COALESCE(headquarter.properties.city,[])})
        SET head.region = headquarter.properties.region,
            head.country = headquarter.properties.country
    """)


# MATCH AND MERGE (person)-[:HEADQUARTERS]->(head)
def person_h_head():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.primary_location.item as headquarter

        MATCH(person:Person{uuid:o.uuid})
        MATCH (head:Headquarters{city:headquarter.properties.city})
        MERGE(person)-[:PRIMARY_LOCATION
            {city: COALESCE(headquarter.properties.city,[]),
            region: COALESCE(headquarter.properties.region,[]),
            country: COALESCE(headquarter.properties.country,[])
            }]->(head)
        """)

# MERGE Partner Investments Funding Round Properties
def partner_props():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.partner_investments.items as investment
        WITH DISTINCT investment

        MERGE(fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        SET fundingRound.type = investment.relationships.funding_round.properties.funding_type,
            fundingRound.announced_on = investment.relationships.funding_round.properties.announced_on,
            fundingRound.series = investment.relationships.funding_round.properties.series,
            fundingRound.money_raised_usd = investment.relationships.funding_round.properties.money_raised_usd,
            fundingRound.money_raised_currency_code = investment.relationships.funding_round.properties.money_raised_currency_code,
            fundingRound.pre_money_valuation_usd = investment.relationships.funding_round.properties.pre_money_valuation_usd
    """)


# MATCH AND MERGE (person)-[:PARTNER_FUNDED]-(fr)
def partner_pf_fr():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.partner_investments.items as investment

        MATCH(person:Person{uuid:o.uuid})
        MATCH(fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        MERGE(person)-[pf:PARTNER_FUNDED]->(fundingRound)
    """)


# MERGE investment company properties
def investment_company():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.partner_investments.items as investment

        MERGE(ic:Company{uuid:investment.relationships.funding_round.relationships.funded_organization.uuid})
        SET ic.name = investment.relationships.funding_round.relationships.funded_organization.properties.name
    """) 


# MATCH AND MERGE (fr)-[:INVESTED_IN]-(ic)
def fr_i_ic():
    return("""
        WITH {json} as value
        UNWIND value.data AS o
        UNWIND o.relationships.partner_investments.items as investment

        MATCH(fundingRound:FundingRounds{uuid:investment.relationships.funding_round.uuid})
        MATCH(ic:Company{uuid:investment.relationships.funding_round.relationships.funded_organization.uuid})
        MERGE(fundingRound)-[:INVESTED_IN]->(ic)
    """)