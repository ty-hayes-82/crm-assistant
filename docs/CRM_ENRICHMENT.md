# HubSpot CRM Data Management Guide

This document provides a comprehensive guide for maintaining a clean, effective, and enriched HubSpot CRM. It is intended for any team member responsible for adding, updating, or managing contact and company data.

## Table of Contents

1.  [Data Hygiene Guide](#part-1-data-hygiene-guide)
    -   [Tier 1: Critical Fields](#tier-1-critical-for-basic-crm-functionality)
    -   [Tier 2: Important Fields](#tier-2-important-for-sales-and-marketing-effectiveness)
    -   [Tier 3: Analytics Fields](#tier-3-useful-for-analytics-and-deeper-insights)
    -   [Common Data Quality Issues](#common-data-quality-issues--manual-cleaning-recommendations)
2.  [Automated Data Enrichment Processes](#part-2-automated-data-enrichment-processes)
    -   [Contact Level Enrichments](#contact-level-enrichments)
    -   [Company Level Enrichments](#company-level-enrichments)
3.  [Enrichment Process Improvement Recommendations](#part-3-enrichment-process-improvement-recommendations)
    -   [1. Track Enrichment Coverage and Confidence](#1-track-enrichment-coverage-and-confidence)
    -   [2. Expand Firmographic and Digital Presence Enrichment](#2-expand-firmographic-and-digital-presence-enrichment)
    -   [3. Upgrade Job Title Parsing to Two-Axis Taxonomy](#3-upgrade-job-title-parsing-to-two-axis-taxonomy)
    -   [4. Automate Deduplication and Association Hygiene](#4-automate-deduplication-and-association-hygiene)
    -   [5. Implement Event-Driven Enrichment with Observability](#5-implement-event-driven-enrichment-with-observability)
4.  [Data Field Reference](#part-4-data-field-reference)
    -   [Company Fields](#company-fields)
    -   [Contact Fields](#contact-fields)

---

## Part 1: Data Hygiene Guide

Maintaining data hygiene is the foundation of an effective CRM. It ensures accurate reporting, successful marketing campaigns, and an efficient sales process.

### Tier 1: Critical for Basic CRM Functionality

These fields are the foundation of your CRM. Inaccurate data here can significantly hinder basic operations.

-   **`Email`**:
    -   **Importance**: The most critical field, serving as the primary unique identifier for contacts and the main channel for communication.
    -   **Cleaning Focus**: Validate email formats, remove invalid or bounced emails, and deduplicate contacts based on this field.

-   **`First Name`** and **`Last Name`**:
    -   **Importance**: Essential for personalization in communications.
    -   **Cleaning Focus**: Ensure proper capitalization, remove extra spaces or characters, and correct entries where non-name values are present (e.g., "Weddings & Catering").

-   **`Company Name`** and **`Associated Company`**:
    -   **Importance**: Crucial for B2B segmentation, account-based marketing, and linking contacts to the correct organizations.
    -   **Cleaning Focus**: Standardize company names (e.g., `IBM` vs. `I.B.M.`), merge duplicate company records, and ensure contacts are correctly associated with their company. It's important to define the relationship between `Company Name` (on the contact) and `Associated Company` to avoid discrepancies.

-   **`Lifecycle Stage`**:
    -   **Importance**: Defines where a contact is in your marketing and sales funnel.
    -   **Cleaning Focus**: Ensure this is accurately updated as a contact progresses.
    -   **Common Values**: `Subscriber`, `Lead`, `Marketing Qualified Lead`, `Sales Qualified Lead`, `Opportunity`, `Customer`, `Evangelist`, `Other`.

-   **`Contact Owner`**:
    -   **Importance**: Ensures accountability and a clear point of contact for sales and relationship management.
    -   **Cleaning Focus**: Assign all valuable contacts to a team member. Periodically review and reassign contacts from owners who are no longer with the company.

---

### Tier 2: Important for Sales and Marketing Effectiveness

These fields enable more advanced segmentation, lead scoring, and efficient sales processes.

-   **`Lead Status`**:
    -   **Importance**: Provides the sales team with immediate insight into a contact's current state of engagement.
    -   **Cleaning Focus**: Regularly update this based on sales activities to avoid stale information.
    -   **Common Values**: `New`, `Open`, `In Progress`, `Open Deal`, `Unqualified`, `Attempted to Contact`, `Connected`, `Bad Timing`.

-   **`Job Title`**:
    -   **Importance**: Helps understand a contact's role, seniority, and influence.
    -   **Cleaning Focus**: Standardize common titles (e.g., "VP" vs "Vice President") and consider parsing seniority or department into separate custom fields for easier segmentation. (See the "Job Title Categorization" section in Part 2 for how this is automated).

---

### Tier 3: Useful for Analytics and Deeper Insights

These fields, often system-generated, are key for understanding engagement and identifying inactive contacts.

-   **`Last Engagement Date`**:
    -   **Importance**: A key indicator of a contact's activity level.
    -   **Cleaning Focus**: Use this field to identify unengaged contacts for re-engagement campaigns or for periodic list cleaning to improve email deliverability.

-   **`Number of Sales Activities`**, **`Total Email Clicks`**, **`Total Email Opens`**:
    -   **Importance**: Engagement metrics that are vital for lead scoring and understanding contact behavior.
    -   **Cleaning Focus**: Ensure these tracking metrics are configured correctly and are being used in your lead scoring and automation workflows.

---

### Common Data Quality Issues & Manual Cleaning Recommendations

While some cleaning is automated, manual vigilance is key. Here are common issues to watch for:

-   **Incorrect Field Usage**:
    -   **Issue**: Fields containing information that doesn't belong (e.g., `Job Title` field has a company slogan).
    -   **Recommendation**: Review data during entry. Implement validation rules where possible during import.

-   **Improperly Parsed Names**:
    -   **Issue**: Personal titles like "Lieutenant" in the `First Name` field.
    -   **Recommendation**: Manually correct these when found. Our automated scripts may not catch all cases.

-   **Inconsistent Company Naming**:
    -   **Issue**: Variations in company names for the same entity (e.g., "Cbigg Management LLC" vs. "CBIGG Management LLC").
    -   **Recommendation**: Before creating a new company, search for existing ones. Use a standard naming convention.


---

## Part 2: Automated Data Enrichment Processes

To assist with data hygiene and add valuable context, several automated scripts run in the background. These are located in the `scripts/hubspot_utils` directory. Understanding what they do will help you understand how data is populated in HubSpot.

### Contact Level Enrichments

#### 1. Job Title Categorization

-   **Script**: `update_hubspot_job_title_categories.py`
-   **Purpose**: This script automatically categorizes contacts into standardized job roles based on their `Job Title`, populating the `Job Title Category` custom property. This is crucial for segmentation.
-   **How it Works**:
    1.  The script finds contacts that are missing a `Job Title Category`.
    2.  It normalizes the job title (lowercase, removes punctuation).
    3.  It then applies rules to classify the title:
        -   **Exclusion**: It checks for keywords (e.g., `hr`, `it`, `maintenance`). Contacts with these titles are marked with a `Job Title Category` of "Exclude" to remove them from certain campaigns. This explains the "Exclude" value you may see.
        -   **Categorization**: If not excluded, it checks for keywords to assign a category like `General Manager`, `Director of Golf`, `Food & Beverage Director`, `C-Level / President / Vice President`, etc.
    4.  The script then updates the contact record in HubSpot with the assigned category.

#### 2. Contact Creation, Update, and Association

-   **Script**: `add_contact_to_company.py`
-   **Purpose**: To create or update contacts and ensure they are correctly associated with a company, maintaining data integrity.
-   **How it Works**:
    -   When given contact details and a company ID, the script first checks if the contact's email already exists.
    -   If the contact exists, it is updated. If not, a new contact is created.
    -   Finally, it ensures the contact is associated with the correct company.

---

### Company Level Enrichments

#### 1. General Company Property Updates

-   **Script**: `update_company_property.py`
-   **Purpose**: This is a general utility script for updating a single property on any HubSpot company.
-   **How it Works**: It can be used for manual or scheduled bulk updates to any company field, such as `company_type` or `facility_complexity`, based on external data or analysis.

#### 2. Company Creation with Duplicate Check

-   **Script**: `create_company.py`
-   **Purpose**: To provide a standardized way of creating new companies while preventing duplicates, which is a key aspect of data hygiene.
-   **How it Works**:
    -   The script takes company details like name and domain.
    -   Before creating a new company, it first searches HubSpot to see if a company with the same domain already exists.
    -   If a duplicate is found, it prevents creation and notifies the user. This ensures that multiple records for the same organization are not created.
    -   If no duplicate is found, it proceeds to create the new company record.

---

## Part 3: Enrichment Process Improvement Recommendations

The following five recommendations will significantly enhance our CRM enrichment process, improving data quality, coverage, and operational efficiency:

### 1. Track Enrichment Coverage and Confidence

**Implementation**: Add custom properties to monitor and audit enrichment quality:
- `enrichment_status` (Pending/Enriched/Needs Review)
- `enrichment_source` (script name/external provider)
- `enrichment_confidence` (0–100 score)
- `enrichment_last_updated` (datetime)

**Benefits**: 
- Audit completeness across all records
- Prioritize manual fixes for low-confidence enrichments
- Measure script effectiveness and identify improvement areas
- Track enrichment drift over time

### 2. Expand Firmographic and Digital Presence Enrichment

**Implementation**: Auto-populate key company fields using external data providers:
- Primary: `domain`, `website`, `linkedin_company_page`
- Secondary: `company_short_name`, `email_pattern`
- Use providers like Clearbit/Apollo with fallback heuristics (Bing/Google search + LinkedIn)
- Implement via `update_company_property.py` for batch processing

**Benefits**:
- Dramatically increase company data completeness
- Enable better email deliverability through domain validation
- Support account-based marketing with LinkedIn integration
- Improve lead routing through email pattern matching

### 3. Upgrade Job Title Parsing to Two-Axis Taxonomy

**Current State**: Single `job_title_category` field
**Enhancement**: Add complementary fields:
- `job_function` (Operations, Food & Beverage, Golf, Sales, etc.)
- `job_seniority` (C-Level, VP, Director, Manager, Individual Contributor)
- `job_title_confidence` (parsing accuracy score)

**Implementation**:
- Maintain versioned rules file with exception handling
- Create function-specific keyword dictionaries
- Implement seniority detection via title hierarchy patterns
- Store confidence scores for quality monitoring

**Benefits**:
- More granular segmentation for targeted campaigns
- Better lead scoring based on decision-making authority
- Improved sales prioritization and routing

### 4. Automate Deduplication and Association Hygiene

**Implementation**: Build automated processes for:
- **Company Deduplication**: Detect duplicates using domain matching + fuzzy company name comparison
- **Canonical Naming**: Standardize company names and propose merges
- **Association Backfill**: Ensure all contacts have proper `associatedcompanyid`
- **Association Reconciliation**: Sync `hs_all_associated_company_ids` with primary associations

**Benefits**:
- Eliminate fragmented account views
- Improve reporting accuracy
- Reduce marketing list inflation
- Ensure proper account-based workflows

### 5. Implement Event-Driven Enrichment with Observability

**Current State**: Batch processing scripts
**Enhancement**: Move to real-time, event-driven architecture:

**Triggers**:
- HubSpot workflows on contact/company create/update
- Webhook endpoints for external system integration
- Maintain nightly backfill jobs for drift correction

**Reliability Features**:
- Idempotency keys to prevent duplicate processing
- Exponential backoff retry logic
- Rate limiting and quota management
- Circuit breaker patterns for external API failures

**Monitoring & Observability**:
- Enrichment coverage percentage metrics
- Error rate tracking and alerting
- Processing latency monitoring
- Detailed logging in `logs/hubspot_updates/`

**Benefits**:
- Near real-time data enrichment
- Improved system reliability and error handling
- Better visibility into enrichment performance
- Reduced manual intervention requirements

### Implementation Priority

1.  **High Impact, Low Effort**: Enrichment tracking (#1) and firmographic enrichment (#2)
2.  **Medium Effort, High Value**: Job title taxonomy upgrade (#3) and deduplication automation (#4)
3.  **High Effort, Transformational**: Event-driven architecture (#5)

---

## Part 4: Data Field Reference

This section provides a complete reference for the fields available for Company and Contact objects, as defined in the export templates.

### Company Fields

| Label | Internal Name |
| :--- | :--- |
| Record ID | `hs_object_id` |
| Company Name | `name` |
| Company Domain Name | `domain` |
| Website URL | `website` |
| LinkedIn Company Page | `linkedin_company_page` |
| Street Address | `street_address` |
| City | `city` |
| State/Region | `state` |
| Postal Code | `postal_code` |
| Country/Region | `country` |
| Number of Associated Contacts | `number_of_associated_contacts` |
| Club Type | `club_type` |
| Company Type | `company_type` |
| Geographic Seasonality | `geographic_seasonality` |
| Type | `type` |
| Facility Complexity | `facility_complexity` |
| Description | `description` |
| Company Short Name | `company_short_name` |
| Email Pattern | `email_pattern` |
| Lifecycle Stage | `lifecyclestage` |
| Club Info | `club_info` |
| Annual Revenue | `annualrevenue` |
| Number of Holes | `number_of_holes` |
| Peak Season End Month | `peak_season_end_month` |
| Peak Season Start Month | `peak_season_start_month` |

### Contact Fields

| Label | Internal Name |
| :--- | :--- |
| Record ID | `hs_object_id` |
| First Name | `firstname` |
| Last Name | `lastname` |
| Lifecycle Stage | `lifecyclestage` |
| Email | `email` |
| Lead Status | `hs_lead_status` |
| Job Title | `jobtitle` |
| Job Title Category | `job_title_category` |
| Total Email Clicks | `hs_analytics_num_email_clicks` |
| Total Email Opens | `hs_analytics_num_email_opens` |
| Lead Score | `hs_predictivecontactscore_v2` |
| Recent Sales Email Replied Date | `hs_sales_email_last_replied` |
| Company Name | `associatedcompanyid.name` |
| Contact owner | `hubspot_owner_id` |
| Number of Sales Activities | `num_sales_activities` |
| State/Region | `state` |
| Associated Company | `associatedcompanyid` |
| Last Engagement Date | `notes_last_updated` |
| Create Date | `createdate` |
| Associated Company IDs | `hs_all_associated_company_ids` |
