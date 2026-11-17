#Requires -Version 7.0

<#
.SYNOPSIS
Pester tests for 05_TOOLS/Export-KoaLibraryXlsx.ps1.

These tests verify the PS7 XLSX export contract:

- script exists
- stdout is valid JSON
- JSON result follows OperationResult-style shape
- XLSX file is created
- workbook contains Library, Lists, and Import_Report sheets
- Library sheet contains canonical columns
- Library rows contain expected exported metadata
- SQLite JSON array fields export as semicolon-separated XLSX text
- Lists sheet contains controlled values
- invalid or missing DB path fails cleanly with JSON stdout

The tests use Python's built-in sqlite3 and zipfile modules only. No openpyxl
dependency is required for the test fixture or workbook inspection.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

BeforeAll {
    function Get-TestRepoRoot {
        $current = Split-Path -Parent $PSCommandPath

        while ($current) {
            $candidate = Join-Path $current "05_TOOLS"
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                return $current
            }

            $parent = Split-Path -Parent $current
            if ($parent -eq $current) {
                break
            }

            $current = $parent
        }

        throw "Could not locate repository root containing 05_TOOLS from $PSCommandPath"
    }

    function Get-PythonCommand {
        $candidatePaths = @()

        if (-not [string]::IsNullOrWhiteSpace($env:KOA_TEST_PYTHON)) {
            $candidatePaths += $env:KOA_TEST_PYTHON
        }

        if (-not [string]::IsNullOrWhiteSpace($env:PYTHON)) {
            $candidatePaths += $env:PYTHON
        }

        if (-not [string]::IsNullOrWhiteSpace($script:RepoRoot)) {
            $candidatePaths += @(
                (Join-Path $script:RepoRoot ".venv/Scripts/python.exe"),
                (Join-Path $script:RepoRoot ".venv/bin/python")
            )
        }

        foreach ($candidatePath in $candidatePaths) {
            if ([string]::IsNullOrWhiteSpace($candidatePath)) {
                continue
            }

            if (Test-Path -LiteralPath $candidatePath -PathType Leaf) {
                return [pscustomobject]@{
                    Exe  = [string] $candidatePath
                    Args = @()
                }
            }

            $resolved = Get-Command $candidatePath -ErrorAction SilentlyContinue
            if ($resolved) {
                return [pscustomobject]@{
                    Exe  = [string] $resolved.Source
                    Args = @()
                }
            }
        }

        foreach ($candidate in @("python", "python3")) {
            $resolved = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($resolved) {
                return [pscustomobject]@{
                    Exe  = [string] $resolved.Source
                    Args = @()
                }
            }
        }

        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) {
            return [pscustomobject]@{
                Exe  = [string] $py.Source
                Args = @("-3")
            }
        }

        throw "Python was not found. These tests need Python's built-in sqlite3 and zipfile modules."
    }

    function Invoke-PythonFixtureScript {
        param(
            [Parameter(Mandatory)]
            [string] $Code,

            [string[]] $Arguments = @()
        )

        $pythonCommand = Get-PythonCommand
        $tempScript = Join-Path $script:TempRoot ("fixture_script_" + [guid]::NewGuid().ToString("N") + ".py")

        New-Item -ItemType Directory -Path (Split-Path -Parent $tempScript) -Force | Out-Null
        Set-Content -LiteralPath $tempScript -Value $Code -Encoding UTF8

        try {
            $allArgs = @($pythonCommand.Args) + @($tempScript) + @($Arguments)
            $output = & $pythonCommand.Exe @allArgs 2>&1
            $exitCode = $LASTEXITCODE
            $raw = ($output | Out-String).Trim()

            if ($exitCode -ne 0) {
                throw "Python fixture script failed with exit code $exitCode.`n$raw"
            }

            return $raw
        }
        finally {
            if (Test-Path -LiteralPath $tempScript) {
                Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function ConvertFrom-KoaJsonStdout {
        param(
            [Parameter(Mandatory)]
            [string] $Raw
        )

        $text = $Raw.Trim()

        if ([string]::IsNullOrWhiteSpace($text)) {
            throw "Script produced no JSON on stdout."
        }

        try {
            return $text | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            $firstBrace = $text.IndexOf("{")
            $lastBrace = $text.LastIndexOf("}")

            if ($firstBrace -lt 0 -or $lastBrace -le $firstBrace) {
                throw
            }

            $candidate = $text.Substring($firstBrace, $lastBrace - $firstBrace + 1)
            return $candidate | ConvertFrom-Json -ErrorAction Stop
        }
    }

    function Invoke-JsonScript {
        param(
            [Parameter(Mandatory)]
            [string] $ScriptPath,

            [Parameter(Mandatory)]
            [hashtable] $Parameters
        )

        if (-not (Test-Path -LiteralPath $ScriptPath -PathType Leaf)) {
            throw "Script not found: $ScriptPath"
        }

        if ($Parameters.ContainsKey("OutputPath") -and -not [string]::IsNullOrWhiteSpace([string] $Parameters.OutputPath)) {
            New-Item -ItemType Directory -Path (Split-Path -Parent ([string] $Parameters.OutputPath)) -Force | Out-Null
        }

        $stderrPath = Join-Path $script:TempRoot ("stderr_" + [guid]::NewGuid().ToString("N") + ".txt")
        $previousProgressPreference = $ProgressPreference

        try {
            $global:ProgressPreference = "SilentlyContinue"

            $stdout = & $ScriptPath @Parameters 2>$stderrPath
            $exitCode = $LASTEXITCODE
            $raw = ($stdout | Out-String).Trim()

            $stderr = ""
            if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                $stderrContent = Get-Content -LiteralPath $stderrPath -Raw -ErrorAction SilentlyContinue
                if ($null -ne $stderrContent) {
                    $stderr = $stderrContent.Trim()
                }
            }

            try {
                $json = ConvertFrom-KoaJsonStdout -Raw $raw
            }
            catch {
                throw "Script stdout was not valid JSON. ExitCode=$exitCode`nRaw stdout:`n$raw`nStderr:`n$stderr"
            }

            return [pscustomobject]@{
                Raw      = $raw
                Json     = $json
                ExitCode = $exitCode
                Stderr   = $stderr
            }
        }
        finally {
            $global:ProgressPreference = $previousProgressPreference

            if (Test-Path -LiteralPath $stderrPath -PathType Leaf) {
                Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
            }
        }
    }

    function New-TestKoaSqliteDatabase {
        param(
            [Parameter(Mandatory)]
            [string] $DbPath
        )

        New-Item -ItemType Directory -Path (Split-Path -Parent $DbPath) -Force | Out-Null

        $code = @'
import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
db_path.parent.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(str(db_path))
cursor = connection.cursor()

try:
    cursor.executescript("""
CREATE TABLE schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE library_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_uuid TEXT NOT NULL,
    version_uuid TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    subtitle TEXT,
    description TEXT,
    summary TEXT,
    original_path TEXT NOT NULL,
    storage_path TEXT,
    filename TEXT NOT NULL,
    extension TEXT,
    mimetype TEXT,
    filesize INTEGER,
    sha256 TEXT,
    filearea TEXT DEFAULT 'media_original',
    media_type TEXT DEFAULT 'document',
    language TEXT DEFAULT 'fr',
    library_scope TEXT DEFAULT 'koa',
    uckk_relevance TEXT DEFAULT 'unknown',
    target_system TEXT DEFAULT 'none',
    target_export_allowed INTEGER DEFAULT 0,
    public_state TEXT DEFAULT 'unknown',
    visibility TEXT DEFAULT 'private',
    access_level TEXT DEFAULT 'private',
    ownership_scope TEXT DEFAULT 'unknown',
    source_type TEXT DEFAULT 'unknown',
    source_ownership TEXT DEFAULT 'unknown_source',
    rights_status TEXT DEFAULT 'unknown',
    rights_note TEXT,
    restriction_state TEXT DEFAULT 'none',
    restriction_reason TEXT,
    redaction_required INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    provenance TEXT DEFAULT 'ai_assisted',
    ai_validation_state TEXT DEFAULT 'ai_uncertain',
    ai_confidence REAL,
    canonical_validation_state TEXT DEFAULT 'unverified',
    human_review_required INTEGER DEFAULT 0,
    review_queue TEXT,
    review_reason TEXT,
    collections_json TEXT DEFAULT '[]',
    tags_json TEXT DEFAULT '[]',
    relations_json TEXT DEFAULT '[]',
    content_flags_json TEXT DEFAULT '[]',
    audience_suitability TEXT DEFAULT 'unknown',
    export_to_uckk TEXT DEFAULT 'no',
    export_to_public TEXT DEFAULT 'no',
    export_policy_note TEXT,
    import_batch TEXT,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE xlsx_import_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_uuid TEXT,
    xlsx_path TEXT,
    mode TEXT,
    row_number INTEGER,
    version_uuid TEXT,
    result TEXT,
    message TEXT,
    changed_fields TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    action TEXT,
    entity_type TEXT,
    entity_uuid TEXT,
    before_json TEXT,
    after_json TEXT,
    note TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

    cursor.execute(
        """
        INSERT INTO schema_meta (key, value)
        VALUES
            ('app_public_name', 'Médiathèque kOA'),
            ('app_component', 'koa_mediatheque'),
            ('schema_version', '001_initial_schema')
        """
    )

    rows = [
        {
            "media_uuid": "11111111-1111-4111-8111-111111111111",
            "version_uuid": "22222222-2222-4222-8222-222222222222",
            "title": "Document public exportable",
            "subtitle": "Fixture",
            "description": "Description test",
            "summary": "Résumé test",
            "original_path": "C:/fixture/public.pdf",
            "storage_path": "02_STORAGE/media_original/22222222-2222-4222-8222-222222222222_public.pdf",
            "filename": "public.pdf",
            "extension": ".pdf",
            "mimetype": "application/pdf",
            "filesize": 12345,
            "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "filearea": "media_original",
            "media_type": "pdf",
            "language": "fr",
            "library_scope": "koa",
            "uckk_relevance": "uckk_reference",
            "target_system": "uckkarchive",
            "target_export_allowed": 1,
            "public_state": "public",
            "visibility": "public",
            "access_level": "public",
            "ownership_scope": "koa_owned",
            "source_type": "produced_by_uckk",
            "source_ownership": "uckk_created",
            "rights_status": "owned",
            "rights_note": "Owned fixture rights",
            "restriction_state": "none",
            "restriction_reason": "",
            "redaction_required": 0,
            "status": "active",
            "provenance": "ai_assisted",
            "ai_validation_state": "ai_validated",
            "ai_confidence": 0.91,
            "canonical_validation_state": "human_reviewed",
            "human_review_required": 0,
            "review_queue": "",
            "review_reason": "",
            "collections_json": '["test_collection"]',
            "tags_json": '["alpha","beta"]',
            "relations_json": '["references:33333333-3333-4333-8333-333333333333"]',
            "content_flags_json": '[]',
            "audience_suitability": "general",
            "export_to_uckk": "yes",
            "export_to_public": "yes",
            "export_policy_note": "Fixture export allowed",
            "import_batch": "test_batch",
            "notes": "Fixture note"
        },
        {
            "media_uuid": "44444444-4444-4444-8444-444444444444",
            "version_uuid": "55555555-5555-4555-8555-555555555555",
            "title": "Document privé non exportable",
            "subtitle": "",
            "description": "Private fixture",
            "summary": "Private summary",
            "original_path": "C:/fixture/private.txt",
            "storage_path": "",
            "filename": "private.txt",
            "extension": ".txt",
            "mimetype": "text/plain",
            "filesize": 789,
            "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "filearea": "media_original",
            "media_type": "document",
            "language": "fr",
            "library_scope": "koa",
            "uckk_relevance": "not_uckk",
            "target_system": "none",
            "target_export_allowed": 0,
            "public_state": "private",
            "visibility": "private",
            "access_level": "private",
            "ownership_scope": "personal",
            "source_type": "unknown",
            "source_ownership": "unknown_source",
            "rights_status": "unknown",
            "rights_note": "",
            "restriction_state": "privacy",
            "restriction_reason": "Private fixture",
            "redaction_required": 1,
            "status": "active",
            "provenance": "imported",
            "ai_validation_state": "ai_uncertain",
            "ai_confidence": 0.2,
            "canonical_validation_state": "unverified",
            "human_review_required": 1,
            "review_queue": "human_review",
            "review_reason": "Unknown rights",
            "collections_json": '[]',
            "tags_json": '["private"]',
            "relations_json": '[]',
            "content_flags_json": '["privacy_sensitive","non_public"]',
            "audience_suitability": "staff_only",
            "export_to_uckk": "no",
            "export_to_public": "no",
            "export_policy_note": "Fixture export blocked",
            "import_batch": "test_batch",
            "notes": "Private fixture note"
        }
    ]

    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    sql = f"INSERT INTO library_rows ({', '.join(columns)}) VALUES ({placeholders})"

    for row in rows:
        cursor.execute(sql, [row[column] for column in columns])

    connection.commit()
finally:
    cursor.close()
    connection.close()
'@

        Invoke-PythonFixtureScript -Code $code -Arguments @($DbPath) | Out-Null
    }

    function Read-XlsxWorkbookFacts {
        param(
            [Parameter(Mandatory)]
            [string] $XlsxPath
        )

        if (-not (Test-Path -LiteralPath $XlsxPath -PathType Leaf)) {
            throw "XLSX file not found for inspection: $XlsxPath"
        }

        $code = @'
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

xlsx_path = sys.argv[1]

NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PACKAGE_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

def col_index(cell_ref):
    match = re.match(r"([A-Z]+)", cell_ref or "")
    if not match:
        return None

    letters = match.group(1)
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1

def load_shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []

    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    result = []
    for si in root.findall(f"{NS_MAIN}si"):
        texts = []
        for text_node in si.iter(f"{NS_MAIN}t"):
            texts.append(text_node.text or "")
        result.append("".join(texts))
    return result

def get_cell_text(cell, shared_strings):
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        inline = cell.find(f"{NS_MAIN}is")
        if inline is None:
            return ""
        return "".join(text_node.text or "" for text_node in inline.iter(f"{NS_MAIN}t"))

    value = cell.find(f"{NS_MAIN}v")
    raw = value.text if value is not None else ""

    if cell_type == "s":
        try:
            return shared_strings[int(raw)]
        except Exception:
            return raw

    if cell_type == "b":
        return "1" if raw == "1" else "0"

    return raw or ""

def parse_sheet_rows(zf, sheet_path, shared_strings):
    xml_path = sheet_path.lstrip("/")
    if not xml_path.startswith("xl/"):
        xml_path = "xl/" + xml_path

    root = ET.fromstring(zf.read(xml_path))
    rows = []

    for row_node in root.findall(f".//{NS_MAIN}sheetData/{NS_MAIN}row"):
        cells_by_index = {}
        max_index = -1

        for cell in row_node.findall(f"{NS_MAIN}c"):
            ref = cell.attrib.get("r", "")
            index = col_index(ref)
            if index is None:
                index = max_index + 1
            cells_by_index[index] = get_cell_text(cell, shared_strings)
            max_index = max(max_index, index)

        if max_index >= 0:
            rows.append([cells_by_index.get(index, "") for index in range(max_index + 1)])

    return rows

with zipfile.ZipFile(xlsx_path, "r") as zf:
    shared_strings = load_shared_strings(zf)

    workbook_root = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))

    rel_targets = {}
    for rel in rels_root.findall(f"{NS_PACKAGE_REL}Relationship"):
        rel_targets[rel.attrib["Id"]] = rel.attrib["Target"]

    sheets = {}
    for sheet in workbook_root.findall(f".//{NS_MAIN}sheets/{NS_MAIN}sheet"):
        sheet_name = sheet.attrib["name"]
        rel_id = sheet.attrib[f"{NS_REL}id"]
        sheet_path = rel_targets[rel_id]
        sheets[sheet_name] = parse_sheet_rows(zf, sheet_path, shared_strings)

    result = {
        "sheet_names": list(sheets.keys()),
        "sheets": sheets,
    }

print(json.dumps(result, ensure_ascii=False))
'@

        $raw = Invoke-PythonFixtureScript -Code $code -Arguments @($XlsxPath)

        try {
            return $raw | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            throw "Workbook inspection did not return valid JSON.`n$raw"
        }
    }

    function Convert-SheetToObjects {
        param(
            [Parameter(Mandatory)]
            [object[]] $Rows
        )

        if (-not $Rows -or $Rows.Count -lt 1) {
            return @()
        }

        $headers = @($Rows[0])
        $objects = @()

        for ($i = 1; $i -lt $Rows.Count; $i++) {
            $row = @($Rows[$i])
            $object = [ordered]@{}

            for ($j = 0; $j -lt $headers.Count; $j++) {
                $header = [string] $headers[$j]
                if (-not $header) {
                    continue
                }

                $value = ""
                if ($j -lt $row.Count) {
                    $value = [string] $row[$j]
                }

                $object[$header] = $value
            }

            if ($object.Count -gt 0) {
                $objects += [pscustomobject] $object
            }
        }

        return $objects
    }

    $script:RepoRoot = Get-TestRepoRoot
    $script:ScriptPath = Join-Path $script:RepoRoot "05_TOOLS/Export-KoaLibraryXlsx.ps1"

    $script:TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("koa_xlsx_export_tests_" + [guid]::NewGuid().ToString("N"))
    $script:DbPath = Join-Path $script:TempRoot "01_DB/koa_mediatheque.sqlite"
    $script:OutputPath = Join-Path $script:TempRoot "04_EXPORTS/xlsx/library_export.xlsx"

    New-Item -ItemType Directory -Path (Split-Path -Parent $script:DbPath) -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path -Parent $script:OutputPath) -Force | Out-Null

    New-TestKoaSqliteDatabase -DbPath $script:DbPath
}

AfterAll {
    if ($script:TempRoot -and (Test-Path -LiteralPath $script:TempRoot)) {
        Remove-Item -LiteralPath $script:TempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Describe "Export-KoaLibraryXlsx.ps1" {
    It "exists in 05_TOOLS" {
        Test-Path -LiteralPath $script:ScriptPath -PathType Leaf | Should -BeTrue
    }

    It "exports an XLSX workbook and returns OperationResult JSON" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $result.Json.success | Should -BeTrue
        $result.Json.operation | Should -Be "Export-KoaLibraryXlsx"
        $result.Json.result | Should -BeIn @("exported", "success")
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -Be 0

        $result.Json.path | Should -Not -BeNullOrEmpty
        Test-Path -LiteralPath $result.Json.path -PathType Leaf | Should -BeTrue
        [System.IO.Path]::GetExtension([string] $result.Json.path) | Should -Be ".xlsx"
    }

    It "creates Library, Lists, and Import_Report sheets" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path

        @($workbook.sheet_names) | Should -Contain "Library"
        @($workbook.sheet_names) | Should -Contain "Lists"
        @($workbook.sheet_names) | Should -Contain "Import_Report"
    }

    It "writes canonical Library columns" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $libraryRows = @($workbook.sheets.Library)
        $headers = @($libraryRows[0])

        $headers | Should -Contain "action"
        $headers | Should -Contain "media_uuid"
        $headers | Should -Contain "version_uuid"
        $headers | Should -Contain "title"
        $headers | Should -Contain "description"
        $headers | Should -Contain "filename"
        $headers | Should -Contain "original_path"
        $headers | Should -Contain "storage_path"
        $headers | Should -Contain "media_type"
        $headers | Should -Contain "language"
        $headers | Should -Contain "uckk_relevance"
        $headers | Should -Contain "target_system"
        $headers | Should -Contain "target_export_allowed"
        $headers | Should -Contain "public_state"
        $headers | Should -Contain "visibility"
        $headers | Should -Contain "access_level"
        $headers | Should -Contain "source_type"
        $headers | Should -Contain "source_ownership"
        $headers | Should -Contain "rights_status"
        $headers | Should -Contain "restriction_state"
        $headers | Should -Contain "canonical_validation_state"
        $headers | Should -Contain "collections"
        $headers | Should -Contain "tags"
        $headers | Should -Contain "relations"
        $headers | Should -Contain "content_flags"
        $headers | Should -Contain "audience_suitability"
        $headers | Should -Contain "export_to_uckk"
        $headers | Should -Contain "export_to_public"
        $headers | Should -Contain "sha256"
        $headers | Should -Contain "filesize"
        $headers | Should -Contain "mimetype"
        $headers | Should -Contain "updated_at"
    }

    It "exports library rows with expected scalar values" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $objects = Convert-SheetToObjects -Rows @($workbook.sheets.Library)

        $row = @($objects) |
            Where-Object { $_.version_uuid -eq "22222222-2222-4222-8222-222222222222" } |
            Select-Object -First 1

        $row | Should -Not -BeNullOrEmpty
        $row.action | Should -BeIn @("", "update", "ignore")
        $row.media_uuid | Should -Be "11111111-1111-4111-8111-111111111111"
        $row.title | Should -Be "Document public exportable"
        $row.filename | Should -Be "public.pdf"
        $row.media_type | Should -Be "pdf"
        $row.language | Should -Be "fr"
        $row.uckk_relevance | Should -Be "uckk_reference"
        $row.target_system | Should -Be "uckkarchive"
        $row.target_export_allowed | Should -Be "1"
        $row.public_state | Should -Be "public"
        $row.visibility | Should -Be "public"
        $row.access_level | Should -Be "public"
        $row.rights_status | Should -Be "owned"
        $row.restriction_state | Should -Be "none"
        $row.canonical_validation_state | Should -Be "human_reviewed"
        $row.export_to_uckk | Should -Be "yes"
        $row.export_to_public | Should -Be "yes"
        $row.sha256 | Should -Be "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        $row.filesize | Should -Be "12345"
        $row.mimetype | Should -Be "application/pdf"
    }

    It "exports SQLite JSON arrays as semicolon-separated XLSX text" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $objects = Convert-SheetToObjects -Rows @($workbook.sheets.Library)

        $publicRow = @($objects) |
            Where-Object { $_.version_uuid -eq "22222222-2222-4222-8222-222222222222" } |
            Select-Object -First 1

        $privateRow = @($objects) |
            Where-Object { $_.version_uuid -eq "55555555-5555-4555-8555-555555555555" } |
            Select-Object -First 1

        $publicRow.collections | Should -Be "test_collection"
        $publicRow.tags | Should -Match "alpha"
        $publicRow.tags | Should -Match "beta"
        $publicRow.relations | Should -Match "references:33333333-3333-4333-8333-333333333333"
        $publicRow.content_flags | Should -Be ""

        $privateRow.tags | Should -Be "private"
        $privateRow.content_flags | Should -Match "privacy_sensitive"
        $privateRow.content_flags | Should -Match "non_public"
    }

    It "writes Lists sheet with controlled values" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $listsRows = @($workbook.sheets.Lists)
        $headers = @($listsRows[0])
        $objects = Convert-SheetToObjects -Rows $listsRows

        $headers | Should -Contain "field"
        $headers | Should -Contain "allowed_value"

        $fields = @($objects | ForEach-Object { $_.field })
        $values = @($objects | ForEach-Object { $_.allowed_value })

        $fields | Should -Contain "visibility"
        $fields | Should -Contain "rights_status"
        $fields | Should -Contain "export_to_public"
        $fields | Should -Contain "xlsx_action"

        $values | Should -Contain "public"
        $values | Should -Contain "private"
        $values | Should -Contain "unknown"
        $values | Should -Contain "yes"
        $values | Should -Contain "no"
        $values | Should -Contain "update"
    }

    It "writes Import_Report sheet with canonical columns" {
        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $script:OutputPath
                FilterJson = "{}"
            }

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $reportRows = @($workbook.sheets.Import_Report)
        $headers = @($reportRows[0])

        $headers | Should -Contain "row_number"
        $headers | Should -Contain "version_uuid"
        $headers | Should -Contain "action"
        $headers | Should -Contain "result"
        $headers | Should -Contain "message"
        $headers | Should -Contain "changed_fields"
    }

    It "supports FilterJson without failing" {
        $filteredOutputPath = Join-Path $script:TempRoot "04_EXPORTS/xlsx/library_export_filtered.xlsx"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $filteredOutputPath
                FilterJson = '{"visibility":"public"}'
            }

        $result.Json.success | Should -BeTrue
        Test-Path -LiteralPath $result.Json.path -PathType Leaf | Should -BeTrue

        $workbook = Read-XlsxWorkbookFacts -XlsxPath $result.Json.path
        $objects = Convert-SheetToObjects -Rows @($workbook.sheets.Library)

        @($objects).Count | Should -BeGreaterOrEqual 1
        @($objects | Where-Object { $_.visibility -eq "public" }).Count | Should -BeGreaterOrEqual 1
    }

    It "fails with valid JSON when database path does not exist" {
        $missingDbPath = Join-Path $script:TempRoot "missing.sqlite"
        $missingOutputPath = Join-Path $script:TempRoot "04_EXPORTS/xlsx/missing_db_export.xlsx"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $missingDbPath
                OutputPath = $missingOutputPath
                FilterJson = "{}"
            }

        $result.Json.success | Should -BeFalse
        $result.Json.operation | Should -Be "Export-KoaLibraryXlsx"
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -BeGreaterThan 0
    }

    It "fails with valid JSON when FilterJson is invalid" {
        $invalidFilterOutputPath = Join-Path $script:TempRoot "04_EXPORTS/xlsx/invalid_filter_export.xlsx"

        $result = Invoke-JsonScript `
            -ScriptPath $script:ScriptPath `
            -Parameters @{
                DbPath     = $script:DbPath
                OutputPath = $invalidFilterOutputPath
                FilterJson = "{invalid json"
            }

        $result.Json.success | Should -BeFalse
        $result.Json.operation | Should -Be "Export-KoaLibraryXlsx"
        $result.Json.PSObject.Properties.Name | Should -Contain "errors"
        @($result.Json.errors).Count | Should -BeGreaterThan 0
    }
}