"""
Agent Tools — functions Claude can call during the governance scan.

Each tool wraps one or more Power BI REST API calls (currently mocked).
The TOOLS list is the schema sent to Claude; execute_tool() is the router.

Real API endpoints each tool maps to:
  list_all_workspaces      → GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports&$top=5000
  get_dataset_refresh      → GET /v1.0/myorg/groups/{gId}/datasets/{dId}/refreshes?$top=1
  list_gateways_and_sources→ GET /v1.0/myorg/gateways  +  /gateways/{id}/datasources
  get_dataset_datasources  → GET /v1.0/myorg/admin/datasets/{datasetId}/datasources
  flag_stale_workspaces    → derived from groups endpoint (lastActivityDate field)
  flag_orphaned_workspaces → derived from groups?$expand=users where users = []
  flag_empty_workspaces    → derived from groups?$expand=datasets,reports
  flag_stale_datasets      → derived from refreshes endpoint per dataset
"""

import json
from datetime import datetime, timedelta, timezone
from mock_powerbi_data import (
    get_groups_as_admin,
    get_dataset_refresh_history,
    get_gateways,
    get_gateway_datasources,
    get_dataset_datasources_as_admin,
)

# ── Tool schema (sent to Claude) ──────────────────────────────────────────────

TOOLS = [
    {
        "name": "list_all_workspaces",
        "description": (
            "Returns all Power BI workspaces for the organisation with their users, "
            "datasets, and reports expanded inline. Calls "
            "GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports&$top=5000. "
            "Use this first to get a full inventory before running any flag checks."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_dataset_refresh_history",
        "description": (
            "Returns the most recent refresh record for a specific dataset. Calls "
            "GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1. "
            "Use this to check whether a dataset's last refresh was recent or stale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id":    {"type": "string", "description": "Workspace (group) ID"},
                "dataset_id":  {"type": "string", "description": "Dataset ID"},
                "dataset_name":{"type": "string", "description": "Dataset name (for context in your reasoning)"},
            },
            "required": ["group_id", "dataset_id", "dataset_name"],
        },
    },
    {
        "name": "list_gateways_and_sources",
        "description": (
            "Returns all on-premises gateway clusters and their registered datasources. "
            "Calls GET /v1.0/myorg/gateways then GET /v1.0/myorg/gateways/{id}/datasources "
            "for each gateway."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_dataset_datasources",
        "description": (
            "Returns the underlying data sources for a specific dataset, including "
            "server, database, gatewayId, and credentialType. Calls "
            "GET /v1.0/myorg/admin/datasets/{datasetId}/datasources."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_id":   {"type": "string", "description": "Dataset ID"},
                "dataset_name": {"type": "string", "description": "Dataset name (for context)"},
            },
            "required": ["dataset_id", "dataset_name"],
        },
    },
    {
        "name": "flag_stale_workspaces",
        "description": (
            "Scans all workspaces and flags those with no activity beyond the threshold. "
            "Derived from the lastActivityDate field on the groups endpoint."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_threshold": {"type": "integer", "description": "Inactivity threshold in days (default 90)", "default": 90}
            },
            "required": [],
        },
    },
    {
        "name": "flag_orphaned_workspaces",
        "description": (
            "Scans all workspaces and flags those with no assigned users (no Admin, Member, "
            "Contributor, or Viewer). Derived from users[] in the groups endpoint. "
            "Corresponds to the OData filter: $filter=(not users/any())."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "flag_empty_workspaces",
        "description": (
            "Scans all workspaces and flags those with no datasets and no reports. "
            "Derived from datasets[] and reports[] in the groups endpoint."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "flag_stale_datasets",
        "description": (
            "Scans all refreshable datasets across all workspaces and flags those whose "
            "last refresh is older than the threshold. Calls the refresh history endpoint "
            "for each refreshable dataset."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_threshold": {"type": "integer", "description": "Staleness threshold in days (default 90)", "default": 90}
            },
            "required": [],
        },
    },
]


# ── Tool execution router ─────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    handlers = {
        "list_all_workspaces":       _list_all_workspaces,
        "get_dataset_refresh_history": _get_dataset_refresh_history,
        "list_gateways_and_sources": _list_gateways_and_sources,
        "get_dataset_datasources":   _get_dataset_datasources,
        "flag_stale_workspaces":     _flag_stale_workspaces,
        "flag_orphaned_workspaces":  _flag_orphaned_workspaces,
        "flag_empty_workspaces":     _flag_empty_workspaces,
        "flag_stale_datasets":       _flag_stale_datasets,
    }
    fn = handlers.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    return json.dumps(fn(**tool_input), indent=2, default=str)


