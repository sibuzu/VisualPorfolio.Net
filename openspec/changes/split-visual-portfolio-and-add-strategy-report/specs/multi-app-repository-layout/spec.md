## ADDED Requirements

### Requirement: Separate application source trees
The repository SHALL keep Visual Portfolio application source under `visual-portfolio/` and Strategy Report application source under `strategy-report/`, with independent backend and frontend entry points and dependency manifests.

#### Scenario: Build either application
- **WHEN** a developer runs the documented build and test commands for either application
- **THEN** that application SHALL build and test without requiring the other application's runtime data directory

### Requirement: Preserve Visual Portfolio behavior through relocation
The relocation SHALL preserve Visual Portfolio's public frontend routes, API behavior, production container identities, and existing persisted data locations.

#### Scenario: Existing production data
- **WHEN** the relocated Visual Portfolio production stack starts with the existing root `data/` directory
- **THEN** it SHALL read and write the same project and database files as before the relocation

#### Scenario: Existing API behavior
- **WHEN** the current Visual Portfolio API tests and frontend build run after relocation
- **THEN** their existing responses and successful build result SHALL remain unchanged

### Requirement: Visual Portfolio is a move only
The relocation SHALL not add Visual Portfolio features or change its parser, analysis calculations, application API, or persisted data schema. Strategy Report SHALL own its new parser and calculations independently.

#### Scenario: Review moved application
- **WHEN** the Visual Portfolio source before and after relocation is compared, excluding required path/build configuration changes
- **THEN** its application logic SHALL be equivalent and no Strategy Report code SHALL be imported by it
