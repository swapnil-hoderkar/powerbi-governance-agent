"""
Scanner API Tools — the 4-step async flow as agent-callable functions.

These plug into the existing agent loop alongside tools.py.
In production, swap mock_scanner_api imports for real requests.get/post calls.

The 4-step flow:
  1. get_modified_workspaces   → which workspaces need scanning
  2. post_workspace_info_scan  → submit scan, get scanId
  3. poll_scan_status          → wait until Succeeded
  4. get_scan_result           → pull full lineage + schema payload

Phase 2 lineage tools (derived from scan result):
  5. get_lineage_for_dataset   → full upstream/downstream chain
  6. get_impact_analysis       → what breaks if X datasource/dataset changes
  7. flag_missing_sensitivity_labels  → assets with no label
  8. flag_uncertified_certified_assets → certified datasets with stale data
"""

import json
from mock_scanner_api import (
    get_modified_workspaces,
    post_workspace_info,
    get_scan_status,
    get_scan_result,
    MOCK_SCAN_ID,
)

# ── Tool schema ────────────────────────────────────────────────────────────────

SCANNER_TOOLS = [
    {
        "name": "scanner_get_modified_workspaces",
        "description": (
            "STEP 1 of Scanner API flow. "
            "Calls GET /v1.0/myorg/admin/workspaces/modified to get all workspace IDs "
            "that need scanning. Pass modifiedSince to do an incremental scan; "
            "omit it for a full tenant scan."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "modified_since": {
                    "type": "string",
                    "description": "ISO 8601 datetime. Omit for full scan."
                }
            },
            "required": []
        }
    },
    {
        "name": "scanner_post_workspace_info",
        "description": (
            "STEP 2 of Scanner API flow. "
            "Submits workspace IDs for scanning. Calls "
            "POST /v1.0/myorg/admin/workspaces/getInfo"
            "?lineage=True&datasourceDetails=True&datasetSchema=True"
            "&datasetExpressions=True&getArtifactUsers=True. "
            "Returns a scanId. Max 100 workspace IDs per call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of workspace IDs to scan (max 100)"
                }
            },
            "required": ["workspace_ids"]
        }
    },
    {
        "name": "scanner_get_scan_status",
        "description": (
            "STEP 3 of Scanner API flow. "
            "Polls GET /v1.0/myorg/admin/workspaces/scanStatus/{scanId}. "
            "In production poll every 2-5 seconds until status = 'Succeeded'. "
            "Returns current status: NotStarted | Running | Succeeded | Failed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string", "description": "The scanId from step 2"}
            },
            "required": ["scan_id"]
        }
    },
    {
        "name": "scanner_get_scan_result",
        "description": (
            "STEP 4 of Scanner API flow. Only call after status = 'Succeeded'. "
            "Calls GET /v1.0/myorg/admin/workspaces/scanResult/{scanId}. "
            "Returns full metadata: dataset tables/columns/measures/DAX expressions, "
            "datasource instances, upstream dataflow lineage, sensitivity labels, "
            "endorsement status, and artifact-level users."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scan_id": {"type": "string", "description": "The scanId from step 2"}
            },
            "required": ["scan_id"]
        }
    },
    {
        "name": "scanner_get_lineage_for_dataset",
        "description": (
            "Derives the full lineage chain for a specific dataset from scan results. "
            "Returns: upstream datasources → upstream dataflows → dataset → "
            "downstream reports → downstream dashboards. "
            "Use this for impact analysis: 'what does this dataset feed?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_id":   {"type": "string", "description": "Dataset ID"},
                "dataset_name": {"type": "string", "description": "Dataset name (for context)"}
            },
            "required": ["dataset_id", "dataset_name"]
        }
    },
    {
        "name": "scanner_get_datasource_impact",
        "description": (
            "Given a datasource server or database name, finds every dataset and report "
            "downstream of it. Use this to answer: 'If this SQL server changes, "
            "what breaks?' Derived from scanner scan result datasourceInstances + lineage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "server_or_database": {
                    "type": "string",
                    "description": "Server name or database name to search for (partial match)"
                }
            },
            "required": ["server_or_database"]
        }
    },
    {
        "name": "scanner_flag_missing_sensitivity_labels",
        "description": (
            "Scans all datasets and reports across all workspaces and flags those "
            "with no sensitivity label applied. Useful for compliance audits."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "scanner_flag_uncertified_datasets",
        "description": (
            "Lists all datasets that are not Certified or Promoted (endorsement = None). "
            "Useful for identifying assets that need governance review before promotion."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []}
    },
]


# ── Router ─────────────────────────────────────────────────────────────────────

def execute_scanner_tool(tool_name: str, tool_input: dict) -> str:
    handlers = {
        "scanner_get_modified_workspaces":      _get_modified_workspaces,
        "scanner_post_workspace_info":          _post_workspace_info,
        "scanner_get_scan_status":              _get_scan_status,
        "scanner_get_scan_result":              _get_scan_result,
        "scanner_get_lineage_for_dataset":      _get_lineage_for_dataset,
        "scanner_get_datasource_impact":        _get_datasource_impact,
        "scanner_flag_missing_sensitivity_labels": _flag_missing_sensitivity_labels,
        "scanner_flag_uncertified_datasets":    _flag_uncertified_datasets,
    }
    fn = handlers.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown scanner tool: {tool_name}"})
    return json.dumps(fn(**tool_input), indent=2, default=str)


