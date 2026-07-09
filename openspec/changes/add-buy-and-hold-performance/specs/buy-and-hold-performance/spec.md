## ADDED Requirements

### Requirement: Buy&Hold Action Placement
The frontend SHALL provide a `+ Buy&Hold` action in strategy portfolio management alongside existing performance creation and project upload actions.

#### Scenario: Strategy portfolio controls render Buy&Hold action
- **WHEN** user views strategy portfolio management
- **THEN** system SHALL show `+ Buy&Hold`, `+新增績效`, and `上傳專案` controls across two display rows.

#### Scenario: Read-only projects cannot create Buy&Hold performance
- **WHEN** user views a read-only project
- **THEN** system SHALL prevent Buy&Hold performance creation.

### Requirement: Buy&Hold Creation Dialog
The frontend SHALL provide a Buy&Hold dialog with date, amount, product type, code, conditional leverage, and contextual help controls.

#### Scenario: Dialog opens from Buy&Hold action
- **WHEN** user clicks `+ Buy&Hold`
- **THEN** system SHALL show a dialog titled `Buy&Hold`.
- **THEN** dialog SHALL include inputs for `日期`, `金額(萬)`, `商品`, and `代碼`.

#### Scenario: Stock product hides leverage input
- **WHEN** user selects `股票`
- **THEN** system SHALL hide the leverage input.

#### Scenario: Futures product shows leverage input
- **WHEN** user selects `期貨`
- **THEN** system SHALL show the leverage input.
- **THEN** system SHALL default leverage to `5`.

#### Scenario: Dialog inputs are plain text
- **WHEN** user edits date, amount, code, or leverage fields
- **THEN** system SHALL use plain textbox-style inputs without numeric spinner controls.

#### Scenario: Dialog remembers last-used settings
- **WHEN** user creates Buy&Hold performance with custom dialog settings
- **THEN** system SHALL remember those settings for the next time the dialog opens.

#### Scenario: Help content is displayed
- **WHEN** user clicks the Buy&Hold help control
- **THEN** system SHALL show help text explaining stock and futures buy-and-hold usage.
- **THEN** help text SHALL include stock examples `2330`, `0050`.
- **THEN** help text SHALL include futures examples `TX`, `TE`, `TF`, `GTF`.
- **THEN** help text SHALL state that stocks reinvest dividends and futures roll over.

### Requirement: Generated Performance Naming
The system SHALL name generated Buy&Hold performance files using a `BH` prefix plus the entered code and amount in ten-thousand units, and SHALL include futures leverage in futures names.

#### Scenario: Stock generated name uses code and amount
- **WHEN** user creates Buy&Hold performance with code `2330` and amount `100`
- **THEN** system SHALL create the performance display name `BH2330_100萬`.

#### Scenario: Futures generated name uses code amount and leverage
- **WHEN** user creates futures Buy&Hold performance with code `TX`, amount `100`, and leverage `5`
- **THEN** system SHALL create the performance display name `BHTX_100萬_5X`.

#### Scenario: Existing generated name is overwritten
- **WHEN** a generated Buy&Hold file with the requested name already exists
- **THEN** system SHALL overwrite the existing generated file.
- **THEN** system SHALL keep the filename derived from the requested performance name.

### Requirement: Stock Buy&Hold Calculation
The backend SHALL generate stock Buy&Hold performance from FinMind data with daily floating equity, fractional position sizing, and dividend reinvestment.

#### Scenario: Stock series starts on requested date
- **WHEN** user creates stock Buy&Hold performance with a valid date, amount, and code
- **THEN** system SHALL fetch FinMind stock market data for the code from the requested date through the most recent available trading date.
- **THEN** system SHALL generate daily floating performance values for each available trading date.

#### Scenario: Stock dividends are reinvested
- **WHEN** FinMind reports dividend events during the stock holding period
- **THEN** system SHALL apply dividends as reinvested capital in the generated performance series.

#### Scenario: Stock entry allows fractional position
- **WHEN** stock entry capital divided by entry price does not produce a whole-share quantity
- **THEN** system SHALL use the fractional quantity in the generated performance calculation.
- **THEN** system SHALL NOT round the quantity to an integer position.

#### Scenario: Missing stock data fails without file creation
- **WHEN** FinMind has no usable stock price data for the requested code and date range
- **THEN** system SHALL reject the request with a clear error.
- **THEN** system SHALL NOT create a generated performance file.

### Requirement: Futures Buy&Hold Calculation
The backend SHALL generate futures Buy&Hold performance from FinMind data with daily floating equity, leverage, fractional position sizing, and rollover.

#### Scenario: Futures series uses leverage
- **WHEN** user creates futures Buy&Hold performance with amount `100`, code `TX`, and leverage `5`
- **THEN** system SHALL calculate exposure using the amount multiplied by the leverage value.
- **THEN** system SHALL generate daily floating performance values for each available trading date.

#### Scenario: Futures entry allows fractional position
- **WHEN** futures exposure divided by entry price does not produce a whole-contract quantity
- **THEN** system SHALL use the fractional quantity in the generated performance calculation.
- **THEN** system SHALL NOT round the quantity to an integer position.

#### Scenario: Futures series rolls contracts
- **WHEN** the held futures contract reaches the configured rollover point
- **THEN** system SHALL roll the holding into the next contract for the same futures code.
- **THEN** system SHALL continue the generated performance series after rollover.

#### Scenario: Missing futures data fails without file creation
- **WHEN** FinMind has no usable futures data for the requested code and date range
- **THEN** system SHALL reject the request with a clear error.
- **THEN** system SHALL NOT create a generated performance file.

### Requirement: Buy&Hold Project Integration
The system SHALL add generated Buy&Hold performance as a project performance file and refresh portfolio analysis.

#### Scenario: Generated performance is saved to project
- **WHEN** Buy&Hold generation succeeds
- **THEN** backend SHALL save the generated performance as a `.sea` file in the project directory.
- **THEN** response SHALL include the generated filename and display name.

#### Scenario: Frontend refreshes generated performance
- **WHEN** frontend receives a successful Buy&Hold generation response
- **THEN** frontend SHALL reload project files.
- **THEN** frontend SHALL include the generated performance in strategy portfolio management.
- **THEN** frontend SHALL refresh analysis using the existing project analysis flow.

#### Scenario: Non-owner cannot mutate project
- **WHEN** a user without owner access requests Buy&Hold generation
- **THEN** backend SHALL reject the request.
- **THEN** backend SHALL NOT create a generated performance file.
