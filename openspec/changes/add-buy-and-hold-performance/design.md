## Context

VisualPortfolio projects currently analyze uploaded `.sea`/`.gsea` performance files. The strategy portfolio UI lists project files through `EquityManager.vue`, and backend file APIs enforce owner-only mutations before analysis refreshes the generated portfolio metrics.

The Buy&Hold flow should behave like adding another performance file: the user enters product parameters, the backend fetches FinMind data, generates a daily floating equity series, saves it as a `.sea` file in the project directory, and the frontend refreshes the project files plus analysis.

## Goals / Non-Goals

**Goals:**
- Add a first-class `+ Buy&Hold` action in strategy portfolio management.
- Generate stock and futures buy-and-hold performance from FinMind data.
- Store the generated result as a project performance file named from `BH{代碼}_{金額}萬` for stocks and `BH{代碼}_{金額}萬_{槓桿}X` for futures.
- Preserve existing owner/read-only access rules for project mutations.
- Keep all inputs as plain text fields without numeric spinners.

**Non-Goals:**
- Implement an interactive brokerage/trading simulator.
- Add intraday pricing, short selling, margin calls, taxes, or transaction cost modeling unless already represented by available source data.
- Replace existing upload/import flows.
- Persist draft dialog input before the user creates the performance.

## Decisions

1. Add a dedicated backend route for Buy&Hold generation.

   Use a project-scoped endpoint such as `POST /projects/{project_id}/buy-hold` instead of overloading file upload. The request payload can be validated with Pydantic fields for `date`, `amount_wan`, `product_type`, `code`, and optional `leverage`. This keeps generated-data errors distinct from upload validation errors while reusing project access and file storage conventions.

   Alternative considered: build the `.sea` file in the browser and upload it. That would expose FinMind details to the frontend and duplicate file generation logic outside backend tests.

2. Generate a `.sea` artifact as the integration boundary.

   The existing analysis pipeline already discovers `.sea`/`.gsea` files and turns them into equities. The Buy&Hold service should write a generated `.sea` archive containing `strategy.toml` metadata plus `events.jsonl` price/equity events that existing parser/analysis code can consume. The frontend then reloads project files and calls the same analysis refresh path used by uploads.

   Alternative considered: add a parallel analysis-only payload that never writes a file. That would make the Buy&Hold series harder to delete, download, share, or include in project packages.

3. Isolate FinMind access in a service module.

   Add a backend service such as `backend/services/buy_hold.py` that owns FinMind fetching, normalization, dividend reinvestment, futures rollover, daily floating equity calculation, and `.sea` serialization. The router should stay thin and handle only auth, request/response, and persistence.

   Alternative considered: fetch directly from the router. That would make edge cases and tests harder to keep focused.

4. Allow fractional entry positions.

   Buy&Hold calculation should size the initial holding as `capital / entry_price` for stocks and `capital * leverage / entry_price` for futures without rounding to whole shares or contracts. This keeps the generated series fully invested from the selected date and avoids lot-size rules that are outside the requested simplification.

   Alternative considered: round down to whole shares/contracts. That would leave idle cash, make futures examples more sensitive to contract size assumptions, and conflict with the requested simplified calculation.

5. Treat the user-entered amount as capital in ten-thousand units.

   The generated stock performance name SHALL be `BH{code}_{amount}萬`; the generated futures performance name SHALL be `BH{code}_{amount}萬_{leverage}X`. The amount and leverage portions preserve normalized user-entered text after trimming. Calculation converts the amount to base currency by multiplying by 10,000. Futures leverage defaults to `5` and only applies when product type is futures.

   Alternative considered: normalize the name to the converted currency amount. That would conflict with the requested naming pattern.

6. Keep the dialog state local and owner-gated.

   The `+ Buy&Hold` action should be disabled or hidden for read-only projects because creating the performance mutates project files. The help button should show the requested explanatory copy without navigating away from the dialog.

   Alternative considered: allow read-only local-only Buy&Hold series. That would not be consistent with project file management and would disappear on refresh.

## Risks / Trade-offs

- FinMind data availability or symbol coverage gaps -> Return a clear validation/API error and do not create a partial file.
- Dividend and rollover rules can be domain-sensitive -> Keep algorithms small, documented in tests, and driven by normalized source records.
- Network calls may be slow -> Use backend timeouts and surface loading/error states in the dialog.
- Generated filename collisions are destructive by design for Buy&Hold -> Sanitize names and overwrite the same generated `.sea` file when it already exists.
- Futures continuous series definitions vary -> Start with a deterministic rollover rule and document any unsupported contracts or missing calendar data.
