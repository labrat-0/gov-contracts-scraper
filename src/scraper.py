"""Core SAM.gov scraping logic. All 3 modes: search_opportunities, search_awards, entity_lookup."""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

import httpx

from .models import (
    ScraperInput,
    ScrapingMode,
    format_opportunity,
    format_organization,
)
from .utils import (
    RateLimiter,
    SAM_FEDERAL_HIERARCHY_URL,
    SAM_OPPORTUNITIES_URL,
    fetch_json,
)

logger = logging.getLogger(__name__)

# SAM.gov API max page size
MAX_PAGE_SIZE = 1000


class SamGovScraper:
    """Scrapes contract data from SAM.gov public APIs."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        rate_limiter: RateLimiter,
        config: ScraperInput,
    ) -> None:
        self.client = client
        self.rate_limiter = rate_limiter
        self.config = config

    async def scrape(self) -> AsyncIterator[dict[str, Any]]:
        """Main entry point -- dispatches to the correct mode."""
        mode = self.config.mode

        if mode == ScrapingMode.SEARCH_OPPORTUNITIES:
            async for item in self._search_opportunities():
                yield item
        elif mode == ScrapingMode.SEARCH_AWARDS:
            async for item in self._search_awards():
                yield item
        elif mode == ScrapingMode.ENTITY_LOOKUP:
            async for item in self._entity_lookup():
                yield item

    # --- Mode 1: Search Opportunities ---

    async def _search_opportunities(self) -> AsyncIterator[dict[str, Any]]:
        """Search for contract opportunities (solicitations, pre-sols, etc.)."""
        logger.info("Searching SAM.gov opportunities")

        params = self._build_opportunity_params()
        # For opportunities, exclude award notices by default
        # unless user explicitly selected award notice type
        if not self.config.procurement_type:
            # Search all non-award types: o, p, k, r, s, g, u, i
            params["ptype"] = "o,p,k,r,s,g,u,i"

        async for item in self._paginate_opportunities(params):
            yield format_opportunity(item)

    # --- Mode 2: Search Awards ---

    async def _search_awards(self) -> AsyncIterator[dict[str, Any]]:
        """Search for contract award notices."""
        logger.info("Searching SAM.gov award notices")

        params = self._build_opportunity_params()
        # Force procurement type to awards only
        params["ptype"] = "a"

        async for item in self._paginate_opportunities(params):
            yield format_opportunity(item)

    # --- Mode 3: Entity Lookup ---

    async def _entity_lookup(self) -> AsyncIterator[dict[str, Any]]:
        """Look up federal organizations via the Federal Hierarchy API."""
        name = self.config.organization_name
        logger.info(f"Looking up federal organizations: '{name}'")

        params: dict[str, Any] = {
            "api_key": self.config.api_key,
            "q": name,
            "limit": min(self.config.max_results, 100),
        }

        data = await fetch_json(
            self.client,
            SAM_FEDERAL_HIERARCHY_URL,
            self.rate_limiter,
            params,
        )

        if not data or not isinstance(data, dict):
            logger.warning("No data returned from Federal Hierarchy API")
            return

        org_list = data.get("orgList", [])
        if not org_list:
            logger.info("No organizations found matching the query")
            return

        for org in org_list:
            yield format_organization(org)

    # --- Helpers ---

    def _build_opportunity_params(self) -> dict[str, Any]:
        """Build query parameters for the opportunities search API."""
        posted_from, posted_to = self.config.get_date_range()

        params: dict[str, Any] = {
            "api_key": self.config.api_key,
            "postedFrom": posted_from,
            "postedTo": posted_to,
            "limit": min(self.config.max_results, MAX_PAGE_SIZE),
            "offset": 0,
        }

        if self.config.keyword:
            params["title"] = self.config.keyword

        if self.config.solicitation_number:
            params["solnum"] = self.config.solicitation_number

        if self.config.procurement_type:
            params["ptype"] = self.config.procurement_type

        if self.config.naics_code:
            params["ncode"] = self.config.naics_code

        if self.config.classification_code:
            params["ccode"] = self.config.classification_code

        if self.config.set_aside:
            params["typeOfSetAside"] = self.config.set_aside

        if self.config.state:
            params["state"] = self.config.state

        if self.config.zip:
            params["zip"] = self.config.zip

        if self.config.organization_code:
            params["organizationCode"] = self.config.organization_code

        if self.config.response_deadline_from:
            params["rdlfrom"] = self.config.response_deadline_from

        if self.config.response_deadline_to:
            params["rdlto"] = self.config.response_deadline_to

        return params

    async def _paginate_opportunities(
        self, params: dict[str, Any]
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate through SAM.gov opportunity search results using offset."""
        offset = 0
        total_yielded = 0
        consecutive_empty = 0

        while True:
            current_params = dict(params)
            current_params["offset"] = offset

            logger.debug(
                f"Fetching opportunities: offset={offset}, "
                f"limit={current_params.get('limit')}"
            )

            data = await fetch_json(
                self.client,
                SAM_OPPORTUNITIES_URL,
                self.rate_limiter,
                current_params,
            )

            if not data or not isinstance(data, dict):
                logger.warning("No data returned from SAM.gov API")
                break

            # SAM.gov returns opportunities in opportunitiesData array
            opportunities = data.get("opportunitiesData", [])

            if not opportunities:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    logger.info("No more results from SAM.gov")
                    break
                # Try next offset in case of transient empty page
                offset += current_params.get("limit", MAX_PAGE_SIZE)
                continue

            consecutive_empty = 0

            for opp in opportunities:
                yield opp
                total_yielded += 1

            total_records = data.get("totalRecords", 0)
            logger.info(
                f"Fetched {total_yielded}/{total_records} opportunities"
            )

            # Check if we've reached the end
            if total_yielded >= total_records:
                break

            # Move to next page
            offset += len(opportunities)

            # Safety: don't paginate forever
            if offset >= 10000:
                logger.info("Reached maximum pagination depth (10,000)")
                break
