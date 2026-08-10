# OCI IAM Policy Statement Counter

A Python utility for inventorying OCI IAM policy usage across an entire tenancy compartment hierarchy.

The script starts at the tenancy root compartment, traverses every active subcompartment, and reports both direct policy usage and cumulative policy statement counts inherited through the compartment hierarchy.

## Purpose

The primary goal is to understand how many OCI IAM policy statements exist at each level of a tenancy and how those statement counts accumulate as you move deeper into the compartment hierarchy.

For every compartment, the script reports:

* Full compartment path
* Compartment OCID
* Parent compartment OCID
* Hierarchy level
* Number of policies defined directly in the compartment
* Number of policy statements defined directly in the compartment
* Total policy statement count from the tenancy root through the current compartment

This makes it easier to identify areas of the tenancy with large or increasingly complex IAM policy footprints.

## How It Works

The script:

1. Loads OCI credentials from the standard OCI configuration file.
2. Determines the tenancy OCID from the selected OCI profile.
3. Uses the tenancy itself as the root compartment.
4. Traverses all active compartments beneath the tenancy.
5. Builds the full compartment path for every compartment.
6. Retrieves IAM policies defined directly in each compartment.
7. Counts:

   * Policies at that compartment
   * Policy statements at that compartment
8. Calculates the cumulative number of policy statements from the tenancy root through each compartment.
9. Writes the results as CSV to standard output.

## Requirements

* Python 3
* OCI Python SDK
* A valid OCI SDK/CLI configuration file
* OCI permissions sufficient to read:

  * Compartments
  * IAM policies

Install the Python dependency with:

```bash
python -m pip install -r requirements.txt
```

A minimal `requirements.txt` is:

```text
oci
```

The OCI SDK version is intentionally not pinned, allowing `pip` to install a current compatible version.

## OCI Configuration

By default, the script uses:

```text
~/.oci/config
```

and the OCI configuration profile:

```text
DEFAULT
```

A typical OCI configuration entry looks similar to:

```ini
[DEFAULT]
user=ocid1.user.oc1...
fingerprint=...
tenancy=ocid1.tenancy.oc1...
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

The tenancy OCID is read automatically from the selected profile:

```text
tenancy=ocid1.tenancy.oc1...
```

There is no need to provide a starting compartment OCID.

## Usage

Basic usage:

```bash
python oci_policy_counts.py
```

On Windows PowerShell:

```powershell
python .\oci_policy_counts.py
```

To use a different OCI profile:

```powershell
python .\oci_policy_counts.py --profile PROD
```

To use a different OCI configuration file:

```powershell
python .\oci_policy_counts.py `
    --config-file "C:\Users\username\.oci\config" `
    --profile PROD
```

## Command-Line Options

```text
--profile
    OCI configuration profile to use.
    Default: DEFAULT

--config-file
    Path to the OCI configuration file.
    Default: ~/.oci/config

-h, --help
    Display command-line help.
```

## Output

The script writes CSV output to standard output.

The columns are:

| Column                  | Description                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- |
| `compartment_path`      | Full compartment path from tenancy root to the current compartment           |
| `compartment_ocid`      | OCID of the current compartment                                              |
| `parent_ocid`           | OCID of the current compartment's parent                                     |
| `level`                 | Compartment depth relative to tenancy root                                   |
| `policy_count`          | Number of IAM policy objects defined directly in the current compartment     |
| `statement_count`       | Number of policy statements defined directly in the current compartment      |
| `total_statement_count` | Total number of statements from tenancy root through the current compartment |

Example:

```csv
compartment_path,compartment_ocid,parent_ocid,level,policy_count,statement_count,total_statement_count
MyTenancy,ocid1.tenancy.oc1..example,,0,8,24,24
MyTenancy/Production,ocid1.compartment.oc1..prod,ocid1.tenancy.oc1..example,1,3,10,34
MyTenancy/Development,ocid1.compartment.oc1..dev,ocid1.tenancy.oc1..example,1,2,6,30
MyTenancy/Production/Database,ocid1.compartment.oc1..db,ocid1.compartment.oc1..prod,2,2,5,39
```

## Understanding the Counts

### `policy_count`

The number of IAM policy objects defined directly in the current compartment.

For example, if a compartment contains three policy objects:

```text
policy_count = 3
```

### `statement_count`

The total number of individual policy statements contained in policies defined directly in the current compartment.

For example, one policy containing:

```text
Allow group Developers to read instances in compartment Development
Allow group Developers to use virtual-network-family in compartment Development
Allow group Developers to inspect volumes in compartment Development
```

would produce:

```text
policy_count = 1
statement_count = 3
```

### `total_statement_count`

The cumulative number of policy statements from the tenancy root through the current compartment.

For example:

```text
Root                         20 statements
Root/Production              10 statements
Root/Production/Database      5 statements
```

The output would be:

```text
Root
statement_count = 20
total_statement_count = 20

