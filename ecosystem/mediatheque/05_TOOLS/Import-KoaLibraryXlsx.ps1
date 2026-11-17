# 05_TOOLS/Import-KoaLibraryXlsx.ps1
# Médiathèque kOA — Import XLSX Library sheet into SQLite
# PowerShell 7 only. Emits one JSON result to stdout.
# Reads .xlsx directly without requiring Excel or ImportExcel.

#requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $DbPath,

    [Parameter(Mandatory)]
    [string] $XlsxPath,

    [Parameter(Mandatory)]
    [string] $BackupDir,

    [ValidateSet("normal", "repair", "dry_run")]
    [string] $Mode = "normal"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Operation = "Import-KoaLibraryXlsx"

$CommonModulePath = Join-Path $PSScriptRoot "KoaMediatheque.Common.psm1"

if (-not (Test-Path -LiteralPath $CommonModulePath -PathType Leaf)) {
    $fallback = [ordered]@{
        success      = $false
        operation    = $Operation
        result       = "failed"
        entity_type  = "xlsx_import"
        entity_uuid  = ""
        version_uuid = ""
        media_uuid   = ""
        path         = $XlsxPath
        data         = @{}
        warnings     = @()
        errors       = @(
            [ordered]@{
                code       = "ERR_COMMON_MODULE_NOT_FOUND"
                severity   = "blocking"
                message    = "Common module not found: $CommonModulePath"
                field      = $null
                row_number = $null
                details    = @{}
            }
        )
    }

    [Console]::Out.WriteLine(($fallback | ConvertTo-Json -Depth 20))
    exit 1
}

Import-Module $CommonModulePath -Force

function ConvertTo-LocalHashtable {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [object] $Value
    )

    if ($null -eq $Value) {
        return @{}
    }

    if ($Value -is [hashtable]) {
        return $Value
    }

    if ($Value -is [System.Collections.Specialized.OrderedDictionary]) {
        $hash = @{}
        foreach ($key in $Value.Keys) {
            $hash[$key] = $Value[$key]
        }
        return $hash
    }

    $result = @{}
    foreach ($property in $Value.PSObject.Properties) {
        $result[$property.Name] = $property.Value
    }

    return $result
}

function Get-XlsxColumnIndexFromCellReference {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $CellReference
    )

    $letters = ([regex]::Match($CellReference, "^[A-Z]+")).Value
    $number = 0

    foreach ($char in $letters.ToCharArray()) {
        $number = ($number * 26) + ([int][char]$char - [int][char]'A' + 1)
    }

    return $number
}

function Get-XlsxSharedStrings {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.IO.Compression.ZipArchive] $Zip
    )

    $entry = $Zip.GetEntry("xl/sharedStrings.xml")
    if ($null -eq $entry) {
        return @()
    }

    $stream = $entry.Open()
    try {
        $reader = [System.IO.StreamReader]::new($stream)
        $xmlText = $reader.ReadToEnd()
    }
    finally {
        if ($null -ne $reader) {
            $reader.Dispose()
        }
        $stream.Dispose()
    }

    [xml] $xml = $xmlText
    $namespaceManager = [System.Xml.XmlNamespaceManager]::new($xml.NameTable)
    $namespaceManager.AddNamespace("x", "http://schemas.openxmlformats.org/spreadsheetml/2006/main")

    $values = @()
    $items = $xml.SelectNodes("//x:si", $namespaceManager)

    foreach ($item in $items) {
        $textNodes = $item.SelectNodes(".//x:t", $namespaceManager)
        $text = ($textNodes | ForEach-Object { $_."#text" }) -join ""
        $values += $text
    }

    return @($values)
}

function Get-XlsxWorkbookSheetMap {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.IO.Compression.ZipArchive] $Zip
    )

    $workbookEntry = $Zip.GetEntry("xl/workbook.xml")
    $relsEntry = $Zip.GetEntry("xl/_rels/workbook.xml.rels")

    if ($null -eq $workbookEntry -or $null -eq $relsEntry) {
        throw "Invalid XLSX: workbook metadata is missing."
    }

    $workbookStream = $workbookEntry.Open()
    $relsStream = $relsEntry.Open()

    try {
        $workbookReader = [System.IO.StreamReader]::new($workbookStream)
        $relsReader = [System.IO.StreamReader]::new($relsStream)
        [xml] $workbookXml = $workbookReader.ReadToEnd()
        [xml] $relsXml = $relsReader.ReadToEnd()
    }
    finally {
        if ($null -ne $workbookReader) {
            $workbookReader.Dispose()
        }

        if ($null -ne $relsReader) {
            $relsReader.Dispose()
        }

        $workbookStream.Dispose()
        $relsStream.Dispose()
    }

    $workbookNs = [System.Xml.XmlNamespaceManager]::new($workbookXml.NameTable)
    $workbookNs.AddNamespace("x", "http://schemas.openxmlformats.org/spreadsheetml/2006/main")
    $workbookNs.AddNamespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

    $relsNs = [System.Xml.XmlNamespaceManager]::new($relsXml.NameTable)
    $relsNs.AddNamespace("rel", "http://schemas.openxmlformats.org/package/2006/relationships")

    $relationTargets = @{}
    foreach ($relationship in $relsXml.SelectNodes("//rel:Relationship", $relsNs)) {
        $id = $relationship.Id
        $target = $relationship.Target

        if ($target -notlike "xl/*") {
            $target = "xl/$target"
        }

        $relationTargets[$id] = $target
    }

    $sheetMap = @{}
    foreach ($sheet in $workbookXml.SelectNodes("//x:sheets/x:sheet", $workbookNs)) {
        $sheetName = $sheet.name
        $relationId = $sheet.GetAttribute("id", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

        if ($relationTargets.ContainsKey($relationId)) {
            $sheetMap[$sheetName] = $relationTargets[$relationId]
        }
    }

    return $sheetMap
}

