"""Pydantic models for Government Contracts Scraper input validation and output formatting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# --- Input Models ---


class ScrapingMode(str, Enum):
    SEARCH_OPPORTUNITIES = "search_opportunities"
    SEARCH_AWARDS = "search_awards"
    ENTITY_LOOKUP = "entity_lookup"


class ProcurementType(str, Enum):
    ALL = ""
    SOLICITATION = "o"
    PRESOLICITATION = "p"
    COMBINED = "k"
    SOURCES_SOUGHT = "r"
    AWARD_NOTICE = "a"
    SPECIAL_NOTICE = "s"
    SALE_OF_SURPLUS = "g"
    JUSTIFICATION = "u"
    INTENT_TO_BUNDLE = "i"


class SetAsideType(str, Enum):
    ALL = ""
    SBA = "SBA"
    EIGHT_A = "8A"
    EIGHT_A_SOLE = "8AN"
    HZC = "HZC"
    HZS = "HZS"
    SDVOSBC = "SDVOSBC"
    SDVOSBS = "SDVOSBS"
    WOSB = "WOSB"
    WOSBSS = "WOSBSS"
    EDWOSB = "EDWOSB"
    EDWOSBSS = "EDWOSBSS"
    VSA = "VSA"
    VSS = "VSS"


class ScraperInput(BaseModel):
    """Validated scraper input from Apify."""

    api_key: str = ""
    mode: ScrapingMode = ScrapingMode.SEARCH_OPPORTUNITIES

    # Search filters
    keyword: str = ""
    solicitation_number: str = ""
    procurement_type: str = ""
    naics_code: str = ""
    classification_code: str = ""
    set_aside: str = ""
    state: str = ""
    zip: str = ""
    organization_code: str = ""
    posted_from: str = ""
    posted_to: str = ""
    response_deadline_from: str = ""
    response_deadline_to: str = ""

    # Entity lookup
    organization_name: str = ""

    # General settings
    max_results: int = 100

    @field_validator("naics_code")
    @classmethod
    def validate_naics(cls, v: str) -> str:
        v = v.strip()
        if v and (not v.isdigit() or len(v) > 6):
            raise ValueError("NAICS code must be up to 6 digits")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.strip().upper()
        if v and len(v) != 2:
            raise ValueError("State must be a 2-letter code (e.g. VA, CA)")
        return v

    @classmethod
    def from_actor_input(cls, raw: dict[str, Any]) -> ScraperInput:
        """Map Apify input schema field names to model field names."""
        return cls(
            api_key=raw.get("apiKey", ""),
            mode=raw.get("mode", "search_opportunities"),
            keyword=raw.get("keyword", ""),
            solicitation_number=raw.get("solicitationNumber", ""),
            procurement_type=raw.get("procurementType", ""),
            naics_code=raw.get("naicsCode", ""),
            classification_code=raw.get("classificationCode", ""),
            set_aside=raw.get("setAside", ""),
            state=raw.get("state", ""),
            zip=raw.get("zip", ""),
            organization_code=raw.get("organizationCode", ""),
            posted_from=raw.get("postedFrom", ""),
            posted_to=raw.get("postedTo", ""),
            response_deadline_from=raw.get("responseDeadlineFrom", ""),
            response_deadline_to=raw.get("responseDeadlineTo", ""),
            organization_name=raw.get("organizationName", ""),
            max_results=raw.get("maxResults", 100),
        )

    def validate_for_mode(self) -> str | None:
        """Return an error message if input is invalid for the selected mode."""
        if not self.api_key:
            return (
                "A SAM.gov API key is required. Get one free at "
                "https://sam.gov (Account Details > Public API Key)."
            )
        if self.mode == ScrapingMode.ENTITY_LOOKUP and not self.organization_name:
            return "An organization name is required for 'Entity Lookup' mode."
        return None

    def get_date_range(self) -> tuple[str, str]:
        """Return (postedFrom, postedTo) with defaults if not provided.

        Defaults to the last 30 days. SAM.gov requires MM/dd/yyyy format.
        """
        now = datetime.now(timezone.utc)

        if self.posted_to:
            to_date = self.posted_to
        else:
            to_date = now.strftime("%m/%d/%Y")

        if self.posted_from:
            from_date = self.posted_from
        else:
            from_date = (now - timedelta(days=30)).strftime("%m/%d/%Y")

        return from_date, to_date


# --- Output Formatting ---

# Mapping of SAM.gov ptype codes to human-readable names
PROCUREMENT_TYPE_NAMES = {
    "o": "Solicitation",
    "p": "Pre-solicitation",
    "k": "Combined Synopsis/Solicitation",
    "r": "Sources Sought",
    "a": "Award Notice",
    "s": "Special Notice",
    "g": "Sale of Surplus",
    "u": "Justification",
    "i": "Intent to Bundle",
}


def format_opportunity(data: dict[str, Any]) -> dict[str, Any]:
    """Format a SAM.gov opportunity into clean output."""
    # Extract point of contact
    contacts = data.get("pointOfContact", [])
    primary_contact = {}
    for contact in contacts:
        if contact.get("type", "").lower() == "primary":
            primary_contact = contact
            break
    if not primary_contact and contacts:
        primary_contact = contacts[0]

    # Extract place of performance
    pop = data.get("placeOfPerformance", {})
    pop_state = ""
    pop_zip = ""
    pop_city = ""
    pop_country = ""
    if pop:
        state_info = pop.get("state", {})
        if isinstance(state_info, dict):
            pop_state = state_info.get("code", "")
        elif isinstance(state_info, str):
            pop_state = state_info
        pop_zip = pop.get("zip", "")
        city_info = pop.get("city", {})
        if isinstance(city_info, dict):
            pop_city = city_info.get("name", "")
        elif isinstance(city_info, str):
            pop_city = city_info
        country_info = pop.get("country", {})
        if isinstance(country_info, dict):
            pop_country = country_info.get("code", "")
        elif isinstance(country_info, str):
            pop_country = country_info

    # Extract office address
    office = data.get("officeAddress", {}) or {}

    # Extract award info (for award notices)
    award = data.get("award", {}) or {}
    awardee = award.get("awardee", {}) or {}

    base_type = data.get("baseType", "")
    notice_type = data.get("type", base_type)

    return {
        "type": PROCUREMENT_TYPE_NAMES.get(notice_type, notice_type),
        "noticeId": data.get("noticeId", ""),
        "title": data.get("title", ""),
        "solicitationNumber": data.get("solicitationNumber", ""),
        "department": data.get("fullParentPathName", ""),
        "departmentCode": data.get("fullParentPathCode", ""),
        "agency": _extract_agency(data.get("fullParentPathName", "")),
        "postedDate": data.get("postedDate", ""),
        "responseDeadline": data.get("responseDeadLine", ""),
        "archiveDate": data.get("archiveDate", ""),
        "active": data.get("active", ""),
        "naicsCode": data.get("naicsCode", ""),
        "classificationCode": data.get("classificationCode", ""),
        "setAside": data.get("typeOfSetAsideDescription", ""),
        "setAsideCode": data.get("typeOfSetAside", ""),
        "placeOfPerformance": {
            "city": pop_city,
            "state": pop_state,
            "zip": pop_zip,
            "country": pop_country,
        },
        "contactName": primary_contact.get("fullName", ""),
        "contactEmail": primary_contact.get("email", ""),
        "contactPhone": primary_contact.get("phone", ""),
        "officeAddress": {
            "city": office.get("city", ""),
            "state": office.get("state", ""),
            "zip": office.get("zipcode", ""),
        },
        "descriptionUrl": data.get("description", ""),
        "resourceLinks": data.get("resourceLinks", []),
        "uiLink": data.get("uiLink", ""),
        # Award-specific fields (populated for award notices)
        "awardDate": award.get("date", ""),
        "awardNumber": award.get("number", ""),
        "awardAmount": award.get("amount", ""),
        "awardeeName": awardee.get("name", ""),
        "awardeeUei": awardee.get("ueiSAM", ""),
    }


def format_organization(data: dict[str, Any]) -> dict[str, Any]:
    """Format a federal organization from the hierarchy API into clean output."""
    return {
        "type": "organization",
        "orgKey": data.get("orgKey", ""),
        "name": data.get("name", ""),
        "code": data.get("code", ""),
        "level": data.get("level", ""),
        "parentOrgKey": data.get("parentOrgKey", ""),
        "parentName": data.get("parentName", ""),
        "parentCode": data.get("parentCode", ""),
        "description": data.get("description", ""),
        "startDate": data.get("startDate", ""),
        "endDate": data.get("endDate", ""),
        "cgac": data.get("cgac", ""),
        "fpdsOrgId": data.get("fpdsOrgId", ""),
        "fhOrgId": data.get("fhOrgId", ""),
    }


def _extract_agency(full_path: str) -> str:
    """Extract the most specific agency name from the full parent path.

    fullParentPathName looks like:
        'DEPT OF DEFENSE.DEPT OF THE ARMY.W6QK ACC-APG NATICK'
    We return the last segment as the most relevant agency name.
    """
    if not full_path:
        return ""
    parts = full_path.split(".")
    return parts[-1].strip()
