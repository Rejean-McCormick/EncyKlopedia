@mod @mod_uckkarchive
Feature: Use UCKK Archive activities
  In order to preserve course memory, proof, decisions, Kristals, media, content advisories, and validated records
  As a teacher, archivist, or learner
  I need UCKK Archive activities to expose safe archive workflows in Moodle

  Background:
    Given the following "users" exist:
      | username | firstname | lastname  | email                 |
      | teacher1 | Ada       | Archivist | teacher1@example.com  |
      | student1 | Jules     | Player    | student1@example.com  |
    And the following "courses" exist:
      | fullname                 | shortname | category |
      | UCKK Archive Test Course | UCKKARCH  | 0        |
    And the following "course enrolments" exist:
      | user     | course   | role           |
      | teacher1 | UCKKARCH | editingteacher |
      | student1 | UCKKARCH | student        |

  @javascript
  Scenario: A teacher creates a UCKK Archive activity
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    When I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Course memory archive |
      | Archive code       | UCKK-ARCH-001         |
      | Archive type       | Course memory         |
      | Archive status     | Active                |
      | Visibility         | Course                |
      | Archive purpose    | Preserve course proofs, decisions, minutes, Kristals, media, and public summaries with provenance and revision history. |
      | Archive scope      | Course-level archive for UCKK Archive Test Course. |
      | Public summary     | Public-safe summary of validated course memory. |
      | Default item type  | Proof                 |
      | Default provenance | Human                 |
      | Provenance policy  | Each item must declare origin, author, source, evidence, validation state, visibility, and revision information. |
      | Evidence policy    | Accepted evidence may include text, files, URLs, decisions, minutes, Kristals, media, portfolio records, and integrity summaries. |
      | Validation workflow | Human review         |
      | Validation criteria | An authorised human reviewer must verify provenance, visibility, restricted data, and validation state before publication or export. |
      | Contestability window in days | 30        |
      | Revision policy    | Version on important change |
      | Retention policy   | Institutional memory |
      | Retention notes    | Archive records must preserve institutional memory while respecting privacy and restricted integrity handling. |
      | Export policy      | Validated items only |
      | AI policy          | AI may assist with summarising, tagging, comparison, and uncertainty detection. AI cannot validate evidence, publish archive items, resolve integrity cases, or replace human review. |
      | Integrity notes    | Restricted and contested records require integrity safeguards. |
    Then I should see "Course memory archive"

  @javascript
  Scenario: A student can view an available UCKK Archive activity
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    And I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Student visible archive |
      | Archive code       | UCKK-ARCH-STUDENT       |
      | Archive type       | Course memory           |
      | Archive status     | Active                  |
      | Visibility         | Course                  |
      | Archive purpose    | Preserve visible course memory for learners. |
      | Archive scope      | Course-level visible archive. |
      | Provenance policy  | All visible archive items require provenance and validation state. |
    And I log out
    When I log in as "student1"
    And I am on "UCKKARCH" course homepage
    Then I should see "Student visible archive"
    When I follow "Student visible archive"
    Then I should see "Student visible archive"
    And I should not see "Validate archive item"
    And I should not see "Export archive"
    And I should not see "Add media"
    And I should not see "Add collection"

  @javascript
  Scenario: A teacher configures validation, revision, and export safeguards
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    When I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Validation archive |
      | Archive code       | UCKK-ARCH-VALIDATION |
      | Archive type       | Proof repository |
      | Archive status     | Pending review |
      | Visibility         | Restricted integrity |
      | Archive purpose    | Preserve high-risk proof with validation, contestability, and restricted integrity safeguards. |
      | Archive scope      | Restricted archive for contested proof and integrity summaries. |
      | Public summary     | Restricted archive with public-safe summaries only. |
      | Default item type  | Integrity summary |
      | Default provenance | Integrity |
      | Provenance policy  | Restricted evidence must include origin, source, review state, validation state, and revision record. |
      | Evidence policy    | Restricted evidence may include proof files, review notes, integrity summaries, media records, and redacted public summaries. |
      | Validation workflow | Integrity review |
      | Validation criteria | Integrity-restricted archive items must be reviewed by an authorised human reviewer before publication or export. |
      | Contestability window in days | 60 |
      | Revision policy    | Version every edit |
      | Retention policy   | Restricted integrity retention |
      | Retention notes    | Restricted evidence is retained for integrity review and institutional memory with redaction where needed. |
      | Export policy      | Restricted export with redaction |
      | AI policy          | AI may assist with comparison and uncertainty detection only. It cannot validate, publish, redact, or resolve integrity cases. |
      | Integrity notes    | Use restricted visibility, redaction, provenance checks, and human validation for every item. |
    Then I should see "Validation archive"

  @javascript
  Scenario: A teacher cannot save an archive without required provenance policy
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    When I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name      | Invalid archive |
      | Archive code      | UCKK-ARCH-INVALID |
      | Archive type      | Course memory |
      | Archive status    | Draft |
      | Visibility        | Course |
      | Archive purpose   | This archive is intentionally incomplete for validation testing. |
      | Provenance policy | |
    Then I should see "Required"

  @javascript
  Scenario: A teacher cannot use an invalid archive code
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    When I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Invalid archive code |
      | Archive code       | UCKK ARCH INVALID ! |
      | Archive type       | Course memory |
      | Archive status     | Draft |
      | Visibility         | Course |
      | Archive purpose    | Test invalid code validation. |
      | Provenance policy  | Every item must declare provenance. |
    Then I should see "The archive code may contain only letters, numbers, underscores, and hyphens."

  @javascript
  Scenario: A teacher enables completion based on archive contribution
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    When I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Completion archive |
      | Archive code       | UCKK-ARCH-COMPLETE |
      | Archive type       | Portfolio archive |
      | Archive status     | Active |
      | Visibility         | Course |
      | Archive purpose    | Preserve learner portfolio records and validated archive contributions. |
      | Archive scope      | Course portfolio archive. |
      | Provenance policy  | Portfolio archive records must preserve source, author, validation state, and visibility. |
      | Completion tracking | Show activity as complete when conditions are met |
      | Student must add at least one archive item to complete this activity | 1 |
      | Student must have at least one validated archive item to complete this activity | 1 |
    Then I should see "Completion archive"

  @javascript
  Scenario: A teacher opens the media library from an archive activity
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    And I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Media library archive |
      | Archive code       | UCKK-ARCH-MEDIA |
      | Archive type       | Course memory |
      | Archive status     | Active |
      | Visibility         | Course |
      | Archive purpose    | Preserve didactic media with provenance and advisories. |
      | Archive scope      | Course media archive. |
      | Provenance policy  | Media must preserve source, author, rights status, visibility, and advisory state. |
    When I follow "Media library archive"
    Then I should see "Media library archive"
    And I should see "Media"
    And I should see "Media library"
    And I should see "Add media"
    And I should see "Add collection"

  @javascript
  Scenario: A teacher can open media export options
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    And I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Exportable media archive |
      | Archive code       | UCKK-ARCH-EXPORT-MEDIA |
      | Archive type       | Course memory |
      | Archive status     | Active |
      | Visibility         | Course |
      | Archive purpose    | Preserve media records that can be exported with audit logging. |
      | Archive scope      | Course media export archive. |
      | Provenance policy  | Exports must preserve provenance, visibility, redaction state, and audit trail. |
      | Export policy      | Validated items only |
    When I follow "Exportable media archive"
    And I follow "Export archive"
    Then I should see "Export archive"
    And I should see "Export options"
    And I should see "Scope"
    And I should see "Format"
    And I should see "Visibility"
    And I should see "Download export"

  @javascript
  Scenario: A teacher sees content advisory controls for archive media
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    And I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Advisory archive |
      | Archive code       | UCKK-ARCH-ADVISORY |
      | Archive type       | Course memory |
      | Archive status     | Active |
      | Visibility         | Course |
      | Archive purpose    | Preserve media with content advisory and cultural protocol notes. |
      | Archive scope      | Course advisory archive. |
      | Provenance policy  | Advisory markers must preserve source, target, review state, visibility, and cultural protocol context. |
    When I follow "Advisory archive"
    Then I should see "Advisory archive"
    And I should see "Content advisories"
    And I should see "Cultural protocol"

  @javascript
  Scenario: A student cannot see teacher-only archive management actions
    Given I log in as "teacher1"
    And I am on "UCKKARCH" course homepage
    And I turn editing mode on
    And I add a "UCKK Archive" to section "1" and I fill the form with:
      | Archive name       | Learner safe archive |
      | Archive code       | UCKK-ARCH-LEARNER-SAFE |
      | Archive type       | Course memory |
      | Archive status     | Active |
      | Visibility         | Course |
      | Archive purpose    | Preserve learner-visible memory while hiding restricted management actions. |
      | Archive scope      | Course learner archive. |
      | Provenance policy  | Learner-facing archive data must expose only safe validated summaries. |
    And I log out
    When I log in as "student1"
    And I am on "UCKKARCH" course homepage
    And I follow "Learner safe archive"
    Then I should see "Learner safe archive"
    And I should not see "Add media"
    And I should not see "Add collection"
    And I should not see "Review advisory"
    And I should not see "Export media"
    And I should not see "Manage external works"