function Get-XlsxCellText {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.Xml.XmlElement] $Cell,

        [Parameter(Mandatory)]
        [object[]] $SharedStrings
    )

    $cellType = $Cell.GetAttribute("t")

    if ($cellType -eq "inlineStr") {
        $inlineTextNodes = $Cell.GetElementsByTagName("t")
        return (($inlineTextNodes | ForEach-Object { $_."#text" }) -join "")
    }

    $valueNode = $Cell.GetElementsByTagName("v") | Select-Object -First 1

    if ($null -eq $valueNode) {
        return ""
    }

    $rawValue = [string] $valueNode.InnerText

    if ($cellType -eq "s") {
        if ([string]::IsNullOrWhiteSpace($rawValue)) {
            return ""
        }

        $index = [int] $rawValue
        if ($index -ge 0 -and $index -lt $SharedStrings.Count) {
            return [string] $SharedStrings[$index]
        }

        return ""
    }

    if ($cellType -eq "str") {
        return $rawValue
    }

    return $rawValue
}

function Read-XlsxSheetRows {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $XlsxPath,

        [Parameter(Mandatory)]
        [string] $SheetName
    )

    Add-Type -AssemblyName System.IO.Compression | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null

    $zip = [System.IO.Compression.ZipFile]::OpenRead($XlsxPath)

    try {
        $sheetMap = Get-XlsxWorkbookSheetMap -Zip $zip

        if (-not $sheetMap.ContainsKey($SheetName)) {
            throw "XLSX sheet not found: $SheetName"
        }

        $sharedStrings = Get-XlsxSharedStrings -Zip $zip
        $sheetEntry = $zip.GetEntry($sheetMap[$SheetName])

        if ($null -eq $sheetEntry) {
            throw "XLSX sheet entry not found: $($sheetMap[$SheetName])"
        }

        $sheetStream = $sheetEntry.Open()

        try {
            $reader = [System.IO.StreamReader]::new($sheetStream)
            [xml] $sheetXml = $reader.ReadToEnd()
        }
        finally {
            if ($null -ne $reader) {
                $reader.Dispose()
            }

            $sheetStream.Dispose()
        }

        $namespaceManager = [System.Xml.XmlNamespaceManager]::new($sheetXml.NameTable)
        $namespaceManager.AddNamespace("x", "http://schemas.openxmlformats.org/spreadsheetml/2006/main")

        $rowNodes = $sheetXml.SelectNodes("//x:sheetData/x:row", $namespaceManager)

        if ($rowNodes.Count -eq 0) {
            return @()
        }

        $rowsByNumber = @{}

        foreach ($rowNode in $rowNodes) {
            $rowNumber = [int] $rowNode.GetAttribute("r")
            $cells = @{}

            foreach ($cell in $rowNode.SelectNodes("x:c", $namespaceManager)) {
                $cellReference = $cell.GetAttribute("r")
                $columnIndex = Get-XlsxColumnIndexFromCellReference -CellReference $cellReference
                $cells[$columnIndex] = Get-XlsxCellText -Cell $cell -SharedStrings $sharedStrings
            }

            $rowsByNumber[$rowNumber] = $cells
        }

        if (-not $rowsByNumber.ContainsKey(1)) {
            return @()
        }

        $headersByColumn = @{}
        foreach ($columnIndex in $rowsByNumber[1].Keys) {
            $header = ([string] $rowsByNumber[1][$columnIndex]).Trim()
            if (-not [string]::IsNullOrWhiteSpace($header)) {
                $headersByColumn[$columnIndex] = $header
            }
        }

        $resultRows = @()

        foreach ($rowNumber in ($rowsByNumber.Keys | Sort-Object)) {
            if ($rowNumber -eq 1) {
                continue
            }

            $data = [ordered]@{
                __row_number = $rowNumber
            }

            $hasAnyValue = $false

            foreach ($columnIndex in ($headersByColumn.Keys | Sort-Object)) {
                $header = $headersByColumn[$columnIndex]
                $value = ""

                if ($rowsByNumber[$rowNumber].ContainsKey($columnIndex)) {
                    $value = [string] $rowsByNumber[$rowNumber][$columnIndex]
                }

                if (-not [string]::IsNullOrWhiteSpace($value)) {
                    $hasAnyValue = $true
                }

                $data[$header] = $value
            }

            if ($hasAnyValue) {
                $resultRows += [pscustomobject] $data
            }
        }

        return @($resultRows)
    }
    finally {
        $zip.Dispose()
    }
}

function ConvertFrom-XlsxSemicolonToJsonArrayText {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string] $Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "[]"
    }

    $trimmed = $Value.Trim()

    if ($trimmed.StartsWith("[") -and $trimmed.EndsWith("]")) {
        try {
            $null = $trimmed | ConvertFrom-Json -Depth 50
            return $trimmed
        }
        catch {
            # Fall back to semicolon parsing.
        }
    }

    $items = @(
        $trimmed.Split(";") |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )

    return ($items | ConvertTo-Json -Depth 20 -Compress)
}

