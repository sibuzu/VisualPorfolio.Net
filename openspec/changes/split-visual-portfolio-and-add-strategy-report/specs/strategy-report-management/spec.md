## ADDED Requirements

### Requirement: Manage saved performances after login
Strategy Report SHALL show a performance management home after login with the signed-in user, a report upload/name form, important performances from all owners, and the user's own performances. The visual structure SHALL follow Visual Portfolio's project management page. Selecting a valid report SHALL upload and open it without a separate create button.

#### Scenario: Create a performance
- **WHEN** an authenticated user uploads a valid `.srp` or `.sea` and leaves the display name empty
- **THEN** Strategy Report SHALL save the original report under that user and use the source StrategyName as the display name

#### Scenario: Reopen a saved performance
- **WHEN** the owner opens a listed performance or its URL
- **THEN** Strategy Report SHALL load its source report and saved analysis settings and display the calculated report

### Requirement: Stable file-derived performance IDs
Strategy Report SHALL assign each uploaded performance an ID beginning `SR-` followed by six uppercase letters derived deterministically from the complete uploaded file bytes. The same bytes SHALL produce the same ID across uploads. A shortened-ID collision with different file bytes SHALL not overwrite a saved report. IDs SHALL be globally unique so a URL identifies one owner and one saved report.

#### Scenario: Upload the same file again
- **WHEN** a user uploads the same file bytes a second time
- **THEN** Strategy Report SHALL return the existing performance with its unchanged ID, owner, and display name

### Requirement: Copy and download performances
An authenticated user SHALL be able to copy a visible performance into a new performance owned by that user. Each copy SHALL receive a random unused `SR-` six-letter ID and its own saved report directory. Authenticated users SHALL be able to download a visible performance with its original source and metadata.

#### Scenario: Copy another owner's performance
- **WHEN** a signed-in viewer copies a performance owned by another user
- **THEN** the viewer SHALL own a separate copy with the source file and settings, a new random ID, and no shared mutable state

#### Scenario: Download a performance
- **WHEN** a signed-in viewer downloads a visible performance
- **THEN** Strategy Report SHALL return a ZIP containing its original `.srp` or `.sea` source and performance metadata

### Requirement: Edit performance metadata and settings
The owner SHALL be able to rename, mark important, unmark important, and delete a performance without changing its ID. Changing capital management or date range inputs SHALL automatically recalculate the report after a short pause. Successful owner recalculation SHALL save its latest settings for the next open.

The report workspace sidebar SHALL follow Visual Portfolio's project page layout: performance name and home link in one row; ID, copy-link icon, edit/view status icon, copy, and download in the next row. Below the divider it SHALL show performance capital management with an optional date range checkbox and date inputs before the capital management mode and parameters. The sidebar SHALL not add unrelated action buttons.

#### Scenario: Rename after creation
- **WHEN** the owner changes the display name
- **THEN** subsequent list and report views SHALL show the new name while the `SR-` ID remains fixed

#### Scenario: Rename from the workspace
- **WHEN** the owner clicks the workspace's edit status icon
- **THEN** it SHALL open the same rename prompt as the home page and update the workspace and home listing after saving; a non-owner's view status icon SHALL remain informational

### Requirement: Enforce account ownership
All saved-performance operations SHALL require login. Owner lists SHALL contain only the caller's records; important lists and known performance URLs SHALL allow signed-in viewers. Metadata changes and deletion SHALL require ownership. A non-owner SHALL be allowed to recalculate with temporary settings without changing the saved settings.

#### Scenario: Another user changes capital management
- **WHEN** an authenticated non-owner opens a known performance ID and changes capital management inputs
- **THEN** the recalculated result SHALL be visible to that viewer, while the owner's saved settings remain unchanged

#### Scenario: Another user edits metadata
- **WHEN** an authenticated non-owner tries to rename or delete a performance
- **THEN** Strategy Report SHALL reject the change

### Requirement: Keep saved data independent of Visual Portfolio
Strategy Report SHALL persist original reports under the repository's root `data/reports/SR-XXXXXX/`, bind mounted into its container, with performance index metadata (ID, owner, name, importance, source information, and timestamps) in its own host-mounted SQLite database at `data/db/reporsts.db`. Capital management and date range settings SHALL be read and written in each report’s `config.json`. It SHALL migrate existing SQLite analysis settings into JSON and legacy BLOB report bytes into report directories without losing existing performances. It SHALL retain a pre-migration database backup and remove the obsolete settings column after successful export. It SHALL not modify Visual Portfolio's project or user databases when creating, editing, or deleting a performance.

#### Scenario: Recreate Strategy Report containers
- **WHEN** the application containers are rebuilt while root `data/reports/` and `data/db/reporsts.db` are retained
- **THEN** saved performances SHALL remain available to their owners

#### Scenario: Migrate existing settings
- **WHEN** the service starts with analysis settings still stored in SQLite
- **THEN** it SHALL export those settings to each report’s `config.json` while preserving the performance index and a pre-migration database backup

#### Scenario: Resume interrupted settings migration
- **WHEN** migration restarts after only some settings files were exported
- **THEN** it SHALL preserve completed files, export the remaining settings, and remove the old SQLite settings column only after all settings files are validated
