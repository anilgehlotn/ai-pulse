"""Creates demo data. Run: python -m app.seed

python -m app.seed             wipes the database and seeds it again
python -m app.seed --if-empty  seeds only if there are no users yet (Docker runs this on every start)

All passwords are: pulse123
"""
import sys

from .db import Base, engine, SessionLocal
from . import models
from .auth import hash_password
from .services.questions import load_questions, questions_for
from .privacy import publish_groups
from .routes.dashboard import load_groups

PEOPLE_NORTHWIND = [
    # name, email, department, role, job_role, seniority
    ("Asha Rao", "asha@northwind.test", None, "admin", "manager", "lead"),
    ("Vikram Shah", "vikram@northwind.test", "Sales", "employee", "sales", "senior"),
    ("Neha Gupta", "neha@northwind.test", "Sales", "employee", "sales", "junior"),
    ("Rohan Mehta", "rohan@northwind.test", "Sales", "employee", "sales", "mid"),
    ("Priya Nair", "priya@northwind.test", "Support", "employee", "support", "junior"),
    ("Arjun Iyer", "arjun@northwind.test", "Support", "employee", "support", "senior"),
    ("Kavitha Menon", "kavitha@northwind.test", "Support", "employee", "support", "mid"),
    ("Dev Malhotra", "dev@northwind.test", "Engineering", "employee", "engineering", "lead"),
    ("Sara Thomas", "sara@northwind.test", "Engineering", "employee", "engineering", "mid"),
    ("Imran Khan", "imran@northwind.test", "HR", "employee", "manager", "senior"),
    # Added so Sales and Support have enough respondents to show on the dashboard.
    ("Farah Ali", "farah@northwind.test", "Sales", "employee", "sales", "mid"),
    ("Anita Desai", "anita@northwind.test", "Sales", "employee", "sales", "senior"),
    ("Karan Joshi", "karan@northwind.test", "Sales", "employee", "sales", "junior"),
    ("Lakshmi Rao", "lakshmi@northwind.test", "Support", "employee", "support", "mid"),
    ("Nikhil Bose", "nikhil@northwind.test", "Support", "employee", "support", "junior"),
    ("Tara Singh", "tara@northwind.test", "Support", "employee", "support", "senior"),
    ("Omar Sheikh", "omar@northwind.test", "Engineering", "employee", "engineering", "senior"),
]
PEOPLE_BLUEPEAK = [
    ("Meera Pillai", "meera@bluepeak.test", None, "admin", "manager", "lead"),
    ("Tom Fernandes", "tom@bluepeak.test", "Stores", "employee", "sales", "mid"),
    ("Lina George", "lina@bluepeak.test", "Stores", "employee", "sales", "junior"),
    ("Kabir Das", "kabir@bluepeak.test", "Customer Care", "employee", "support", "senior"),
]

# People who completed the whole diagnostic. Every MCQ is answered with the option worth `level`
# points and every open answer is scored `level`, so each person's average is exactly `level`,
# unless they are in SAFETY_LEVELS below. The flags go on their open answers.
FULL_DIAGNOSTICS = [
    # email, organization, level, open answer, flags
    ("neha@northwind.test", "Northwind Logistics", 2, "I paste call notes into ChatGPT and send the summary to customers without reading it.", ["unreviewed_output"]),
    ("rohan@northwind.test", "Northwind Logistics", 3, "I draft follow-up emails with AI most days but rarely check the product details it adds.", ["unreviewed_output"]),
    ("anita@northwind.test", "Northwind Logistics", 5, "I built a prompt library for account research that the whole sales team uses, with a review step.", []),
    ("karan@northwind.test", "Northwind Logistics", 2, "Copilot writes my CRM notes and I paste them in as they are.", ["unreviewed_output"]),
    ("arjun@northwind.test", "Northwind Logistics", 4, "I draft replies with AI, then check every policy detail against our help centre before sending.", []),
    ("kavitha@northwind.test", "Northwind Logistics", 3, "I summarise long ticket threads with ChatGPT, including the customer's details.", ["customer_data_shared"]),
    ("lakshmi@northwind.test", "Northwind Logistics", 3, "I pasted a customer's order history into an AI tool to work out a refund.", ["customer_data_shared"]),
    ("nikhil@northwind.test", "Northwind Logistics", 2, "AI suggests a reply and I usually send it straight away.", ["unreviewed_output"]),
    ("tara@northwind.test", "Northwind Logistics", 4, "I use AI to spot recurring issues across tickets and check the patterns by hand.", []),
    ("dev@northwind.test", "Northwind Logistics", 4, "I use a code assistant for tests and refactors and review every change before merging.", []),
    ("sara@northwind.test", "Northwind Logistics", 3, "I ask Copilot to write small functions and then read them through.", []),
    ("omar@northwind.test", "Northwind Logistics", 2, "I let the assistant generate migration scripts and ship them if the tests pass.", ["unreviewed_output"]),
    ("imran@northwind.test", "Northwind Logistics", 2, "I've tried ChatGPT for job descriptions; I'm not sure what our AI policy says.", ["policy_unaware"]),
    ("ravi@consult.test", "Northwind Logistics", 3, "I use AI to draft workshop agendas and edit them before sharing.", []),
    ("ravi@consult.test", "Bluepeak Retail", 3, "I summarise store visit notes with AI and check the figures myself.", []),
]