# ── Step implementations ───────────────────────────────────────────────────────

def _get_modified_workspaces(modified_since: str = None) -> dict:
    ids = get_modified_workspaces(modified_since)
    return {
        "workspaceIds": ids,
        "count": len(ids),
        "_note": "Pass these IDs to scanner_post_workspace_info in batches of 100."
    }

def _post_workspace_info(workspace_ids: list) -> dict:
    result = post_workspace_info(workspace_ids)
    return {
        **result,
        "_note": "Now poll scanner_get_scan_status with this scanId until status = Succeeded."
    }

def _get_scan_status(scan_id: str) -> dict:
    result = get_scan_status(scan_id)
    return {
        **result,
        "_note": "When status = Succeeded, call scanner_get_scan_result."
    }

def _get_scan_result(scan_id: str) -> dict:
    """
    Returns scan metadata trimmed for Claude's context window.
    Tables, columns, measures, and Power Query expressions are stripped —
    they are large and not needed for governance/lineage reporting.
    Derived tools (lineage, impact, labels, endorsement) call get_scan_result()
    directly from mock_scanner_api and still receive the full payload.
    """
    raw = get_scan_result(scan_id)

    trimmed_workspaces = []
    for ws in raw.get("workspaces", []):
        trimmed_datasets = []
        for ds in ws.get("datasets", []):
            trimmed_datasets.append({
                "id": ds["id"],
                "name": ds["name"],
                "configuredBy": ds.get("configuredBy"),
                "datasourceUsages": ds.get("datasourceUsages", []),
                "upstreamDataflows": ds.get("upstreamDataflows", []),
                "sensitivityLabel": ds.get("sensitivityLabel"),
                "endorsementDetails": ds.get("endorsementDetails"),
            })

        trimmed_reports = []
        for r in ws.get("reports", []):
            trimmed_reports.append({
                "id": r["id"],
                "name": r["name"],
                "datasetId": r.get("datasetId"),
                "sensitivityLabel": r.get("sensitivityLabel"),
            })

        trimmed_workspaces.append({
            "id": ws["id"],
            "name": ws["name"],
            "type": ws.get("type"),
            "state": ws.get("state"),
            "isOnDedicatedCapacity": ws.get("isOnDedicatedCapacity"),
            "datasets": trimmed_datasets,
            "reports": trimmed_reports,
            "datasourceInstances": ws.get("datasourceInstances", []),
        })

    return {
        "workspaces": trimmed_workspaces,
        "datasourceInstances": raw.get("datasourceInstances", []),
        "_note": (
            "Tables, columns, measures, and expressions omitted to save context. "
            "Use scanner_get_lineage_for_dataset / scanner_get_datasource_impact "
            "for full lineage detail."
        ),
    }


# ── Derived lineage tools ──────────────────────────────────────────────────────

def _get_lineage_for_dataset(dataset_id: str, dataset_name: str) -> dict:
    """
    Builds the full lineage chain for one dataset from the scan result.
    Chain: datasource(s) → dataflow(s) → dataset → reports
    """
    result = get_scan_result(MOCK_SCAN_ID)
    all_workspaces = result["workspaces"]
    tenant_sources = {ds["datasourceId"]: ds for ds in result.get("datasourceInstances", [])}

    target_dataset = None
    target_workspace = None

    for ws in all_workspaces:
        for ds in ws.get("datasets", []):
            if ds["id"] == dataset_id:
                target_dataset = ds
                target_workspace = ws
                break

    if not target_dataset:
        return {"error": f"Dataset {dataset_id} not found in scan results"}

    # Upstream: datasources
    upstream_sources = []
    for usage in target_dataset.get("datasourceUsages", []):
        src = tenant_sources.get(usage["datasourceInstanceId"])
        if src:
            upstream_sources.append(src)

    # Upstream: dataflows
    upstream_dataflows = target_dataset.get("upstreamDataflows", [])

    # Downstream: reports in same workspace that use this dataset
    downstream_reports = [
        {"id": r["id"], "name": r["name"], "workspaceId": target_workspace["id"], "workspaceName": target_workspace["name"]}
        for r in target_workspace.get("reports", [])
        if r.get("datasetId") == dataset_id
    ]

    # Downstream: reports in OTHER workspaces (cross-workspace lineage)
    for ws in all_workspaces:
        if ws["id"] == target_workspace["id"]:
            continue
        for r in ws.get("reports", []):
            if r.get("datasetId") == dataset_id:
                downstream_reports.append({
                    "id": r["id"], "name": r["name"],
                    "workspaceId": ws["id"], "workspaceName": ws["name"],
                    "_crossWorkspace": True
                })

    return {
        "datasetId":   dataset_id,
        "datasetName": dataset_name,
        "workspaceId":   target_workspace["id"],
        "workspaceName": target_workspace["name"],
        "endorsement": (target_dataset.get("endorsementDetails") or {}).get("endorsement"),
        "sensitivityLabel": (target_dataset.get("sensitivityLabel") or {}).get("labelDisplayName"),
        "lineage": {
            "upstream": {
                "datasources": upstream_sources,
                "dataflows":   upstream_dataflows,
            },
            "downstream": {
                "reports": downstream_reports,
                "reportCount": len(downstream_reports),
            }
        },
        "tableCount":   len(target_dataset.get("tables", [])),
        "tables": [
            {
                "name": t["name"],
                "columnCount": len(t.get("columns", [])),
                "measureCount": len(t.get("measures", [])),
            }
            for t in target_dataset.get("tables", [])
        ]
    }