function Convert-XlsxValueForColumn {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ColumnName,

        [AllowNull()]
        [string] $Value
    )

    if ($null -eq $Value) {
        return $null
    }

    $trimmed = ([string] $Value).Trim()

    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        return $null
    }

    switch ($ColumnName) {
        { $_ -in @("target_export_allowed", "filesize", "redaction_required", "human_review_required") } {
            return [int64] $trimmed
        }

        "ai_confidence" {
            return [double]::Parse($trimmed, [System.Globalization.CultureInfo]::InvariantCulture)
        }

        { $_ -in @("collections_json", "tags_json", "relations_json", "content_flags_json") } {
            return ConvertFrom-XlsxSemicolonToJsonArrayText -Value $trimmed
        }

        default {
            return $trimmed
        }
    }
}

function Get-KoaLibraryRowByVersionUuid {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $VersionUuid
    )

    if ([string]::IsNullOrWhiteSpace($VersionUuid)) {
        return $null
    }

    $rows = Invoke-KoaSqliteQuery `
        -Connection $Connection `
        -Sql "SELECT * FROM library_rows WHERE version_uuid = @version_uuid LIMIT 1;" `
        -Parameters @{ version_uuid = $VersionUuid } `
        -ReadOnly

    if ($rows.Count -eq 0) {
        return $null
    }

    return $rows[0]
}

function Get-KoaAllowedImportColumns {
    [CmdletBinding()]
    param()

    return @(
        "media_uuid",
        "version_uuid",
        "title",
        "subtitle",
        "description",
        "summary",
        "original_path",
        "storage_path",
        "filename",
        "extension",
        "mimetype",
        "filesize",
        "sha256",
        "filearea",
        "media_type",
        "language",
        "library_scope",
        "uckk_relevance",
        "target_system",
        "target_export_allowed",
        "public_state",
        "visibility",
        "access_level",
        "ownership_scope",
        "source_type",
        "source_ownership",
        "rights_status",
        "rights_note",
        "restriction_state",
        "restriction_reason",
        "redaction_required",
        "status",
        "provenance",
        "ai_validation_state",
        "ai_confidence",
        "canonical_validation_state",
        "human_review_required",
        "review_queue",
        "review_reason",
        "collections_json",
        "tags_json",
        "relations_json",
        "content_flags_json",
        "audience_suitability",
        "export_to_uckk",
        "export_to_public",
        "export_policy_note",
        "import_batch",
        "notes"
    )
}

function Get-KoaProtectedXlsxColumns {
    [CmdletBinding()]
    param()

    return @(
        "media_uuid",
        "version_uuid",
        "filename",
        "original_path",
        "storage_path",
        "sha256",
        "filesize",
        "mimetype",
        "updated_at"
    )
}

function Test-KoaXlsxAction {
    [CmdletBinding()]
    param(
        [AllowNull()]
        [string] $Action
    )

    if ([string]::IsNullOrWhiteSpace($Action)) {
        return "update"
    }

    $normalized = $Action.Trim().ToLowerInvariant()

    if ($normalized -in @("update", "ignore", "archive", "new")) {
        return $normalized
    }

    throw "Invalid xlsx_action: $Action"
}

function Test-KoaImportedFieldValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string] $ColumnName,

        [AllowNull()]
        [object] $Value,

        [Parameter(Mandatory)]
        [int] $RowNumber
    )

    $messages = @()

    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string] $Value)) {
        return @()
    }

    $enumValues = Get-KoaEnumValuesForField -FieldName $ColumnName
    if ($enumValues.Count -gt 0 -and $enumValues -notcontains ([string] $Value)) {
        $messages += New-KoaMessage `
            -Code "ERR_INVALID_ENUM" `
            -Severity "blocking" `
            -Message "Invalid value '$Value' for field '$ColumnName'." `
            -Field $ColumnName `
            -RowNumber $RowNumber `
            -Details @{ allowed_values = $enumValues }
    }

    return @($messages)
}

function Build-KoaImportUpdate {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $ExistingRow,

        [Parameter(Mandatory)]
        [hashtable] $XlsxRow,

        [Parameter(Mandatory)]
        [string] $Mode,

        [Parameter(Mandatory)]
        [int] $RowNumber
    )

    $warnings = @()
    $errors = @()
    $updates = @{}
    $protectedChanges = @()
    $allowedColumns = Get-KoaAllowedImportColumns
    $protectedColumns = Get-KoaProtectedXlsxColumns

    $existingHash = ConvertTo-LocalHashtable -Value $ExistingRow

    foreach ($column in $allowedColumns) {
        if (-not $XlsxRow.ContainsKey($column)) {
            continue
        }

        $rawValue = [string] $XlsxRow[$column]
        $newValue = Convert-XlsxValueForColumn -ColumnName $column -Value $rawValue

        if ($null -eq $newValue) {
            continue
        }

        $fieldErrors = Test-KoaImportedFieldValue `
            -ColumnName $column `
            -Value $newValue `
            -RowNumber $RowNumber

        $errors += @($fieldErrors)

        if ($column -eq "canonical_validation_state" -and $newValue -eq "verified" -and $Mode -ne "repair") {
            $errors += New-KoaMessage `
                -Code "ERR_BLOCKED_VERIFIED" `
                -Severity "blocking" `
                -Message "XLSX import cannot set canonical_validation_state to verified outside repair mode." `
                -Field $column `
                -RowNumber $RowNumber
        }

        $oldValue = $null
        if ($existingHash.ContainsKey($column)) {
            $oldValue = $existingHash[$column]
        }

        if ([string] $oldValue -eq [string] $newValue) {
            continue
        }

        if ($protectedColumns -contains $column -and $Mode -ne "repair") {
            $protectedChanges += [ordered]@{
                field = $column
                old   = $oldValue
                new   = $newValue
            }

            $warnings += New-KoaMessage `
                -Code "ERR_PROTECTED_FIELD_UPDATE" `
                -Severity "warning" `
                -Message "Protected field change ignored outside repair mode: $column" `
                -Field $column `
                -RowNumber $RowNumber `
                -Details @{
                    old = $oldValue
                    new = $newValue
                }

            continue
        }

        $updates[$column] = $newValue
    }

    if ($updates.Count -gt 0) {
        $updates["updated_at"] = Get-KoaTimestamp
    }

    return [ordered]@{
        updates           = $updates
        protected_changes = $protectedChanges
        warnings          = @($warnings)
        errors            = @($errors)
    }
}