# These people use AI as much as their level says but skip the safeguards: their safety MCQs
# get these points instead. Together with Vikram's skimmed review below, this puts Sales in
# the "Exposed" quadrant (adoption 3.2, safety 2.2) while Support stays "Leading".
SAFETY_LEVELS = {
    "neha@northwind.test": 1,
    "rohan@northwind.test": 2,
    "karan@northwind.test": 1,
}


def print_summary(db, orgs):
    """Respondents per team, and what leadership will see under the anonymity rule."""
    for org in orgs:
        groups = load_groups(db, org)
        print(f"{org.name}: " + ", ".join(f"{g['name']} {len(g['respondents'])}" for g in groups))
        published = publish_groups(groups)
        shown = ", ".join(f"{g['name']} ({g['privacy']})" for g in published["groups"])
        print(f"  leadership sees: {shown}; overall {published['overall']['privacy']}")


def run():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    def make_org(name, depts):
        org = models.Organization(name=name)
        db.add(org)
        db.flush()
        d = {}
        for dn in depts:
            dept = models.Department(org_id=org.id, name=dn)
            db.add(dept)
            db.flush()
            d[dn] = dept.id
        return org, d

    nw, nw_depts = make_org("Northwind Logistics", ["Sales", "Support", "Engineering", "HR"])
    bp, bp_depts = make_org("Bluepeak Retail", ["Stores", "Customer Care"])

    users = {}
    # bcrypt is deliberately slow, so hash the shared demo password once instead of per user.
    demo_password_hash = hash_password("pulse123")

    def add_people(org, depts, people):
        for name, email, dept, role, job_role, seniority in people:
            u = users.get(email)
            if not u:
                u = models.User(name=name, email=email, password_hash=demo_password_hash)
                db.add(u)
                db.flush()
                users[email] = u
            db.add(models.Membership(
                user_id=u.id, org_id=org.id,
                department_id=depts.get(dept) if dept else None,
                role=role, job_role=job_role, seniority=seniority,
            ))

    add_people(nw, nw_depts, PEOPLE_NORTHWIND)
    add_people(bp, bp_depts, PEOPLE_BLUEPEAK)

    # A consultant who works with both companies
    add_people(nw, nw_depts, [("Ravi Kapoor", "ravi@consult.test", "HR", "employee", "manager", "senior")])
    add_people(bp, bp_depts, [("Ravi Kapoor", "ravi@consult.test", None, "admin", "manager", "senior")])
    db.flush()

    # Some existing results so dashboards aren't empty
    question_types = {q["id"]: q["type"] for q in load_questions()}

    def answer(email, org, qid, text, score, reason=None, flags=None):
        m = db.query(models.Membership).filter_by(user_id=users[email].id, org_id=org.id).first()
        status = "mcq" if question_types[qid] == "mcq" else "scored"
        db.add(models.Response(membership_id=m.id, question_id=qid, answer=text, score=score, reason=reason,
                               flags=flags or [], status=status, scoring_version=None if status == "mcq" else "seed"))

    answer("vikram@northwind.test", nw, "common-freq", "Daily", 4)
    answer("vikram@northwind.test", nw, "common-open", "Used ChatGPT to draft 20 follow-up emails and edited each one.", 4, "Regular use with editing.", [])
    answer("vikram@northwind.test", nw, "common-review", "Skim it", 2)
    answer("priya@northwind.test", nw, "common-freq", "A few times a month", 2)
    answer("priya@northwind.test", nw, "common-open", "Pasted a customer's complaint thread into ChatGPT to summarise it.", 3, "Useful summary but shared customer data.", ["customer_data_shared"])
    answer("tom@bluepeak.test", bp, "common-freq", "A few times a week", 3)
    answer("kabir@bluepeak.test", bp, "common-open", "Uploaded our full customer refund list to an AI tool to find patterns.", 3, "Good idea, unsafe data handling.", ["customer_data_shared", "confidential_data_shared"])
    answer("kabir@bluepeak.test", bp, "common-freq", "Daily", 4)

    orgs = {nw.name: nw, bp.name: bp}
    for email, org_name, level, open_text, flags in FULL_DIAGNOSTICS:
        org = orgs[org_name]
        m = db.query(models.Membership).filter_by(user_id=users[email].id, org_id=org.id).first()
        for q in questions_for(m.job_role, m.seniority):
            if q["type"] == "mcq":
                points = SAFETY_LEVELS.get(email, level) if q["dimension"] == "safety" else level
                option = next(o for o in q["options"] if o["points"] == points)
                answer(email, org, q["id"], option["text"], points)
            else:
                answer(email, org, q["id"], open_text, level, f"Seeded at level {level}.", flags)

    db.commit()
    print("Seeded. Log in with any seeded email and password 'pulse123'.")
    print_summary(db, [nw, bp])
    db.close()


def run_if_empty():
    """Seed only a database with no users, so restarting a container never wipes real data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    has_users = db.query(models.User).first() is not None
    db.close()
    if has_users:
        print("Database already has data; not seeding.")
        return False
    run()
    return True


def main(argv):
    if "--if-empty" in argv:
        run_if_empty()
    else:
        run()


if __name__ == "__main__":
    main(sys.argv[1:])
