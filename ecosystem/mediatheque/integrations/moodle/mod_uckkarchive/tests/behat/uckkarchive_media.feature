@mod @mod_uckkarchive @uckkarchive @uckkarchive_media
Feature: UCKK Archive media library
  In order to preserve and organize archive media
  As a user with appropriate archive permissions
  I need to create, view, update, version, tag, relate, collect, and export media

  Background:
    Given the following "users" exist:
      | username        | firstname  | lastname | email                         |
      | teacher1        | Teacher    | One      | teacher1@example.test         |
      | student1        | Student    | One      | student1@example.test         |
      | manager1        | Manager    | One      | manager1@example.test         |
      | restricteduser1 | Restricted | Viewer   | restricteduser1@example.test  |
    And the following "courses" exist:
      | fullname       | shortname | category |
      | Archive Course | ARCH101   | 0        |
    And the following "course enrolments" exist:
      | user            | course  | role           |
      | teacher1        | ARCH101 | editingteacher |
      | student1        | ARCH101 | student        |
      | manager1        | ARCH101 | manager        |
      | restricteduser1 | ARCH101 | editingteacher |
    And the following "activities" exist:
      | activity    | course  | idnumber   | name         | intro                       |
      | uckkarchive | ARCH101 | archive001 | UCKK Archive | UCKK Archive media testing. |

  @javascript
  Scenario: A teacher can open the media library
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    Then I should see "Media library"
    And I should see "Add media"

  @javascript
  Scenario: A teacher can create an image media record
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    And I press "Add media"
    And I set the following fields to these values:
      | Title       | Archive image                 |
      | Media type  | image                         |
      | Visibility  | course                        |
      | Status      | active                        |
      | Summary     | A course-visible image item.  |
      | Description | Image description for tests.  |
    And I press "Save changes"
    Then I should see "Archive image"
    And I should see "image"
    And I should see "course"
    And I should see "A course-visible image item."

  @javascript
  Scenario: A teacher can create a video media record
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    And I press "Add media"
    And I set the following fields to these values:
      | Title       | Archive video                 |
      | Media type  | video                         |
      | Visibility  | course                        |
      | Status      | active                        |
      | Summary     | A course-visible video item.  |
      | Description | Video description for tests.  |
    And I press "Save changes"
    Then I should see "Archive video"
    And I should see "video"
    And I should see "course"

  @javascript
  Scenario: Students can view course-visible active media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                | mediatype | visibility | status |
      | archive001 | Course visible media | video     | course     | active |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    Then I should see "Course visible media"
    When I follow "Course visible media"
    Then I should see "Course visible media"
    And I should see "video"

  @javascript
  Scenario: Students cannot see private teacher media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title             | mediatype | visibility | status | owner     |
      | archive001 | Private teacher media | image | private    | active | teacher1  |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    Then I should not see "Private teacher media"

  @javascript
  Scenario: A teacher can edit media metadata
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Original title | document  | course     | draft  |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Original title"
    And I press "Edit media"
    And I set the following fields to these values:
      | Title       | Updated title                    |
      | Status      | active                           |
      | Visibility  | course                           |
      | Summary     | Updated media summary.           |
      | Description | Updated media description.       |
    And I press "Save changes"
    Then I should see "Updated title"
    And I should see "active"
    And I should see "Updated media summary."
    And I should not see "Original title"

  @javascript
  Scenario: A teacher can soft-delete media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Delete me media | image     | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Delete me media"
    And I press "Delete media"
    And I press "Confirm delete"
    Then I should see "Media deleted"
    And I should not see "Delete me media"

  @javascript
  Scenario: Students cannot add media
    Given I am on the "Archive Course" course page logged in as "student1"
    When I follow "UCKK Archive"
    And I follow "Media"
    Then I should not see "Add media"

  @javascript
  Scenario: Students cannot edit media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title               | mediatype | visibility | status |
      | archive001 | Student visible doc | document  | course     | active |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Student visible doc"
    Then I should not see "Edit media"
    And I should not see "Delete media"

  @javascript
  Scenario: A teacher can upload an original media file
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    And I press "Add media"
    And I set the following fields to these values:
      | Title      | Uploaded document |
      | Media type | document          |
      | Visibility | course            |
      | Status     | active            |
    And I upload "lib/tests/fixtures/empty.txt" file to "Original file" filemanager
    And I press "Save changes"
    Then I should see "Uploaded document"
    And I should see "empty.txt"

  @javascript
  Scenario: A teacher can add a new media version
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Versioned file | document  | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Versioned file"
    And I press "Add media version"
    And I set the following fields to these values:
      | Version label | Revised source file |
      | Status        | active              |
      | Change note   | Corrected document. |
    And I upload "lib/tests/fixtures/empty.txt" file to "Version file" filemanager
    And I press "Save changes"
    Then I should see "Media version created"
    And I should see "Revised source file"
    And I should see "Corrected document."

  @javascript
  Scenario: A teacher can view media version history
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title         | mediatype | visibility | status |
      | archive001 | Version media | video     | course     | active |
    And the following "mod_uckkarchive > media versions" exist:
      | archive    | media         | versionnumber | label        | status |
      | archive001 | Version media | 1             | First cut    | active |
      | archive001 | Version media | 2             | Second cut   | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Version media"
    And I press "Versions"
    Then I should see "First cut"
    And I should see "Second cut"
    And I should see "Version history"

  @javascript
  Scenario: A teacher can tag media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title       | mediatype | visibility | status |
      | archive001 | Tagged item | image     | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Tagged item"
    And I press "Add media tag"
    And I set the following fields to these values:
      | Tag | ceremony |
    And I press "Save changes"
    Then I should see "ceremony"

  @javascript
  Scenario: A teacher can remove a media tag
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title       | mediatype | visibility | status |
      | archive001 | Tagged item | image     | course     | active |
    And the following "mod_uckkarchive > media tags" exist:
      | archive    | media       | tag      |
      | archive001 | Tagged item | ceremony |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Tagged item"
    Then I should see "ceremony"
    When I press "Remove tag ceremony"
    And I press "Confirm"
    Then I should not see "ceremony"

  @javascript
  Scenario: A teacher can create a media collection
    Given I am on the "Archive Course" course page logged in as "teacher1"
    When I follow "UCKK Archive"
    And I follow "Media"
    And I press "Collections"
    And I press "Add media collection"
    And I set the following fields to these values:
      | Title       | Course media collection       |
      | Visibility  | course                        |
      | Description | Collection for course media.  |
    And I press "Save changes"
    Then I should see "Course media collection"
    And I should see "Collection for course media."

  @javascript
  Scenario: A teacher can add media to a collection
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Collection item | video     | course     | active |
    And the following "mod_uckkarchive > media collections" exist:
      | archive    | title             | visibility |
      | archive001 | Class collection  | course     |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Collection item"
    And I press "Add to collection"
    And I set the field "Collection" to "Class collection"
    And I press "Save changes"
    Then I should see "Class collection"
    And I should see "Media added to collection"

  @javascript
  Scenario: A teacher can remove media from a collection
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Collection item | video     | course     | active |
    And the following "mod_uckkarchive > media collections" exist:
      | archive    | title             | visibility |
      | archive001 | Class collection  | course     |
    And the following "mod_uckkarchive > media collection items" exist:
      | archive    | collection       | media           |
      | archive001 | Class collection | Collection item |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I press "Collections"
    And I follow "Class collection"
    Then I should see "Collection item"
    When I press "Remove from collection"
    And I press "Confirm"
    Then I should see "Media removed from collection"

  @javascript
  Scenario: A teacher can create a relation between media records
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Original media | video     | course     | active |
      | archive001 | Edited media   | video     | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Edited media"
    And I press "Add media relation"
    And I set the following fields to these values:
      | Relation type | derivative_of  |
      | Target type   | media          |
      | Target media  | Original media |
      | Description   | Edited version of source material. |
    And I press "Save changes"
    Then I should see "Media relation created"
    And I should see "derivative_of"
    And I should see "Original media"

  @javascript
  Scenario: A teacher can remove a media relation
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Original media | video     | course     | active |
      | archive001 | Edited media   | video     | course     | active |
    And the following "mod_uckkarchive > media relations" exist:
      | archive    | source       | target         | relationtype  |
      | archive001 | Edited media | Original media | derivative_of |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Edited media"
    Then I should see "Original media"
    And I should see "derivative_of"
    When I press "Remove media relation"
    And I press "Confirm"
    Then I should see "Media relation removed"
    And I should not see "derivative_of"

  @javascript
  Scenario: A teacher can search media by title
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title              | mediatype | visibility | status |
      | archive001 | Searchable video   | video     | course     | active |
      | archive001 | Different document | document  | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I set the field "Search media" to "Searchable"
    And I press "Search"
    Then I should see "Searchable video"
    And I should not see "Different document"

  @javascript
  Scenario: A teacher can filter media by type
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Filter video   | video     | course     | active |
      | archive001 | Filter image   | image     | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I set the field "Media type" to "video"
    And I press "Apply filters"
    Then I should see "Filter video"
    And I should not see "Filter image"

  @javascript
  Scenario: A teacher can filter media by tag
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Ceremony image  | image     | course     | active |
      | archive001 | Lecture video   | video     | course     | active |
    And the following "mod_uckkarchive > media tags" exist:
      | archive    | media          | tag      |
      | archive001 | Ceremony image | ceremony |
      | archive001 | Lecture video  | lecture  |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I set the field "Tag" to "ceremony"
    And I press "Apply filters"
    Then I should see "Ceremony image"
    And I should not see "Lecture video"

  @javascript
  Scenario: Restricted media is redacted for users without restricted access
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                  | mediatype | visibility | status     | summary                    |
      | archive001 | Restricted media item  | video     | restricted | restricted | Restricted summary detail. |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    Then I should not see "Restricted summary detail."

  @javascript
  Scenario: Culturally restricted media shows protocol notice for authorized viewers
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                    | mediatype | visibility          | status     | culturalprotocol |
      | archive001 | Cultural protocol media  | image     | restricted_cultural | restricted | 1                |
    When I am on the "Archive Course" course page logged in as "restricteduser1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "Cultural protocol media"
    Then I should see "Cultural protocol"
    And I should see "restricted_cultural"

  @javascript
  Scenario: Media thumbnails are displayed in the media library
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title           | mediatype | visibility | status |
      | archive001 | Thumbnail image | image     | course     | active |
    And the following "mod_uckkarchive > media files" exist:
      | archive    | media           | filearea        | filename      |
      | archive001 | Thumbnail image | media_thumbnail | thumbnail.png |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    Then I should see "Thumbnail image"
    And the "Thumbnail image" "img" should exist

  @javascript
  Scenario: A teacher can export selected media
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title          | mediatype | visibility | status |
      | archive001 | Export video   | video     | course     | active |
      | archive001 | Export image   | image     | course     | active |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I set the field "Select Export video" to "1"
    And I set the field "Select Export image" to "1"
    And I press "Export selected media"
    And I set the following fields to these values:
      | Format             | zip                     |
      | Redaction level    | standard                |
      | Reason             | Course archive package. |
    And I press "Create export"
    Then I should see "Export queued"
    And I should see "manifest.json"

  @javascript
  Scenario: Export excludes restricted media when user lacks restricted authority
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title                 | mediatype | visibility | status     |
      | archive001 | Public export media   | video     | course     | active     |
      | archive001 | Restricted export media | video   | restricted | restricted |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I set the field "Select Public export media" to "1"
    And I set the field "Select Restricted export media" to "1"
    And I press "Export selected media"
    And I press "Create export"
    Then I should see "Export queued"
    And I should see "Restricted export media"
    And I should see "excluded"

  @javascript
  Scenario: Media record keeps UUID after metadata update
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title       | mediatype | visibility | status | uuid                                 |
      | archive001 | UUID media  | document  | course     | active | 11111111-1111-4111-8111-111111111111 |
    When I am on the "Archive Course" course page logged in as "teacher1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "UUID media"
    And I press "Edit media"
    And I set the field "Title" to "UUID media updated"
    And I press "Save changes"
    Then I should see "UUID media updated"
    And I should see "11111111-1111-4111-8111-111111111111"

  @javascript
  Scenario: Media file URLs are controlled by pluginfile handling
    Given the following "mod_uckkarchive > media" exist:
      | archive    | title       | mediatype | visibility | status |
      | archive001 | File media  | document  | course     | active |
    And the following "mod_uckkarchive > media files" exist:
      | archive    | media      | filearea       | filename  |
      | archive001 | File media | media_original | source.txt |
    When I am on the "Archive Course" course page logged in as "student1"
    And I follow "UCKK Archive"
    And I follow "Media"
    And I follow "File media"
    Then I should see "source.txt"
    And I should see "/pluginfile.php/"