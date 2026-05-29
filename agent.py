# -*- coding: utf-8 -*-
"""
Governance Agent - core agentic loop.

Supports two modes:
  - GOVERNANCE SCAN  (default)  uses tools.py       ? stale/orphaned/empty checks
  - LINEAGE / PHASE 2 SCAN      uses scanner_tools.py ? full metadata + impact analysis

Both tool sets can run in the same session; Claude decides which to call.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anthropic
import json
from tools import TOOLS, execute_tool
from scanner_tools import SCANNER_TOOLS, execute_scanner_tool

ALL_TOOLS = TOOLS + SCANNER_TOOLS

SYSTEM_PROMPT = """
You are a Power BI Governance Agent for a large enterprise.

You have two sets of tools:

GOVERNANCE TOOLS - use for Phase 1 governance scans:
  - flag_stale_workspaces, flag_orphaned_workspaces, flag_empty_workspaces,
    flag_stale_datasets, list_gateways_and_sources

SCANNER API TOOLS - use for Phase 2 lineage/impact scans (4-step flow):
  Step 1: scanner_get_modified_workspaces
  Step 2: scanner_post_workspace_info
  Step 3: scanner_get_scan_status
  Step 4: scanner_get_scan_result
  Then: scanner_get_lineage_for_dataset, scanner_get_datasource_impact,
        scanner_flag_missing_sensitivity_labels, scanner_flag_uncertified_datasets

IMPORTANT - be efficient with tool calls:
- For governance scans: call the 4 flag_ tools directly, do NOT call
  list_all_workspaces first. Go straight to flag_ tools.
- For scanner scans: complete all 4 steps then call derived tools. Do not repeat steps.
- Write the report as soon as you have enough data. Do not over-call tools.

GOVERNANCE RULES:
- Stale workspaces:    no activity 90+ days
- Orphaned workspaces: no users
- Empty workspaces:    no datasets or reports
- Stale datasets:      not refreshed 90+ days

REPORT FORMAT:
1. EXECUTIVE SUMMARY - 3-4 sentences, key numbers only
2. Issues by severity: HIGH / MEDIUM / LOW - name, problem, action
3. RECOMMENDED ACTIONS - prioritised by impact
"""


def run_governance_scan(task: str = None, on_step=None) -> dict:
    client = anthropic.Anthropic()

    if task is None:
        task = (
            "Run a full Power BI governance audit using the governance tools. "
            "Check for stale workspaces, orphaned workspaces, empty workspaces, "
            "and stale datasets. Produce a prioritised governance report."
        )

    messages = [{"role": "user", "content": task}]
    tools_called = []
    steps = []
    total_input_tokens = 0
    total_output_tokens = 0

    def log(step_type, message):
        steps.append({"type": step_type, "message": message})
        if on_step:
            on_step(step_type, message)

    log("start", "[SCAN] Starting governance scan...")

    max_iterations = 50
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8192,
            system=SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages
        )

        total_input_tokens  += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        if response.stop_reason == "end_turn":
            final_text = "".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            log("complete", "[OK] Scan complete.")
            return {
                "report": final_text,
                "tools_called": tools_called,
                "steps": steps,
                "iterations": iteration,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
            }

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                tool_name  = block.name
                tool_input = block.input
                log("tool_call", f"[TOOL] Calling: {tool_name}({json.dumps(tool_input) if tool_input else ''})")
                tools_called.append({"tool": tool_name, "input": tool_input})

                # Route to the right executor
                if tool_name.startswith("scanner_"):
                    result = execute_scanner_tool(tool_name, tool_input)
                else:
                    result = execute_tool(tool_name, tool_input)

                summary = _summarise(tool_name, json.loads(result))
                log("tool_result", f"   ? {summary}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })

            messages.append({"role": "user", "content": tool_results})

        else:
            log("error", f"Unexpected stop reason: {response.stop_reason}")
            break

    return {
        "report": "Agent reached iteration limit.",
        "tools_called": tools_called,
        "steps": steps,
        "iterations": iteration,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
    }


def _summarise(tool_name: str, result: dict) -> str:
    s = {
        "list_all_workspaces":                   lambda r: f"Found {r.get('totalCount', 0)} workspaces",
        "flag_stale_workspaces":                 lambda r: f"{r.get('count', 0)} stale workspaces (>{r.get('thresholdDays')} days)",
        "flag_orphaned_workspaces":              lambda r: f"{r.get('count', 0)} orphaned workspaces",
        "flag_empty_workspaces":                 lambda r: f"{r.get('count', 0)} empty workspaces",
        "flag_stale_datasets":                   lambda r: f"{r.get('count', 0)} stale datasets",
        "get_dataset_refresh_history":           lambda r: f"{len(r.get('value', []))} refresh record(s)",
        "list_gateways_and_sources":             lambda r: f"{r.get('gatewayCount', 0)} gateways",
        "get_dataset_datasources":               lambda r: f"{len(r.get('value', []))} datasource(s)",
        "scanner_get_modified_workspaces":       lambda r: f"{r.get('count', 0)} workspaces to scan",
        "scanner_post_workspace_info":           lambda r: f"Scan submitted: {r.get('id')} ? {r.get('status')}",
        "scanner_get_scan_status":               lambda r: f"Scan status: {r.get('status')}",
        "scanner_get_scan_result":               lambda r: f"{len(r.get('workspaces', []))} workspaces scanned",
        "scanner_get_lineage_for_dataset":       lambda r: f"Lineage for '{r.get('datasetName')}': {r.get('lineage', {}).get('downstream', {}).get('reportCount', 0)} downstream report(s)",
        "scanner_get_datasource_impact":         lambda r: f"Impact of '{r.get('searchTerm')}': {r.get('impactSummary', {}).get('impactedReportCount', 0)} reports affected",
        "scanner_flag_missing_sensitivity_labels": lambda r: f"{r.get('summary', {}).get('unlabelledDatasetCount', 0)} unlabelled datasets",
        "scanner_flag_uncertified_datasets":     lambda r: f"{r.get('count', 0)} uncertified datasets",
    }
    try:
        return s.get(tool_name, lambda r: "Done")(result)
    except Exception:
        return "Done"


if __name__ == "__main__":
    def print_step(step_type, message):
        print(message)

    result = run_governance_scan(on_step=print_step)
    print("\n" + "=" * 60)
    print("GOVERNANCE REPORT")
    print("=" * 60)
    print(result["report"])
    print(f"\n[Tools: {len(result['tools_called'])} | Iterations: {result['iterations']}]")