function Build-KoaNewRowFromXlsx {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [hashtable] $XlsxRow,

        [Parameter(Mandatory)]
        [int] $RowNumber,

        [Parameter(Mandatory)]
        [string] $Mode,

        [Parameter(Mandatory)]
        [string] $ImportUuid
    )

    $warnings = @()
    $errors = @()
    $rowData = @{}

    $allowedColumns = Get-KoaAllowedImportColumns

    foreach ($column in $allowedColumns) {
        if (-not $XlsxRow.ContainsKey($column)) {
            continue
        }

        $value = Convert-XlsxValueForColumn -ColumnName $column -Value ([string] $XlsxRow[$column])
        if ($null -ne $value) {
            $rowData[$column] = $value
        }
    }

    if (-not $rowData.ContainsKey("title") -or [string]::IsNullOrWhiteSpace([string] $rowData["title"])) {
        $errors += New-KoaMessage `
            -Code "ERR_REQUIRED_FIELD" `
            -Severity "blocking" `
            -Message "New XLSX rows require title." `
            -Field "title" `
            -RowNumber $RowNumber
    }

    if (-not $rowData.ContainsKey("version_uuid") -or [string]::IsNullOrWhiteSpace([string] $rowData["version_uuid"])) {
        $rowData["version_uuid"] = New-KoaUuid
    }

    if (-not $rowData.ContainsKey("media_uuid") -or [string]::IsNullOrWhiteSpace([string] $rowData["media_uuid"])) {
        $rowData["media_uuid"] = New-KoaUuid
    }

    if (-not $rowData.ContainsKey("original_path") -or [string]::IsNullOrWhiteSpace([string] $rowData["original_path"])) {
        $errors += New-KoaMessage `
            -Code "ERR_REQUIRED_FIELD" `
            -Severity "blocking" `
            -Message "New XLSX rows require original_path so technical facts can be recalculated locally." `
            -Field "original_path" `
            -RowNumber $RowNumber
    }
    elseif (-not (Test-Path -LiteralPath ([string] $rowData["original_path"]) -PathType Leaf)) {
        $errors += New-KoaMessage `
            -Code "ERR_FILE_NOT_FOUND" `
            -Severity "blocking" `
            -Message "original_path file not found for new XLSX row." `
            -Field "original_path" `
            -RowNumber $RowNumber `
            -Details @{ original_path = $rowData["original_path"] }
    }
    else {
        $facts = ConvertTo-LocalHashtable -Value (Get-KoaFileFacts -FilePath ([string] $rowData["original_path"]))
        $rowData["original_path"] = $facts["original_path"]
        $rowData["filename"] = $facts["filename"]
        $rowData["extension"] = $facts["extension"]
        $rowData["mimetype"] = $facts["mimetype"]
        $rowData["filesize"] = $facts["filesize"]
        $rowData["sha256"] = $facts["sha256"]
    }

    $defaults = Get-KoaLibraryRowColumnDefaults
    foreach ($key in $defaults.Keys) {
        if (-not $rowData.ContainsKey($key)) {
            $rowData[$key] = $defaults[$key]
        }
    }

    if (-not $rowData.ContainsKey("collections_json")) {
        $rowData["collections_json"] = "[]"
    }

    if (-not $rowData.ContainsKey("tags_json")) {
        $rowData["tags_json"] = "[]"
    }

    if (-not $rowData.ContainsKey("relations_json")) {
        $rowData["relations_json"] = "[]"
    }

    if (-not $rowData.ContainsKey("content_flags_json")) {
        $rowData["content_flags_json"] = "[]"
    }

    $rowData["import_batch"] = $ImportUuid

    foreach ($column in $rowData.Keys) {
        $fieldErrors = Test-KoaImportedFieldValue `
            -ColumnName $column `
            -Value $rowData[$column] `
            -RowNumber $RowNumber

        $errors += @($fieldErrors)
    }

    if ($rowData["canonical_validation_state"] -eq "verified" -and $Mode -ne "repair") {
        $errors += New-KoaMessage `
            -Code "ERR_BLOCKED_VERIFIED" `
            -Severity "blocking" `
            -Message "XLSX import cannot create verified rows outside repair mode." `
            -Field "canonical_validation_state" `
            -RowNumber $RowNumber
    }

    if ($rowData["rights_status"] -eq "unknown" -or $rowData["source_type"] -eq "unknown") {
        $rowData["human_review_required"] = 1
        $warnings += New-KoaMessage `
            -Code "WARN_REVIEW_REQUIRED" `
            -Severity "warning" `
            -Message "New row has unknown source or rights; human_review_required set to 1." `
            -RowNumber $RowNumber
    }

    return [ordered]@{
        row_data = $rowData
        warnings = @($warnings)
        errors   = @($errors)
    }
}

