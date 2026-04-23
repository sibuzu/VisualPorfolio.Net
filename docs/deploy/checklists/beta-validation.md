# Beta Validation Checklist

## Functional Parity

- [ ] Core pages load and route normally on `visualporforlio-beta.sibuzu.com`
- [ ] Project create/load/delete flow works
- [ ] File upload (`.srp`, `.xrp`) works
- [ ] Analysis runs and returns expected panel data
- [ ] Dynamic compounding tab renders and recalculates correctly

## Health and Routing

- [ ] `https://visualporforlio-beta.sibuzu.com/` returns HTTP 200
- [ ] `https://api-visualporforlio-beta.sibuzu.com/healthz` returns HTTP 200
- [ ] Frontend domain routes only to beta frontend container
- [ ] API domain routes only to beta backend container

## Data Isolation

- [ ] New beta operations create/update files only under `data-beta`
- [ ] Production `data` directory has no new writes from beta test window
- [ ] Production database is unchanged by beta operations

## Release Decision

- [ ] All blocking defects are resolved or explicitly waived
- [ ] Smoke checks pass
- [ ] Release owner approves production promotion
