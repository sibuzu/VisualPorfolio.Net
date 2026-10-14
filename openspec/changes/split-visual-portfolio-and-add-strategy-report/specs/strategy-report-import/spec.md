## ADDED Requirements

### Requirement: Reuse Visual Portfolio account credentials
Strategy Report SHALL offer a login and sign-up screen consistent with Visual Portfolio and SHALL authenticate accounts through Visual Portfolio's existing authentication service. It SHALL keep its browser session on the Strategy Report hostname and SHALL validate the session before processing an uploaded report.

#### Scenario: Existing account login
- **WHEN** a user submits a valid Visual Portfolio user ID and password on Strategy Report
- **THEN** Strategy Report SHALL start a session on its own hostname and allow the user to import reports

#### Scenario: Unauthenticated upload
- **WHEN** a user submits a report without a valid session
- **THEN** the report API SHALL reject the request without parsing the uploaded file

#### Scenario: Existing account logout
- **WHEN** a user logs out of Strategy Report
- **THEN** its hostname session SHALL be cleared without changing the user's Visual Portfolio session

### Requirement: Import SRP and SEA reports
Strategy Report SHALL accept one `.srp` XML file or one `.sea` archive and normalize its strategy metadata, settings, ordered trade events, quantities, prices, symbols, timestamps, point values, and available initial capital.

#### Scenario: Import SRP
- **WHEN** a user uploads a valid `.srp` file
- **THEN** Strategy Report SHALL show its source format, strategy information, trade count, and a report computed from the normalized events

#### Scenario: Import SEA
- **WHEN** a user uploads a valid `.sea` file
- **THEN** Strategy Report SHALL show the same categories of metadata and a report computed from its `strategy.toml` and `events.jsonl`

#### Scenario: Equivalent source reports
- **WHEN** paired `.srp` and `.sea` fixtures encode the same strategy and transactions
- **THEN** Strategy Report SHALL produce equivalent normalized trades and numerical report results within the documented rounding tolerance

### Requirement: Detect initial capital from report settings
Strategy Report SHALL recognize a positive `InitCapital`, `InitialCapital`, or `初始資金` setting in either supported source format, including thousands separators and the `萬` unit where present.

#### Scenario: Capital is present
- **WHEN** a supported file contains a valid positive initial capital setting
- **THEN** the normalized report SHALL expose that value as the source initial capital

#### Scenario: Capital is absent
- **WHEN** a supported file has no valid initial capital setting
- **THEN** the normalized report SHALL indicate that the value is absent so analysis can apply the mode specific default

### Requirement: Reject invalid or unsafe uploads
The import API SHALL reject unsupported formats, malformed source content, and archives exceeding documented size, entry count, or decompressed size limits; it SHALL not extract archive members to arbitrary filesystem paths or log report contents.

#### Scenario: Malformed upload
- **WHEN** a user uploads a malformed or unsupported file
- **THEN** the API SHALL return a clear validation error without creating a report

#### Scenario: Unsafe SEA archive
- **WHEN** a `.sea` contains traversal paths or exceeds configured archive limits
- **THEN** the API SHALL reject it without writing archive content outside its temporary request context

### Requirement: Isolate uploaded report data
The first release SHALL not write uploaded reports into Visual Portfolio's `data/` or `data-beta/` directories or make one user's report available to another user.

#### Scenario: Complete calculation request
- **WHEN** a report calculation finishes
- **THEN** the service SHALL discard the uploaded file and any request scoped parsed data, except for an explicitly configured expiring session cache
