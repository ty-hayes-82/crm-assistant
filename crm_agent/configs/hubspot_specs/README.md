# HubSpot OpenAPI Specifications

This directory contains pinned HubSpot CRM API specifications downloaded from the official HubSpot public API spec collection.

## Source Repository
- **Repository**: [HubSpot/HubSpot-public-api-spec-collection](https://github.com/HubSpot/HubSpot-public-api-spec-collection)
- **Path**: `PublicApiSpecs/CRM/`
- **Downloaded**: 2025-01-09

## Available Specifications

### Companies API (`companies.json`)
- **Source**: `PublicApiSpecs/CRM/Companies/Rollouts/424/v3/companies.json`
- **Version**: v3
- **Description**: HubSpot Companies CRM API specification

### Contacts API (`contacts.json`)
- **Source**: `PublicApiSpecs/CRM/Contacts/Rollouts/424/v3/contacts.json`
- **Version**: v3
- **Description**: HubSpot Contacts CRM API specification

## Usage

These specifications are used by the `create_hubspot_openapi_tool()` function in `crm_agent/core/factory.py` to create typed HubSpot API tools instead of relying on remote spec URLs.

## Updating Specs

To update these specifications:

1. Check the source repository for newer versions
2. Download the latest specs from the appropriate rollout directories
3. Update this README with the new source paths and download date
4. Test the updated specs with the factory function

## Fallback

If OpenAPI tools are not available, the system falls back to using the official HubSpot Python SDK or the `hubspot_safe_connector.py` implementation.