def _get_datasource_impact(server_or_database: str) -> dict:
    """
    Finds all datasets and reports downstream of a given server/database.
    Answers: 'If sql-prod-01 changes, what breaks?'
    """
    result = get_scan_result(MOCK_SCAN_ID)
    search = server_or_database.lower()
    tenant_sources = result.get("datasourceInstances", [])

    # Find matching datasource instances
    matching_source_ids = set()
    matched_sources = []
    for src in tenant_sources:
        conn = src.get("connectionDetails", {})
        conn_str = " ".join(str(v).lower() for v in conn.values())
        if search in conn_str:
            matching_source_ids.add(src["datasourceId"])
            matched_sources.append(src)

    if not matching_source_ids:
        return {"error": f"No datasources found matching '{server_or_database}'"}

    # Find all datasets that use those datasources
    impacted_datasets = []
    impacted_reports = []

    for ws in result["workspaces"]:
        for ds in ws.get("datasets", []):
            used_ids = {u["datasourceInstanceId"] for u in ds.get("datasourceUsages", [])}
            if used_ids & matching_source_ids:
                impacted_datasets.append({
                    "datasetId": ds["id"],
                    "datasetName": ds["name"],
                    "workspaceId": ws["id"],
                    "workspaceName": ws["name"],
                    "endorsement": (ds.get("endorsementDetails") or {}).get("endorsement"),
                    "configuredBy": ds.get("configuredBy"),
                })
                # All reports downstream of this dataset
                for r in ws.get("reports", []):
                    if r.get("datasetId") == ds["id"]:
                        impacted_reports.append({
                            "reportId": r["id"],
                            "reportName": r["name"],
                            "datasetId": ds["id"],
                            "datasetName": ds["name"],
                            "workspaceId": ws["id"],
                            "workspaceName": ws["name"],
                        })

    return {
        "searchTerm": server_or_database,
        "matchedDatasources": matched_sources,
        "impactSummary": {
            "datasourceCount": len(matched_sources),
            "impactedDatasetCount": len(impacted_datasets),
            "impactedReportCount": len(impacted_reports),
        },
        "impactedDatasets": impacted_datasets,
        "impactedReports": impacted_reports,
    }


def _flag_missing_sensitivity_labels() -> dict:
    result = get_scan_result(MOCK_SCAN_ID)
    unlabelled_datasets = []
    unlabelled_reports = []

    for ws in result["workspaces"]:
        for ds in ws.get("datasets", []):
            if not ds.get("sensitivityLabel"):
                unlabelled_datasets.append({
                    "id": ds["id"], "name": ds["name"],
                    "workspaceId": ws["id"], "workspaceName": ws["name"],
                    "configuredBy": ds.get("configuredBy"),
                })
        for r in ws.get("reports", []):
            if not r.get("sensitivityLabel"):
                unlabelled_reports.append({
                    "id": r["id"], "name": r["name"],
                    "workspaceId": ws["id"], "workspaceName": ws["name"],
                })

    return {
        "unlabelledDatasets": unlabelled_datasets,
        "unlabelledReports":  unlabelled_reports,
        "summary": {
            "unlabelledDatasetCount": len(unlabelled_datasets),
            "unlabelledReportCount":  len(unlabelled_reports),
        }
    }


def _flag_uncertified_datasets() -> dict:
    result = get_scan_result(MOCK_SCAN_ID)
    uncertified = []

    for ws in result["workspaces"]:
        for ds in ws.get("datasets", []):
            endorsement = (ds.get("endorsementDetails") or {}).get("endorsement", "None")
            if endorsement not in ("Certified", "Promoted"):
                uncertified.append({
                    "id": ds["id"], "name": ds["name"],
                    "workspaceId": ws["id"], "workspaceName": ws["name"],
                    "endorsement": endorsement,
                    "configuredBy": ds.get("configuredBy"),
                    "sensitivityLabel": ds.get("sensitivityLabel", {}).get("labelDisplayName") if ds.get("sensitivityLabel") else None,
                })

    return {
        "uncertifiedDatasets": uncertified,
        "count": len(uncertified),
        "_note": "These datasets have no endorsement. Review for Certified or Promoted status."
    }
