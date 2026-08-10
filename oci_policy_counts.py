#!/usr/bin/env python3

import argparse
import csv
import sys
from collections import deque

import oci


parser = argparse.ArgumentParser(
    description=(
        "Count OCI IAM policies and policy statements across the entire "
        "tenancy compartment hierarchy."
    )
)

parser.add_argument(
    "--profile",
    default="DEFAULT",
    help="OCI config profile name (default: DEFAULT)",
)

parser.add_argument(
    "--config-file",
    default="~/.oci/config",
    help="OCI config file path (default: ~/.oci/config)",
)

args = parser.parse_args()


# Load OCI configuration and create Identity client.
config = oci.config.from_file(args.config_file, args.profile)
identity = oci.identity.IdentityClient(config)
tenancy_id = config["tenancy"]


# The tenancy itself is the root compartment.
start = identity.get_compartment(
    compartment_id=tenancy_id
).data


# Queue entries contain:
#   compartment object
#   hierarchy level
#   full compartment path
queue = deque([
    (start, 0, start.name)
])

seen = set()
rows = []


# Discover the complete active compartment hierarchy.
while queue:
    comp, level, path = queue.popleft()

    if comp.id in seen:
        continue

    seen.add(comp.id)

    rows.append({
        "comp": comp,
        "level": level,
        "path": path,
    })

    children = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        compartment_id=comp.id,
        access_level="ANY",
    ).data

    for child in children:
        if child.lifecycle_state == "ACTIVE":
            child_path = f"{path}/{child.name}"

            queue.append(
                (
                    child,
                    level + 1,
                    child_path,
                )
            )


# Stores the cumulative policy statement count for each compartment.
# Child compartments use their parent's cumulative total.
cumulative_statement_counts = {}


writer = csv.writer(sys.stdout)

writer.writerow([
    "compartment_path",
    "compartment_ocid",
    "parent_ocid",
    "level",
    "policy_count",
    "statement_count",
    "total_statement_count",
])


# Sorting by level ensures parents are processed before their children.
for row in sorted(
    rows,
    key=lambda x: (x["level"], x["path"].lower()),
):
    comp = row["comp"]
    level = row["level"]
    path = row["path"]

    policies = oci.pagination.list_call_get_all_results(
        identity.list_policies,
        compartment_id=comp.id,
    ).data

    # Number of policy objects defined directly in this compartment.
    policy_count = len(policies)

    # Number of policy statements defined directly in this compartment.
    statement_count = sum(
        len(policy.statements or [])
        for policy in policies
    )

    # Get the cumulative statement count inherited from the parent.
    # The tenancy/root compartment has no parent in this traversal,
    # so its parent total defaults to zero.
    parent_statement_count = cumulative_statement_counts.get(
        comp.compartment_id,
        0,
    )

    # Statements at this compartment plus all ancestor compartments.
    total_statement_count = (
        parent_statement_count
        + statement_count
    )

    # Store this compartment's cumulative total so its children
    # can inherit it.
    cumulative_statement_counts[comp.id] = total_statement_count

    writer.writerow([
        path,
        comp.id,
        comp.compartment_id or "",
        level,
        policy_count,
        statement_count,
        total_statement_count,
    ])