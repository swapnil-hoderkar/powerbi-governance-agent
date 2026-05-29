"""
Mock Power BI REST API responses.

Response shapes are taken directly from the official Microsoft Learn docs:

  GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports
      https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-groups-as-admin

  GET /v1.0/myorg/admin/groups/{groupId}/users
      https://learn.microsoft.com/en-us/rest/api/power-bi/admin/groups-get-group-users-as-admin

  GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes
      https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/get-refresh-history-in-group

  GET /v1.0/myorg/gateways
      https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/get-gateways

  GET /v1.0/myorg/gateways/{gatewayId}/datasources
      https://learn.microsoft.com/en-us/rest/api/power-bi/gateways/get-datasources

  GET /v1.0/myorg/admin/datasets/{datasetId}/datasources
      https://learn.microsoft.com/en-us/rest/api/power-bi/admin/datasets-get-datasources-as-admin

Every field name, type, and nesting level matches what the real API returns.
To move to production: replace each function body with a real requests.get() call.
"""

from datetime import datetime, timedelta, timezone

# ── Helpers ────────────────────────────────────────────────────────────────────

def _iso(dt: datetime) -> str:
    """Return ISO 8601 UTC string as Power BI emits it."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

NOW = datetime.now(timezone.utc)

def _ago(**kwargs) -> str:
    return _iso(NOW - timedelta(**kwargs))


# ══════════════════════════════════════════════════════════════════════════════
# Admin - Groups GetGroupsAsAdmin
# GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports&$top=5000
#
# Real response shape (from MS Learn):
# {
#   "value": [
#     {
#       "id": "e380d1d0-...",
#       "isReadOnly": false,
#       "isOnDedicatedCapacity": true,
#       "capacityId": "0f084df7-...",
#       "defaultDatasetStorageFormat": "Small",
#       "name": "Sample Group 1",
#       "description": "Sample group",
#       "type": "Workspace",
#       "state": "Active",
#       "hasWorkspaceLevelSettings": true,
#       "users": [ { "emailAddress": "john@contoso.com",
#                    "groupUserAccessRight": "Admin" } ],
#       "datasets": [ { "id": "cfafbeb1-...", "name": "SalesMarketing",
#                       "addRowsAPIEnabled": false,
#                       "configuredBy": "john@contoso.com",
#                       "isRefreshable": true,
#                       "isEffectiveIdentityRequired": false,
#                       "isEffectiveIdentityRolesRequired": false,
#                       "isOnPremGatewayRequired": true,
#                       "targetStorageMode": "Abf",
#                       "createdDate": "2019-04-30T21:35:15.867-07:00",
#                       "ContentProviderType": "PbixInImportMode",
#                       "isInPlaceSharingEnabled": false } ],
#       "reports": [ { "id": "5DBA60B0-...",
#                      "reportType": "PowerBIReport",
#                      "name": "SQlAzure-Refresh",
#                      "datasetId": "8ce96c50-..." } ]
#     }
#   ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_groups_as_admin() -> dict:
    """
    Mimics: GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports&$top=5000
    Returns the full { "value": [...] } envelope the real API returns.
    """
    return {
        "value": [
            # ── ws-001  Finance Reporting  (healthy, active) ───────────────
            {
                "id": "e380d1d0-1fa6-460b-9a90-1a5c6b02414c",
                "isReadOnly": False,
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "defaultDatasetStorageFormat": "Small",
                "name": "Finance Reporting",
                "description": "Enterprise finance reports and dashboards",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": True,
                "users": [
                    {"emailAddress": "alice@contoso.com",   "groupUserAccessRight": "Admin"},
                    {"emailAddress": "finance@contoso.com", "groupUserAccessRight": "Member"},
                    {"emailAddress": "bob@contoso.com",     "groupUserAccessRight": "Contributor"},
                ],
                "datasets": [
                    {
                        "id": "cfafbeb1-8037-4d0c-896e-a46fb27ff229",
                        "name": "Finance DW",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "alice@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": True,
                        "targetStorageMode": "Abf",
                        "createdDate": "2022-01-10T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": False,
                    },
                    {
                        "id": "8ce96c50-85a0-4db3-85c6-7ccc3ed46523",
                        "name": "GL Summary",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "alice@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": True,
                        "targetStorageMode": "Abf",
                        "createdDate": "2022-03-15T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": False,
                    },
                ],
                "reports": [
                    {"id": "5DBA60B0-D9A7-42AE-B12C-6D9D51E7739A", "reportType": "PowerBIReport", "name": "Monthly P&L",     "datasetId": "cfafbeb1-8037-4d0c-896e-a46fb27ff229", "webUrl": "https://app.powerbi.com/groups/e380d1d0/reports/5DBA60B0", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=5DBA60B0"},
                    {"id": "A1B2C3D4-0000-0000-0000-111111111111", "reportType": "PowerBIReport", "name": "Budget vs Actual", "datasetId": "8ce96c50-85a0-4db3-85c6-7ccc3ed46523", "webUrl": "https://app.powerbi.com/groups/e380d1d0/reports/A1B2C3D4", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=A1B2C3D4"},
                ],
            },

            # ── ws-002  HR Analytics OLD  (stale — 120 days inactive) ──────
            {
                "id": "183dcf10-47b8-48c4-84aa-f0bf9d5f8fcf",
                "isReadOnly": False,
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "defaultDatasetStorageFormat": "Small",
                "name": "HR Analytics OLD",
                "description": "Legacy HR headcount reporting — migrated to Fabric",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": False,
                "users": [
                    {"emailAddress": "bob@contoso.com", "groupUserAccessRight": "Admin"},
                ],
                "datasets": [
                    {
                        "id": "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69",
                        "name": "HR Headcount 2022",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "bob@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": False,
                        "targetStorageMode": "Abf",
                        "createdDate": "2022-06-01T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": False,
                    }
                ],
                "reports": [
                    {"id": "B2C3D4E5-0000-0000-0000-222222222222", "reportType": "PowerBIReport", "name": "Headcount Report OLD", "datasetId": "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69", "webUrl": "https://app.powerbi.com/groups/183dcf10/reports/B2C3D4E5", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=B2C3D4E5"},
                ],
            },

            # ── ws-003  Sales Dashboard  (healthy, active) ─────────────────
            {
                "id": "94E57E92-CEE2-486D-8CC8-218C97200579",
                "isReadOnly": False,
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "defaultDatasetStorageFormat": "Large",
                "name": "Sales Dashboard",
                "description": "Live sales pipeline and regional performance",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": True,
                "users": [
                    {"emailAddress": "carol@contoso.com", "groupUserAccessRight": "Admin"},
                    {"emailAddress": "sales@contoso.com", "groupUserAccessRight": "Member"},
                ],
                "datasets": [
                    {
                        "id": "d778934f-bda2-41d9-b5c7-6cf41372abcd",
                        "name": "Sales CRM Live",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "carol@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": True,
                        "targetStorageMode": "Abf",
                        "createdDate": "2024-01-20T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": True,
                    }
                ],
                "reports": [
                    {"id": "C3D4E5F6-0000-0000-0000-333333333333", "reportType": "PowerBIReport", "name": "Sales Pipeline",       "datasetId": "d778934f-bda2-41d9-b5c7-6cf41372abcd", "webUrl": "https://app.powerbi.com/groups/94E57E92/reports/C3D4E5F6", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=C3D4E5F6"},
                    {"id": "D4E5F6A7-0000-0000-0000-444444444444", "reportType": "PowerBIReport", "name": "Regional Performance", "datasetId": "d778934f-bda2-41d9-b5c7-6cf41372abcd", "webUrl": "https://app.powerbi.com/groups/94E57E92/reports/D4E5F6A7", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=D4E5F6A7"},
                ],
            },

            # ── ws-004  Test Workspace 2022  (stale 400 days, empty, orphaned, on Premium — waste) ──
            {
                "id": "d5caa808-8c91-400a-911d-06af08dbcc31",
                "isReadOnly": False,
                "isOnDedicatedCapacity": True,
                "capacityId": "0f084df7-c13d-451b-af5f-ed0c466403b2",
                "defaultDatasetStorageFormat": "Small",
                "name": "Test Workspace 2022",
                "description": "",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": False,
                "users": [],           # ORPHANED — no users
                "datasets": [],        # EMPTY
                "reports": [],         # EMPTY
            },

            # ── ws-005  Marketing Campaigns  (moderately stale dataset) ────
            {
                "id": "EC1EE11F-845D-495E-82A3-9DAC2072305A",
                "isReadOnly": False,
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "defaultDatasetStorageFormat": "Small",
                "name": "Marketing Campaigns",
                "description": "Campaign ROI and attribution analytics",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": True,
                "users": [
                    {"emailAddress": "dave@contoso.com",      "groupUserAccessRight": "Admin"},
                    {"emailAddress": "marketing@contoso.com", "groupUserAccessRight": "Viewer"},
                ],
                "datasets": [
                    {
                        "id": "a8f18ca7-63e8-4220-bc1c-f576ec180b98",
                        "name": "Campaign Tracker",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "dave@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": False,
                        "targetStorageMode": "Abf",
                        "createdDate": "2023-07-01T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": False,
                    }
                ],
                "reports": [
                    {"id": "E5F6A7B8-0000-0000-0000-555555555555", "reportType": "PowerBIReport", "name": "Q3 Campaign ROI", "datasetId": "a8f18ca7-63e8-4220-bc1c-f576ec180b98", "webUrl": "https://app.powerbi.com/groups/EC1EE11F/reports/E5F6A7B8", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=E5F6A7B8"},
                ],
            },

            # ── ws-006  Dev Sandbox - John  (stale 95 days, no reports) ────
            {
                "id": "f089354e-8366-4e18-aea3-4cb4a3a50b48",
                "isReadOnly": False,
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "defaultDatasetStorageFormat": "Small",
                "name": "Dev Sandbox - John",
                "description": "Personal dev workspace",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": False,
                "users": [
                    {"emailAddress": "john@contoso.com", "groupUserAccessRight": "Admin"},
                ],
                "datasets": [
                    {
                        "id": "4668133c-ae3f-42fb-ad7c-214a8623280c",
                        "name": "Test Dataset",
                        "addRowsAPIEnabled": True,
                        "configuredBy": "john@contoso.com",
                        "isRefreshable": False,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": False,
                        "targetStorageMode": "Abf",
                        "createdDate": "2023-09-01T08:00:00Z",
                        "ContentProviderType": "PushStreaming",
                        "isInPlaceSharingEnabled": False,
                    }
                ],
                "reports": [],
            },

            # ── ws-007  Supply Chain Metrics  (healthy) ────────────────────
            {
                "id": "ccccdddd-2222-eeee-3333-ffff4444aaaa",
                "isReadOnly": False,
                "isOnDedicatedCapacity": True,
                "capacityId": "1a2b3c4d-5e6f-7890-abcd-ef1234567890",
                "defaultDatasetStorageFormat": "Large",
                "name": "Supply Chain Metrics",
                "description": "Supplier KPIs, logistics, and inventory analytics",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": True,
                "users": [
                    {"emailAddress": "eve@contoso.com", "groupUserAccessRight": "Admin"},
                    {"emailAddress": "ops@contoso.com", "groupUserAccessRight": "Member"},
                ],
                "datasets": [
                    {
                        "id": "eeee1111-ffff-2222-aaaa-333344445555",
                        "name": "Supply Chain KPI",
                        "addRowsAPIEnabled": False,
                        "configuredBy": "eve@contoso.com",
                        "isRefreshable": True,
                        "isEffectiveIdentityRequired": False,
                        "isEffectiveIdentityRolesRequired": False,
                        "isOnPremGatewayRequired": True,
                        "targetStorageMode": "Abf",
                        "createdDate": "2023-05-10T08:00:00Z",
                        "ContentProviderType": "PbixInImportMode",
                        "isInPlaceSharingEnabled": False,
                    }
                ],
                "reports": [
                    {"id": "F6A7B8C9-0000-0000-0000-666666666666", "reportType": "PowerBIReport", "name": "Supplier Scorecard", "datasetId": "eeee1111-ffff-2222-aaaa-333344445555", "webUrl": "https://app.powerbi.com/groups/ccccdddd/reports/F6A7B8C9", "embedUrl": "https://app.powerbi.com/reportEmbed?reportId=F6A7B8C9"},
                ],
            },

            # ── ws-008  Temp Migration Test  (stale 200 days, empty, orphaned) ──
            {
                "id": "aaaabbbb-cccc-dddd-eeee-ffff00001111",
                "isReadOnly": False,
                "isOnDedicatedCapacity": False,
                "capacityId": None,
                "defaultDatasetStorageFormat": "Small",
                "name": "Temp - Migration Test",
                "description": "Temporary workspace created during data lake migration",
                "type": "Workspace",
                "state": "Active",
                "hasWorkspaceLevelSettings": False,
                "users": [],     # ORPHANED
                "datasets": [],  # EMPTY
                "reports": [],   # EMPTY
            },
        ]
    }


# ══════════════════════════════════════════════════════════════════════════════
# Datasets - Get Refresh History In Group
# GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1
#
# Real response shape (from MS Learn):
# {
#   "value": [
#     {
#       "refreshType": "Scheduled",
#       "startTime": "2017-06-13T09:25:43.153Z",
#       "endTime":   "2017-06-13T09:31:43.153Z",
#       "status":    "Completed",
#       "requestId": "9399bb89-25d1-44f8-8576-136d7e9014b1"
#     }
#   ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_dataset_refresh_history(group_id: str, dataset_id: str, top: int = 1) -> dict:
    """
    Mimics: GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1
    Returns the most recent refresh record. Empty value[] if never refreshed.
    """
    history = {
        # Finance DW — refreshed yesterday
        "cfafbeb1-8037-4d0c-896e-a46fb27ff229": {
            "value": [{"refreshType": "Scheduled", "startTime": _ago(days=1, hours=2), "endTime": _ago(days=1, hours=1, minutes=47), "status": "Completed", "requestId": "aaa00001-0000-0000-0000-000000000001"}]
        },
        # GL Summary — refreshed yesterday
        "8ce96c50-85a0-4db3-85c6-7ccc3ed46523": {
            "value": [{"refreshType": "Scheduled", "startTime": _ago(days=1, hours=3), "endTime": _ago(days=1, hours=2, minutes=55), "status": "Completed", "requestId": "aaa00002-0000-0000-0000-000000000002"}]
        },
        # HR Headcount 2022 — last refreshed 130 days ago (STALE)
        "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69": {
            "value": [{"refreshType": "Scheduled", "startTime": _ago(days=130), "endTime": _ago(days=130, minutes=-25), "status": "Completed", "requestId": "aaa00003-0000-0000-0000-000000000003"}]
        },
        # Sales CRM Live — refreshed today
        "d778934f-bda2-41d9-b5c7-6cf41372abcd": {
            "value": [{"refreshType": "Scheduled", "startTime": _ago(hours=4), "endTime": _ago(hours=3, minutes=48), "status": "Completed", "requestId": "aaa00004-0000-0000-0000-000000000004"}]
        },
        # Campaign Tracker — last refreshed 50 days ago (approaching stale)
        "a8f18ca7-63e8-4220-bc1c-f576ec180b98": {
            "value": [{"refreshType": "OnDemand", "startTime": _ago(days=50), "endTime": _ago(days=50, minutes=-18), "status": "Completed", "requestId": "aaa00005-0000-0000-0000-000000000005"}]
        },
        # Test Dataset — push streaming, never formally refreshed
        "4668133c-ae3f-42fb-ad7c-214a8623280c": {
            "value": []
        },
        # Supply Chain KPI — refreshed yesterday
        "eeee1111-ffff-2222-aaaa-333344445555": {
            "value": [{"refreshType": "Scheduled", "startTime": _ago(days=1, hours=1), "endTime": _ago(days=1, minutes=50), "status": "Completed", "requestId": "aaa00006-0000-0000-0000-000000000006"}]
        },
    }
    return history.get(dataset_id, {"value": []})


# ══════════════════════════════════════════════════════════════════════════════
# Gateways - Get Gateways
# GET /v1.0/myorg/gateways
#
# Real response shape (from MS Learn):
# {
#   "value": [
#     {
#       "id": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
#       "name": "My_Sample_Gateway",
#       "type": "Resource",
#       "gatewayAnnotation": "{\"gatewayContactInformation\":[\"gatewayUser@microsoft.com\"],
#                             \"gatewayVersion\":\"3000.6.8\",
#                             \"gatewayMachine\":\"MACHINE\",
#                             \"gatewayDepartment\":\"\"}"
#     }
#   ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_gateways() -> dict:
    """Mimics: GET /v1.0/myorg/gateways"""
    return {
        "value": [
            {
                "id": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                "name": "Corp Gateway Cluster A",
                "type": "Resource",
                "gatewayAnnotation": '{"gatewayContactInformation":["it-admin@contoso.com"],"gatewayVersion":"3000.109.14","gatewayMachine":"GWSERVER-PROD-01","gatewayDepartment":"IT Infrastructure"}',
            },
            {
                "id": "2a79f809-6963-5efe-bc12-44cc25c7f045",
                "name": "Corp Gateway Cluster B",
                "type": "Resource",
                "gatewayAnnotation": '{"gatewayContactInformation":["it-admin@contoso.com"],"gatewayVersion":"3000.109.14","gatewayMachine":"GWSERVER-PROD-02","gatewayDepartment":"IT Infrastructure"}',
            },
        ]
    }


# ══════════════════════════════════════════════════════════════════════════════
# Gateways - Get Datasources
# GET /v1.0/myorg/gateways/{gatewayId}/datasources
#
# Real response shape (from MS Learn):
# {
#   "value": [
#     {
#       "id": "252b9de8-d915-4788-aaeb-ec8c2395f970",
#       "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
#       "datasourceType": "Sql",
#       "connectionDetails": "{\"server\":\"MyServer\",\"database\":\"MyDatabase\"}",
#       "credentialType": "Windows",
#       "datasourceName": "Sample Datasource"
#     }
#   ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_gateway_datasources(gateway_id: str) -> dict:
    """Mimics: GET /v1.0/myorg/gateways/{gatewayId}/datasources"""
    datasources = {
        "1f69e798-5852-4fdd-ab01-33bb14b6e934": {
            "value": [
                {
                    "id": "252b9de8-d915-4788-aaeb-ec8c2395f970",
                    "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                    "datasourceType": "Sql",
                    "connectionDetails": '{"server":"sql-prod-01.contoso.com","database":"FinanceDB"}',
                    "credentialType": "Windows",
                    "datasourceName": "SQL-PROD-Finance",
                },
                {
                    "id": "363c0ef9-ea26-5899-cd13-55dd36d8001",
                    "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                    "datasourceType": "Sql",
                    "connectionDetails": '{"server":"sql-prod-01.contoso.com","database":"SalesDB"}',
                    "credentialType": "Windows",
                    "datasourceName": "SQL-PROD-Sales",
                },
                {
                    "id": "474d1f0a-fb37-6900-de24-66ee47e9112",
                    "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                    "datasourceType": "Sql",
                    "connectionDetails": '{"server":"sql-legacy-01.contoso.com","database":"HRDB"}',
                    "credentialType": "Windows",
                    "datasourceName": "SQL-LEGACY-HR",
                },
            ]
        },
        "2a79f809-6963-5efe-bc12-44cc25c7f045": {
            "value": [
                {
                    "id": "585e2a1b-0c48-7a11-ef35-77ff58fa223",
                    "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045",
                    "datasourceType": "Oracle",
                    "connectionDetails": '{"server":"ora-prod-01.contoso.com","database":"SCM"}',
                    "credentialType": "Windows",
                    "datasourceName": "Oracle-Supply",
                },
                {
                    "id": "696f3b2c-1d59-8b22-f046-88006 9fb334",
                    "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045",
                    "datasourceType": "SharePoint",
                    "connectionDetails": '{"url":"https://contoso.sharepoint.com/sites/reports"}',
                    "credentialType": "OAuth2",
                    "datasourceName": "SharePoint-Reports",
                },
            ]
        },
    }
    return datasources.get(gateway_id, {"value": []})


# ══════════════════════════════════════════════════════════════════════════════
# Admin - Datasets GetDatasourcesAsAdmin
# GET /v1.0/myorg/admin/datasets/{datasetId}/datasources
#
# Real response shape (from MS Learn):
# {
#   "value": [
#     {
#       "name": "301",
#       "connectionString": "data source=MyServer...;initial catalog=MyDatabase;...",
#       "datasourceType": "Sql",
#       "datasourceId": "16a54ccd-620d-4af3-9197-0b8c779a9a6d",
#       "gatewayId": "7f1c4e55-544b-403f-b132-da0d3a024674",
#       "connectionDetails": { "server": "MyServer.database.windows.net",
#                              "database": "MyDatabase" }
#     }
#   ]
# }
# ══════════════════════════════════════════════════════════════════════════════

def get_dataset_datasources_as_admin(dataset_id: str) -> dict:
    """Mimics: GET /v1.0/myorg/admin/datasets/{datasetId}/datasources"""
    sources = {
        "cfafbeb1-8037-4d0c-896e-a46fb27ff229": {   # Finance DW
            "value": [{
                "name": "FinanceDB",
                "connectionString": "data source=sql-prod-01.contoso.com;initial catalog=FinanceDB;persist security info=True;encrypt=True;trustservercertificate=False",
                "datasourceType": "Sql",
                "datasourceId": "252b9de8-d915-4788-aaeb-ec8c2395f970",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "FinanceDB"},
            }]
        },
        "8ce96c50-85a0-4db3-85c6-7ccc3ed46523": {   # GL Summary
            "value": [{
                "name": "FinanceDB",
                "connectionString": "data source=sql-prod-01.contoso.com;initial catalog=FinanceDB;persist security info=True;encrypt=True;trustservercertificate=False",
                "datasourceType": "Sql",
                "datasourceId": "252b9de8-d915-4788-aaeb-ec8c2395f970",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "FinanceDB"},
            }]
        },
        "7d6a4f72-1906-4e08-a469-bd6bc1ab7b69": {   # HR Headcount 2022
            "value": [{
                "name": "HRDB",
                "connectionString": "data source=sql-legacy-01.contoso.com;initial catalog=HRDB;persist security info=True;encrypt=True;trustservercertificate=False",
                "datasourceType": "Sql",
                "datasourceId": "474d1f0a-fb37-6900-de24-66ee47e9112",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                "connectionDetails": {"server": "sql-legacy-01.contoso.com", "database": "HRDB"},
            }]
        },
        "d778934f-bda2-41d9-b5c7-6cf41372abcd": {   # Sales CRM Live
            "value": [{
                "name": "SalesDB",
                "connectionString": "data source=sql-prod-01.contoso.com;initial catalog=SalesDB;persist security info=True;encrypt=True;trustservercertificate=False",
                "datasourceType": "Sql",
                "datasourceId": "363c0ef9-ea26-5899-cd13-55dd36d8001",
                "gatewayId": "1f69e798-5852-4fdd-ab01-33bb14b6e934",
                "connectionDetails": {"server": "sql-prod-01.contoso.com", "database": "SalesDB"},
            }]
        },
        "a8f18ca7-63e8-4220-bc1c-f576ec180b98": {   # Campaign Tracker
            "value": [{
                "name": "SharePoint-Reports",
                "connectionString": "",
                "datasourceType": "SharePoint",
                "datasourceId": "696f3b2c-1d59-8b22-f046-8800 69fb334",
                "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045",
                "connectionDetails": {"url": "https://contoso.sharepoint.com/sites/reports"},
            }]
        },
        "eeee1111-ffff-2222-aaaa-333344445555": {   # Supply Chain KPI
            "value": [{
                "name": "SCM",
                "connectionString": "",
                "datasourceType": "Oracle",
                "datasourceId": "585e2a1b-0c48-7a11-ef35-77ff58fa223",
                "gatewayId": "2a79f809-6963-5efe-bc12-44cc25c7f045",
                "connectionDetails": {"server": "ora-prod-01.contoso.com", "database": "SCM"},
            }]
        },
    }
    return sources.get(dataset_id, {"value": []})