function Insert-KoaXlsxImportLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $ImportUuid,

        [Parameter(Mandatory)]
        [string] $XlsxPath,

        [Parameter(Mandatory)]
        [string] $Action,

        [string] $VersionUuid = "",

        [int] $RowNumber = 0,

        [object] $Before = $null,

        [object] $After = $null,

        [string] $ValidationStatus = "unknown",

        [object[]] $ValidationErrors = @()
    )

    $sql = @"
INSERT INTO xlsx_import_log(
    import_uuid,
    xlsx_path,
    action,
    version_uuid,
    row_number,
    before_json,
    after_json,
    validation_status,
    validation_errors,
    created_at
)
VALUES (
    @import_uuid,
    @xlsx_path,
    @action,
    @version_uuid,
    @row_number,
    @before_json,
    @after_json,
    @validation_status,
    @validation_errors,
    CURRENT_TIMESTAMP
);
"@

    $beforeJson = $null
    $afterJson = $null

    if ($null -ne $Before) {
        $beforeJson = ($Before | ConvertTo-Json -Depth 50 -Compress)
    }

    if ($null -ne $After) {
        $afterJson = ($After | ConvertTo-Json -Depth 50 -Compress)
    }

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql `
        -Parameters @{
            import_uuid       = $ImportUuid
            xlsx_path         = $XlsxPath
            action            = $Action
            version_uuid      = $VersionUuid
            row_number        = $RowNumber
            before_json       = $beforeJson
            after_json        = $afterJson
            validation_status = $ValidationStatus
            validation_errors = ($ValidationErrors | ConvertTo-Json -Depth 50 -Compress)
        } | Out-Null
}

function Insert-KoaAuditLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $Action,

        [Parameter(Mandatory)]
        [string] $EntityType,

        [string] $EntityUuid = "",

        [object] $Before = $null,

        [object] $After = $null,

        [string] $Note = ""
    )

    $sql = @"
INSERT INTO audit_log(action, entity_type, entity_uuid, before_json, after_json, actor, note, created_at)
VALUES (
    @action,
    @entity_type,
    @entity_uuid,
    @before_json,
    @after_json,
    'local_user',
    @note,
    CURRENT_TIMESTAMP
);
"@

    $beforeJson = $null
    $afterJson = $null

    if ($null -ne $Before) {
        $beforeJson = ($Before | ConvertTo-Json -Depth 50 -Compress)
    }

    if ($null -ne $After) {
        $afterJson = ($After | ConvertTo-Json -Depth 50 -Compress)
    }

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql `
        -Parameters @{
            action      = $Action
            entity_type = $EntityType
            entity_uuid = $EntityUuid
            before_json = $beforeJson
            after_json  = $afterJson
            note        = $Note
        } | Out-Null
}

function Apply-KoaUpdateRow {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $VersionUuid,

        [Parameter(Mandatory)]
        [hashtable] $Updates
    )

    if ($Updates.Count -eq 0) {
        return
    }

    $whereSql = "version_uuid = $(ConvertTo-KoaSqlLiteral -Value $VersionUuid)"
    $sql = Join-KoaSqlUpdate -TableName "library_rows" -Data $Updates -WhereSql $whereSql

    Invoke-KoaSqliteNonQuery -Connection $Connection -Sql $sql | Out-Null
}

function Apply-KoaArchiveRow {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [string] $VersionUuid
    )

    $sql = @"
UPDATE library_rows
SET status = 'archived',
    updated_at = @updated_at
