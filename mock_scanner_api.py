"""
Mock Power BI Admin Scanner API (Workspace Info / Metadata Scanning API)

This module simulates the full 4-step async Scanner API flow:

  STEP 1 — GET  /v1.0/myorg/admin/workspaces/modified
            (GetModifiedWorkspaces) → returns list of workspace IDs to scan

  STEP 2 — POST /v1.0/myorg/admin/workspaces/getInfo
            ?lineage=True&datasourceDetails=True&datasetSchema=True
            &datasetExpressions=True&getArtifactUsers=True
            (PostWorkspaceInfo) → submits scan, returns scanId + status

  STEP 3 — GET  /v1.0/myorg/admin/workspaces/scanStatus/{scanId}
            (GetScanStatus) → poll until status = "Succeeded"

  STEP 4 — GET  /v1.0/myorg/admin/workspaces/scanResult/{scanId}
            (GetScanResult) → full metadata payload

What GetScanResult returns that no other API gives you:
  - Dataset tables, columns (dataType, columnType), measures (DAX), RLS roles
  - M query expressions (Power Query) per table
  - Datasource instances with full connection details + gatewayId
  - Upstream dataflow lineage per dataset
  - Report → dataset lineage (datasetId on each report)
  - Sensitivity labels (labelId, labelDisplayName)
  - Endorsement status (Certified / Promoted)
  - Artifact-level users (per report, dataset, dataflow)
  - Tiles → dataset lineage on dashboards

Real API docs:
  https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-post-workspace-info
  https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-get-scan-status
  https://learn.microsoft.com/en-us/rest/api/power-bi/admin/workspace-info-get-scan-result
  https://learn.microsoft.com/en-us/power-bi/enterprise/service-admin-metadata-scanning

NOTE: datasetSchema + datasetExpressions require the tenant admin setting
      "Enhance admin APIs responses with detailed metadata" to be ON.
      If it is off, tables/columns/measures/expressions return empty.
"""

from datetime import datetime, timezone, timedelta
import uuid

# ── Helpers ────────────────────────────────────────────────────────────────────

def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

NOW = datetime.now(timezone.utc)

# Reuse the same workspace IDs from mock_powerbi_data.py so IDs are consistent
WORKSPACE_IDS = [
    "e380d1d0-1fa6-460b-9a90-1a5c6b02414c",  # Finance Reporting
    "183dcf10-47b8-48c4-84aa-f0bf9d5f8fcf",  # HR Analytics OLD
    "94E57E92-CEE2-486D-8CC8-218C97200579",  # Sales Dashboard
    "d5caa808-8c91-400a-911d-06af08dbcc31",  # Test Workspace 2022
    "EC1EE11F-845D-495E-82A3-9DAC2072305A",  # Marketing Campaigns
    "f089354e-8366-4e18-aea3-4cb4a3a50b48",  # Dev Sandbox - John
    "ccccdddd-2222-eeee-3333-ffff4444aaaa",  # Supply Chain Metrics
    "aaaabbbb-cccc-dddd-eeee-ffff00001111",  # Temp - Migration Test
]

# Simulate one scan ID (in production this is a fresh UUID per scan request)
MOCK_SCAN_ID = "e7d03602-4873-4760-b37e-1563ef5358e3"


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — GetModifiedWorkspaces
# GET /v1.0/myorg/admin/workspaces/modified
# Optional: ?modifiedSince=2024-01-01T00:00:00Z  (ISO 8601)
#
# Real response shape:
# [ "97d03602-...", "67b7e93a-..." ]   ← just a flat list of workspace ID strings
# ══════════════════════════════════════════════════════════════════════════════

