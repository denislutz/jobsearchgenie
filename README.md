# JobSearchGenie

A unified REST API that aggregates job and freelance project listings from multiple DACH (Germany, Austria, Switzerland) job boards into a single, searchable interface.

## What it does

Instead of checking multiple job boards separately, you query one API and get deduplicated, normalized results across all sources — covering permanent positions, contracts, and freelance projects in the DACH IT/tech market.

## Key Features

- **Unified search** across multiple job boards with a single API call
- **Normalized data** — consistent fields regardless of source
- **Smart deduplication** — same job posted to multiple boards appears once
- **Flexible filtering** — by location, salary range, job type, contract type
- **Skill extraction** — automatically parsed from job descriptions
- **Trending analytics** — most in-demand skills and locations over time
- **Salary insights** — distribution data by role and location
- **Saved searches** — set up alerts for new matching jobs

## Target Market

IT/tech professionals in Germany, Austria, and Switzerland looking for permanent roles, contracts, or freelance projects.

## Status

Pre-launch MVP in development. Initial release targeting Q1 2026.

## API Overview

```
GET /jobs/search              Search jobs across all sources
GET /jobs/{id}                Get full job details
GET /jobs/filters             Available filter options
GET /analytics/trending       Trending skills and locations
GET /analytics/salary-ranges  Salary distribution data
POST /saved-searches          Save a search with email alerts
POST /auth/signup             Create an account
POST /auth/login              Authenticate
```

## Pricing

| Tier    | Price     | Requests      |
| ------- | --------- | ------------- |
| Free    | €0/month  | 100 req/day   |
| Starter | €9/month  | 1,000 req/day |
| Pro     | €29/month | Unlimited     |
