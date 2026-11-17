@mod @mod_uckkarchive @uckkarchive @uckkarchive_content_advisory
Feature: UCKK Archive content advisories
  In order to give learners and staff context before viewing sensitive archive material
  As a user with appropriate archive permissions
  I need to create, view, review, and enforce content advisory markers

  Background:
    Given the following "users" exist:
      | username        | firstname | lastname | email                         |
      | teacher1        | Teacher   | One      | teacher1@example.test         |
      | student1        | Student   | One      | student1@example.test         |
      | reviewer1       | Reviewer  | One      | reviewer1@example.test        |
      | restricteduser1 | Restricted| Viewer   | restricteduser1@example.test  |
    And the following "courses" exist:
      | fullname        | shortname | category |
      | Archive Course  | ARCH101   | 0        |
    And the following "course enrolments" exist:
      | user            | course  | role           |
      | teacher1        | ARCH101 | editingteacher |
      | student1        | ARCH101 | student        |
      | reviewer1       | ARCH101 | editingteacher |
      | restricteduser1 | ARCH101 | editingteacher |
    And the following "activities" exist:
      | activity    | course  | idnumber     | name         | intro                         |
      | uckkarchive | ARCH101 | archive001   | UCKK Archive | UCKK Archive test activity.   |

  @javascript
  Scenario: A teacher can create a content advisory marker for media
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    And I press "Add media"
    And I set the following fields to these values:
      | Title       | Test video                      |
      | Media type  | video                           |
      | Visibility  | course                          |
      | Summary     | A test video with advisory data |
    And I press "Save changes"
    Then I should see "Test video"

    When I press "Content advisories"
    And I press "Add content advisory"
    And I set the following fields to these values:
      | Advisory tag         | violence             |
      | Locator type         | timecode_range       |
      | Locator start        | 00:01:10             |
      | Locator end          | 00:01:40             |
      | Severity             | moderate             |
      | Audience suitability | guided               |
      | Note                 | Brief violent scene. |
    And I press "Save changes"
    Then I should see "Content advisory created"
    And I should see "violence"
    And I should see "00:01:10"
    And I should see "00:01:40"
    And I should see "guided"

  @javascript
  Scenario: A student can see approved content advisories before viewing media
    Given the following "mod_uckkarchive > media" exist:
      | archive     | title             | mediatype | visibility | status |
      | archive001  | Advisory video    | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media          | tagkey           | locatortype    | locatorstart | locatorend | severity | audiencesuitability | reviewstate |
      | archive001 | Advisory video | explicit_language| timecode_range | 00:02:00     | 00:02:15   | notice   | guided              | approved    |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Advisory video"
    Then I should see "Content advisory"
    And I should see "explicit_language"
    And I should see "00:02:00"
    And I should see "00:02:15"
    And I should see "guided"

  @javascript
  Scenario: A reviewer can approve a pending content advisory marker
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title              | mediatype | visibility | status |
      | archive001 | Review test video  | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media             | tagkey          | locatortype    | locatorstart | locatorend | severity | audiencesuitability | reviewstate    |
      | archive001 | Review test video | sexual_violence | timecode_range | 00:04:00     | 00:04:30   | strong   | mature              | pending_review |
    When I am on the "Archive Course" course page logged in as "reviewer1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Review test video"
    And I press "Review content advisory"
    And I set the following fields to these values:
      | Review state         | approved                         |
      | Rationale            | Verified by human reviewer.      |
      | Audience suitability | mature                           |
      | Severity             | strong                           |
    And I press "Save review"
    Then I should see "Content marker reviewed"
    And I should see "approved"
    And I should see "Verified by human reviewer"

  @javascript
  Scenario: A reviewer can contest a content advisory marker
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                | mediatype | visibility | status |
      | archive001 | Contest test article | document  | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media                | tagkey | locatortype | locatorstart | severity | audiencesuitability | reviewstate |
      | archive001 | Contest test article | death  | page        | 12           | notice   | guided              | approved    |
    When I am on the "Archive Course" course page logged in as "reviewer1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Contest test article"
    And I press "Review content advisory"
    And I set the following fields to these values:
      | Review state | contested                       |
      | Rationale    | Locator should be page 13.      |
    And I press "Save review"
    Then I should see "Content marker reviewed"
    And I should see "contested"
    And I should see "Locator should be page 13"

  @javascript
  Scenario: Cultural protocol advisories are marked visibly for authorized users
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                    | mediatype | visibility          | status     |
      | archive001 | Cultural protocol image  | image     | restricted_cultural | restricted |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media                   | tagkey              | locatortype | severity   | audiencesuitability | reviewstate | culturalprotocol | restricted |
      | archive001 | Cultural protocol image | sacred_content      | manual      | restricted | restricted_cultural | approved    | 1                | 1          |
    When I am on the "Archive Course" course page logged in as "restricteduser1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Cultural protocol image"
    Then I should see "Content advisory"
    And I should see "sacred_content"
    And I should see "Cultural protocol"
    And I should see "restricted_cultural"

  @javascript
  Scenario: Students cannot create content advisory markers
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title              | mediatype | visibility | status |
      | archive001 | Student view video | video     | course     | active |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Student view video"
    Then I should not see "Add content advisory"
    And I should not see "Review content advisory"

  @javascript
  Scenario: Restricted advisory details are redacted for unauthorized users
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title              | mediatype | visibility | status |
      | archive001 | Restricted details | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media              | tagkey             | locatortype    | locatorstart | locatorend | severity   | audiencesuitability | reviewstate | restricted |
      | archive001 | Restricted details | restricted_knowledge | timecode_range | 00:10:00     | 00:11:00   | restricted | restricted          | approved    | 1          |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Restricted details"
    Then I should see "Content advisory"
    And I should see "restricted_knowledge"
    And I should not see "00:10:00"
    And I should not see "00:11:00"

  @javascript
  Scenario: Content advisory filters can narrow the media advisory panel
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title        | mediatype | visibility | status |
      | archive001 | Filter media | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media        | tagkey   | locatortype | severity | audiencesuitability | reviewstate |
      | archive001 | Filter media | violence | scene       | moderate | guided              | approved    |
      | archive001 | Filter media | death    | scene       | notice   | guided              | approved    |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Filter media"
    And I set the field "Filter advisory tag" to "violence"
    And I press "Apply filters"
    Then I should see "violence"
    And I should not see "death"

  @javascript
  Scenario: Content advisory markers are preserved after editing media metadata
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title               | mediatype | visibility | status |
      | archive001 | Editable media      | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media          | tagkey        | locatortype    | locatorstart | locatorend | severity | audiencesuitability | reviewstate |
      | archive001 | Editable media | substance_use | timecode_range | 00:03:00     | 00:03:25   | moderate | mature              | approved    |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Editable media"
    And I press "Edit media"
    And I set the field "Title" to "Edited media"
    And I press "Save changes"
    Then I should see "Edited media"
    And I should see "substance_use"
    And I should see "00:03:00"
    And I should see "00:03:25"

  @javascript
  Scenario: A teacher can delete a content advisory marker
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Delete advisory | video     | course     | active |
    And the following "mod_uckkarchive > content markers" exist:
      | archive    | media           | tagkey | locatortype | severity | audiencesuitability | reviewstate |
      | archive001 | Delete advisory | death  | scene       | notice   | guided              | approved    |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Delete advisory"
    Then I should see "death"
    When I press "Delete content advisory"
    And I press "Confirm delete"
    Then I should see "Content advisory deleted"
    And I should not see "death"