Root/Production
statement_count = 10
total_statement_count = 30

Root/Production/Database
statement_count = 5
total_statement_count = 35
```

Sibling compartments do not contribute to one another's totals.

For example:

```text
Root
├── Production
└── Development
```

Policies under `Production` do not increase the `total_statement_count` for `Development`.

## Compartment Paths

Each compartment is shown using its full hierarchy path.

For example:

```text
MyTenancy
MyTenancy/Production
MyTenancy/Production/Applications
MyTenancy/Production/Applications/Finance
```

This makes it easier to identify compartments with duplicate or similar names located in different parts of the tenancy.

## Hierarchy Levels

The tenancy root is assigned:

```text
level = 0
```

Its direct child compartments are:

```text
level = 1
```

Their children are:

```text
level = 2
```

and so on.

The script processes parent compartments before their children so cumulative statement counts can be calculated correctly.

## Saving the Output

Because the script writes CSV to standard output, results can be redirected directly to a file.

Windows PowerShell:

```powershell
python .\oci_policy_counts.py > oci_policy_counts.csv
```

Using a named OCI profile:

```powershell
python .\oci_policy_counts.py --profile PROD > oci_policy_counts.csv
```

Linux/macOS:

```bash
python oci_policy_counts.py > oci_policy_counts.csv
```

The resulting CSV can be opened directly in Excel or imported into another analysis tool.

## Scope and Interpretation

The script counts policy statements based on where policies are defined in the OCI compartment hierarchy.

`total_statement_count` is therefore a structural cumulative count:

```text
current compartment statements
+
all ancestor compartment statements
```

It does not parse the text of individual policy statements or determine whether every ancestor statement actually applies to every resource in the current compartment.

OCI IAM policies can define scope and conditions within the policy statement itself, so this utility should be considered an inventory and complexity-analysis tool rather than an effective-permissions analyzer.

## Active Compartments

Only compartments whose lifecycle state is:

```text
ACTIVE
```

are traversed.

Inactive or deleted compartments are excluded from further traversal.

## Permissions

The OCI identity used by the selected configuration profile must have sufficient permission to enumerate the relevant compartments and policies.

If the executing identity cannot see a compartment or its policies, that information may not appear in the output.

## Security

OCI credentials should never be stored directly in the source code.

The application uses the OCI SDK configuration file and private key referenced by that configuration.

Sensitive files should not be committed to Git.

Recommended `.gitignore` entries include:

```gitignore
.oci/
*.pem
.env
.venv/
venv/
__pycache__/
```

Before committing changes, review staged and unstaged files with:

```bash
git status
```

## Example Workflow

Run the script:

```powershell
python .\oci_policy_counts.py > oci_policy_counts.csv
```

Review the CSV:

```text
compartment_path
MyTenancy
MyTenancy/Production
MyTenancy/Development
MyTenancy/Production/Database
MyTenancy/Production/Applications
```

Use `statement_count` to understand IAM policy complexity defined directly at each compartment.

Use `total_statement_count` to understand how the cumulative statement count increases as a workload is placed deeper in the compartment hierarchy.

## Current Limitations

The current implementation:

* Produces CSV output only
* Counts statements but does not parse their contents
* Does not determine effective IAM permissions
* Does not identify duplicate policy statements
* Does not categorize policies by subject, verb, resource type, or scope
* Does not traverse inactive compartments
* Depends on the visibility granted to the OCI identity running the script

## Possible Future Enhancements

Potential enhancements include:

* Add JSON output
* Add direct output-file support
* Add tenancy-wide summary totals
* Add per-level aggregate totals
* Parse policy statements by:

  * Subject
  * Verb
  * Resource type
  * Compartment scope
* Identify duplicate or redundant policy statements
* Highlight compartments with unusually high statement counts
* Add include/exclude filters for compartment paths
* Generate hierarchy-oriented reports
* Export directly to Excel
* Add effective-policy analysis
* Add error handling and reporting for inaccessible compartments

## License

Add the appropriate license for the intended use of this project.
