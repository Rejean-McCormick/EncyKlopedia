<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

defined('MOODLE_INTERNAL') || die();

/**
 * English language strings for the UCKK Registrar activity module.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

// -----------------------------------------------------------------------------
// Plugin identity.
// -----------------------------------------------------------------------------

$string['pluginname'] = 'UCKK Registrar';
$string['pluginadministration'] = 'UCKK Registrar administration';
$string['modulename'] = 'UCKK Registrar';
$string['modulenameplural'] = 'UCKK Registrar activities';
$string['modulename_help'] = 'The UCKK Registrar activity stores registry records, evidence, decisions, course work, Kristals, portfolio items, integrity summaries, version records, and exportable registry packages with provenance, visibility, validation, and revision history.';
$string['modulename_link'] = 'mod/uckkarchive/view';
$string['uckkarchive:addinstance'] = 'Add a new UCKK Registrar activity';
$string['uckkarchive:view'] = 'View UCKK Registrar';
$string['uckkarchive:additem'] = 'Add registry item';
$string['uckkarchive:validateitem'] = 'Validate registry item';
$string['uckkarchive:reviseitem'] = 'Revise registry item';
$string['uckkarchive:versionitem'] = 'Version registry item';
$string['uckkarchive:viewrestricted'] = 'View restricted registry items';
$string['uckkarchive:export'] = 'Export registry packages';

// -----------------------------------------------------------------------------
// General labels.
// -----------------------------------------------------------------------------

$string['activity'] = 'Activity';
$string['actions'] = 'Actions';
$string['add'] = 'Add';
$string['additem'] = 'Add registry item';
$string['archive'] = 'Registry';
$string['archiveactivity'] = 'Registrar activity';
$string['archiveitem'] = 'Registry item';
$string['archiveitems'] = 'Registry items';
$string['archiveitemdetails'] = 'Registry item details';
$string['archiveoverview'] = 'Registrar overview';
$string['archivepolicy'] = 'Registry policy';
$string['archives'] = 'Registries';
$string['backtoarchive'] = 'Back to registry';
$string['backtoarchives'] = 'Back to registries';
$string['cancel'] = 'Cancel';
$string['close'] = 'Close';
$string['confirm'] = 'Confirm';
$string['continue'] = 'Continue';
$string['course'] = 'Course';
$string['created'] = 'Created';
$string['createdby'] = 'Created by';
$string['description'] = 'Description';
$string['details'] = 'Details';
$string['download'] = 'Download';
$string['edit'] = 'Edit';
$string['empty'] = 'Nothing to display.';
$string['export'] = 'Export';
$string['files'] = 'Files';
$string['filter'] = 'Filter';
$string['item'] = 'Item';
$string['items'] = 'Items';
$string['metadata'] = 'Metadata';
$string['modified'] = 'Modified';
$string['modifiedby'] = 'Modified by';
$string['name'] = 'Name';
$string['none'] = 'None';
$string['notes'] = 'Notes';
$string['open'] = 'Open';
$string['openexternal'] = 'Open external reference';
$string['openexternal_help'] = 'Open the external source URL in a new tab. The media record remains governed by UCKK metadata, rights, visibility, advisories, and cultural protocols.';
$string['owner'] = 'Owner';
$string['preview'] = 'Preview';
$string['provenance'] = 'Provenance';
$string['reason'] = 'Reason';
$string['records'] = 'Records';
$string['restricted'] = 'Restricted';
$string['restricted_integrity'] = 'Restricted integrity';
$string['revision'] = 'Revision';
$string['revisions'] = 'Revisions';
$string['save'] = 'Save';
$string['search'] = 'Search';
$string['source'] = 'Source';
$string['status'] = 'Status';
$string['submit'] = 'Submit';
$string['summary'] = 'Summary';
$string['title'] = 'Title';
$string['type'] = 'Type';
$string['validation'] = 'Validation';
$string['visibility'] = 'Visibility';
$string['version'] = 'Version';
$string['versionno'] = 'Version {$a}';
$string['view'] = 'View';
$string['viewdetails'] = 'View details';

// -----------------------------------------------------------------------------
// Activity instance form.
// -----------------------------------------------------------------------------

$string['archivename'] = 'Registry name';
$string['archivename_help'] = 'Name of this UCKK Registrar activity.';
$string['archiveintro'] = 'Registry introduction';
$string['archivecode'] = 'Registry code';
$string['archivecode_help'] = 'Stable internal code for this registry. Use letters, numbers, underscores, or hyphens.';
$string['archivecontext'] = 'Registry context';
$string['archivecontext_help'] = 'Describe what this registry is meant to preserve and who may use it.';
$string['archivepurpose'] = 'Registry purpose';
$string['archivepurpose_help'] = 'Explain why this registry exists: evidence, decisions, portfolio, course memory, Kristals, integrity summaries, or institutional memory.';
$string['defaultvisibility'] = 'Default visibility';
$string['defaultvisibility_help'] = 'Default visibility applied to new items unless the item form overrides it.';
$string['allowpublicitems'] = 'Allow public items';
$string['allowpublicitems_help'] = 'Allow manually validated registry items to be made public.';
$string['requirevalidation'] = 'Require validation before publication';
$string['requirevalidation_help'] = 'Require a Registrar or authorised reviewer to validate items before they are treated as verified or public.';
$string['allowkristals'] = 'Allow Kristals';
$string['allowkristals_help'] = 'Allow this registry to store Kristal records: distilled learning, decision, proof, or memory fragments.';
$string['allowexports'] = 'Allow exports';
$string['allowexports_help'] = 'Allow authorised users to export registry packages.';
$string['completionrequirevalidateditem'] = 'Student must have a validated registry item';
$string['completionrequireitem'] = 'Student must add a registry item';
$string['completionrequirekristal'] = 'Student must create a Kristal';

// -----------------------------------------------------------------------------
// Settings.
// -----------------------------------------------------------------------------

$string['settings:general'] = 'General registry settings';
$string['settings:general_desc'] = 'Configure UCKK Registrar defaults.';
$string['settings:defaultvisibility'] = 'Default registry visibility';
$string['settings:defaultvisibility_desc'] = 'Default visibility used when a new registry item does not specify a visibility.';
$string['settings:requirevalidation'] = 'Require validation';
$string['settings:requirevalidation_desc'] = 'Require validation before registry items become verified or public.';
$string['settings:allowpublicarchives'] = 'Allow public registry items';
$string['settings:allowpublicarchives_desc'] = 'Allow registry items to become publicly visible after manual validation.';
$string['settings:allowrestrictedintegrity'] = 'Allow restricted integrity registries';
$string['settings:allowrestrictedintegrity_desc'] = 'Allow registry items to be marked as restricted to users with integrity or restricted registry capabilities.';
$string['settings:enablekristals'] = 'Enable Kristals';
$string['settings:enablekristals_desc'] = 'Enable Kristal creation and display in UCKK Registrar.';
$string['settings:enableexports'] = 'Enable export packages';
$string['settings:enableexports_desc'] = 'Allow authorised users to generate export packages.';
$string['settings:retentiondays'] = 'Default retention period';
$string['settings:retentiondays_desc'] = 'Default retention period in days. Use 0 for no automatic expiry.';
$string['settings:maxexportitems'] = 'Maximum items per export';
$string['settings:maxexportitems_desc'] = 'Maximum number of registry items included in one export package.';
$string['settings:provenance'] = 'Provenance settings';
$string['settings:provenance_desc'] = 'Configure registry provenance and validation behaviour.';
$string['settings:requireprovenance'] = 'Require provenance';
$string['settings:requireprovenance_desc'] = 'Require a provenance statement for every registry item.';
$string['settings:requirevalidationnotes'] = 'Require validation notes';
$string['settings:requirevalidationnotes_desc'] = 'Require validators to provide notes when validating, rejecting, or invalidating an item.';

// -----------------------------------------------------------------------------
// Item form.
// -----------------------------------------------------------------------------

$string['archiveitemform'] = 'Registry item form';
$string['itemtitle'] = 'Item title';
$string['itemtitle_help'] = 'Clear title for the registry item.';
$string['itemsummary'] = 'Item summary';
$string['itemsummary_help'] = 'Short summary safe for the selected visibility level.';
$string['itemcontent'] = 'Item content';
$string['itemcontent_help'] = 'Main registry content. Do not include restricted details unless the item visibility allows it.';
$string['itemtype'] = 'Item type';
$string['itemtype_help'] = 'Choose the type that best describes the registry item.';
$string['itemstatus'] = 'Item status';
$string['itemvisibility'] = 'Item visibility';
$string['itemvisibility_help'] = 'Controls who may see this registry item. Restricted integrity items require explicit capability.';
$string['itemprovenance'] = 'Item provenance';
$string['itemprovenance_help'] = 'Explain where the item comes from, who produced it, what was transformed, and what can be verified.';
$string['itemsource'] = 'Source';
$string['itemsource_help'] = 'Original source, system, activity, person, registry, or external reference for this item.';
$string['sourcecomponent'] = 'Source component';
$string['sourcecomponent_help'] = 'Moodle component that originated the item, when known.';
$string['sourceid'] = 'Source ID';
$string['sourceid_help'] = 'Record ID in the source component, when known.';
$string['sourceurl'] = 'Source URL';
$string['sourceurl_help'] = 'Optional URL pointing to the source.';
$string['externalurl'] = 'External URL';
$string['sourceauthor'] = 'Source or author';
$string['sourceauthor_help'] = 'Person, group, system, activity, or registry source behind the item.';
$string['sourcedate'] = 'Source date';
$string['sourcedate_help'] = 'Date associated with the original source.';
$string['license'] = 'Licence';
$string['license_help'] = 'Licence or reuse condition attached to the item, when applicable.';
$string['tags'] = 'Tags';
$string['tags_help'] = 'Optional comma-separated tags for filtering and reporting.';
$string['files_help'] = 'Files attached to this registry item. Files inherit the item visibility unless a service applies a stricter rule.';
$string['prooffiles'] = 'Proof files';
$string['decisionattachments'] = 'Decision attachments';
$string['minutesfiles'] = 'Minutes files';
$string['kristalfiles'] = 'Kristal files';
$string['portfoliofiles'] = 'Portfolio files';
$string['integrityexports'] = 'Integrity exports';
$string['addarchiveitem'] = 'Add registry item';
$string['editarchiveitem'] = 'Edit registry item';
$string['archiveitemsaved'] = 'Registry item saved.';
$string['archiveitemcreated'] = 'Registry item created.';
$string['archiveitemupdated'] = 'Registry item updated.';
$string['cannotadditem'] = 'You cannot add registry items here.';
$string['cannotedititem'] = 'You cannot edit this registry item.';
$string['cannotviewitem'] = 'You cannot view this registry item.';
$string['missingarchiveitem'] = 'Registry item not found.';
$string['invaliditemtype'] = 'Invalid registry item type.';
$string['invaliditemstatus'] = 'Invalid registry item status.';
$string['invaliditemvisibility'] = 'Invalid registry item visibility.';
$string['provenancerequired'] = 'A provenance statement is required.';
$string['contentorsourcefilesrequired'] = 'Add content, a source URL, or at least one file.';

// -----------------------------------------------------------------------------
// Kristals.
// -----------------------------------------------------------------------------

$string['kristal'] = 'Kristal';
$string['kristals'] = 'Kristals';
$string['kristalform'] = 'Kristal form';
$string['addkristal'] = 'Add Kristal';
$string['editkristal'] = 'Edit Kristal';
$string['kristaltitle'] = 'Kristal title';
$string['kristaltitle_help'] = 'Short title for this Kristal.';
$string['kristalstatement'] = 'Kristal statement';
$string['kristalstatement_help'] = 'Distilled statement of learning, decision, proof, insight, or memory.';
$string['kristalcontext'] = 'Kristal context';
$string['kristalcontext_help'] = 'Explain the context from which this Kristal was distilled.';
$string['kristalproof'] = 'Kristal proof';
$string['kristalproof_help'] = 'Evidence or references supporting the Kristal.';
$string['kristaltype'] = 'Kristal type';
$string['kristalvisibility'] = 'Kristal visibility';
$string['kristalcreated'] = 'Kristal created.';
$string['kristalupdated'] = 'Kristal updated.';
$string['kristalempty'] = 'No Kristals are available.';
$string['cannotaddkristal'] = 'You cannot add Kristals here.';
$string['cannoteditkristal'] = 'You cannot edit this Kristal.';
$string['cannotviewkristal'] = 'You cannot view this Kristal.';
$string['invalidkristaltype'] = 'Invalid Kristal type.';

// -----------------------------------------------------------------------------
// Validation.
// -----------------------------------------------------------------------------

$string['validate'] = 'Validate';
$string['validateitem'] = 'Validate registry item';
$string['validationform'] = 'Validation form';
$string['validationstate'] = 'Validation state';
$string['validationnotes'] = 'Validation notes';
$string['validationnotes_help'] = 'Explain the validation decision, uncertainty, corrections required, or reason for rejection.';
$string['validationdecision'] = 'Validation decision';
$string['validationdecision_help'] = 'Choose how this registry item should be treated after review.';
$string['validatedby'] = 'Validated by';
$string['timevalidated'] = 'Validation time';
$string['archiveitemvalidated'] = 'Registry item validated.';
$string['archiveitemrejected'] = 'Registry item rejected.';
$string['archiveiteminvalidated'] = 'Registry item invalidated.';
$string['archiveitemcorrectionrequired'] = 'Correction required for registry item.';
$string['archiveitemcontested'] = 'Registry item contested.';
$string['cannotvalidateitem'] = 'You cannot validate this registry item.';
$string['validationrequiresnotes'] = 'Validation notes are required for this decision.';
$string['manualvalidationrequired'] = 'Manual validation required';
$string['publicvalidationrequired'] = 'Public registry items must be manually validated.';
$string['restrictedvalidationrequired'] = 'Restricted integrity registry items require explicit validation.';

$string['validationdecision:validate'] = 'Validate';
$string['validationdecision:reject'] = 'Reject';
$string['validationdecision:correction_required'] = 'Correction required';
$string['validationdecision:contest'] = 'Contest';
$string['validationdecision:invalidate'] = 'Invalidate';

// -----------------------------------------------------------------------------
// Revision and versioning.
// -----------------------------------------------------------------------------

$string['revise'] = 'Revise';
$string['reviseitem'] = 'Revise registry item';
$string['revisionform'] = 'Revision form';
$string['revisionreason'] = 'Revision reason';
$string['revisionreason_help'] = 'Explain why this revision is needed. Registry history must remain traceable.';
$string['revisionnotes'] = 'Revision notes';
$string['revisioncreated'] = 'Revision created.';
$string['archiveitemrevised'] = 'Registry item revised.';
$string['previousversion'] = 'Previous version';
$string['currentversion'] = 'Current version';
$string['versionhistory'] = 'Version history';
$string['versionrecord'] = 'Version record';
$string['cannotreviseitem'] = 'You cannot revise this registry item.';
$string['cannotversionitem'] = 'You cannot create a version record for this item.';
$string['revisionrequiresreason'] = 'A revision reason is required.';
$string['revisionnonsovereignnotice'] = 'A revision preserves registry history. It must not silently erase evidence or provenance.';

// -----------------------------------------------------------------------------
// Export.
// -----------------------------------------------------------------------------

$string['exportarchive'] = 'Export registry';
$string['exportform'] = 'Export form';
$string['exportpackage'] = 'Export package';
$string['exportpackages'] = 'Export packages';
$string['exportformat'] = 'Export format';
$string['exportscope'] = 'Export scope';
$string['exportvisibility'] = 'Export visibility';
$string['exportreason'] = 'Export reason';
$string['exportreason_help'] = 'Explain why this registry export is needed.';
$string['exportincludeproofs'] = 'Include proof files';
$string['exportincludeprovenance'] = 'Include provenance';
$string['exportincludehistory'] = 'Include revision history';
$string['exportincludeintegrity'] = 'Include integrity summaries';
$string['exportredactrestricted'] = 'Redact restricted details';
$string['exportredactrestricted_help'] = 'Remove or summarize restricted integrity details from the export package unless the viewer has explicit permission.';
$string['exportgenerated'] = 'Registry export generated.';
$string['archiveitemexported'] = 'Registry item exported.';
$string['cannotexportarchive'] = 'You cannot export this registry.';
$string['cannotexportitem'] = 'You cannot export this registry item.';
$string['exportrequiresreason'] = 'An export reason is required.';
$string['exportempty'] = 'No export packages are available.';
$string['downloadexport'] = 'Download export';
$string['exportqueued'] = 'Export queued.';
$string['exportfailed'] = 'Export failed.';
$string['exportsucceeded'] = 'Export completed.';

$string['exportformat:json'] = 'JSON';
$string['exportformat:zip'] = 'ZIP package';
$string['exportformat:csv'] = 'CSV';
$string['exportformat:pdf'] = 'PDF summary';
$string['exportscope:item'] = 'Single item';
$string['exportscope:archive'] = 'Whole registry';
$string['exportscope:course'] = 'Course registry';
$string['exportscope:user'] = 'User portfolio registry';
$string['exportscope:integrity'] = 'Integrity registry';

// -----------------------------------------------------------------------------
// Item types.
// -----------------------------------------------------------------------------

$string['itemtype:proof'] = 'Proof';
$string['itemtype:decision'] = 'Decision';
$string['itemtype:course_work'] = 'Course work';
$string['itemtype:challenge_result'] = 'Challenge result';
$string['itemtype:assembly_minutes'] = 'Assembly minutes';
$string['itemtype:integrity_case_summary'] = 'Integrity case summary';
$string['itemtype:kristal'] = 'Kristal';
$string['itemtype:reflection'] = 'Reflection';
$string['itemtype:portfolio_item'] = 'Portfolio item';
$string['itemtype:version_record'] = 'Version record';
$string['itemtype:archive_item'] = 'Registry item';
// -----------------------------------------------------------------------------
// Kristal types.
// -----------------------------------------------------------------------------

$string['kristaltype:learning'] = 'Learning Kristal';
$string['kristaltype:decision'] = 'Decision Kristal';
$string['kristaltype:proof'] = 'Proof Kristal';
$string['kristaltype:reflection'] = 'Reflection Kristal';
$string['kristaltype:method'] = 'Method Kristal';
$string['kristaltype:governance'] = 'Governance Kristal';
$string['kristaltype:integrity'] = 'Integrity Kristal';
$string['kristaltype:memory'] = 'Memory Kristal';

// -----------------------------------------------------------------------------
// Proof types.
// -----------------------------------------------------------------------------

$string['prooftype'] = 'Proof type';
$string['prooftype:text'] = 'Text';
$string['prooftype:file'] = 'File';
$string['prooftype:url'] = 'URL';
$string['prooftype:dataset'] = 'Dataset';
$string['prooftype:image'] = 'Image';
$string['prooftype:video'] = 'Video';
$string['prooftype:testimony'] = 'Testimony';
$string['prooftype:observation'] = 'Observation';
$string['prooftype:ai_log'] = 'AI log';
$string['prooftype:decision_record'] = 'Decision record';
$string['prooftype:archive_item'] = 'Registry item';

// -----------------------------------------------------------------------------
// Statuses.
// -----------------------------------------------------------------------------

$string['status:draft'] = 'Draft';
$string['status:active'] = 'Active';
$string['status:hidden'] = 'Hidden';
$string['status:pending'] = 'Pending';
$string['status:pending_review'] = 'Pending review';
$string['status:validated'] = 'Validated';
$string['status:rejected'] = 'Rejected';
$string['status:correction_required'] = 'Correction required';
$string['status:contested'] = 'Contested';
$string['status:invalidated'] = 'Invalidated';
$string['status:closed'] = 'Closed';
$string['status:archived'] = 'Preserved';
$string['status:cancelled'] = 'Cancelled';

$string['statuslabel:draft'] = 'Draft';
$string['statuslabel:active'] = 'Active';
$string['statuslabel:hidden'] = 'Hidden';
$string['statuslabel:pending'] = 'Pending';
$string['statuslabel:pendingreview'] = 'Pending review';
$string['statuslabel:validated'] = 'Validated';
$string['statuslabel:rejected'] = 'Rejected';
$string['statuslabel:correctionrequired'] = 'Correction required';
$string['statuslabel:contested'] = 'Contested';
$string['statuslabel:invalidated'] = 'Invalidated';
$string['statuslabel:closed'] = 'Closed';
$string['statuslabel:archived'] = 'Preserved';
$string['statuslabel:cancelled'] = 'Cancelled';

// -----------------------------------------------------------------------------
// Visibility.
// -----------------------------------------------------------------------------

$string['visibility:private'] = 'Private';
$string['visibility:user'] = 'User';
$string['visibility:group'] = 'Group';
$string['visibility:course'] = 'Course';
$string['visibility:cohort'] = 'Cohort';
$string['visibility:program'] = 'Program';
$string['visibility:institution'] = 'Institution';
$string['visibility:institutional'] = 'Institutional';
$string['visibility:public'] = 'Public';
$string['visibility:restricted'] = 'Restricted';
$string['visibility:restricted_integrity'] = 'Restricted integrity';
$string['visibility:hidden'] = 'Hidden';
$string['visibility:archived'] = 'Preserved';

$string['visibility_help:private'] = 'Visible only to authorised owners and reviewers.';
$string['visibility_help:course'] = 'Visible within the course context to users with permission.';
$string['visibility_help:program'] = 'Visible within the related UCKK program.';
$string['visibility_help:institution'] = 'Visible to authorised institutional viewers.';
$string['visibility_help:public'] = 'Public only after manual validation.';
$string['visibility_help:restricted_integrity'] = 'Visible only to users with restricted registry or integrity permissions.';

// -----------------------------------------------------------------------------
// Provenance.
// -----------------------------------------------------------------------------

$string['provenance:human'] = 'Human';
$string['provenance:ai_assisted'] = 'AI-assisted';
$string['provenance:imported'] = 'Imported';
$string['provenance:system'] = 'System';
$string['provenance:archive'] = 'Registry';
$string['provenance:assembly'] = 'Assembly';
$string['provenance:challenge'] = 'Challenge';
$string['provenance:integrity'] = 'Integrity';

$string['provenancehash'] = 'Provenance hash';
$string['provenancehash_help'] = 'Optional hash used to detect or document provenance changes.';
$string['provenancepanel'] = 'Provenance panel';
$string['provenancesource'] = 'Provenance source';
$string['provenancestatement'] = 'Provenance statement';
$string['provenancestatement_help'] = 'Explain origin, authorship, transformations, uncertainty, and verification path.';
$string['provenanceverified'] = 'Provenance verified';
$string['provenanceunverified'] = 'Provenance unverified';
$string['provenancewarning'] = 'Provenance warning';

// -----------------------------------------------------------------------------
// Validation states.
// -----------------------------------------------------------------------------

$string['validationstate:unverified'] = 'Unverified';
$string['validationstate:human_reviewed'] = 'Human reviewed';
$string['validationstate:verified'] = 'Verified';
$string['validationstate:contested'] = 'Contested';
$string['validationstate:invalidated'] = 'Invalidated';
$string['validationstate:archived'] = 'Preserved';

$string['validation:unverified'] = 'Unverified';
$string['validation:human_reviewed'] = 'Human reviewed';
$string['validation:verified'] = 'Verified';
$string['validation:contested'] = 'Contested';
$string['validation:invalidated'] = 'Invalidated';
$string['validation:archived'] = 'Preserved';

// -----------------------------------------------------------------------------
// Archive policies.
// -----------------------------------------------------------------------------

$string['archivepolicy:none'] = 'No registry policy';
$string['archivepolicy:summary'] = 'Summary registry';
$string['archivepolicy:full'] = 'Full registry';
$string['archivepolicy:restricted_integrity'] = 'Restricted integrity registry';
$string['archivepolicy:portfolio'] = 'Portfolio registry';
$string['archivepolicy:institutional_memory'] = 'Institutional memory';

// -----------------------------------------------------------------------------
// Pages and panels.
// -----------------------------------------------------------------------------

$string['archiveview'] = 'Registrar view';
$string['archiveviewempty'] = 'No registry items are available for this view.';
$string['archiveitemcard'] = 'Registry item card';
$string['kristalcard'] = 'Kristal card';
$string['proofcard'] = 'Proof card';
$string['validationpanel'] = 'Validation panel';
$string['archiveactions'] = 'Registry actions';
$string['itemactions'] = 'Item actions';
$string['kristalactions'] = 'Kristal actions';
$string['validationactions'] = 'Validation actions';
$string['exportactions'] = 'Export actions';
$string['viewarchiveitem'] = 'View registry item';
$string['viewkristal'] = 'View Kristal';
$string['viewprovenance'] = 'View provenance';
$string['viewrevisionhistory'] = 'View revision history';
$string['viewvalidation'] = 'View validation';
$string['viewexport'] = 'View export';
$string['emptyarchive'] = 'This registry has no visible items.';
$string['emptykristals'] = 'This registry has no visible Kristals.';
$string['emptyproofs'] = 'No proof records are available.';
$string['emptyrevisions'] = 'No revisions are available.';
$string['emptyexports'] = 'No exports are available.';
$string['restrictednotice'] = 'This item contains restricted registry data.';
$string['publicnotice'] = 'Public registry visibility requires manual validation.';
$string['archivenonsovereignnotice'] = 'Registry records preserve memory and evidence. Validation, integrity decisions, public visibility, and exports require authorised human review.';
$string['archivegovernancenotice'] = 'The UCKK Registrar preserves evidence, decisions, Kristals, portfolios, and version history. It must not be used to silently erase evidence or bypass integrity review.';

// -----------------------------------------------------------------------------
// Controller messages.
// -----------------------------------------------------------------------------

$string['invalidarchiveaction'] = 'Invalid registry action.';
$string['invalidvalidationaction'] = 'Invalid validation action.';
$string['invalidexportaction'] = 'Invalid export action.';
$string['invalidrevisionaction'] = 'Invalid revision action.';
$string['invalidvisibility'] = 'Invalid visibility.';
$string['invalidstatus'] = 'Invalid status.';
$string['invalidprovenance'] = 'Invalid provenance.';
$string['cannotviewarchive'] = 'You cannot view this registry.';
$string['cannotviewrestricted'] = 'You cannot view restricted registry data.';
$string['cannotmanagearchive'] = 'You cannot manage this registry.';
$string['cannotdeleteitem'] = 'You cannot delete this registry item.';
$string['deleteitemnotallowed'] = 'Registry items must be revised or invalidated, not silently deleted.';
$string['itemnotfound'] = 'Registry item not found.';
$string['archivenotfound'] = 'Registry not found.';
$string['kristalnotfound'] = 'Kristal not found.';
$string['exportnotfound'] = 'Export package not found.';
$string['nopermission'] = 'You do not have permission to perform this registry action.';

// -----------------------------------------------------------------------------
// Events.
// -----------------------------------------------------------------------------

$string['eventarchiveitemcreated'] = 'Registry item created';
$string['eventarchiveitemvalidated'] = 'Registry item validated';
$string['eventarchiveitemrevised'] = 'Registry item revised';
$string['eventarchiveitemexported'] = 'Registry item exported';
$string['eventkristalcreated'] = 'Kristal created';
$string['eventkristalupdated'] = 'Kristal updated';
$string['eventarchiveviewed'] = 'Registrar viewed';
$string['eventarchiveitemviewed'] = 'Registry item viewed';
$string['eventexportgenerated'] = 'Registry export generated';

// -----------------------------------------------------------------------------
// Scheduled tasks.
// -----------------------------------------------------------------------------

$string['task:validate_pending_items'] = 'Validate pending registry items';
$string['task:generate_archive_exports'] = 'Generate registry exports';
$string['task:cleanup_expired_exports'] = 'Clean up expired registry exports';

// -----------------------------------------------------------------------------
// External services and Ajax.
// -----------------------------------------------------------------------------

$string['service:get_archive_view'] = 'Get registrar view';
$string['service:get_archive_item'] = 'Get registry item';
$string['service:save_archive_item'] = 'Save registry item';
$string['service:validate_archive_item'] = 'Validate registry item';
$string['service:revise_archive_item'] = 'Revise registry item';
$string['service:create_kristal'] = 'Create Kristal';
$string['service:generate_export'] = 'Generate registry export';

$string['archive:refreshing'] = 'Refreshing registry…';
$string['archive:refreshed'] = 'Registry refreshed.';
$string['archive:refreshfailed'] = 'Unable to refresh registry.';
$string['archive:saving'] = 'Saving registry item…';
$string['archive:saved'] = 'Registry item saved.';
$string['archive:savefailed'] = 'Unable to save registry item.';
$string['archive:validating'] = 'Validating registry item…';
$string['archive:validated'] = 'Registry item validated.';
$string['archive:validationfailed'] = 'Unable to validate registry item.';
$string['archive:exporting'] = 'Generating registry export…';
$string['archive:exported'] = 'Registry export generated.';
$string['archive:exportfailed'] = 'Unable to generate registry export.';

$string['kristal:refreshing'] = 'Refreshing Kristal…';
$string['kristal:refreshed'] = 'Kristal refreshed.';
$string['kristal:refreshfailed'] = 'Unable to refresh Kristal.';
$string['kristal:saving'] = 'Saving Kristal…';
$string['kristal:saved'] = 'Kristal saved.';
$string['kristal:savefailed'] = 'Unable to save Kristal.';

// -----------------------------------------------------------------------------
// Completion.
// -----------------------------------------------------------------------------

$string['completiondetail:items'] = 'Add registry item';
$string['completiondetail:validateditems'] = 'Have validated registry item';
$string['completiondetail:kristals'] = 'Create Kristal';
$string['completionitems'] = 'Registry items required';
$string['completionvalidateditems'] = 'Validated registry items required';
$string['completionkristals'] = 'Kristals required';

// -----------------------------------------------------------------------------
// Privacy.
// -----------------------------------------------------------------------------

$string['privacy:metadata'] = 'The UCKK Registrar activity stores registry records, evidence, provenance, validation decisions, revisions, Kristals, and export records.';
$string['privacy:metadata:uckkarchive'] = 'Registrar activity instance settings.';
$string['privacy:metadata:uckkarchive_item'] = 'Registry items created or validated by users.';
$string['privacy:metadata:uckkarchive_item:userid'] = 'The user associated with the registry item.';
$string['privacy:metadata:uckkarchive_item:createdby'] = 'The user who created the registry item.';
$string['privacy:metadata:uckkarchive_item:modifiedby'] = 'The user who last modified the registry item.';
$string['privacy:metadata:uckkarchive_item:title'] = 'The registry item title.';
$string['privacy:metadata:uckkarchive_item:summary'] = 'The registry item summary.';
$string['privacy:metadata:uckkarchive_item:content'] = 'The registry item content.';
$string['privacy:metadata:uckkarchive_item:status'] = 'The registry item status.';
$string['privacy:metadata:uckkarchive_item:visibility'] = 'The registry item visibility.';
$string['privacy:metadata:uckkarchive_item:metadata'] = 'Additional registry item metadata.';
$string['privacy:metadata:uckkarchive_kristal'] = 'Kristal records created from registry items or learning evidence.';
$string['privacy:metadata:uckkarchive_proof'] = 'Proof records associated with registry items.';
$string['privacy:metadata:uckkarchive_prov'] = 'Provenance records associated with registry items.';
$string['privacy:metadata:uckkarchive_rev'] = 'Revision records associated with registry items.';
$string['privacy:metadata:uckkarchive_export'] = 'Export package records.';
$string['privacy:metadata:files'] = 'Files attached to registry items, proofs, decisions, minutes, Kristals, portfolios, or integrity exports.';
$string['privacy:path:archives'] = 'UCKK registry records';
$string['privacy:path:kristals'] = 'UCKK registry Kristals';
$string['privacy:path:proofs'] = 'UCKK registry proofs';
$string['privacy:path:revisions'] = 'UCKK registry revisions';
$string['privacy:path:exports'] = 'UCKK registry exports';

// -----------------------------------------------------------------------------
// Backup and restore.
// -----------------------------------------------------------------------------

$string['backupincludeitems'] = 'Include registry items';
$string['backupincludeproofs'] = 'Include proof files';
$string['backupincludekristals'] = 'Include Kristals';
$string['backupincludeprovenance'] = 'Include provenance';
$string['backupincluderevisions'] = 'Include revision history';
$string['restorearchiveitems'] = 'Restore registry items';

// -----------------------------------------------------------------------------
// Errors.
// -----------------------------------------------------------------------------

$string['error:missingcontext'] = 'Missing registry context.';
$string['error:missingcourse'] = 'Missing course.';
$string['error:missingcm'] = 'Missing course module.';
$string['error:missingitem'] = 'Missing registry item.';
$string['error:missingarchive'] = 'Missing registry.';
$string['error:missingkristal'] = 'Missing Kristal.';
$string['error:missingexport'] = 'Missing export package.';
$string['error:invalidjson'] = 'Invalid JSON metadata.';
$string['error:invalidsource'] = 'Invalid source reference.';
$string['error:invalidfilearea'] = 'Invalid registry file area.';
$string['error:restricted'] = 'This registry item is restricted.';
$string['error:publicrequiresvalidation'] = 'Public registry items require manual validation.';
$string['error:cannotautomatevalidation'] = 'Registry validation cannot be automated.';
$string['error:cannotdeletehistory'] = 'Registry history cannot be silently deleted.';
$string['error:exporttoolarge'] = 'This export package is too large.';
$string['error:nothingtoexport'] = 'There is nothing to export.';

// -----------------------------------------------------------------------------
// File areas.
// -----------------------------------------------------------------------------

$string['filearea:proof_files'] = 'Proof files';
$string['filearea:decision_attachments'] = 'Decision attachments';
$string['filearea:minutes_files'] = 'Minutes files';
$string['filearea:kristal_files'] = 'Kristal files';
$string['filearea:portfolio_files'] = 'Portfolio files';
$string['filearea:integrity_exports'] = 'Integrity exports';
$string['filearea:item_content'] = 'Registry item content';
$string['filearea:export_packages'] = 'Export packages';

// -----------------------------------------------------------------------------
// Reports and filters.
// -----------------------------------------------------------------------------

$string['filter:itemtype'] = 'Filter by item type';
$string['filter:status'] = 'Filter by status';
$string['filter:visibility'] = 'Filter by visibility';
$string['filter:validationstate'] = 'Filter by validation state';
$string['filter:provenance'] = 'Filter by provenance';
$string['filter:createdby'] = 'Filter by creator';
$string['filter:datefrom'] = 'Date from';
$string['filter:dateto'] = 'Date to';
$string['report:archiveproduction'] = 'Registry production';
$string['report:validateditems'] = 'Validated items';
$string['report:pendingitems'] = 'Pending items';
$string['report:restricteditems'] = 'Restricted items';
$string['report:exports'] = 'Exports';

// -----------------------------------------------------------------------------
// Misc UI.
// -----------------------------------------------------------------------------

$string['confirmvalidate'] = 'Validate this registry item?';
$string['confirmreject'] = 'Reject this registry item?';
$string['confirminvalidate'] = 'Invalidate this registry item?';
$string['confirmrevision'] = 'Create a new revision for this registry item?';
$string['confirmexport'] = 'Generate this registry export?';
$string['confirmpublicvisibility'] = 'Make this registry item public after validation?';
$string['yesvalidate'] = 'Yes, validate';
$string['yesreject'] = 'Yes, reject';
$string['yesinvalidate'] = 'Yes, invalidate';
$string['yesrevise'] = 'Yes, revise';
$string['yesexport'] = 'Yes, export';
// -----------------------------------------------------------------------------
// Inventory additions from missing string scan.
// -----------------------------------------------------------------------------

// General additions.
$string['action:done'] = 'Action completed.';
$string['action:failed'] = 'Action failed.';
$string['action:running'] = 'Action in progress…';
$string['aiassistancemustbedisclosed'] = 'AI assistance must be disclosed.';
$string['aiassisted'] = 'AI assisted';
$string['aigovernance'] = 'AI governance';
$string['ailog'] = 'AI log';
$string['ailogrequired'] = 'An AI log is required.';
$string['aimetadatarequired'] = 'AI metadata is required.';
$string['ainonsovereignnotice'] = 'AI assistance is non-authoritative. Registry and validation decisions require authorised human review.';
$string['aipolicy'] = 'AI policy';
$string['all'] = 'All';
$string['allowailogs'] = 'Allow AI logs';
$string['allowarchiveitems'] = 'Allow registry items';
$string['allowcontestation'] = 'Allow contestation';
$string['allowportfolioitems'] = 'Allow portfolio items';
$string['allowproofs'] = 'Allow proofs';
$string['archivistnotes'] = 'Registrar notes';
$string['atleastonearchivetypeenabled'] = 'At least one registry type must be enabled.';
$string['backtoarchiveitem'] = 'Back to registry item';
$string['badgekeys'] = 'Badge keys';
$string['calendarevent:closes'] = '{$a} closes';
$string['calendarevent:opens'] = '{$a} opens';
$string['cancelexport'] = 'Cancel export';
$string['cancelexportbody'] = 'Cancel this registry export request?';
$string['canonref'] = 'Canon reference';
$string['canonreference'] = 'Canon reference';
$string['competencycodes'] = 'Competency codes';
$string['confirmarchiveaction'] = 'Confirm registry action';
$string['confirmarchiveactionbody'] = 'Confirm that you want to perform this registry action.';
$string['confirmexportbody'] = 'Generate this registry export package?';
$string['confirmkristalsubmit'] = 'Submit Kristal?';
$string['confirmkristalsubmitbody'] = 'Submit this Kristal for the configured registry workflow?';
$string['confirmrestrictedexportbody'] = 'This export may contain restricted registry data. Confirm that you are authorised to continue.';
$string['content'] = 'Content';
$string['contestabilitydays'] = 'Contestability period';
$string['contestabilitydaysinvalid'] = 'The contestability period must be zero or more days.';
$string['contestationallowed'] = 'Contestation allowed';
$string['correctionrequiresrevision'] = 'A correction requires a revision record.';
$string['createversionrecord'] = 'Create version record';
$string['currentstatus'] = 'Current status';
$string['currentvalidationstate'] = 'Current validation state';
$string['currentvisibility'] = 'Current visibility';
$string['defaultaipolicy'] = 'Default AI policy';
$string['defaultitemtype'] = 'Default item type';
$string['defaultprovenance'] = 'Default provenance';
$string['defaultvalidationstate'] = 'Default validation state';
$string['ethicalnotes'] = 'Ethical notes';
$string['evidencepolicy'] = 'Evidence policy';
$string['forcerevisions'] = 'Force revisions';
$string['format'] = 'Format';
$string['general'] = 'General';
$string['generatedat'] = 'Generated at';
$string['includefilesinexports'] = 'Include files in exports';
$string['includerevisionsinexports'] = 'Include revisions in exports';
$string['integrityandai'] = 'Integrity and AI';
$string['integritynotes'] = 'Integrity notes';
$string['integritynotesrequired'] = 'Integrity notes are required.';
$string['integrityrequired'] = 'Integrity review is required.';
$string['integrityreview'] = 'Integrity review';
$string['integritysummary'] = 'Integrity summary';
$string['integritysummaryrequired'] = 'An integrity summary is required.';
$string['invalidarchivecode'] = 'Invalid registry code.';
$string['invalidexportformat'] = 'Invalid export format.';
$string['invalidexportmode'] = 'Invalid export mode.';
$string['invalidexportscope'] = 'Invalid export scope.';
$string['invalidexportvisibility'] = 'Invalid export visibility.';
$string['invalidjsonorlist'] = 'Enter valid JSON or a valid list.';
$string['invalidmetadatajson'] = 'Invalid metadata JSON.';
$string['invalidshortname'] = 'Invalid short name.';
$string['invalidsourcecomponent'] = 'Invalid source component.';
$string['invalidvalidationstate'] = 'Invalid validation state.';
$string['itemcount'] = 'Item count';
$string['itemtype:integrity_summary'] = 'Integrity summary';
$string['itemtype:minutes'] = 'Minutes';
$string['itemtype:public_summary'] = 'Public summary';
$string['itemvalidated'] = 'Item validated';
$string['metadatajson'] = 'Metadata JSON';
$string['nouserarchiveitems'] = 'No user registry items are available.';
$string['originarea'] = 'Origin area';
$string['origincomponent'] = 'Origin component';
$string['originid'] = 'Origin ID';
$string['originrecord'] = 'Origin record';
$string['origintype'] = 'Origin type';
$string['privatefeedback'] = 'Private feedback';
$string['proof'] = 'Proof';
$string['proof_files'] = 'Proof files';
$string['proofrecords'] = 'Proof records';
$string['proofs'] = 'Proofs';
$string['proofs:none'] = 'No proofs are available.';
$string['publicsummary'] = 'Public summary';
$string['publicsummaryrequired'] = 'A public summary is required.';
$string['readyforexport'] = 'Ready for export';
$string['recordid'] = 'Record ID';
$string['redactrestrictedexports'] = 'Redact restricted exports';
$string['requestexport'] = 'Request export';
$string['requestvalidation'] = 'Request validation';
$string['required'] = 'Required';
$string['requiresintegritycase'] = 'Requires integrity case';
$string['requiresrevision'] = 'Requires revision';
$string['restrictednotes'] = 'Restricted notes';
$string['restrictednotesrequired'] = 'Restricted notes are required.';
$string['restrictedvisibletoyou'] = 'Restricted information is visible to you.';
$string['retentionnotes'] = 'Retention notes';
$string['retentionpolicy'] = 'Retention policy';
$string['retentionpolicy:course_lifetime'] = 'Course lifetime';
$string['retentionpolicy:institutional_memory'] = 'Institutional memory';
$string['retentionpolicy:program_lifetime'] = 'Program lifetime';
$string['retentionpolicy:restricted_integrity'] = 'Restricted integrity retention';
$string['revisearchiveitem'] = 'Revise registry item';
$string['revisionandmemory'] = 'Revision and memory';
$string['revisionandretention'] = 'Revision and retention';
$string['revisionhistory'] = 'Revision history';
$string['revisioninstructions'] = 'Revision instructions';
$string['revisioninstructionsrequired'] = 'Revision instructions are required.';
$string['revisionpolicy'] = 'Revision policy';
$string['revisionpolicy:none'] = 'No revision policy';
$string['revisionpolicy:version_every_edit'] = 'Version every edit';
$string['revisionpolicy:version_on_change'] = 'Version on change';
$string['revisionpolicy:version_on_validation'] = 'Version on validation';
$string['savearchiveitem'] = 'Save registry item';
$string['savekristaldraft'] = 'Save Kristal draft';
$string['savevalidationdraft'] = 'Save validation draft';
$string['scope'] = 'Scope';
$string['shortname'] = 'Short name';
$string['sourcetitle'] = 'Source title';
$string['status:pendingreview'] = 'Pending review';
$string['submitkristal'] = 'Submit Kristal';
$string['submitvalidation'] = 'Submit validation';
$string['timecreated'] = 'Time created';
$string['timemodified'] = 'Time modified';
$string['uncertaintynotes'] = 'Uncertainty notes';
$string['updatepreview'] = 'Update preview';
$string['validatearchiveitems'] = 'Validate registry items';
$string['validateditemneedsreviewstate'] = 'Validated items must use a reviewed validation state.';
$string['versionnumber'] = 'Version number';
$string['versionx'] = 'Version {$a}';
$string['visibilityandreview'] = 'Visibility and review';
$string['visibilityconfirmed'] = 'Visibility confirmed';
$string['visibilitymustbeconfirmed'] = 'Visibility must be confirmed.';
$string['visibilitynotes'] = 'Visibility notes';
$string['visibilityreview'] = 'Visibility review';

// Archive item and governance additions.
$string['archiveaddnotice'] = 'Add registry records only when provenance, visibility, and review requirements are clear.';
$string['archiveexport'] = 'Registry export';
$string['archiveexportqueued'] = 'Registry export queued.';
$string['archivegovernance'] = 'Registry governance';
$string['archiveitem:loaded'] = 'Registry item loaded.';
$string['archiveitem:loadfailed'] = 'Unable to load registry item.';
$string['archiveitem:loading'] = 'Loading registry item…';
$string['archiveitemactions'] = 'Registry item actions';
$string['archiveitembody'] = 'Registry item body';
$string['archiveitemcontent'] = 'Registry item content';
$string['archiveitemfiles'] = 'Registry item files';
$string['archiveitemgovernancenotice'] = 'Registry items must preserve provenance, visibility, validation state, and revision history.';
$string['archiveitemidentity'] = 'Registry item identity';
$string['archiveitempolicy'] = 'Registry item policy';
$string['archiveitemrequirescontent'] = 'Registry item content is required.';
$string['archiveitems:none'] = 'No registry items are available.';
$string['archiveitemtitle'] = 'Registry item title';
$string['archiveitemtype'] = 'Registry item type';
$string['archivememorynotice'] = 'Registry memory preserves evidence and decisions; it must not replace review or consent.';
$string['archivemissingidentifiers'] = 'Registry identifiers are missing.';
$string['archivereason'] = 'Registry reason';
$string['archivescope'] = 'Registry scope';
$string['archivescopefield'] = 'Registry scope field';
$string['archivesource'] = 'Registry source';
$string['archivestatus'] = 'Registry status';
$string['archivetype'] = 'Registry type';
$string['archivetype:assembly_memory'] = 'Assembly memory';
$string['archivetype:challenge_output'] = 'Challenge output';
$string['archivetype:course_memory'] = 'Course memory';
$string['archivetype:integrity_memory'] = 'Integrity memory';
$string['archivetype:kristal_library'] = 'Kristal library';
$string['archivetype:portfolio_archive'] = 'Portfolio registry';
$string['archivetype:proof_repository'] = 'Proof repository';
$string['archivevalidation'] = 'Registry validation';
$string['badge:aiassisted'] = 'AI assisted';
$string['badge:contested'] = 'Contested';
$string['badge:invalidated'] = 'Invalidated';
$string['badge:restricted'] = 'Restricted';
$string['badge:validated'] = 'Validated';
$string['notice:aiassisted'] = 'AI assistance was used. Treat this as non-authoritative until reviewed.';
$string['notice:archiveitem'] = 'Registry item notice';
$string['notice:restricted'] = 'This registry record contains restricted information.';

// Kristal additions.
$string['kristalalignment'] = 'Kristal alignment';
$string['kristalbody'] = 'Kristal body';
$string['kristalbodyrequired'] = 'Kristal body is required.';
$string['kristalcontent'] = 'Kristal content';
$string['kristalerror'] = 'Kristal error';
$string['kristalgovernancenotice'] = 'Kristals must preserve provenance, context, visibility, and validation requirements.';
$string['kristalidentity'] = 'Kristal identity';
$string['kristalmissingcontent'] = 'Kristal content is required.';
$string['kristalmissingtitle'] = 'Kristal title is required.';
$string['kristalrefreshed'] = 'Kristal refreshed.';
$string['kristalrefreshfailed'] = 'Unable to refresh Kristal.';
$string['kristalrefreshing'] = 'Refreshing Kristal…';
$string['kristals:none'] = 'No Kristals are available.';
$string['kristalsaved'] = 'Kristal saved.';
$string['kristalsavefailed'] = 'Unable to save Kristal.';
$string['kristalsaving'] = 'Saving Kristal…';
$string['kristalshortname'] = 'Kristal short name';
$string['kristalsubmitfailed'] = 'Unable to submit Kristal.';
$string['kristalsubmitted'] = 'Kristal submitted.';
$string['kristalsubmitting'] = 'Submitting Kristal…';
$string['kristalsummary'] = 'Kristal summary';
$string['kristaltype:canonlink'] = 'Canon link';
$string['kristaltype:concept'] = 'Concept';
$string['kristaltype:decisionmemory'] = 'Decision memory';
$string['kristaltype:definition'] = 'Definition';
$string['kristaltype:principle'] = 'Principle';
$string['kristaltype:proofsynthesis'] = 'Proof synthesis';
$string['kristaltype:synthesis'] = 'Synthesis';

// Validation and provenance additions.
$string['contextverified'] = 'Context verified';
$string['evidencerelationverified'] = 'Evidence relation verified';
$string['provenance:loaded'] = 'Provenance loaded.';
$string['provenance:loadfailed'] = 'Unable to load provenance.';
$string['provenance:loading'] = 'Loading provenance…';
$string['provenancegovernancenotice'] = 'Provenance records must identify origin, transformations, validation state, and limits of authority.';
$string['provenancemustbeverified'] = 'Provenance must be verified.';
$string['provenancenotes'] = 'Provenance notes';
$string['provenancepolicy'] = 'Provenance policy';
$string['provenancerecordcount'] = 'Provenance record count';
$string['provenancerecords'] = 'Provenance records';
$string['provenancerecords:none'] = 'No provenance records are available.';
$string['provenancestatementrequired'] = 'A provenance statement is required.';
$string['provenancevalidation'] = 'Provenance validation';
$string['sourceverified'] = 'Source verified';
$string['validationcriteria'] = 'Validation criteria';
$string['validationgovernancenotice'] = 'Validation decisions must be traceable, human-reviewable, and separate from registry storage.';
$string['validationgrade'] = 'Validation grade';
$string['validationgrademustbeinrange'] = 'The validation grade must be within the allowed range.';
$string['validationrequested'] = 'Validation requested.';
$string['validationstatement'] = 'Validation statement';
$string['validationstatementrequired'] = 'A validation statement is required.';
$string['validationworkflow'] = 'Validation workflow';
$string['validationworkflow:archivist_review'] = 'Registrar review';
$string['validationworkflow:human_review'] = 'Human review';
$string['validationworkflow:integrity_review'] = 'Integrity review';
$string['validationworkflow:none'] = 'No validation workflow';

// Export additions.
$string['export:failed'] = 'Export failed.';
$string['export:noitems:body'] = 'There are no registry items available for this export.';
$string['export:noitems:title'] = 'No items to export';
$string['export:previewfailed'] = 'Unable to load export preview.';
$string['export:previewloaded'] = 'Export preview loaded.';
$string['export:previewloading'] = 'Loading export preview…';
$string['export:started'] = 'Export started.';
$string['export:starting'] = 'Starting export…';
$string['exportarchiveitem'] = 'Export registry item';
$string['exportauditnote'] = 'Export audit note';
$string['exportcancelfailed'] = 'Unable to cancel export.';
$string['exportcancelled'] = 'Export cancelled.';
$string['exportconfirmpolicy'] = 'Confirm export policy';
$string['exportconfirmpolicyrequired'] = 'You must confirm the export policy.';
$string['exportdescription'] = 'Export description';
$string['exporterror'] = 'Export error';
$string['exporterror:missingarchive'] = 'The registry for this export could not be found.';
$string['exportformat:html'] = 'HTML';
$string['exportformat:mbz_manifest'] = 'Moodle backup manifest';
$string['exportgovernance'] = 'Export governance';
$string['exportgovernancenotice'] = 'Exports must respect provenance, visibility, integrity restrictions, and privacy requirements.';
$string['exportincludefiles'] = 'Include files';
$string['exportincludehashes'] = 'Include hashes';
$string['exportincludeintegritysummary'] = 'Include integrity summary';
$string['exportincludekristals'] = 'Include Kristals';
$string['exportincludemetadata'] = 'Include metadata';
$string['exportincludeprivatefields'] = 'Include private fields';
$string['exportincludeversions'] = 'Include versions';
$string['exportitemids'] = 'Export item IDs';
$string['exportitemidsrequired'] = 'Select at least one registry item to export.';
$string['exportmissingidentifiers'] = 'Export identifiers are missing.';
$string['exportmode'] = 'Export mode';
$string['exportmode:immediate'] = 'Immediate';
$string['exportmode:queued'] = 'Queued';
$string['exportnotice'] = 'Export notice';
$string['exportnotice_desc'] = 'Explain how registry exports should be reviewed, redacted, and used.';
$string['exportoptions'] = 'Export options';
$string['exportpackagename'] = 'Export package name';
$string['exportpolicy'] = 'Export policy';
$string['exportpolicy:full_with_revisions'] = 'Full export with revisions';
$string['exportpolicy:none'] = 'No export policy';
$string['exportpolicy:public_only'] = 'Public items only';
$string['exportpolicy:restricted_redacted'] = 'Restricted items, redacted';
$string['exportpolicy:validated_only'] = 'Validated items only';
$string['exportpollingstopped'] = 'Export status polling stopped.';
$string['exportpreparing'] = 'Preparing export…';
$string['exportpreview'] = 'Export preview';
$string['exportprivacy'] = 'Export privacy';
$string['exportprovenance'] = 'Export provenance';
$string['exportready'] = 'Export ready.';
$string['exportreasonrequired'] = 'An export reason is required.';
$string['exportredactpersonaldata'] = 'Redact personal data';
$string['exportrefreshed'] = 'Export refreshed.';
$string['exportrefreshfailed'] = 'Unable to refresh export.';
$string['exportrefreshing'] = 'Refreshing export…';
$string['exportrestrictednotallowed'] = 'Restricted registry data cannot be included in this export.';
$string['exports'] = 'Exports';
$string['exports:none'] = 'No exports are available.';
$string['exportscope:portfolio'] = 'Portfolio';
$string['exportscope:publicitems'] = 'Public items';
$string['exportscope:restrictedintegrity'] = 'Restricted integrity items';
$string['exportscope:selecteditems'] = 'Selected items';
$string['exportscope:validateditems'] = 'Validated items';
$string['exportstatusfilter'] = 'Export status filter';
$string['exportsummary'] = 'Export summary';
$string['exporttimefrom'] = 'Export time from';
$string['exporttimeto'] = 'Export time to';
$string['exporttimetomustbeafterfrom'] = 'The export end time must be after the start time.';
$string['exporttypefilter'] = 'Export type filter';
$string['exportunredactednotallowed'] = 'Unredacted restricted registry data cannot be exported.';

// Settings additions.
$string['settings:ai'] = 'AI settings';
$string['settings:ai_desc'] = 'Configure AI assistance, AI validation boundaries, uncertainty labels, and AI-use logging.';
$string['settings:allowaiassistance'] = 'Allow AI assistance';
$string['settings:allowaiassistance_desc'] = 'Allow AI assistance in registry workflows while keeping final authority with authorised users.';
$string['settings:allowaivalidation'] = 'Allow AI validation support';
$string['settings:allowaivalidation_desc'] = 'Allow AI to support validation review without making authoritative decisions.';
$string['settings:allowpublicitems'] = 'Allow public registry items';
$string['settings:allowpublicitems_desc'] = 'Allow registry items to become public when validation and visibility requirements are met.';
$string['settings:blockrestrictedexports'] = 'Block restricted exports';
$string['settings:blockrestrictedexports_desc'] = 'Prevent exports from including restricted registry data unless explicitly allowed.';
$string['settings:defaultexportformat'] = 'Default export format';
$string['settings:defaultexportformat_desc'] = 'Default format used for new registry export requests.';
$string['settings:defaultprovenance'] = 'Default provenance';
$string['settings:defaultprovenance_desc'] = 'Default provenance assigned to new registry records when no specific value is provided.';
$string['settings:defaultvalidationstate'] = 'Default validation state';
$string['settings:defaultvalidationstate_desc'] = 'Default validation state assigned to new registry records.';
$string['settings:enabled'] = 'Enable UCKK Registrar';
$string['settings:enabled_desc'] = 'Enable UCKK Registrar activity features.';
$string['settings:enablerevisions'] = 'Enable revisions';
$string['settings:enablerevisions_desc'] = 'Allow registry items and Kristals to keep revision history.';
$string['settings:enablevalidation'] = 'Enable validation';
$string['settings:enablevalidation_desc'] = 'Enable validation workflows for registry records.';
$string['settings:export'] = 'Export settings';
$string['settings:export_desc'] = 'Configure registry export behaviour and limits.';
$string['settings:generateexports'] = 'Generate exports';
$string['settings:generateexports_desc'] = 'Allow queued registry export packages to be generated by scheduled tasks.';
$string['settings:includefilesinexports'] = 'Include files in exports';
$string['settings:includefilesinexports_desc'] = 'Include attached files in registry export packages when permitted.';
$string['settings:itempolicy'] = 'Item policy';
$string['settings:itempolicy_desc'] = 'Configure registry item creation, protection, visibility, and revision rules.';
$string['settings:kristal'] = 'Kristal settings';
$string['settings:kristal_desc'] = 'Configure Kristal creation, validation, and limits.';
$string['settings:kristalsrequirevalidation'] = 'Kristals require validation';
$string['settings:kristalsrequirevalidation_desc'] = 'Require Kristals to be validated before they are treated as verified registry records.';
$string['settings:lockvalidateditems'] = 'Lock validated items';
$string['settings:lockvalidateditems_desc'] = 'Prevent direct editing of validated registry items unless a revision workflow is used.';
$string['settings:logaiuse'] = 'Log AI use';
$string['settings:logaiuse_desc'] = 'Record AI assistance metadata for registry transparency and review.';
$string['settings:maxkristalitems'] = 'Maximum Kristals';
$string['settings:maxkristalitems_desc'] = 'Maximum number of Kristals that can be created for one registry context.';
$string['settings:pausevalidationonintegritycase'] = 'Pause validation during integrity cases';
$string['settings:pausevalidationonintegritycase_desc'] = 'Pause registry validation when an associated integrity case is open.';
$string['settings:protectrestricteditems'] = 'Protect restricted items';
$string['settings:protectrestricteditems_desc'] = 'Apply additional safeguards to restricted registry items.';
$string['settings:requireaiuncertaintylabel'] = 'Require AI uncertainty label';
$string['settings:requireaiuncertaintylabel_desc'] = 'Require AI-assisted outputs to disclose uncertainty and non-authority boundaries.';
$string['settings:requirechangereason'] = 'Require change reason';
$string['settings:requirechangereason_desc'] = 'Require users to explain changes to registry records.';
$string['settings:requirecontext'] = 'Require context';
$string['settings:requirecontext_desc'] = 'Require contextual information for registry records and Kristals.';
$string['settings:requirehumanvalidation'] = 'Require human validation';
$string['settings:requirehumanvalidation_desc'] = 'Require authorised human review before registry records are treated as validated.';
$string['settings:requirevisibility'] = 'Require visibility selection';
$string['settings:requirevisibility_desc'] = 'Require users to select an explicit visibility level for registry records.';
$string['settings:taskbatchsize'] = 'Task batch size';
$string['settings:taskbatchsize_desc'] = 'Maximum number of registry records processed by each scheduled task run.';
$string['settings:tasks'] = 'Scheduled tasks';
$string['settings:tasks_desc'] = 'Configure scheduled registry maintenance, validation, and export tasks.';
$string['settings:validatependingitems'] = 'Validate pending items';
$string['settings:validatependingitems_desc'] = 'Allow scheduled tasks to prepare pending registry items for validation review.';
$string['settings:validation'] = 'Validation settings';
$string['settings:validation_desc'] = 'Configure registry validation workflow, review requirements, and safeguards.';

// Completion, privacy, and task additions.
$string['completionarchiveexported_desc'] = 'Require the student to export a registry package.';
$string['completionarchivestate_desc'] = 'Require the registry to reach the selected state.';
$string['completionarchivevalidated_desc'] = 'Require the registry to contain a validated item.';
$string['completionitemadded_desc'] = 'Require the student to add a registry item.';
$string['completionitemvalidated_desc'] = 'Require the student to have a registry item validated.';
$string['completionkristalcreated_desc'] = 'Require the student to create a Kristal.';
$string['privacy:deleted'] = 'This registry record has been deleted.';
$string['resetarchivespreserved'] = 'Registry records are preserved during reset.';
$string['task:validation_correction_reason'] = 'Automatic validation marked this item as requiring correction.';
$string['task:validation_ready_reason'] = 'Automatic validation marked this item as ready for review.';
$string['task_generate_archive_exports'] = 'Generate registry exports';
$string['useroutline'] = 'Registrar activity contribution';

// -----------------------------------------------------------------------------
// Media, content advisory, external work, and service additions.
// -----------------------------------------------------------------------------
$string['actor'] = 'Actor';
$string['addcollection'] = 'Add collection';
$string['addcontentmarker'] = 'Add content marker';
$string['addmedia'] = 'Add media';
$string['addmediarelation'] = 'Add media relation';
$string['addmediaversion'] = 'Add media version';
$string['addtocollection'] = 'Add to collection';
$string['advisoryhintrequired'] = 'An advisory hint is required.';
$string['advisoryseverity'] = 'Advisory severity';
$string['advisoryseverity:moderate'] = 'Moderate';
$string['advisoryseverity:notice'] = 'Notice';
$string['advisoryseverity:restricted'] = 'Restricted';
$string['advisoryseverity:strong'] = 'Strong';
$string['aiassistancedisclosed'] = 'AI assistance disclosed';
$string['aiprovencenotice'] = 'AI assistance must not replace provenance review.';
$string['allstatuses'] = 'All statuses';
$string['allvalidationstates'] = 'All validation states';
$string['archived'] = 'Preserved';
$string['archivefilters'] = 'Registry filters';
$string['archivestats'] = 'Registry statistics';
$string['archivesummary'] = 'Registry summary';
$string['attentionrequired'] = 'Attention required';
$string['audience'] = 'Audience';
$string['audience:general'] = 'General';
$string['audience:guided'] = 'Guided';
$string['audience:mature'] = 'Mature';
$string['audience:restricted'] = 'Restricted';
$string['audience:restricted_cultural'] = 'Restricted cultural';
$string['audience:restricted_integrity'] = 'Restricted integrity';
$string['audience:staff_only'] = 'Staff only';
$string['audiencesuitability'] = 'Audience suitability';
$string['audio'] = 'Audio';
$string['author'] = 'Author';
$string['by'] = 'by';
$string['citation'] = 'Citation';
$string['clearfilters'] = 'Clear filters';
$string['collection'] = 'Collection';
$string['collections'] = 'Collections';
$string['confirmdeletemedia'] = 'Delete this media item?';
$string['contentadvisories'] = 'Content advisories';
$string['contentadvisory'] = 'Content advisory';
$string['contentadvisory:title'] = 'Content advisory';
$string['contentadvisorycount'] = 'Content advisory count: {$a}';
$string['contentadvisoryhints'] = 'Content advisory hints';
$string['contentadvisoryseverity'] = 'Content advisory severity';
$string['contenthash'] = 'Content hash';
$string['contentmarkercount'] = 'Content marker count: {$a}';
$string['contentmarkerrequired'] = 'Select a content marker.';
$string['contentmarkers'] = 'Content markers';
$string['contentreview'] = 'Content review';
$string['contentreview:culturalprotocol_help'] = 'Explain any cultural protocol obligations that affect review.';
$string['contentreview:restricted_help'] = 'Explain why this marker should be treated as restricted.';
$string['contentreviewfiles'] = 'Review files';
$string['contentreviewnote'] = 'Review note';
$string['contentreviewrationale'] = 'Review rationale';
$string['contentreviewrationalerequired'] = 'A review rationale is required.';
$string['contentreviewrestrictedrationalerequired'] = 'A rationale is required for restricted content reviews.';
$string['contentreviewstate'] = 'Review state';
$string['contenttag:active'] = 'Active';
$string['contenttag:active_desc'] = 'Active.';
$string['contenttag:advisory'] = 'Advisory';
$string['contenttag:category'] = 'Category';
$string['contenttag:defaultaudience'] = 'Defaultaudience';
$string['contenttag:description'] = 'Contenttag.';
$string['contenttag:error:invalidaudience'] = 'Error:invalidaudience';
$string['contenttag:error:invalidcategory'] = 'Error:invalidcategory';
$string['contenttag:error:invalidmetadata'] = 'Error:invalidmetadata';
$string['contenttag:error:invalidreviewstate'] = 'Error:invalidreviewstate';
$string['contenttag:error:invalidseverity'] = 'Error:invalidseverity';
$string['contenttag:error:invalidtagkey'] = 'Error:invalidtagkey';
$string['contenttag:identity'] = 'Identity';
$string['contenttag:iscultural'] = 'Iscultural';
$string['contenttag:iscultural_desc'] = 'Iscultural.';
$string['contenttag:label'] = 'Label';
$string['contenttag:metadata'] = 'Metadata';
$string['contenttag:metadatajson'] = 'Metadatajson';
$string['contenttag:restrictsdefault'] = 'Restrictsdefault';
$string['contenttag:restrictsdefault_desc'] = 'Restrictsdefault.';
$string['contenttag:review'] = 'Review';
$string['contenttag:reviewstate'] = 'Reviewstate';
$string['contenttag:severity'] = 'Severity';
$string['contenttag:sortorder'] = 'Sortorder';
$string['contenttag:tag'] = 'Tag';
$string['contenttag:tagkey'] = 'Tagkey';
$string['contenttag:tagset'] = 'Tagset';
$string['contentwarnings'] = 'Content warnings';
$string['culturallyrestricted'] = 'Culturally restricted';
$string['culturalprotocol'] = 'Cultural protocol';
$string['culturalprotocolnote'] = 'Cultural protocol note';
$string['culturalprotocolnoterequired'] = 'A cultural protocol note is required.';
$string['culturalprotocolrequired'] = 'A cultural protocol note is required.';
$string['culturalprotocols'] = 'Cultural protocols';
$string['delete'] = 'Delete';
$string['deleted'] = 'Deleted';
$string['document'] = 'Document';
$string['event:archiveviewed'] = 'Registrar viewed';
$string['event:contentmarkercreated'] = 'Content marker created';
$string['event:contentmarkerreviewed'] = 'Content marker reviewed';
$string['event:externalworkcreated'] = 'External work created';
$string['event:mediacreated'] = 'Media created';
$string['event:mediaupdated'] = 'Media updated';
$string['event:mediaversioncreated'] = 'Media version created';
$string['eventcontentmarkercreated'] = 'Content marker created';
$string['eventcontentmarkerreviewed'] = 'Content marker reviewed';
$string['eventexternalworkcreated'] = 'External work created';
$string['eventmediacollectioncreated'] = 'Media collection created';
$string['eventmediacreated'] = 'Media created';
$string['eventmediaexported'] = 'Media exported';
$string['eventmediaupdated'] = 'Media updated';
$string['eventmediaversioncreated'] = 'Media version created';
$string['exportmedia'] = 'Export media';
$string['externalreference'] = 'External reference';
$string['mediaexternalreference'] = 'External reference';
$string['mediaexternalurl'] = 'External URL';
$string['mediaopenexternal'] = 'Open external reference';
$string['externalwork'] = 'External work';
$string['externalworkcitation'] = 'Citation';
$string['externalworkcreator'] = 'Creator';
$string['externalworkculturalprotocolnote'] = 'Cultural protocol note';
$string['externalworkdescription'] = 'Description';
$string['externalworkgovernance'] = 'External work governance';
$string['externalworkid'] = 'External work ID';
$string['externalworkidentifier'] = 'Identifier';
$string['externalworkidentifiertype'] = 'Identifier type';
$string['externalworkidentity'] = 'External work identity';
$string['externalworklanguage'] = 'Language';
$string['externalworklicensekey'] = 'Licence key';
$string['externalworklicenserequired'] = 'A licence is required.';
$string['externalworknote'] = 'External work note';
$string['externalworkpublicationyear'] = 'Publication year';
$string['externalworkpublisher'] = 'Publisher';
$string['externalworkreference'] = 'External work reference';
$string['externalworkreferencerequired'] = 'An external work reference is required.';
$string['externalworkrestrictionnoterequired'] = 'A restriction note is required.';
$string['externalworkrights'] = 'Rights';
$string['externalworkrightsstatement'] = 'Rights statement';
$string['externalworkrightsstatementrequired'] = 'A rights statement is required.';
$string['externalworkrightsstatus'] = 'Rights status';
$string['externalworksource'] = 'Source';
$string['externalworksourcenote'] = 'Source note';
$string['externalworksourceurl'] = 'Source URL';
$string['externalworksubtitle'] = 'Subtitle';
$string['externalworkteachingandprotocol'] = 'Teaching and protocol';
$string['externalworkteachingnote'] = 'Teaching note';
$string['externalworktitle'] = 'External work title';
$string['externalworktype'] = 'External work type';
$string['externalworktype:article'] = 'Article';
$string['externalworktype:book'] = 'Book';
$string['externalworktype:external_image'] = 'External image';
$string['externalworktype:external_video'] = 'External video';
$string['externalworktype:film'] = 'Film';
$string['externalworktype:other'] = 'Other';
$string['externalworktype:podcast'] = 'Podcast';
$string['externalworktype:public_archive_item'] = 'Public registry item';
$string['externalworktype:third_party_pdf'] = 'Third party pdf';
$string['externalworktype:website'] = 'Website';
$string['externalworkyear'] = 'External work year';
$string['filearea'] = 'File area';
$string['filearea:media_attachment'] = 'Media attachment';
$string['filearea:media_caption'] = 'Media caption';
$string['filearea:media_derivative'] = 'Media derivative';
$string['filearea:media_original'] = 'Media original';
$string['filearea:media_preview'] = 'Media preview';
$string['filearea:media_thumbnail'] = 'Media thumbnail';
$string['filearea:media_transcript'] = 'Media transcript';
$string['filename'] = 'Filename';
$string['filesize'] = 'File size';
$string['identifier'] = 'Identifier';
$string['identifiertype:accession_number'] = 'Accession number';
$string['identifiertype:archive_identifier'] = 'Registry identifier';
$string['identifiertype:catalogue_number'] = 'Catalogue number';
$string['identifiertype:doi'] = 'Doi';
$string['identifiertype:isbn'] = 'Isbn';
$string['identifiertype:issn'] = 'Issn';
$string['identifiertype:local_identifier'] = 'Local identifier';
$string['identifiertype:other'] = 'Other';
$string['identifiertype:uri'] = 'Uri';
$string['identifiertype:url'] = 'Url';
$string['image'] = 'Image';
$string['integrity'] = 'Integrity';
$string['integrityrestricted'] = 'Integrity restricted';
$string['integrityreviewrequired'] = 'Integrity review required';
$string['internalnote'] = 'Internal note';
$string['invalidaudiencesuitability'] = 'Invalid audience suitability.';
$string['invalidexternalworkyear'] = 'Enter a valid publication year.';
$string['invalidjson'] = 'Invalid JSON.';
$string['invalidmetadata'] = 'Invalid metadata.';
$string['invalidseverity'] = 'Invalid severity.';
$string['invalidstate'] = 'Invalid state.';
$string['invalidtaglist'] = 'Invalid tag list.';
$string['makecurrent'] = 'Make current';
$string['manageadvisories'] = 'Manageadvisories';
$string['media'] = 'Media';
$string['media:alttext'] = 'Alternative text';
$string['media:alttext_help'] = 'Describe the media for accessibility.';
$string['media:audiencesuitability'] = 'Audience suitability';
$string['media:caption'] = 'Caption';
$string['media:license'] = 'Licence';
$string['media:rightsnote'] = 'Rights note';
$string['media:source'] = 'Source';
$string['media:type'] = 'Media type';
$string['mediaadvisoryhint'] = 'Advisory hint';
$string['mediaalttext'] = 'Alternative text';
$string['mediacitation'] = 'Citation';
$string['mediacollection:noitems'] = 'This collection has no media items.';
$string['mediacollectionhint'] = 'Collection hint';
$string['mediacollections'] = 'Media collections';
$string['mediacreator'] = 'Creator';
$string['mediadatecreated'] = 'Date created';
$string['mediadescription'] = 'Media description';
$string['mediafile'] = 'Media file';
$string['mediafilearea'] = 'Media file area';
$string['mediafiles'] = 'Media files';
$string['mediagovernance'] = 'Media governance';
$string['mediahascontentadvisory'] = 'This media has content advisories';
$string['mediaid'] = 'Media ID';
$string['mediaidentity'] = 'Media identity';
$string['mediaitems'] = 'Media items';
$string['medialanguage'] = 'Language';
$string['medialibrary'] = 'Media library';
$string['medialibraryerror'] = 'Unable to load the media library.';
$string['medialicense'] = 'Media licence';
$string['mediarelation'] = 'Media relation';
$string['mediarelationfromid'] = 'Mediarelationfromid';
$string['mediarelationfromtype'] = 'Mediarelationfromtype';
$string['mediarelationidentity'] = 'Mediarelationidentity';
$string['mediarelationinvalidtargettype'] = 'Mediarelationinvalidtargettype';
$string['mediarelationnote'] = 'Mediarelationnote';
$string['mediarelationobject:archive_item'] = 'Registry item';
$string['mediarelationobject:content_marker'] = 'Content marker';
$string['mediarelationobject:external_work'] = 'External work';
$string['mediarelationobject:kristal'] = 'Kristal';
$string['mediarelationobject:media'] = 'Media';
$string['mediarelationobject:media_collection'] = 'Media collection';
$string['mediarelationobject:media_collection_item'] = 'Media collection item';
$string['mediarelationobject:media_version'] = 'Media version';
$string['mediarelationobject:proof'] = 'Proof';
$string['mediarelationrequiresmediaobjects'] = 'Mediarelationrequiresmediaobjects';
$string['mediarelationrequiresmediaobjectsource'] = 'Mediarelationrequiresmediaobjectsource';
$string['mediarelations'] = 'Media relations';
$string['mediarelationselfnotallowed'] = 'Mediarelationselfnotallowed';
$string['mediarelationtoid'] = 'Mediarelationtoid';
$string['mediarelationtotype'] = 'Mediarelationtotype';
$string['mediarelationtype'] = 'Mediarelationtype';
$string['mediarelationtype:belongs_to_collection'] = 'Belongs to collection';
$string['mediarelationtype:belongs_to_item'] = 'Belongs to item';
$string['mediarelationtype:belongs_to_kristal'] = 'Belongs to kristal';
$string['mediarelationtype:contains_content_marker'] = 'Contains content marker';
$string['mediarelationtype:duplicates'] = 'Duplicates';
$string['mediarelationtype:is_derivative_of'] = 'Is derivative of';
$string['mediarelationtype:is_excerpt_of'] = 'Is excerpt of';
$string['mediarelationtype:is_proof_for'] = 'Is proof for';
$string['mediarelationtype:is_source_for'] = 'Is source for';
$string['mediarelationtype:is_translation_of'] = 'Is translation of';
$string['mediarelationtype:references'] = 'References';
$string['mediarelationtype:references_external_work'] = 'References external work';
$string['mediarelationtype:replaces'] = 'Replaces';
$string['mediarightsnote'] = 'Rights note';
$string['mediasource'] = 'Media source';
$string['mediasource:external_reference_only'] = 'External reference only';
$string['mediasource:fair_use_reference'] = 'Fair use reference';
$string['mediasource:imported'] = 'Imported';
$string['mediasource:licensed_external'] = 'Licensed external';
$string['mediasource:produced_by_uckk'] = 'Produced by UCKK';
$string['mediasource:public_domain'] = 'Public domain';
$string['mediasource:restricted_reference'] = 'Restricted reference';
$string['mediasource:submitted_to_uckk'] = 'Submitted to UCKK';
$string['mediasourceownership'] = 'Source ownership';
$string['mediasourcetype'] = 'Source type';
$string['mediasourceurl'] = 'Source URL';
$string['mediastatus'] = 'Media status';
$string['mediatags'] = 'Media tags';
$string['mediatitle'] = 'Media title';
$string['mediatranscriptsummary'] = 'Transcript summary';
$string['mediatype'] = 'Media type';
$string['mediatype:attachment'] = 'Attachment';
$string['mediatype:audio'] = 'Audio';
$string['mediatype:caption'] = 'Caption';
$string['mediatype:derivative'] = 'Derivative';
$string['mediatype:document'] = 'Document';
$string['mediatype:external'] = 'External';
$string['mediatype:image'] = 'Image';
$string['mediatype:other'] = 'Other';
$string['mediatype:pdf'] = 'Pdf';
$string['mediatype:preview'] = 'Preview';
$string['mediatype:thumbnail'] = 'Thumbnail';
$string['mediatype:transcript'] = 'Transcript';
$string['mediatype:video'] = 'Video';
$string['mediaupload:acceptedtypes'] = 'Accepted file types';
$string['mediaupload:access'] = 'Access';
$string['mediaupload:advisorylater'] = 'Content advisories can be added after upload.';
$string['mediaupload:description'] = 'Upload a media file and its governance metadata.';
$string['mediaupload:dropfile'] = 'Drop file here or choose a file.';
$string['mediaupload:file'] = 'File';
$string['mediaupload:isversionupload'] = 'This upload creates a new version.';
$string['mediaupload:maxbytes'] = 'Maximum file size';
$string['mediaupload:metadata'] = 'Metadata';
$string['mediaupload:needsadvisory'] = 'This media may need a content advisory.';
$string['mediaupload:newversion'] = 'Upload new version';
$string['mediaupload:nopermission'] = 'You do not have permission to upload media.';
$string['mediaupload:rights'] = 'Rights';
$string['mediaupload:save'] = 'Save media';
$string['mediaupload:saveversion'] = 'Save version';
$string['mediaupload:title'] = 'Upload media';
$string['mediaupload:versioning'] = 'Versioning';
$string['mediaupload:versionnote'] = 'Version note';
$string['mediaversions'] = 'Media versions';
$string['metadatakeyvalues'] = 'Metadata key/value pairs';
$string['mimetype'] = 'MIME type';
$string['nocontentadvisories'] = 'No content advisories';
$string['nofilteredrecords'] = 'No records match the current filters.';
$string['nomediacollections'] = 'No media collections are available.';
$string['nomediafound'] = 'No media found.';
$string['nomediarelations'] = 'No media relations are available.';
$string['nomediaversions'] = 'No media versions are available.';
$string['nopermissiontoaddmedia'] = 'You do not have permission to add media.';
$string['nopermissiontoeditmedia'] = 'You do not have permission to edit media.';
$string['norelations'] = 'Norelations';
$string['noversionfiles'] = 'This version has no files.';
$string['origin'] = 'Origin';
$string['passed'] = 'Passed';
$string['primarysource'] = 'Primary source';
$string['proofcontent'] = 'Proof content';
$string['proofgovernance'] = 'Proof governance';
$string['provenancechain'] = 'Provenance chain';
$string['provenancehashes'] = 'Provenance hashes';
$string['purgeexpiredexports'] = 'Purge expired exports';
$string['purpose'] = 'Purpose';
$string['rebuildcontentmarkerindex'] = 'Rebuild content marker index';
$string['recordsvisible'] = 'Records visible';
$string['redacted'] = 'Redacted';
$string['refresharchive'] = 'Refresh registry';
$string['relatedrecords'] = 'Related records';
$string['relationcount'] = 'Relation count: {$a}';
$string['relations'] = 'Relations';
$string['relationtype'] = 'Relation type';
$string['remove'] = 'Remove';
$string['requestmediareview'] = 'Request media review';
$string['requirescontextnotice'] = 'Context notice required';
$string['restrictedcontent'] = 'Restricted content';
$string['restrictedcontentnotice'] = 'This record contains restricted content.';
$string['restrictedculturalcontent'] = 'Restricted cultural content';
$string['restricteddata'] = 'Restricted data';
$string['restricteddatapresent'] = 'Restricted data present';
$string['restrictedmedia'] = 'Restricted media';
$string['restrictednote'] = 'Restricted note';
$string['restrictedproofnotice'] = 'This proof contains restricted information.';
$string['restrictedtarget'] = 'Restricted target';
$string['review'] = 'Review';
$string['reviewedby'] = 'Reviewed by';
$string['rightsnote'] = 'Rights note';
$string['rightsstatement'] = 'Rights statement';
$string['rightsstatus'] = 'Rights status';
$string['rightsstatus:fair_use_reference'] = 'Fair use reference';
$string['rightsstatus:licensed_external'] = 'Licensed external';
$string['rightsstatus:open_license'] = 'Open license';
$string['rightsstatus:public_domain'] = 'Public domain';
$string['rightsstatus:restricted_reference'] = 'Restricted reference';
$string['rightsstatus:third_party_copyright'] = 'Third party copyright';
$string['rightsstatus:unknown'] = 'Unknown';
$string['saveexternalwork'] = 'Save external work';
$string['savemedia'] = 'Save media';
$string['savemediarelation'] = 'Save media relation';
$string['searcharchive'] = 'Search registry';
$string['searcharchiveplaceholder'] = 'Search registry records';
$string['service:add_content_marker'] = 'Add content marker';
$string['service:add_external_work'] = 'Add external work';
$string['service:add_media'] = 'Add media';
$string['service:add_media_collection'] = 'Add media collection';
$string['service:add_media_relation'] = 'Add media relation';
$string['service:add_media_to_collection'] = 'Add media to collection';
$string['service:add_media_version'] = 'Add media version';
$string['service:delete_content_marker'] = 'Delete content marker';
$string['service:delete_media'] = 'Delete media';
$string['service:export_collection'] = 'Export collection';
$string['service:export_media'] = 'Export media';
$string['service:get_content_markers'] = 'Get content markers';
$string['service:get_content_tag_sets'] = 'Get content tag sets';
$string['service:get_content_tags'] = 'Get content tags';
$string['service:get_external_work'] = 'Get external work';
$string['service:get_external_works'] = 'Get external works';
$string['service:get_media'] = 'Get media';
$string['service:get_media_card'] = 'Get media card';
$string['service:get_media_collection'] = 'Get media collection';
$string['service:get_media_collections'] = 'Get media collections';
$string['service:get_media_item'] = 'Get media item';
$string['service:get_media_relations'] = 'Get media relations';
$string['service:get_media_versions'] = 'Get media versions';
$string['service:remove_media_from_collection'] = 'Remove media from collection';
$string['service:remove_media_relation'] = 'Remove media relation';
$string['service:review_content_marker'] = 'Review content marker';
$string['service:search_media'] = 'Search media';
$string['service:tag_media'] = 'Tag media';
$string['service:untag_media'] = 'Untag media';
$string['service:update_content_marker'] = 'Update content marker';
$string['service:update_external_work'] = 'Update external work';
$string['service:update_media'] = 'Update media';
$string['service:update_media_collection'] = 'Update media collection';
$string['sortorder'] = 'Sort order';
$string['sourcenote'] = 'Source note';
$string['sourceownership:external_reference'] = 'External reference';
$string['sourceownership:member_submitted'] = 'Member submitted';
$string['sourceownership:open_license'] = 'Open license';
$string['sourceownership:partner_submitted'] = 'Partner submitted';
$string['sourceownership:public_domain'] = 'Public domain';
$string['sourceownership:third_party_copyright'] = 'Third party copyright';
$string['sourceownership:uckk_commissioned'] = 'UCKK commissioned';
$string['sourceownership:uckk_created'] = 'UCKK created';
$string['sourceownership:unknown_source'] = 'Unknown source';
$string['sources'] = 'Sources';
$string['status:deleted_soft'] = 'Deleted soft';
$string['status:restricted'] = 'Restricted';
$string['status:submitted'] = 'Submitted';
$string['status:superseded'] = 'Superseded';
$string['targetid'] = 'Target ID';
$string['targettype'] = 'Target type';
$string['task:generatemediaderivatives'] = 'Generate media derivatives';
$string['task:generatemediathumbnails'] = 'Generate media thumbnails';
$string['task:purgeexpiredexports'] = 'Purge expired exports';
$string['task:rebuildcontentmarkerindex'] = 'Rebuild content marker index';
$string['task_rebuild_media_search'] = 'Rebuild media search index';
$string['taskgeneratemediathumbnails'] = 'Generate media thumbnails';
$string['teachingcontext'] = 'Teaching context';
$string['teachingnote'] = 'Teaching note';
$string['time'] = 'Time';
$string['toggledetails'] = 'Toggle details';
$string['uckkarchive:addmedia'] = 'Add Médiathèque media';
$string['uckkarchive:deletemedia'] = 'Delete Médiathèque media';
$string['uckkarchive:editmedia'] = 'Edit Médiathèque media';
$string['uckkarchive:exportmedia'] = 'Export Médiathèque media';
$string['uckkarchive:manageadvisories'] = 'Manage content advisories';
$string['uckkarchive:manageexternalworks'] = 'Manage external works';
$string['uckkarchive:managemediacollections'] = 'Manage media collections';
$string['uckkarchive:reviewadvisories'] = 'Review content advisories';
$string['uckkarchive:versionmedia'] = 'Create media versions';
$string['uckkarchive:viewadvisories'] = 'View content advisories';
$string['uckkarchive:viewmedia'] = 'View Médiathèque media';
$string['validationchecks'] = 'Validation checks';
$string['validationevidence'] = 'Validation evidence';
$string['validationreason'] = 'Validation reason';
$string['versions'] = 'Versions';
$string['video'] = 'Video';
$string['viewintegrityrecord'] = 'View integrity record';
$string['viewsource'] = 'View source';
$string['visibility:restricted_cultural'] = 'Restricted cultural';

// -----------------------------------------------------------------------------
// Canonical option labels and missing capability strings added for media/advisory integration.
// -----------------------------------------------------------------------------

$string['itemtype_challenge_result'] = 'Challenge result';
$string['itemtype_course_work'] = 'Course work';
$string['itemtype_decision'] = 'Decision';
$string['itemtype_integrity_summary'] = 'Integrity summary';
$string['itemtype_kristal'] = 'Kristal';
$string['itemtype_minutes'] = 'Minutes';
$string['itemtype_portfolio_item'] = 'Portfolio item';
$string['itemtype_proof'] = 'Proof';
$string['itemtype_public_summary'] = 'Public summary';
$string['mediastatus_active'] = 'Active';
$string['mediastatus_archived'] = 'Preserved';
$string['mediastatus_deleted_soft'] = 'Soft deleted';
$string['mediastatus_draft'] = 'Draft';
$string['mediastatus_restricted'] = 'Restricted';
$string['mediatype_audio'] = 'Audio';
$string['mediatype_document'] = 'Document';
$string['mediatype_image'] = 'Image';
$string['mediatype_link'] = 'Link';
$string['mediatype_other'] = 'Other';
$string['mediatype_video'] = 'Video';
$string['provenance_ai_assisted'] = 'AI-assisted';
$string['provenance_archive'] = 'Registry';
$string['provenance_assembly'] = 'Assembly';
$string['provenance_challenge'] = 'Challenge';
$string['provenance_human'] = 'Human';
$string['provenance_imported'] = 'Imported';
$string['provenance_integrity'] = 'Integrity';
$string['provenance_system'] = 'System';
$string['status_active'] = 'Active';
$string['status_archived'] = 'Preserved';
$string['status_contested'] = 'Contested';
$string['status_deleted_soft'] = 'Soft deleted';
$string['status_draft'] = 'Draft';
$string['status_invalidated'] = 'Invalidated';
$string['status_published'] = 'Published';
$string['status_restricted'] = 'Restricted';
$string['status_submitted'] = 'Submitted';
$string['status_superseded'] = 'Superseded';
$string['status_under_review'] = 'Under review';
$string['status_validated'] = 'Validated';
$string['uckkarchive:downloadmedia'] = 'Download Médiathèque media';
$string['uckkarchive:managecontentadvisories'] = 'Manage content advisories';
$string['uckkarchive:viewculturallyrestricted'] = 'View culturally restricted content';
$string['uckkarchive:viewrestrictedmedia'] = 'View restricted Médiathèque media';
$string['validationstate_archived'] = 'Preserved';
$string['validationstate_contested'] = 'Contested';
$string['validationstate_human_reviewed'] = 'Human reviewed';
$string['validationstate_invalidated'] = 'Invalidated';
$string['validationstate_unverified'] = 'Unverified';
$string['validationstate_verified'] = 'Verified';
$string['visibility_cohort'] = 'Cohort';
$string['visibility_course'] = 'Course';
$string['visibility_institution'] = 'Institution';
$string['visibility_private'] = 'Private';
$string['visibility_program'] = 'Program';
$string['visibility_public'] = 'Public';
$string['visibility_restricted'] = 'Restricted';
$string['visibility_restricted_cultural'] = 'Restricted cultural';
$string['visibility_restricted_integrity'] = 'Restricted integrity';
// -----------------------------------------------------------------------------
// Runtime AJAX/UI language strings added for media, content advisory and external work integration.
// -----------------------------------------------------------------------------

$string['contentadvisory:loaded'] = 'Content advisories loaded.';
$string['contentadvisory:loadfailed'] = 'Content advisories could not be loaded.';
$string['contentadvisory:loading'] = 'Loading content advisories…';
$string['contentmarker'] = 'Content marker';
$string['deletemedia'] = 'Delete media';
$string['deletemediaconfirm'] = 'Are you sure you want to delete this media item?';
$string['externalwork:loaded'] = 'External work loaded.';
$string['externalwork:loadfailed'] = 'External work could not be loaded.';
$string['externalwork:loading'] = 'Loading external work…';
$string['externalworks'] = 'External works';
$string['externalworks:refreshed'] = 'External works refreshed.';
$string['externalworks:refreshfailed'] = 'External works could not be refreshed.';
$string['externalworks:refreshing'] = 'Refreshing external works…';
$string['media:loaded'] = 'Media loaded.';
$string['media:loadfailed'] = 'Media could not be loaded.';
$string['media:loading'] = 'Loading media…';
$string['media:refreshed'] = 'Media refreshed.';
$string['media:refreshfailed'] = 'Media could not be refreshed.';
$string['media:refreshing'] = 'Refreshing media…';
$string['mediacollection:loaded'] = 'Media collection loaded.';
$string['mediacollection:loadfailed'] = 'Media collection could not be loaded.';
$string['mediacollection:loading'] = 'Loading media collection…';
$string['mediacollections:refreshed'] = 'Media collections refreshed.';
$string['mediacollections:refreshfailed'] = 'Media collections could not be refreshed.';
$string['mediacollections:refreshing'] = 'Refreshing media collections…';
$string['medianotfound'] = 'Media not found.';
$string['mediaversions:loaded'] = 'Media versions loaded.';
$string['mediaversions:loadfailed'] = 'Media versions could not be loaded.';
$string['mediaversions:loading'] = 'Loading media versions…';
$string['noitemsselected'] = 'No items selected.';
$string['uckkarchive:addexternalworks'] = 'Add external works';
$string['uckkarchive:deleteexternalworks'] = 'Delete external works';
$string['uckkarchive:editexternalworks'] = 'Edit external works';
$string['uckkarchive:viewexternalworks'] = 'View external works';

// -----------------------------------------------------------------------------
// Media-library editor.
// -----------------------------------------------------------------------------

$string['medialibraryeditor'] = 'Media library editor';
$string['medialibraryeditor_desc'] = 'Qualify, contextualise, relate, govern, and validate Médiathèque media.';
$string['backtomedialibrary'] = 'Back to media library';
$string['mediaeditorpreview'] = 'Media preview';
$string['mediaeditorworkflow'] = 'Workflow';
$string['mediaeditorgovernance'] = 'Governance';
$string['mediaeditoractions'] = 'Editor actions';
$string['mediaeditorform'] = 'Media qualification form';
$string['mediaeditorform_desc'] = 'Edit the media identity, source, rights, visibility, audience suitability, advisory hints, and metadata.';
$string['mediaeditorstep_reception'] = 'Reception';
$string['mediaeditorstep_identification'] = 'Identification';
$string['mediaeditorstep_qualification'] = 'Qualification';
$string['mediaeditorstep_markers'] = 'Passage markers';
$string['mediaeditorstep_advisories'] = 'Advisories and protocols';
$string['mediaeditorstep_relations'] = 'Relations';
$string['mediaeditorstep_validation'] = 'Validation';
$string['newmediarecord'] = 'New media record';
$string['passagemarkers'] = 'Passage markers';
$string['passagemarkers_desc'] = 'Point to a specific passage in a video, audio recording, book, PDF, website, or external work.';
$string['managepassagemarkers'] = 'Manage passage markers';
$string['mediaeditoradvisories_desc'] = 'Review content warnings, cultural advisories, cultural protocols, and audience-suitability conditions.';
$string['mediaeditorrelations_desc'] = 'Connect this media to collections, registry items, versions, external works, proofs, or other media.';
$string['mediaeditorvalidation_desc'] = 'Track review state, publication readiness, restrictions, and contestability.';
$string['mediaeditorprovenance_desc'] = 'Provenance and audit information remain governed by the server-side registry services.';
$string['mediacreated'] = 'Media created.';
$string['mediaupdated'] = 'Media updated.';

// -----------------------------------------------------------------------------
// Public Médiathèque / Explorer.
// -----------------------------------------------------------------------------

$string['mediatheque'] = 'Médiathèque';
$string['mediatheque_title'] = 'UCKK Médiathèque';
$string['mediatheque_eyebrow'] = 'Public Médiathèque';
$string['mediatheque_summary'] = 'Explore public media, collections, external works, and documented passages from the UCKK Médiathèque.';
$string['mediatheque_explorer'] = 'Médiathèque Explorer';
$string['mediatheque_explorer_title'] = 'Médiathèque Explorer';
$string['mediatheque_explorer_desc'] = 'Search and filter the public Médiathèque. Results are filtered by visibility, rights, content advisories, cultural protocols, and publication and access policies.';
$string['mediatheque_search'] = 'Search the Médiathèque';
$string['mediatheque_search_placeholder'] = 'Search by title, description, source, tag, collection, or passage';
$string['mediatheque_search_button'] = 'Search';
$string['mediatheque_reset_filters'] = 'Reset filters';
$string['mediatheque_apply_filters'] = 'Apply filters';
$string['mediatheque_load_more'] = 'Load more';
$string['mediatheque_loading'] = 'Loading Médiathèque results…';
$string['mediatheque_loading_failed'] = 'Médiathèque results could not be loaded.';
$string['mediatheque_empty'] = 'No public media match these filters.';
$string['mediatheque_empty_title'] = 'No results';
$string['mediatheque_empty_desc'] = 'Try another search term or remove some filters.';
$string['mediatheque_results'] = 'Médiathèque results';
$string['mediatheque_result_count'] = '{$a} result(s)';
$string['mediatheque_page'] = 'Page';
$string['mediatheque_perpage'] = 'Results per page';
$string['mediatheque_sort'] = 'Sort';
$string['mediatheque_sort_relevance'] = 'Relevance';
$string['mediatheque_sort_newest'] = 'Newest';
$string['mediatheque_sort_title'] = 'Title';
$string['mediatheque_sort_type'] = 'Type';

$string['mediatheque_filter_type'] = 'Object type';
$string['mediatheque_filter_mediatype'] = 'Media type';
$string['mediatheque_filter_collection'] = 'Collection';
$string['mediatheque_filter_tag'] = 'Tag';
$string['mediatheque_filter_source'] = 'Source';
$string['mediatheque_filter_advisory'] = 'Content advisory';
$string['mediatheque_filter_cultural'] = 'Cultural protocol';
$string['mediatheque_filter_audience'] = 'Audience';
$string['mediatheque_filter_language'] = 'Language';
$string['mediatheque_filter_validation'] = 'Validation';

$string['mediatheque_filter_all'] = 'All';
$string['mediatheque_filter_none'] = 'None';
$string['mediatheque_filter_has_advisory'] = 'With advisory';
$string['mediatheque_filter_has_public_advisory'] = 'With public advisory';
$string['mediatheque_filter_has_public_protocol'] = 'With public protocol';

$string['mediatheque_object_media'] = 'Media';
$string['mediatheque_object_collection'] = 'Collection';
$string['mediatheque_object_external_work'] = 'External work';
$string['mediatheque_object_archive_item'] = 'Linked registry item';
$string['mediatheque_object_content_marker'] = 'Passage marker';

$string['mediatheque_mediatype_video'] = 'Video';
$string['mediatheque_mediatype_audio'] = 'Audio';
$string['mediatheque_mediatype_image'] = 'Image';
$string['mediatheque_mediatype_pdf'] = 'PDF';
$string['mediatheque_mediatype_document'] = 'Document';
$string['mediatheque_mediatype_book'] = 'Book';
$string['mediatheque_mediatype_external_reference'] = 'External reference';
$string['mediatheque_mediatype_other'] = 'Other';

$string['mediatheque_source_produced_by_uckk'] = 'Produced by UCKK';
$string['mediatheque_source_submitted_to_uckk'] = 'Submitted to UCKK';
$string['mediatheque_source_imported'] = 'Imported';
$string['mediatheque_source_external_reference_only'] = 'External reference only';
$string['mediatheque_source_unknown'] = 'Unknown source';

$string['mediatheque_audience_general'] = 'General';
$string['mediatheque_audience_guided'] = 'Guided';
$string['mediatheque_audience_mature'] = 'Mature';
$string['mediatheque_audience_restricted'] = 'Restricted';

$string['mediatheque_validation_unverified'] = 'Unverified';
$string['mediatheque_validation_human_reviewed'] = 'Human reviewed';
$string['mediatheque_validation_verified'] = 'Verified';
$string['mediatheque_validation_archived'] = 'Preserved';

$string['mediatheque_public_notice'] = 'The Médiathèque only shows public, policy-filtered records.';
$string['mediatheque_restricted_notice'] = 'Some content is hidden or summarized according to rights, content advisories, cultural protocols, and publication and access policies.';
$string['mediatheque_policy_filtered_notice'] = 'Results are filtered by server-side publication and access policies.';
$string['mediatheque_no_download_notice'] = 'This public card does not grant access to the original file.';
$string['mediatheque_external_reference_notice'] = 'This record references an external work. UCKK does not claim ownership of the external content.';

$string['mediatheque_action_view_detail'] = 'View details';
$string['mediatheque_action_view_file'] = 'View file';
$string['mediatheque_action_download'] = 'Download';
$string['mediatheque_action_open_external'] = 'Open external reference';

$string['mediatheque_badge_public'] = 'Public';
$string['mediatheque_badge_restricted'] = 'Restricted';
$string['mediatheque_badge_advisory'] = 'Advisory';
$string['mediatheque_badge_cultural_protocol'] = 'Cultural protocol';
$string['mediatheque_badge_external_work'] = 'External work';
$string['mediatheque_badge_passage_marker'] = 'Passage marker';

$string['mediatheque_service_search'] = 'Search the public Médiathèque';
$string['mediatheque_service_error_invalidscope'] = 'Invalid Médiathèque search scope.';
$string['mediatheque_service_error_invalidfilters'] = 'Invalid Médiathèque filters.';
$string['mediatheque_service_error_unavailable'] = 'The Médiathèque search service is currently unavailable.';
$string['mediatheque_service_warning_policyfiltered'] = 'Some results may be hidden by publication and access policies.';
$string['mediatheque_service_warning_restrictedhidden'] = 'Restricted content was hidden from the public response.';


$string['libraryadmin'] = 'Media libraries and bridges';
$string['libraryadminintro'] = 'Each Univers-Cité uses an autonomous media library by default. The same library can be attached to several sites, while directional bridges can expose a whole library, a collection, or one media object without duplicating content.';
$string['libraryschemamissing'] = 'The autonomous media-library schema is not installed. Run the Moodle upgrade first.';
$string['libraries'] = 'Media libraries';
$string['libraryslug'] = 'Library key';
$string['createlibrary'] = 'Create a media library';
$string['attachlibrarysite'] = 'Attach / share a library with an Univers-Cité site';
$string['sitekey'] = 'Univers-Cité site key';
$string['primary'] = 'Primary';
$string['shared'] = 'Secondary (not used as the public primary fund)';
$string['assignmedialibrary'] = 'Move media to its home library';
$string['assigncollectionlibrary'] = 'Move collection to its home library';
$string['mediauuid'] = 'Media UUID';
$string['collectionuuid'] = 'Collection UUID';
$string['librarybridges'] = 'Media-library bridges';
$string['createbridge'] = 'Create bridge';
$string['sourcelibrary'] = 'Source library';
$string['targetlibrary'] = 'Target library';
$string['scopeuuid'] = 'Collection or media UUID (empty for a whole library)';
$string['wholelibrary'] = 'Whole library';
$string['libraryadminlink'] = 'Manage media libraries and bridges';
$string['privacy:metadata:uckkarchive_library'] = 'Registry of autonomous public media libraries.';
$string['privacy:metadata:uckkarchive_library_site'] = 'Mappings between Univers-Cité sites and media libraries.';
$string['privacy:metadata:uckkarchive_library_bridge'] = 'Explicit sharing bridges between media libraries.';
$string['libraryrole'] = 'Media-library role';
$string['bridgesource'] = 'Source';
$string['bridgetarget'] = 'Target';
$string['bridgelabel'] = 'Bridge label';
$string['librarysitemappings'] = 'Univers-Cité ↔ media-library mappings';
$string['uckkarchive:managelibraries'] = 'Manage autonomous media libraries and bridges';
