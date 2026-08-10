#!/usr/bin/env python3
import csv
import sys
import argparse
from collections import deque
import oci

parser = argparse.ArgumentParser(
    description="Count OCI IAM policy statements for a compartment subtree."
)
parser.add_argument(
    "--profile",
    default="DEFAULT",
    help="OCI config profile name (default: DEFAULT)"
)
parser.add_argument(
    "--config-file",
    default="~/.oci/config",
    help="OCI config file path (default: ~/.oci/config)"
)
parser.add_argument(
    "--start-compartment-id",
    required=True,
    help="Compartment OCID to start the crawl from"
)
args = parser.parse_args()

config = oci.config.from_file(args.config_file, args.profile)
identity = oci.identity.IdentityClient(config)

start = identity.get_compartment(
    compartment_id=args.start_compartment_id
).data

seen = set()
queue = deque([(start, 0)])
rows = []

while queue:
    comp, level = queue.popleft()
    if comp.id in seen:
        continue
    seen.add(comp.id)
    rows.append((comp, level))

    children = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        compartment_id=comp.id,
        access_level="ANY"
    ).data

    for child in children:
        if child.lifecycle_state == "ACTIVE":
            queue.append((child, level + 1))

writer = csv.writer(sys.stdout)
writer.writerow([
    "compartment_name",
    "compartment_ocid",
    "parent_ocid",
    "relative_level",
    "policy_count",
    "statement_count"
])

for comp, level in sorted(rows, key=lambda x: (x[1], x[0].name.lower())):
    policies = oci.pagination.list_call_get_all_results(
        identity.list_policies,
        compartment_id=comp.id
    ).data

    policy_count = len(policies)
    statement_count = sum(len(p.statements or []) for p in policies)

    writer.writerow([
        comp.name,
        comp.id,
        comp.compartment_id or "",
        level,
        policy_count,
        statement_count
    ])