from scholarship_intelligence.domain.enums import AmountPeriod, ConflictStatus
"""Idempotent seed database loader for Phase 1A data foundation."""
from typing import Dict
from sqlalchemy.orm import Session

from scholarship_intelligence.models.application_requirement import ApplicationRequirement
from scholarship_intelligence.models.deadline import Deadline
from scholarship_intelligence.models.eligibility import EligibilityRule, Requirement
from scholarship_intelligence.models.funding import Award, FundingComponent
from scholarship_intelligence.models.opportunity import ScholarshipOpportunity
from scholarship_intelligence.models.provider import Provider
from scholarship_intelligence.models.source import DiscoverySource, OfficialSource
from scholarship_intelligence.models.university import University
from scholarship_intelligence.models.conflict import ConflictRecord
from scholarship_intelligence.models.verification import VerificationRecord
from scholarship_intelligence.seed.seed_data import (
    SEED_OPPORTUNITIES,
    SEED_PROVIDERS,
    SEED_UNIVERSITIES,
    compute_fingerprint,
)


def seed_database(session: Session) -> Dict[str, int]:
    """Loads seed universities, providers, and opportunities idempotently.
    
    Returns a dictionary of creation counts.
    If run repeatedly on an already seeded database, created counts will be 0
    and no duplicate records will be generated.
    """
    stats = {
        "universities_created": 0,
        "providers_created": 0,
        "opportunities_created": 0,
        "awards_created": 0,
        "funding_components_created": 0,
        "deadlines_created": 0,
        "official_sources_created": 0,
        "discovery_sources_created": 0,
        "eligibility_rules_created": 0,
        "requirements_created": 0,
        "application_requirements_created": 0,
        "verification_records_created": 0,
        "conflict_records_created": 0,
    }

    # 1. Seed Universities
    univ_map = {}
    for u_data in SEED_UNIVERSITIES:
        existing = session.query(University).filter_by(name=u_data["name"]).first()
        if not existing:
            univ = University(
                name=u_data["name"],
                city=u_data["city"],
                state=u_data["state"],
                country=u_data["country"],
                admissions_need_policy=u_data["admissions_need_policy"],
                official_admissions_url=u_data.get("official_admissions_url"),
                official_financial_aid_url=u_data.get("official_financial_aid_url"),
            )
            session.add(univ)
            session.flush()
            stats["universities_created"] += 1
            univ_map[u_data["name"]] = univ.id
        else:
            univ_map[u_data["name"]] = existing.id

    # 2. Seed Providers
    prov_map = {}
    for p_data in SEED_PROVIDERS:
        existing = session.query(Provider).filter_by(name=p_data["name"]).first()
        if not existing:
            prov = Provider(
                name=p_data["name"],
                provider_type=p_data["provider_type"],
                website_url=p_data.get("website_url"),
                country=p_data.get("country", "US"),
                description=p_data.get("description"),
            )
            session.add(prov)
            session.flush()
            stats["providers_created"] += 1
            prov_map[p_data["name"]] = prov.id
        else:
            prov_map[p_data["name"]] = existing.id

    # 3. Seed Opportunities
    for opp_data in SEED_OPPORTUNITIES:
        slug = opp_data["slug"]
        cycle = opp_data["academic_cycle"]
        fingerprint = compute_fingerprint(slug, cycle)

        existing = session.query(ScholarshipOpportunity).filter_by(fingerprint_sha256=fingerprint).first()
        if existing:
            continue

        univ_id = univ_map.get(opp_data.get("university_name"))
        prov_id = prov_map.get(opp_data.get("provider_name"))

        opp = ScholarshipOpportunity(
            university_id=univ_id,
            provider_id=prov_id,
            title=opp_data["title"],
            slug=slug,
            description=opp_data.get("description"),
            target_degree_level=opp_data.get("target_degree_level", "BACHELOR"),
            destination_country=opp_data.get("destination_country", "US"),
            academic_cycle=cycle,
            varies_by_program=opp_data.get("varies_by_program", False),
            international_students_allowed=opp_data.get("international_students_allowed").value,
            requires_sat=opp_data.get("requires_sat").value,
            requires_act=opp_data.get("requires_act").value,
            requires_css_profile=opp_data.get("requires_css_profile").value,
            financial_need_required=opp_data.get("financial_need_required").value,
            verification_status=opp_data.get("verification_status").value,
            fingerprint_sha256=fingerprint,
        )
        session.add(opp)
        session.flush()
        stats["opportunities_created"] += 1

        # Seed Official Sources
        for s in opp_data.get("official_sources", []):
            src = OfficialSource(
                scholarship_id=opp.id,
                url=s["url"],
                source_domain=s["source_domain"],
                authority_tier=s["authority_tier"].value,
                is_primary=s.get("is_primary", True),
                page_title=s.get("page_title"),
                extracted_text_snippet=s.get("extracted_text_snippet"),
                last_crawled_at=s.get("last_crawled_at"),
                last_http_status=s.get("last_http_status"),
            )
            session.add(src)
            stats["official_sources_created"] += 1

        # Seed Discovery Sources
        for ds in opp_data.get("discovery_sources", []):
            d_src = DiscoverySource(
                scholarship_id=opp.id,
                url=ds["url"],
                source_name=ds["source_name"],
                authority_tier=ds["authority_tier"].value,
                discovery_notes=ds.get("discovery_notes"),
            )
            session.add(d_src)
            stats["discovery_sources_created"] += 1

        # Seed Award & Funding Components
        award_data = opp_data.get("award")
        if award_data:
            award = Award(
                scholarship_id=opp.id,
                funding_classification=award_data["funding_classification"].value,
                title=award_data["title"],
                is_renewable=award_data["is_renewable"].value,
                renewal_criteria=award_data.get("renewal_criteria"),
                estimated_annual_value_usd=award_data.get("estimated_annual_value_usd"),
            )
            session.add(award)
            session.flush()
            stats["awards_created"] += 1

            for fc in award_data.get("funding_components", []):
                comp = FundingComponent(
                    award_id=award.id,
                    component_type=fc["component_type"].value,
                    amount_min=fc.get("amount_min"),
                    amount_max=fc.get("amount_max"),
                    currency=fc.get("currency", "USD"),
                    amount_period=fc.get("amount_period", AmountPeriod.ANNUAL).value,
                    percentage_tuition=fc.get("percentage_tuition"),
                    description=fc.get("description"),
                    source_evidence_snippet=fc.get("source_evidence_snippet"),
                )
                session.add(comp)
                stats["funding_components_created"] += 1

        # Seed Deadlines
        for d in opp_data.get("deadlines", []):
            dl = Deadline(
                scholarship_id=opp.id,
                deadline_type=d["deadline_type"].value,
                deadline_date=d.get("deadline_date"),
                is_exact_date=d.get("is_exact_date", True),
                timezone=d.get("timezone", "America/New_York"),
                academic_cycle=d.get("academic_cycle", "2026-2027"),
                varies_by_program=d.get("varies_by_program", False),
                context_description=d.get("context_description"),
                source_evidence_snippet=d.get("source_evidence_snippet"),
            )
            session.add(dl)
            stats["deadlines_created"] += 1

        # Seed Eligibility Rules
        for r in opp_data.get("eligibility_rules", []):
            rule = EligibilityRule(
                scholarship_id=opp.id,
                rule_id=r["rule_id"],
                kind=r["kind"].value,
                expression_json=r["expression"],
                description=r.get("description"),
                source_evidence_snippet=r.get("source_evidence_snippet"),
                is_verified=r.get("is_verified", False),
            )
            session.add(rule)
            stats["eligibility_rules_created"] += 1

        # Seed Requirements
        for req in opp_data.get("requirements", []):
            rq = Requirement(
                scholarship_id=opp.id,
                requirement_type=req["requirement_type"].value,
                kind=req["kind"].value,
                name=req["name"],
                description=req.get("description"),
                source_evidence_snippet=req.get("source_evidence_snippet"),
            )
            session.add(rq)
            stats["requirements_created"] += 1

        # Seed Application Requirements
        for app_req in opp_data.get("application_requirements", []):
            ar = ApplicationRequirement(
                scholarship_id=opp.id,
                requirement_type=app_req["requirement_type"].value,
                kind=app_req["kind"].value,
                title=app_req["title"],
                description=app_req.get("description"),
                instructions=app_req.get("instructions"),
                submission_format=app_req.get("submission_format"),
                source_evidence_snippet=app_req.get("source_evidence_snippet"),
            )
            session.add(ar)
            stats["application_requirements_created"] += 1

        # Seed Verification Records
        for vr in opp_data.get("verification_records", []):
            ver = VerificationRecord(
                scholarship_id=opp.id,
                verification_state=vr["verification_state"].value,
                verifier_identity=vr["verifier_identity"],
                verification_method=vr["verification_method"],
                evidence_url=vr["evidence_url"],
                evidence_quote=vr["evidence_quote"],
                notes=vr.get("notes"),
                verified_at=vr.get("verified_at"),
            )
            session.add(ver)
            stats["verification_records_created"] += 1

        # Seed Conflict Records
        for cr in opp_data.get("conflict_records", []):
            cnf = ConflictRecord(
                scholarship_id=opp.id,
                field_name=cr["field_name"],
                source_a_value=cr["source_a_value"],
                source_a_url=cr["source_a_url"],
                source_b_value=cr["source_b_value"],
                source_b_url=cr["source_b_url"],
                resolution_status=cr.get("resolution_status", ConflictStatus.OPEN).value,
                resolution_notes=cr.get("resolution_notes"),
                recorded_at=cr.get("recorded_at"),
            )
            session.add(cnf)
            stats["conflict_records_created"] += 1

    session.commit()
    return stats