def get_modified_workspaces(modified_since: str = None) -> list:
    """
    Mimics: GET /v1.0/myorg/admin/workspaces/modified
    Returns all workspace IDs (or those modified since the given date).
    In production: omit modifiedSince on first run; pass last-run timestamp for incremental scans.
    """
    return WORKSPACE_IDS


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — PostWorkspaceInfo
# POST /v1.0/myorg/admin/workspaces/getInfo
#      ?lineage=True&datasourceDetails=True&datasetSchema=True
#       &datasetExpressions=True&getArtifactUsers=True
# Body: { "workspaces": ["id1", "id2", ...] }   (max 100 per request)
#
# Real response shape:
# { "id": "<scanId>", "createdDateTime": "...", "status": "NotStarted" }
# ══════════════════════════════════════════════════════════════════════════════

def post_workspace_info(workspace_ids: list, lineage=True, datasource_details=True,
                        dataset_schema=True, dataset_expressions=True,
                        get_artifact_users=True) -> dict:
    """
    Mimics: POST /v1.0/myorg/admin/workspaces/getInfo
    Returns a scan request object with scanId and initial status.
    """
    return {
        "id": MOCK_SCAN_ID,
        "createdDateTime": _iso(NOW),
        "status": "NotStarted"
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — GetScanStatus
# GET /v1.0/myorg/admin/workspaces/scanStatus/{scanId}
#
# Real response shape (poll until status = "Succeeded"):
# { "id": "<scanId>", "createdDateTime": "...", "status": "Succeeded" }
# Possible statuses: NotStarted | Running | Succeeded | Failed
# ══════════════════════════════════════════════════════════════════════════════

def get_scan_status(scan_id: str) -> dict:
    """
    Mimics: GET /v1.0/myorg/admin/workspaces/scanStatus/{scanId}
    In production: poll every 2-5 seconds until status = "Succeeded".
    Mock immediately returns Succeeded (no need to poll in prototype).
    """
    return {
        "id": scan_id,
        "createdDateTime": _iso(NOW - timedelta(seconds=3)),
        "status": "Succeeded"
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — GetScanResult
# GET /v1.0/myorg/admin/workspaces/scanResult/{scanId}
#
# This is the rich payload. Real response shape (simplified):
# {
#   "workspaces": [
#     {
#       "id": "...",
#       "name": "...",
#       "type": "Workspace",
#       "state": "Active",
#       "isOnDedicatedCapacity": true,
#       "capacityId": "...",
#       "defaultDatasetStorageFormat": "Small",
#       "datasets": [
#         {
#           "id": "...",
#           "name": "...",
#           "tables": [
#             {
#               "name": "Sales",
#               "columns": [
#                 { "name": "SalesAmount", "dataType": "Double", "columnType": "Data" },
#                 { "name": "SalesDate",   "dataType": "DateTime", "columnType": "Data" }
#               ],
#               "measures": [
#                 { "name": "Total Sales", "expression": "SUM(Sales[SalesAmount])" }
#               ],
#               "source": [
#                 { "expression": "let\n  Source = Sql.Database(...)\nin\n  Source" }
#               ]
#             }
#           ],
#           "datasourceUsages": [
#             { "datasourceInstanceId": "..." }
#           ],
#           "upstreamDataflows": [
#             { "targetDataflowId": "...", "groupId": "..." }
#           ],
#           "sensitivityLabel": { "labelId": "...", "labelDisplayName": "Confidential" },
#           "endorsementDetails": { "endorsement": "Certified", "certifiedBy": "alice@contoso.com" }
#         }
#       ],
#       "reports": [
#         {
#           "id": "...", "name": "...", "datasetId": "...",
#           "sensitivityLabel": { ... },
#           "users": [ { "emailAddress": "...", "reportUserAccessRight": "Owner" } ]
#         }
#       ],
#       "dataflows": [
#         {
#           "objectId": "...", "name": "...",
#           "datasourceUsages": [ { "datasourceInstanceId": "..." } ]
#         }
#       ],
#       "datasourceInstances": [
#         {
#           "datasourceType": "Sql",
#           "connectionDetails": { "server": "...", "database": "..." },
#           "datasourceId": "...",
#           "gatewayId": "..."
#         }
#       ]
#     }
#   ],
#   "datasourceInstances": [ ... ],   ← tenant-level deduped list
#   "misconfiguredDatasourceInstances": [ ... ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_scan_result(scan_id: str) -> dict:
    """
    Mimics: GET /v1.0/myorg/admin/workspaces/scanResult/{scanId}
    Returns the full metadata payload with lineage, schema, expressions, and users.
    """
    return {
        "workspaces": [

            # ── Finance Reporting ──────────────────────────────────────────
            {
                "id": "e380d1d0-1fa6-460b-9a90-1a5c6b02414c",
                "name": "Finance Reporting",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "defaultDatasetStorageFormat": "Small",
                "datasets": [
                    {
                        "id": "cfafbeb1-8037-4d0c-896e-a46fb27ff229",
                        "name": "Finance DW",
                        "configuredBy": "alice@contoso.com",
                        "sensitivityLabel": {
                            "labelId": "sl-confidential-001",
                            "labelDisplayName": "Confidential"
                        },
                        "endorsementDetails": {
                            "endorsement": "Certified",
                            "certifiedBy": "alice@contoso.com"
                        },
                        "tables": [
                            {
                                "name": "FactSales",
                                "columns": [
                                    {"name": "SalesKey",    "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "DateKey",     "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "CustomerKey", "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "ProductKey",  "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "SalesAmount", "dataType": "Double",   "columnType": "Data"},
                                    {"name": "Quantity",    "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "Discount",    "dataType": "Double",   "columnType": "Data"},
                                    {"name": "Year",        "dataType": "Int64",    "columnType": "Calculated"},
                                ],
                                "measures": [
                                    {"name": "Total Sales",   "expression": "SUM(FactSales[SalesAmount])"},
                                    {"name": "Total Qty",     "expression": "SUM(FactSales[Quantity])"},
                                    {"name": "Avg Discount",  "expression": "AVERAGE(FactSales[Discount])"},
                                    {"name": "YTD Sales",     "expression": "TOTALYTD([Total Sales], DimDate[Date])"},
                                ],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "FinanceDB"),\n  dbo_FactSales = Source{[Schema="dbo",Item="FactSales"]}[Data]\nin\n  dbo_FactSales'}]
                            },
                            {
                                "name": "DimDate",
                                "columns": [
                                    {"name": "DateKey",       "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "Date",          "dataType": "DateTime", "columnType": "Data"},
                                    {"name": "Year",          "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "Quarter",       "dataType": "Text",     "columnType": "Data"},
                                    {"name": "Month",         "dataType": "Text",     "columnType": "Data"},
                                    {"name": "MonthNumber",   "dataType": "Int64",    "columnType": "Data"},
                                ],
                                "measures": [],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "FinanceDB"),\n  dbo_DimDate = Source{[Schema="dbo",Item="DimDate"]}[Data]\nin\n  dbo_DimDate'}]
                            },
                            {
                                "name": "DimCustomer",
                                "columns": [
                                    {"name": "CustomerKey",   "dataType": "Int64",  "columnType": "Data"},
                                    {"name": "CustomerName",  "dataType": "Text",   "columnType": "Data"},
                                    {"name": "Region",        "dataType": "Text",   "columnType": "Data"},
                                    {"name": "Segment",       "dataType": "Text",   "columnType": "Data"},
                                ],
                                "measures": [],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "FinanceDB"),\n  dbo_DimCustomer = Source{[Schema="dbo",Item="DimCustomer"]}[Data]\nin\n  dbo_DimCustomer'}]
                            },
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "252b9de8-d915-4788-aaeb-ec8c2395f970"}
                        ],
                        "upstreamDataflows": [
                            {"targetDataflowId": "df-finance-001", "groupId": "e380d1d0-1fa6-460b-9a90-1a5c6b02414c"}
                        ],
                        "users": [
                            {"emailAddress": "alice@contoso.com",   "datasetUserAccessRight": "ReadWriteReshareExplore"},
                            {"emailAddress": "finance@contoso.com", "datasetUserAccessRight": "Read"},
                        ]
                    },
                    {
                        "id": "8ce96c50-85a0-4db3-85c6-7ccc3ed46523",
                        "name": "GL Summary",
                        "configuredBy": "alice@contoso.com",
                        "sensitivityLabel": {
                            "labelId": "sl-confidential-001",
                            "labelDisplayName": "Confidential"
                        },
                        "endorsementDetails": {"endorsement": "Promoted", "certifiedBy": None},
                        "tables": [
                            {
                                "name": "GLEntries",
                                "columns": [
                                    {"name": "EntryId",     "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "AccountCode", "dataType": "Text",     "columnType": "Data"},
                                    {"name": "PostingDate", "dataType": "DateTime", "columnType": "Data"},
                                    {"name": "Amount",      "dataType": "Double",   "columnType": "Data"},
                                    {"name": "CostCentre",  "dataType": "Text",     "columnType": "Data"},
                                ],
                                "measures": [
                                    {"name": "Net Balance", "expression": "SUM(GLEntries[Amount])"},
                                    {"name": "Debit Total", "expression": "CALCULATE(SUM(GLEntries[Amount]), GLEntries[Amount] > 0)"},
                                ],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "FinanceDB"),\n  dbo_GLEntries = Source{[Schema="dbo",Item="GLEntries"]}[Data]\nin\n  dbo_GLEntries'}]
                            }
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "252b9de8-d915-4788-aaeb-ec8c2395f970"}
                        ],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "alice@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                        ]
                    }
                ],
                "reports": [
                    {
                        "id": "5DBA60B0-D9A7-42AE-B12C-6D9D51E7739A",
                        "name": "Monthly P&L",
                        "datasetId": "cfafbeb1-8037-4d0c-896e-a46fb27ff229",
                        "sensitivityLabel": {"labelId": "sl-confidential-001", "labelDisplayName": "Confidential"},
                        "users": [
                            {"emailAddress": "alice@contoso.com",   "reportUserAccessRight": "Owner"},
                            {"emailAddress": "finance@contoso.com", "reportUserAccessRight": "Read"},
                        ]
                    },
                    {
                        "id": "A1B2C3D4-0000-0000-0000-111111111111",
                        "name": "Budget vs Actual",
                        "datasetId": "8ce96c50-85a0-4db3-85c6-7ccc3ed46523",
                        "sensitivityLabel": {"labelId": "sl-confidential-001", "labelDisplayName": "Confidential"},
                        "users": [
                            {"emailAddress": "alice@contoso.com", "reportUserAccessRight": "Owner"},
                        ]
                    }
                ],
                "dataflows": [
                    {
                        "objectId": "df-finance-001",
                        "name": "Finance Source Dataflow",
                        "description": "Ingests raw GL and sales data from SQL Server",
                        "configuredBy": "alice@contoso.com",
                        "datasourceUsages": [
                            {"datasourceInstanceId": "252b9de8-d915-4788-aaeb-ec8c2395f970"}
                        ]
                    }
                ],
                "datasourceInstances": [
                    {
                        "datasourceType": "Sql",
                        "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "FinanceDB"},
                        "datasourceId": "252b9de8-d915-4788-aaeb-ec8c2395f970",
                        "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
                    }
                ]
            },

            # ── HR Analytics OLD ───────────────────────────────────────────
            {
                "id": "183dcf10-47b8-48c4-84aa-f0bf9d5f8fcf",
                "name": "HR Analytics OLD",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "defaultDatasetStorageFormat": "Small",
                "datasets": [
                    {
                        "id": "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69",
                        "name": "HR Headcount 2022",
                        "configuredBy": "bob@contoso.com",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "endorsementDetails": {"endorsement": "None", "certifiedBy": None},
                        "tables": [
                            {
                                "name": "Headcount",
                                "columns": [
                                    {"name": "EmployeeId",   "dataType": "Int64",  "columnType": "Data"},
                                    {"name": "FullName",     "dataType": "Text",   "columnType": "Data"},
                                    {"name": "Department",   "dataType": "Text",   "columnType": "Data"},
                                    {"name": "HireDate",     "dataType": "DateTime","columnType": "Data"},
                                    {"name": "IsActive",     "dataType": "Boolean","columnType": "Data"},
                                    {"name": "YearsService", "dataType": "Double", "columnType": "Calculated"},
                                ],
                                "measures": [
                                    {"name": "Headcount", "expression": "COUNTROWS(Headcount)"},
                                    {"name": "Active Employees", "expression": "CALCULATE(COUNTROWS(Headcount), Headcount[IsActive] = TRUE())"},
                                ],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-legacy-01.contoso.com", "HRDB"),\n  dbo_Employees = Source{[Schema="dbo",Item="Employees"]}[Data]\nin\n  dbo_Employees'}]
                            }
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "474d1f0a-fb37-6900-de24-66ee47e9112"}
                        ],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "bob@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                        ]
                    }
                ],
                "reports": [
                    {
                        "id": "B2C3D4E5-0000-0000-0000-222222222222",
                        "name": "Headcount Report OLD",
                        "datasetId": "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "users": [
                            {"emailAddress": "bob@contoso.com", "reportUserAccessRight": "Owner"},
                        ]
                    }
                ],
                "dataflows": [],
                "datasourceInstances": [
                    {
                        "datasourceType": "Sql",
                        "connectionDetails": {"server": "sql-legacy-01.contoso.com", "database": "HRDB"},
                        "datasourceId": "474d1f0a-fb37-6900-de24-66ee47e9112",
                        "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
                    }
                ]
            },

            # ── Sales Dashboard ────────────────────────────────────────────
            {
                "id": "94E57E92-CEE2-486D-8CC8-218C97200579",
                "name": "Sales Dashboard",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "defaultDatasetStorageFormat": "Large",
                "datasets": [
                    {
                        "id": "d778934f-bda2-41d9-b5c7-6cf41372abcd",
                        "name": "Sales CRM Live",
                        "configuredBy": "carol@contoso.com",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "endorsementDetails": {"endorsement": "Certified", "certifiedBy": "carol@contoso.com"},
                        "tables": [
                            {
                                "name": "Opportunities",
                                "columns": [
                                    {"name": "OpportunityId", "dataType": "Text",     "columnType": "Data"},
                                    {"name": "AccountName",   "dataType": "Text",     "columnType": "Data"},
                                    {"name": "Stage",         "dataType": "Text",     "columnType": "Data"},
                                    {"name": "CloseDate",     "dataType": "DateTime", "columnType": "Data"},
                                    {"name": "Amount",        "dataType": "Double",   "columnType": "Data"},
                                    {"name": "OwnerId",       "dataType": "Text",     "columnType": "Data"},
                                    {"name": "Region",        "dataType": "Text",     "columnType": "Data"},
                                ],
                                "measures": [
                                    {"name": "Pipeline Value",  "expression": "SUM(Opportunities[Amount])"},
                                    {"name": "Win Rate",        "expression": "DIVIDE(CALCULATE(COUNTROWS(Opportunities), Opportunities[Stage]=\"Closed Won\"), COUNTROWS(Opportunities))"},
                                    {"name": "Avg Deal Size",   "expression": "AVERAGE(Opportunities[Amount])"},
                                ],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "SalesDB"),\n  dbo_Opportunities = Source{[Schema="dbo",Item="Opportunities"]}[Data]\nin\n  dbo_Opportunities'}]
                            },
                            {
                                "name": "Accounts",
                                "columns": [
                                    {"name": "AccountId",   "dataType": "Text", "columnType": "Data"},
                                    {"name": "AccountName", "dataType": "Text", "columnType": "Data"},
                                    {"name": "Industry",    "dataType": "Text", "columnType": "Data"},
                                    {"name": "Region",      "dataType": "Text", "columnType": "Data"},
                                    {"name": "Tier",        "dataType": "Text", "columnType": "Data"},
                                ],
                                "measures": [],
                                "source": [{"expression": 'let\n  Source = Sql.Database("sql-prod-01.contoso.com", "SalesDB"),\n  dbo_Accounts = Source{[Schema="dbo",Item="Accounts"]}[Data]\nin\n  dbo_Accounts'}]
                            }
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "363c0ef9-ea26-5899-cd13-55dd36d8001"}
                        ],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "carol@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                            {"emailAddress": "sales@contoso.com", "datasetUserAccessRight": "Read"},
                        ]
                    }
                ],
                "reports": [
                    {
                        "id": "C3D4E5F6-0000-0000-0000-333333333333",
                        "name": "Sales Pipeline",
                        "datasetId": "d778934f-bda2-41d9-b5c7-6cf41372abcd",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "users": [
                            {"emailAddress": "carol@contoso.com", "reportUserAccessRight": "Owner"},
                            {"emailAddress": "sales@contoso.com", "reportUserAccessRight": "Read"},
                        ]
                    },
                    {
                        "id": "D4E5F6A7-0000-0000-0000-444444444444",
                        "name": "Regional Performance",
                        "datasetId": "d778934f-bda2-41d9-b5c7-6cf41372abcd",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "users": [
                            {"emailAddress": "carol@contoso.com", "reportUserAccessRight": "Owner"},
                        ]
                    }
                ],
                "dataflows": [],
                "datasourceInstances": [
                    {
                        "datasourceType": "Sql",
                        "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "SalesDB"},
                        "datasourceId": "363c0ef9-ea26-5899-cd13-55dd36d8001",
                        "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
                    }
                ]
            },

            # ── Test Workspace 2022 (empty + orphaned) ─────────────────────
            {
                "id": "d5caa808-8c91-400a-911d-06af08dbcc31",
                "name": "Test Workspace 2022",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "datasets": [], "reports": [], "dataflows": [],
                "datasourceInstances": []
            },

            # ── Marketing Campaigns ────────────────────────────────────────
            {
                "id": "EC1EE11F-845D-495E-82A3-9DAC2072305A",
                "name": "Marketing Campaigns",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "datasets": [
                    {
                        "id": "a8f18ca7-63e8-4220-bc1c-f576ec180b98",
                        "name": "Campaign Tracker",
                        "configuredBy": "dave@contoso.com",
                        "sensitivityLabel": {"labelId": "sl-public-003", "labelDisplayName": "Public"},
                        "endorsementDetails": {"endorsement": "None", "certifiedBy": None},
                        "tables": [
                            {
                                "name": "Campaigns",
                                "columns": [
                                    {"name": "CampaignId",   "dataType": "Text",   "columnType": "Data"},
                                    {"name": "CampaignName", "dataType": "Text",   "columnType": "Data"},
                                    {"name": "Channel",      "dataType": "Text",   "columnType": "Data"},
                                    {"name": "StartDate",    "dataType": "DateTime","columnType": "Data"},
                                    {"name": "Budget",       "dataType": "Double", "columnType": "Data"},
                                    {"name": "Spend",        "dataType": "Double", "columnType": "Data"},
                                    {"name": "Conversions",  "dataType": "Int64",  "columnType": "Data"},
                                ],
                                "measures": [
                                    {"name": "ROI",          "expression": "DIVIDE([Total Revenue] - SUM(Campaigns[Spend]), SUM(Campaigns[Spend]))"},
                                    {"name": "Cost Per Lead","expression": "DIVIDE(SUM(Campaigns[Spend]), SUM(Campaigns[Conversions]))"},
                                ],
                                "source": [{"expression": 'let\n  Source = SharePoint.Tables("https://contoso.sharepoint.com/sites/reports"),\n  CampaignData = Source{[Name="CampaignData"]}[Data]\nin\n  CampaignData'}]
                            }
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "696f3b2c-1d59-8b22-f046-880069fb334"}
                        ],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "dave@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                        ]
                    }
                ],
                "reports": [
                    {
                        "id": "E5F6A7B8-0000-0000-0000-555555555555",
                        "name": "Q3 Campaign ROI",
                        "datasetId": "a8f18ca7-63e8-4220-bc1c-f576ec180b98",
                        "sensitivityLabel": {"labelId": "sl-public-003", "labelDisplayName": "Public"},
                        "users": [
                            {"emailAddress": "dave@contoso.com", "reportUserAccessRight": "Owner"},
                        ]
                    }
                ],
                "dataflows": [],
                "datasourceInstances": [
                    {
                        "datasourceType": "SharePoint",
                        "connectionDetails": {"url": "https://contoso.sharepoint.com/sites/reports"},
                        "datasourceId": "696f3b2c-1d59-8b22-f046-880069fb334",
                        "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045"
                    }
                ]
            },

            # ── Dev Sandbox - John ─────────────────────────────────────────
            {
                "id": "f089354e-8366-4e18-aea3-4cb4a3a50b48",
                "name": "Dev Sandbox - John",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "datasets": [
                    {
                        "id": "4668133c-ae3f-42fb-ad7c-214a8623280c",
                        "name": "Test Dataset",
                        "configuredBy": "john@contoso.com",
                        "sensitivityLabel": None,
                        "endorsementDetails": {"endorsement": "None", "certifiedBy": None},
                        "tables": [
                            {
                                "name": "TestData",
                                "columns": [
                                    {"name": "Id",    "dataType": "Int64", "columnType": "Data"},
                                    {"name": "Value", "dataType": "Double","columnType": "Data"},
                                ],
                                "measures": [],
                                "source": [{"expression": "let\n  Source = Table.FromRows({})\nin\n  Source"}]
                            }
                        ],
                        "datasourceUsages": [],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "john@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                        ]
                    }
                ],
                "reports": [],
                "dataflows": [],
                "datasourceInstances": []
            },

            # ── Supply Chain Metrics ───────────────────────────────────────
            {
                "id": "ccccdddd-2222-eeee-3333-ffff4444aaaa",
                "name": "Supply Chain Metrics",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": True,
                "capacityId": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
                "datasets": [
                    {
                        "id": "eeee1111-ffff-2222-aaaa-333344445555",
                        "name": "Supply Chain KPI",
                        "configuredBy": "eve@contoso.com",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "endorsementDetails": {"endorsement": "Certified", "certifiedBy": "eve@contoso.com"},
                        "tables": [
                            {
                                "name": "SupplierScorecard",
                                "columns": [
                                    {"name": "SupplierId",      "dataType": "Text",     "columnType": "Data"},
                                    {"name": "SupplierName",    "dataType": "Text",     "columnType": "Data"},
                                    {"name": "DeliveryScore",   "dataType": "Double",   "columnType": "Data"},
                                    {"name": "QualityScore",    "dataType": "Double",   "columnType": "Data"},
                                    {"name": "PriceIndex",      "dataType": "Double",   "columnType": "Data"},
                                    {"name": "LeadTimeDays",    "dataType": "Int64",    "columnType": "Data"},
                                    {"name": "LastOrderDate",   "dataType": "DateTime", "columnType": "Data"},
                                    {"name": "OverallScore",    "dataType": "Double",   "columnType": "Calculated"},
                                ],
                                "measures": [
                                    {"name": "Avg Delivery Score", "expression": "AVERAGE(SupplierScorecard[DeliveryScore])"},
                                    {"name": "At Risk Suppliers",  "expression": "CALCULATE(COUNTROWS(SupplierScorecard), SupplierScorecard[OverallScore] < 60)"},
                                ],
                                "source": [{"expression": 'let\n  Source = Oracle.Database("ora-prod-01.contoso.com", [Query="SELECT * FROM SCM.SUPPLIER_SCORECARD"]),\n  Data = Source\nin\n  Data'}]
                            },
                            {
                                "name": "Inventory",
                                "columns": [
                                    {"name": "SKU",          "dataType": "Text",   "columnType": "Data"},
                                    {"name": "ProductName",  "dataType": "Text",   "columnType": "Data"},
                                    {"name": "StockOnHand",  "dataType": "Int64",  "columnType": "Data"},
                                    {"name": "ReorderPoint", "dataType": "Int64",  "columnType": "Data"},
                                    {"name": "DaysOfSupply", "dataType": "Double", "columnType": "Calculated"},
                                ],
                                "measures": [
                                    {"name": "Low Stock Items", "expression": "CALCULATE(COUNTROWS(Inventory), Inventory[StockOnHand] < Inventory[ReorderPoint])"},
                                ],
                                "source": [{"expression": 'let\n  Source = Oracle.Database("ora-prod-01.contoso.com", [Query="SELECT * FROM SCM.INVENTORY"]),\n  Data = Source\nin\n  Data'}]
                            }
                        ],
                        "datasourceUsages": [
                            {"datasourceInstanceId": "585e2a1b-0c48-7a11-ef35-77ff58fa223"}
                        ],
                        "upstreamDataflows": [],
                        "users": [
                            {"emailAddress": "eve@contoso.com", "datasetUserAccessRight": "ReadWriteReshareExplore"},
                            {"emailAddress": "ops@contoso.com", "datasetUserAccessRight": "Read"},
                        ]
                    }
                ],
                "reports": [
                    {
                        "id": "F6A7B8C9-0000-0000-0000-666666666666",
                        "name": "Supplier Scorecard",
                        "datasetId": "eeee1111-ffff-2222-aaaa-333344445555",
                        "sensitivityLabel": {"labelId": "sl-internal-002", "labelDisplayName": "Internal"},
                        "users": [
                            {"emailAddress": "eve@contoso.com", "reportUserAccessRight": "Owner"},
                            {"emailAddress": "ops@contoso.com", "reportUserAccessRight": "Read"},
                        ]
                    }
                ],
                "dataflows": [],
                "datasourceInstances": [
                    {
                        "datasourceType": "Oracle",
                        "connectionDetails": {"server": "ora-prod-01.contoso.com", "database": "SCM"},
                        "datasourceId": "585e2a1b-0c48-7a11-ef35-77ff58fa223",
                        "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045"
                    }
                ]
            },

            # ── Temp Migration Test (empty + orphaned) ─────────────────────
            {
                "id": "aaaabbbb-cccc-dddd-eeee-ffff00001111",
                "name": "Temp - Migration Test",
                "type": "Workspace",
                "state": "Active",
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "datasets": [], "reports": [], "dataflows": [],
                "datasourceInstances": []
            },
        ],

        # Tenant-level deduplicated datasource instance list
        "datasourceInstances": [
            {
                "datasourceType": "Sql",
                "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "FinanceDB"},
                "datasourceId": "252b9de8-d915-4788-aaeb-ec8c2395f970",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
            },
            {
                "datasourceType": "Sql",
                "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "SalesDB"},
                "datasourceId": "363c0ef9-ea26-5899-cd13-55dd36d8001",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
            },
            {
                "datasourceType": "Sql",
                "connectionDetails": {"server": "sql-legacy-01.contoso.com", "database": "HRDB"},
                "datasourceId": "474d1f0a-fb37-6900-de24-66ee47e9112",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934"
            },
            {
                "datasourceType": "Oracle",
                "connectionDetails": {"server": "ora-prod-01.contoso.com", "database": "SCM"},
                "datasourceId": "585e2a1b-0c48-7a11-ef35-77ff58fa223",
                "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045"
            },
            {
                "datasourceType": "SharePoint",
                "connectionDetails": {"url": "https://contoso.sharepoint.com/sites/reports"},
                "datasourceId": "696f3b2c-1d59-8b22-f046-880069fb334",
                "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045"
            },
        ],
        "misconfiguredDatasourceInstances": []
    }
