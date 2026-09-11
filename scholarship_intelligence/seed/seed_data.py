"""Curated, authentic seed opportunities for U.S. Undergraduate International Students.

Each record represents an authentic U.S. undergraduate financial aid or scholarship program,
with traceable source evidence, decomposed funding, multiple deadlines, and verification records.
Zero fabricated requirements, zero invented acceptance probabilities.
"""
import hashlib
from datetime import date, datetime
from typing import Any, Dict, List

from scholarship_intelligence.domain.enums import (
    AmountPeriod,
    AuthorityTier,
    ConflictStatus,
    DeadlineType,
    FundingClassification,
    FundingComponentType,
    NeedPolicy,
    RequirementKind,
    RequirementType,
    RuleComparisonOp,
    RuleKind,
    RuleLogicalOp,
    TriState,
    VerificationState,
)

def compute_fingerprint(slug: str, cycle: str) -> str:
    payload = f"{slug}::{cycle}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

SEED_UNIVERSITIES: List[Dict[str, Any]] = [
    {
        "name": "Clark University",
        "city": "Worcester",
        "state": "MA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.clarku.edu/admissions/",
        "official_financial_aid_url": "https://www.clarku.edu/offices/financial-aid/prospective-students/international-students/",
    },
    {
        "name": "Berea College",
        "city": "Berea",
        "state": "KY",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.berea.edu/admissions/",
        "official_financial_aid_url": "https://www.berea.edu/admissions/international-students/costs-and-financial-aid",
    },
    {
        "name": "Dartmouth College",
        "city": "Hanover",
        "state": "NH",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_BLIND_INTERNATIONAL.value,
        "official_admissions_url": "https://admissions.dartmouth.edu/",
        "official_financial_aid_url": "https://admissions.dartmouth.edu/financial-aid/apply/international-students",
    },
    {
        "name": "Harvard University",
        "city": "Cambridge",
        "state": "MA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_BLIND_INTERNATIONAL.value,
        "official_admissions_url": "https://college.harvard.edu/admissions",
        "official_financial_aid_url": "https://college.harvard.edu/financial-aid/types-aid/international-students",
    },
    {
        "name": "Amherst College",
        "city": "Amherst",
        "state": "MA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_BLIND_INTERNATIONAL.value,
        "official_admissions_url": "https://www.amherst.edu/admission",
        "official_financial_aid_url": "https://www.amherst.edu/admission/financial_aid/international_students",
    },
    {
        "name": "Emory University",
        "city": "Atlanta",
        "state": "GA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://apply.emory.edu/",
        "official_financial_aid_url": "https://apply.emory.edu/financial-aid/types-of-aid/scholar-programs.html",
    },
    {
        "name": "University of Miami",
        "city": "Coral Gables",
        "state": "FL",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://admissions.miami.edu/",
        "official_financial_aid_url": "https://admissions.miami.edu/undergraduate/financial-aid/scholarships/stamps/index.html",
    },
    {
        "name": "Davidson College",
        "city": "Davidson",
        "state": "NC",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.davidson.edu/admission-and-financial-aid",
        "official_financial_aid_url": "https://www.davidson.edu/admission-and-financial-aid/financial-aid/scholarships/john-m-belk-scholarship",
    },
    {
        "name": "Soka University of America",
        "city": "Aliso Viejo",
        "state": "CA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.soka.edu/admission",
        "official_financial_aid_url": "https://www.soka.edu/financial-aid/undergraduate-tuition-and-fees/scholarships-and-grants",
    },
    {
        "name": "Skidmore College",
        "city": "Saratoga Springs",
        "state": "NY",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.skidmore.edu/admissions/",
        "official_financial_aid_url": "https://www.skidmore.edu/financialaid/international.php",
    },
    {
        "name": "Macalester College",
        "city": "Saint Paul",
        "state": "MN",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.macalester.edu/admissions/",
        "official_financial_aid_url": "https://www.macalester.edu/admissions/financial-aid/international/",
    },
    {
        "name": "Duke University",
        "city": "Durham",
        "state": "NC",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://admissions.duke.edu/",
        "official_financial_aid_url": "https://ousf.duke.edu/karsh-international-scholars/",
    },
    {
        "name": "Bowdoin College",
        "city": "Brunswick",
        "state": "ME",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_BLIND_INTERNATIONAL.value,
        "official_admissions_url": "https://www.bowdoin.edu/admissions/",
        "official_financial_aid_url": "https://www.bowdoin.edu/student-aid/prospective-students/international-students/index.html",
    },
    {
        "name": "Colby College",
        "city": "Waterville",
        "state": "ME",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.colby.edu/admission/",
        "official_financial_aid_url": "https://www.colby.edu/admission/financial-aid/international-students/",
    },
    {
        "name": "Washington and Lee University",
        "city": "Lexington",
        "state": "VA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.wlu.edu/admissions/",
        "official_financial_aid_url": "https://www.wlu.edu/admissions/scholarships-and-financial-aid/the-johnson-scholarship/",
    },
    {
        "name": "University of Richmond",
        "city": "Richmond",
        "state": "VA",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://admissions.richmond.edu/",
        "official_financial_aid_url": "https://scholars.richmond.edu/",
    },
    {
        "name": "Wesleyan University",
        "city": "Middletown",
        "state": "CT",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://www.wesleyan.edu/admission/",
        "official_financial_aid_url": "https://www.wesleyan.edu/admission/international/freeman.html",
    },
    {
        "name": "Vanderbilt University",
        "city": "Nashville",
        "state": "TN",
        "country": "US",
        "admissions_need_policy": NeedPolicy.NEED_AWARE_INTERNATIONAL.value,
        "official_admissions_url": "https://admissions.vanderbilt.edu/",
        "official_financial_aid_url": "https://www.vanderbilt.edu/scholarships/merit.php",
    },
]

SEED_PROVIDERS: List[Dict[str, Any]] = [
    {
        "name": "Stamps Scholars Program",
        "provider_type": "FOUNDATION",
        "website_url": "https://www.stampsscholars.org/",
        "country": "US",
        "description": "National merit scholarship foundation partnering with top U.S. colleges.",
    }
]

from scholarship_intelligence.seed.opportunities_builder import get_seed_opportunities

SEED_OPPORTUNITIES: List[Dict[str, Any]] = get_seed_opportunities()