# ── Tool implementations ──────────────────────────────────────────────────────

def _list_all_workspaces() -> dict:
    """GET /v1.0/myorg/admin/groups?$expand=users,datasets,reports&$top=5000"""
    response = get_groups_as_admin()
    return {
        "@odata.context": "https://api.powerbi.com/v1.0/myorg/$metadata#groups",
        "value": response["value"],
        "totalCount": len(response["value"]),
    }


def _get_dataset_refresh_history(group_id: str, dataset_id: str, dataset_name: str) -> dict:
    """GET /v1.0/myorg/groups/{groupId}/datasets/{datasetId}/refreshes?$top=1"""
    return get_dataset_refresh_history(group_id, dataset_id, top=1)


def _list_gateways_and_sources() -> dict:
    """GET /v1.0/myorg/gateways  +  GET /v1.0/myorg/gateways/{id}/datasources"""
    gateways = get_gateways()["value"]
    result = []
    for gw in gateways:
        sources = get_gateway_datasources(gw["id"])
        result.append({
            "gateway": gw,
            "datasources": sources.get("value", []),
            "datasourceCount": len(sources.get("value", [])),
        })
    return {
        "@odata.context": "https://api.powerbi.com/v1.0/myorg/$metadata#gateways",
        "gateways": result,
        "gatewayCount": len(result),
    }


def _get_dataset_datasources(dataset_id: str, dataset_name: str) -> dict:
    """GET /v1.0/myorg/admin/datasets/{datasetId}/datasources"""
    return get_dataset_datasources_as_admin(dataset_id)


def _flag_stale_workspaces(days_threshold: int = 90) -> dict:
    """Derived: workspaces where lastActivityDate < NOW - threshold."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)
    stale = []
    for ws in get_groups_as_admin()["value"]:
        last = ws.get("lastActivityDate")
        if last:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if last_dt < cutoff:
                stale.append({**ws, "_daysInactive": (datetime.now(timezone.utc) - last_dt).days})
    return {
        "thresholdDays": days_threshold,
        "staleWorkspaces": stale,
        "count": len(stale),
        "_note": "lastActivityDate not returned by the real admin/groups endpoint. "
                 "In production derive this from the Activity Events API: "
                 "GET /v1.0/myorg/admin/activityevents",
    }


def _flag_orphaned_workspaces() -> dict:
    """Derived: workspaces where users[] is empty (no Admin or any member)."""
    orphaned = []
    for ws in get_groups_as_admin()["value"]:
        if not ws.get("users"):
            orphaned.append(ws)
    return {
        "orphanedWorkspaces": orphaned,
        "count": len(orphaned),
        "_oDataEquivalent": "$expand=users&$filter=(not users/any())",
    }


def _flag_empty_workspaces() -> dict:
    """Derived: workspaces with no datasets AND no reports."""
    empty = []
    for ws in get_groups_as_admin()["value"]:
        if not ws.get("datasets") and not ws.get("reports"):
            empty.append(ws)
    return {
        "emptyWorkspaces": empty,
        "count": len(empty),
    }


def _flag_stale_datasets(days_threshold: int = 90) -> dict:
    """Calls refresh history for every refreshable dataset; flags stale ones."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_threshold)
    stale = []
    for ws in get_groups_as_admin()["value"]:
        for ds in ws.get("datasets", []):
            if not ds.get("isRefreshable"):
                continue
            history = get_dataset_refresh_history(ws["id"], ds["id"])
            entries = history.get("value", [])
            if not entries:
                # Never refreshed counts as stale
                stale.append({
                    **ds,
                    "_workspaceId": ws["id"],
                    "_workspaceName": ws["name"],
                    "_lastRefreshStatus": "NeverRefreshed",
                    "_daysSinceRefresh": None,
                })
            else:
                last_end = entries[0].get("endTime") or entries[0].get("startTime")
                if last_end:
                    last_dt = datetime.fromisoformat(last_end.replace("Z", "+00:00"))
                    if last_dt < cutoff:
                        stale.append({
                            **ds,
                            "_workspaceId": ws["id"],
                            "_workspaceName": ws["name"],
                            "_lastRefreshEndTime": last_end,
                            "_lastRefreshStatus": entries[0].get("status"),
                            "_daysSinceRefresh": (datetime.now(timezone.utc) - last_dt).days,
                        })
    return {
        "thresholdDays": days_threshold,
        "staleDatasets": stale,
        "count": len(stale),
    }
