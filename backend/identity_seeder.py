"""
HoneyNet Company Identity Seeder
Uses Python Faker to generate ONE consistent corporate identity per attacker session.
Ensures identical employee names, company domain, executive titles, and payroll figures
across all generated files (.xlsx, .csv, .env, org charts, git history).
"""
import random
from typing import List
from faker import Faker
from backend.models import EmployeeIdentity, CompanyIdentity

fake = Faker()

def generate_company_identity(seed_key: str = "") -> CompanyIdentity:
    """
    Generates a deterministic corporate identity using a seed key (e.g. session_id).
    Same session always gets the exact same company identity.
    """
    if seed_key:
        Faker.seed(hash(seed_key) % 1000000)
        random.seed(hash(seed_key) % 1000000)
    
    company_name = f"{fake.company()} {random.choice(['Technologies', 'Holdings', 'Dynamics', 'Systems', 'Global', 'Capital'])}"
    domain = company_name.lower().replace(" ", "").replace(",", "").replace(".", "") + ".io"
    tax_id = f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
    hq = f"{fake.city()}, {fake.state_abbr()}"
    industry = "Enterprise SaaS & Cloud Infrastructure"

    # Standard corporate executive and engineering roster
    roles = [
        ("Chief Executive Officer", "Executive", "$385,000", "$150,000"),
        ("Chief Financial Officer", "Finance", "$320,000", "$110,000"),
        ("Chief Technology Officer", "Engineering", "$340,000", "$120,000"),
        ("VP of People & HR", "Human Resources", "$245,000", "$60,000"),
        ("Lead Infrastructure Engineer", "DevOps", "$210,000", "$40,000"),
        ("Staff Security Engineer", "Security", "$225,000", "$45,000"),
        ("Senior Accountant & Payroll Admin", "Finance", "$145,000", "$25,000"),
        ("Senior Backend Architect", "Engineering", "$195,000", "$35,000"),
    ]

    employees: List[EmployeeIdentity] = []
    for idx, (role, dept, salary, bonus) in enumerate(roles, start=101):
        first_name = fake.first_name()
        last_name = fake.last_name()
        full_name = f"{first_name} {last_name}"
        email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        emp_id = f"EMP-{idx}"

        employees.append(EmployeeIdentity(
            id=emp_id,
            name=full_name,
            email=email,
            role=role,
            department=dept,
            salary=salary,
            annual_bonus=bonus
        ))

    return CompanyIdentity(
        name=company_name,
        domain=domain,
        tax_id=tax_id,
        industry=industry,
        headquarters=hq,
        employees=employees
    )