WHERE version_uuid = @version_uuid;
"@

    Invoke-KoaSqliteNonQuery `
        -Connection $Connection `
        -Sql $sql `
        -Parameters @{
            version_uuid = $VersionUuid
            updated_at   = Get-KoaTimestamp
        } | Out-Null
}

function Apply-KoaInsertRow {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [object] $Connection,

        [Parameter(Mandatory)]
        [hashtable] $RowData
    )

    $columns = Get-KoaLibraryRowColumns
    $insertData = @{}

    foreach ($column in $columns) {
        if ($RowData.ContainsKey($column)) {
            $insertData[$column] = $RowData[$column]
        }
    }

    $sql = Join-KoaSqlInsert -TableName "library_rows" -Data $insertData
    Invoke-KoaSqliteNonQuery -Connection $Connection -Sql $sql | Out-Null
}

try {
    $warnings = @()
    $errors = @()

    Test-KoaDbPath -DbPath $DbPath -ThrowOnMissing | Out-Null

    if (-not (Test-Path -LiteralPath $XlsxPath -PathType Leaf)) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Operation $Operation `
            -Result "xlsx_not_found" `
            -EntityType "xlsx_import" `
            -Path $XlsxPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_FILE_NOT_FOUND" `
                    -Severity "blocking" `
                    -Message "XLSX file not found: $XlsxPath" `
                    -Field "XlsxPath"
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    if ([System.IO.Path]::GetExtension($XlsxPath).ToLowerInvariant() -ne ".xlsx") {
        $result = New-KoaOperationResult `
            -Success $false `
            -Operation $Operation `
            -Result "invalid_xlsx_path" `
            -EntityType "xlsx_import" `
            -Path $XlsxPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_XLSX_INVALID_FILE" `
                    -Severity "blocking" `
                    -Message "XlsxPath must point to a .xlsx file." `
                    -Field "XlsxPath"
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $connection = Open-KoaSqliteConnection -DbPath $DbPath
    $importUuid = New-KoaUuid

    $xlsxRows = Read-XlsxSheetRows `
        -XlsxPath $XlsxPath `
        -SheetName "Library"

    if ($xlsxRows.Count -eq 0) {
        $result = New-KoaOperationResult `
            -Success $false `
            -Operation $Operation `
            -Result "empty_library_sheet" `
            -EntityType "xlsx_import" `
            -EntityUuid $importUuid `
            -Path $XlsxPath `
            -Errors @(
                New-KoaMessage `
                    -Code "ERR_XLSX_MISSING_SHEET" `
                    -Severity "blocking" `
                    -Message "Library sheet is missing or empty." `
                    -Field "Library"
            )

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $changes = @()
    $rowsTotal = $xlsxRows.Count
    $rowsUpdate = 0
    $rowsNew = 0
    $rowsArchive = 0
    $rowsIgnore = 0
    $rowsBlocked = 0
    $rowsNoChange = 0

    foreach ($rawRow in $xlsxRows) {
        $rowHash = ConvertTo-LocalHashtable -Value $rawRow
        $rowNumber = [int] $rowHash["__row_number"]

        try {
            $action = Test-KoaXlsxAction -Action ([string] $rowHash["xlsx_action"])
        }
        catch {
            $rowError = New-KoaMessage `
                -Code "ERR_XLSX_INVALID_ACTION" `
                -Severity "blocking" `
                -Message $_.Exception.Message `
                -Field "xlsx_action" `
                -RowNumber $rowNumber

            $errors += $rowError
            $rowsBlocked++

            $changes += [ordered]@{
                row_number = $rowNumber
                action     = "blocked"
                reason     = "invalid_action"
                errors     = @($rowError)
            }

            continue
        }

        if ($action -eq "ignore") {
            $rowsIgnore++
            $changes += [ordered]@{
                row_number = $rowNumber
                action     = "ignore"
                result     = "ignored"
            }
            continue
        }

        $versionUuid = ""
        if ($rowHash.ContainsKey("version_uuid")) {
            $versionUuid = ([string] $rowHash["version_uuid"]).Trim()
        }

        if ($action -in @("update", "archive") -and [string]::IsNullOrWhiteSpace($versionUuid)) {
            $rowError = New-KoaMessage `
                -Code "ERR_VERSION_UUID_MISSING" `
                -Severity "blocking" `
                -Message "$action requires version_uuid." `
                -Field "version_uuid" `
                -RowNumber $rowNumber

            $errors += $rowError
            $rowsBlocked++

            $changes += [ordered]@{
                row_number = $rowNumber
                action     = "blocked"
                reason     = "missing_version_uuid"
                errors     = @($rowError)
            }

            continue
        }

        if ($action -eq "new") {
            $newBuild = Build-KoaNewRowFromXlsx `
                -XlsxRow $rowHash `
                -RowNumber $rowNumber `
                -Mode $Mode `
                -ImportUuid $importUuid

            $warnings += @($newBuild.warnings)

            if ($newBuild.errors.Count -gt 0) {
                $errors += @($newBuild.errors)
                $rowsBlocked++

                $changes += [ordered]@{
                    row_number = $rowNumber
                    action     = "new"
                    result     = "blocked"
                    errors     = $newBuild.errors
                }

                continue
            }

            $rowData = ConvertTo-LocalHashtable -Value $newBuild.row_data
            $newVersionUuid = [string] $rowData["version_uuid"]

            $existing = Get-KoaLibraryRowByVersionUuid `
                -Connection $connection `
                -VersionUuid $newVersionUuid

            if ($null -ne $existing) {
                $rowError = New-KoaMessage `
                    -Code "ERR_VERSION_UUID_DUPLICATE" `
                    -Severity "blocking" `
                    -Message "New row version_uuid already exists." `
                    -Field "version_uuid" `
                    -RowNumber $rowNumber `
                    -Details @{ version_uuid = $newVersionUuid }

                $errors += $rowError
                $rowsBlocked++

                $changes += [ordered]@{
                    row_number   = $rowNumber
                    action       = "new"
                    result       = "blocked"
                    version_uuid = $newVersionUuid
                    errors       = @($rowError)
                }

                continue
            }

            $rowsNew++

            $changes += [ordered]@{
                row_number   = $rowNumber
                action       = "new"
                result       = if ($Mode -eq "dry_run") { "would_insert" } else { "insert" }
                version_uuid = $newVersionUuid
                media_uuid   = $rowData["media_uuid"]
                after        = $rowData
            }

            continue
        }

        $existingRow = Get-KoaLibraryRowByVersionUuid `
            -Connection $connection `
            -VersionUuid $versionUuid

        if ($null -eq $existingRow) {
            $rowError = New-KoaMessage `
                -Code "ERR_VERSION_UUID_MISSING" `
                -Severity "blocking" `
                -Message "version_uuid not found in SQLite." `
                -Field "version_uuid" `
                -RowNumber $rowNumber `
                -Details @{ version_uuid = $versionUuid }

            $errors += $rowError
            $rowsBlocked++

            $changes += [ordered]@{
                row_number   = $rowNumber
                action       = $action
                result       = "blocked"
                version_uuid = $versionUuid
                errors       = @($rowError)
            }

            continue
        }

        if ($action -eq "archive") {
            $rowsArchive++

            $changes += [ordered]@{
                row_number   = $rowNumber
                action       = "archive"
                result       = if ($Mode -eq "dry_run") { "would_archive" } else { "archive" }
                version_uuid = $versionUuid
                before       = $existingRow
                after        = @{
                    status     = "archived"
                    updated_at = Get-KoaTimestamp
                }
            }

            continue
        }

        $updateBuild = Build-KoaImportUpdate `
            -ExistingRow $existingRow `
            -XlsxRow $rowHash `
            -Mode $Mode `
            -RowNumber $rowNumber

        $warnings += @($updateBuild.warnings)

        if ($updateBuild.errors.Count -gt 0) {
            $errors += @($updateBuild.errors)
            $rowsBlocked++

            $changes += [ordered]@{
                row_number   = $rowNumber
                action       = "update"
                result       = "blocked"
                version_uuid = $versionUuid
                errors       = $updateBuild.errors
            }

            continue
        }

        $updates = ConvertTo-LocalHashtable -Value $updateBuild.updates

        if ($updates.Count -eq 0) {
            $rowsNoChange++
            $changes += [ordered]@{
                row_number        = $rowNumber
                action            = "update"
                result            = "no_change"
                version_uuid      = $versionUuid
                protected_changes = $updateBuild.protected_changes
            }

            continue
        }

        $rowsUpdate++

        $changes += [ordered]@{
            row_number        = $rowNumber
            action            = "update"
            result            = if ($Mode -eq "dry_run") { "would_update" } else { "update" }
            version_uuid      = $versionUuid
            before            = $existingRow
            updates           = $updates
            protected_changes = $updateBuild.protected_changes
        }
    }

    $isBlocked = ($errors | Where-Object { $_.severity -eq "blocking" }).Count -gt 0

    if ($isBlocked) {
        foreach ($change in $changes) {
            $changeHash = ConvertTo-LocalHashtable -Value $change
            $versionUuidForLog = ""
            if ($changeHash.ContainsKey("version_uuid")) {
                $versionUuidForLog = [string] $changeHash["version_uuid"]
            }

            Insert-KoaXlsxImportLog `
                -Connection $connection `
                -ImportUuid $importUuid `
                -XlsxPath $XlsxPath `
                -Action ([string] $changeHash["action"]) `
                -VersionUuid $versionUuidForLog `
                -RowNumber ([int] $changeHash["row_number"]) `
                -Before $changeHash["before"] `
                -After $change `
                -ValidationStatus "blocked" `
                -ValidationErrors $errors
        }

        $result = New-KoaOperationResult `
            -Success $false `
            -Operation $Operation `
            -Result "import_blocked" `
            -EntityType "xlsx_import" `
            -EntityUuid $importUuid `
            -Path $XlsxPath `
            -Data @{
                import_uuid   = $importUuid
                mode          = $Mode
                db_path       = $DbPath
                xlsx_path     = $XlsxPath
                rows_total    = $rowsTotal
                rows_update   = $rowsUpdate
                rows_new      = $rowsNew
                rows_archive  = $rowsArchive
                rows_ignore   = $rowsIgnore
                rows_blocked  = $rowsBlocked
                rows_nochange = $rowsNoChange
                changes       = $changes
            } `
            -Warnings $warnings `
            -Errors $errors

        Write-KoaJsonResult -Result $result
        exit 1
    }

    $backupResult = $null

    if ($Mode -ne "dry_run") {
        $backupResult = Backup-KoaDatabase `
            -DbPath $DbPath `
            -BackupDir $BackupDir `
            -Reason "xlsx_import"

        if (-not $backupResult.success) {
            $result = New-KoaOperationResult `
                -Success $false `
                -Operation $Operation `
                -Result "backup_failed" `
                -EntityType "xlsx_import" `
                -EntityUuid $importUuid `
                -Path $XlsxPath `
                -Data @{
                    import_uuid = $importUuid
                    backup      = $backupResult
                } `
                -Warnings $warnings `
                -Errors $backupResult.errors

            Write-KoaJsonResult -Result $result
            exit 1
        }
    }

    if ($Mode -ne "dry_run") {
        Invoke-KoaSqliteNonQuery -Connection $connection -Sql "BEGIN TRANSACTION;" | Out-Null

        try {
            foreach ($change in $changes) {
                $changeHash = ConvertTo-LocalHashtable -Value $change
                $action = [string] $changeHash["action"]
                $resultName = [string] $changeHash["result"]

                if ($action -eq "ignore" -or $resultName -eq "no_change") {
                    continue
                }

                if ($action -eq "new") {
                    $rowData = ConvertTo-LocalHashtable -Value $changeHash["after"]
                    Apply-KoaInsertRow -Connection $connection -RowData $rowData

                    Insert-KoaAuditLog `
                        -Connection $connection `
                        -Action "library_row_inserted" `
                        -EntityType "library_row" `
                        -EntityUuid ([string] $rowData["version_uuid"]) `
                        -Before $null `
                        -After $rowData `
                        -Note "Import-KoaLibraryXlsx.ps1 import_uuid=$importUuid"
                }
                elseif ($action -eq "archive") {
                    $versionUuid = [string] $changeHash["version_uuid"]
                    Apply-KoaArchiveRow -Connection $connection -VersionUuid $versionUuid

                    Insert-KoaAuditLog `
                        -Connection $connection `
                        -Action "library_row_archived" `
                        -EntityType "library_row" `
                        -EntityUuid $versionUuid `
                        -Before $changeHash["before"] `
                        -After $changeHash["after"] `
                        -Note "Import-KoaLibraryXlsx.ps1 import_uuid=$importUuid"
                }
                elseif ($action -eq "update") {
                    $versionUuid = [string] $changeHash["version_uuid"]
                    $updates = ConvertTo-LocalHashtable -Value $changeHash["updates"]

                    Apply-KoaUpdateRow `
                        -Connection $connection `
                        -VersionUuid $versionUuid `
                        -Updates $updates

                    Insert-KoaAuditLog `
                        -Connection $connection `
                        -Action "library_row_updated" `
                        -EntityType "library_row" `
                        -EntityUuid $versionUuid `
                        -Before $changeHash["before"] `
                        -After $updates `
                        -Note "Import-KoaLibraryXlsx.ps1 import_uuid=$importUuid"
                }

                $versionUuidForLog = ""
                if ($changeHash.ContainsKey("version_uuid")) {
                    $versionUuidForLog = [string] $changeHash["version_uuid"]
                }

                Insert-KoaXlsxImportLog `
                    -Connection $connection `
                    -ImportUuid $importUuid `
                    -XlsxPath $XlsxPath `
                    -Action $action `
                    -VersionUuid $versionUuidForLog `
                    -RowNumber ([int] $changeHash["row_number"]) `
                    -Before $changeHash["before"] `
                    -After $change `
                    -ValidationStatus "applied" `
                    -ValidationErrors @()
            }

            Insert-KoaAuditLog `
                -Connection $connection `
                -Action "xlsx_import_applied" `
                -EntityType "xlsx_import" `
                -EntityUuid $importUuid `
                -Before $null `
                -After @{
                    import_uuid  = $importUuid
                    xlsx_path    = $XlsxPath
                    mode         = $Mode
                    rows_total   = $rowsTotal
                    rows_update  = $rowsUpdate
                    rows_new     = $rowsNew
                    rows_archive = $rowsArchive
                    rows_ignore  = $rowsIgnore
                } `
                -Note "Import-KoaLibraryXlsx.ps1"

            Invoke-KoaSqliteNonQuery -Connection $connection -Sql "COMMIT;" | Out-Null
        }
        catch {
            try {
                Invoke-KoaSqliteNonQuery -Connection $connection -Sql "ROLLBACK;" | Out-Null
            }
            catch {
                # Keep original exception.
            }

            throw
        }
    }
    else {
        foreach ($change in $changes) {
            $changeHash = ConvertTo-LocalHashtable -Value $change
            $versionUuidForLog = ""

            if ($changeHash.ContainsKey("version_uuid")) {
                $versionUuidForLog = [string] $changeHash["version_uuid"]
            }

            Insert-KoaXlsxImportLog `
                -Connection $connection `
                -ImportUuid $importUuid `
                -XlsxPath $XlsxPath `
                -Action ([string] $changeHash["action"]) `
                -VersionUuid $versionUuidForLog `
                -RowNumber ([int] $changeHash["row_number"]) `
                -Before $changeHash["before"] `
                -After $change `
                -ValidationStatus "dry_run" `
                -ValidationErrors @()
        }

        Insert-KoaAuditLog `
            -Connection $connection `
            -Action "xlsx_import_previewed" `
            -EntityType "xlsx_import" `
            -EntityUuid $importUuid `
            -Before $null `
            -After @{
                import_uuid  = $importUuid
                xlsx_path    = $XlsxPath
                mode         = $Mode
                rows_total   = $rowsTotal
                rows_update  = $rowsUpdate
                rows_new     = $rowsNew
                rows_archive = $rowsArchive
                rows_ignore  = $rowsIgnore
            } `
            -Note "Import-KoaLibraryXlsx.ps1"
    }

    $resultName = if ($Mode -eq "dry_run") { "import_previewed" } else { "import_applied" }

    $result = New-KoaOperationResult `
        -Success $true `
        -Operation $Operation `
        -Result $resultName `
        -EntityType "xlsx_import" `
        -EntityUuid $importUuid `
        -Path $XlsxPath `
        -Data @{
            import_uuid   = $importUuid
            mode          = $Mode
            db_path       = $DbPath
            xlsx_path     = $XlsxPath
            backup        = $backupResult
            rows_total    = $rowsTotal
            rows_update   = $rowsUpdate
            rows_new      = $rowsNew
            rows_archive  = $rowsArchive
            rows_ignore   = $rowsIgnore
            rows_blocked  = $rowsBlocked
            rows_nochange = $rowsNoChange
            changes       = $changes
        } `
        -Warnings $warnings `
        -Errors @()

    Write-KoaJsonResult -Result $result
    exit 0
}
catch {
    $errorResult = New-KoaOperationResult `
        -Success $false `
        -Operation $Operation `
        -Result "failed" `
        -EntityType "xlsx_import" `
        -Path $XlsxPath `
        -Errors @(
            New-KoaMessage `
                -Code "ERR_XLSX_IMPORT_FAILED" `
                -Severity "blocking" `
                -Message $_.Exception.Message
        )

    Write-KoaJsonResult -Result $errorResult
    exit 1
}

