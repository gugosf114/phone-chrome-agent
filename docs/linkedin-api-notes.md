# LinkedIn page API research — 2026-10-27 PDT

Verdict: **partial**. Search and combined job details were reproduced successfully with `window.fetch` inside George's signed-in laptop tab. The Easy Apply question schema has not been exposed by an observed GET without opening Apply. No application dialog was opened.

## Route and evidence

- Source: live Network events on the existing headed laptop Chrome, reached only through `127.0.0.1:19222`.
- `Network.enable`, `Page.navigate`, `Network.getResponseBody`, and `Runtime.evaluate` supplied the evidence. Job fields come from JSON, not DOM extraction.
- Search page: `/jobs/search/?keywords=legal%20operations&location=United%20States&sortBy=DD&f_TPR=r172800&f_AL=true`.
- Detail page: `/jobs/view/4483291551/`. Its document and `/preload/` returned HTML; its applicant-insights GET returned JSON. The search page's selected-job pane exposed the richer detail GETs below.
- Private captures are under `logs/api-research/`; the first successful in-page replays are `replay/search.json` and `replay/combined.json`. Logs are ignored by Git. Cookies and CSRF values are redacted from network logs.
- Live validation and the five-job comparison are recorded below.

## Endpoints actually read

All paths below are on `https://www.linkedin.com`. All issued service calls were GETs. These IDs are evidence from this run, not constants in the script. Each new run observes fresh IDs and headers in its own tab.

### Search cards

`/voyager/api/voyagerJobsDashJobCards`

Observed parameters:

```text
decorationId=com.linkedin.voyager.dash.deco.jobs.search.JobSearchCardsCollection-221
count=25
q=jobSearch
query=(origin:JOB_SEARCH_PAGE_OTHER_ENTRY,keywords:legal%20operations,locationUnion:(seoLocation:(location:United%20States)),selectedFilters:(sortBy:List(DD),applyWithLinkedin:List(true),timePostedRange:List(r172800)),spellCorrectionEnabled:true)
start=0
```

Returns `{data, meta, included}`. `data.elements[].jobCardUnion['*jobPostingCard']` gives ordered card URNs; `data.paging` gives start, count and total. The captured first page had 25 jobs and a total of 38. The 178 included entities held search cards, job stubs, companies, job state, verification, and relevance records. Referenced `JOB_DETAILS` cards here were only stubs.

Search cards carry title, company, location/workplace text, advertised pay when present, Easy Apply footer, and listing time. Paging changes only `start` and keeps `count=25`. The script retains the search filters emitted by the page, including `--any`, `--remote`, and `--location` when supplied.

### Combined detail sections — production route

`/voyager/api/graphql`

```text
includeWebMetadata=true
queryId=voyagerJobsDashJobPostingDetailSections.bc2eee77d01abc6616b8c8855344dfd5
variables=(cardSectionTypes:List(TOP_CARD,HOW_YOU_FIT_CARD),jobPostingUrn:urn%3Ali%3Afsd_jobPosting%3A4483291551,includeSecondaryActionsV2:true,jobDetailsContext:(isJobSearch:true))
```

The page separately sent the same query ID with:

```text
variables=(cardSectionTypes:List(JOB_DESCRIPTION_CARD),jobPostingUrn:urn%3Ali%3Afsd_jobPosting%3A4483291551,includeSecondaryActionsV2:true)
variables=(cardSectionTypes:List(JOB_APPLICANT_INSIGHTS),jobPostingUrn:urn%3Ali%3Afsd_jobPosting%3A4483291551,includeSecondaryActionsV2:true)
```

The tested combined GET retains the observed top-card variables and changes its section list to `List(TOP_CARD,HOW_YOU_FIT_CARD,JOB_DESCRIPTION_CARD)`. This is a tested combination of observed section names using the observed query ID. It returned HTTP 200 and about 240 KB. The script refuses to combine section templates if their query IDs differ.

Returns a graph of `JobPosting`, `JobPostingCard`, `JobDescription`, `WorkplaceType`, `Company`, `Geo`, and `JobSeekerApplicationDetail`. The latter is included data describing the button and application state; the script never calls an application endpoint. The top card supplies the applicant text and pay/workplace insights. The applicant-insights-only call also returned HTTP 200, but is unnecessary for production.

### Full job object — research only

`/voyager/api/graphql`

```text
includeWebMetadata=true
queryId=voyagerJobsDashJobPostings.8e5cd9bc41fc386f2e8ae995edea6721
variables=(jobPostingUrn:urn%3Ali%3Afsd_jobPosting%3A4483291551)
```

Returned HTTP 200, full description, company reference, location, and listing timestamps. `jobPostingTalentQuestions` was null. A GraphQL error inside that HTTP-200 body denied the employer-only `jobBudget` field with `extensions.status=403`. This was not an HTTP 403 response. No attempt was made to access that field separately. Production uses the narrower combined-sections query above and does not request this full-job query.

## Headers and in-page replay

The actual search request used:

- `accept: application/vnd.linkedin.normalized+json+2.1`
- `x-restli-protocol-version: 2.0.0`
- `x-li-lang: en_US`
- `x-li-track`, `x-li-page-instance`, `x-li-deco-include-micro-schema`, `x-li-pem-metadata`
- `csrf-token`, plus browser-generated User-Agent, Referer, and `sec-*` headers.

The script copies `accept`, `x-restli-protocol-version`, and the observed `x-li-*` header values from that run's matching request. It reads `JSESSIONID` through `document.cookie` in the page, removes its surrounding quotes, and uses it as `csrf-token`. The token never returns to Node. `window.fetch` uses `method:"GET"`, `credentials:"include"`, and `redirect:"manual"`. Chrome supplies cookies and browser-controlled headers. No cookie is written, rotated, or replaced. No guessed header or query ID is used.

## Graph decoding and output

`included` objects are indexed and merged by `entityUrn`. `*` references resolve through that map. Search order comes from `data.elements`, not the arbitrary order of `included`.

- Existing columns: `jobId`, URL, title, company, location, workplace, age, top, applyButton, applied, pay, desc, gatheredAt, walls, easy.
- Added: `workplaceType`, `applicantCount`, `applicantCountIsLowerBound`, `applicantCountKind`, `salaryInsight`, `easyApply`, `postingAge`, `postingAgeHours`, `listedAt`, `companyUrn`.
- Counts displayed as "Over N" are lower bounds. "People clicked apply" is labeled as apply clicks. Missing counts remain null.
- Salary insight is the text supplied by the job card. It is not a salary estimate. Description pay remains available through the existing `pay` column.
- Paragraph and list-item offsets restore line breaks in rich description text. Full descriptions are retained.
- `walls.json` uses the same title/where/description sentence rules and matched excerpts as `gather.cjs`.
- `no.json` always excludes a job. `seen.json` is shared with the DOM gather; `--all` includes seen jobs again.
- `--questions` writes `questions:null` and an explicit `questionsStatus`. This does not mean the application has zero questions.

Outputs: `logs/gather/gather-api-<stamp>.json`, the same seven-column `.md` table, and `.network.jsonl` with methods, URLs, redacted request headers, HTTP statuses, and up to 2 KB of response preview.

## Hard limits

The request gate blocks every non-GET before it is sent, including page telemetry. It also blocks page-owned data calls other than an explicit permitted job GET. Apply, save, follow, message, and connection calls are never permitted. No dialog is opened and no form is edited.

Data/document GETs share one queue: 2.5–4 seconds between sends, randomized, with a 60-call ceiling including navigation. Static page assets remain browser-owned GETs. The navigation settle is independently 1.5–3.5 seconds. `HUMAN_SPEED=0` does not disable these delays. Paging uses at most 25 cards. `--max` is a ceiling, not a promise to exceed the 60-call budget.

HTTP 429/999/403, checkpoint/authwall redirects, and any inspected data/document body mentioning "unusual activity" stop the run. The reason is appended to this file; there is no retry. An opaque redirect also stops without following it. Completed records are saved on interruption.

The script refuses a running DOM gather and a DOM output from the last minute. Use a two-minute gap in either direction. It never launches Chrome and refuses every CDP port except 19222.

## Failed or incomplete approaches

1. The first capture treated a canceled CDP interception ID as a fatal error. No ban signal caused that stop. The handler now records the canceled request and continues; it never retries the canceled request.
2. A research-only page snapshot had a quoted-selector error. It was replaced with a serialized function before the detail-page capture. This did not affect the JSON replays.
3. Search-prefetched detail cards were empty stubs. One combined detail GET per job supplies the missing fields; reading many separate sections would waste the 60-call budget.
4. The full-job query exposed an employer-field error inside HTTP 200. The narrower detail-sections route supplies the needed job data.
5. No observed GET supplied the Easy Apply form schema. `JobSeekerApplicationDetail` described the button/application state, and `jobPostingTalentQuestions` was null. Pressing Apply or calling guessed application endpoints would cross this task's read-only boundary, so neither was tried.
6. On the standalone job page, the page attempted a POST to `/flagship-web/rsc-action/actions/app-config`; the guard blocked it locally. Search-pane detail GETs supplied the needed records without using that POST.

## Validation

Command: `CDP_PORT=19222 node scripts/gather_api.cjs --keywords "legal operations" --hours 48 --max 30 --questions`.

Result: **30 jobs in 104.5 seconds, 0.287 jobs/second**, with 33 data/document GETs (one navigation, two search pages, 30 combined details). Actual send gaps were 2.501–3.958 seconds. All 32 API responses were HTTP 200. No non-GET passed the gate. No HTTP 403, 429, 999, checkpoint/authwall redirect, or unusual-activity body was seen in research or this run.

Every record has a title, company, full description, workplace, applicant count, and company URN. Sixteen have a job-card salary insight. The remaining jobs can still have pay found in their description. All 30 question schemas are explicitly unavailable; no dialog was opened.

Private evidence: `logs/gather/gather-api-2026-10-27-07-13-31.json`, its Markdown table and network log. Saved-payload decoding checks passed, including the bar-admission wall. Offline stop-guard checks covered HTTP 403/429/999 and a manual 302 redirect to `/checkpoint/`. The redirect-header check was added after the live run; no extra LinkedIn run was used for that local change.

The unmodified DOM gather ran with `--keywords "legal operations" --hours 48 --max 5 --all`, starting **120.293 seconds after the API run finished**. A separate CDP guard kept its page requests GET-only, paced, and capped. It used 40 data/document GETs and stopped normally with no ban signal. The DOM gathered a different subset of the search results; all five IDs were present in the API's 30 records.

**Five of five matched exactly on title, company, pay, and workplace: 20 field checks, zero mismatches.**

The guarded DOM run returned empty descriptions for all five jobs. This comparison therefore validates the four requested fields, not description or wall equivalence. The API run retained all 30 full descriptions; the saved-payload check separately verified the bar-admission wall against one of them. The cause of the DOM's empty descriptions was not established in this task.

| Job ID | Company | Title / company / pay / workplace |
|---|---|---|
| 4483291551 | Turing | All four match |
| 4481805800 | Jendryk Hamer & Begley, LLC | All four match |
| 4483218978 | D3 Search | All four match |
| 4481497261 | We Are Legal Revolution | All four match |
| 4481495473 | HCL Global Systems Inc | All four match |

Comparison evidence: `logs/api-research/comparison.json`, `dom-run.json`, `dom-network.jsonl`, and `logs/gather/gather-2026-10-27-07-17-16.json`. No application was staged or submitted.

## Follow-up 1 — one Easy Apply dialog (2026-10-27)

**Schema extraction did not land under the GET-only rule.** Exactly one Easy Apply click was made, with `human.cjs`, on Turing job `4483291551`. Network recording and the write-blocking gate were active before navigation and the click. The browser attempted:

```text
POST /flagship-web/rsc-action/actions/navigation?screenId=com.linkedin.sdui.flagshipnav.jobs.easyapply.EasyApply&sduiid=com.linkedin.sdui.flagshipnav.jobs.easyapply.EasyApply
```

Its JSON request body contained `clientArguments.payload.jobId`, `companyName`, and `applicantTrackingSystemName:"LinkedIn"`. The guard blocked it before transmission. The dialog shell said `Apply to Turing`, then `Something went wrong on our end`, with only Dismiss and Refresh buttons. There were zero fields and no Next or Review button. No second screen could be reached. Refresh was not clicked.

Dismiss was clicked with `human.cjs`; the final snapshot proved `dialog:false`. No Discard prompt appeared. No answers were entered, no request was changed to another method, and the dialog was not reopened. Two data/document GETs passed the gate. No account-warning signal was seen.

This establishes that the observed live UI loads Easy Apply through a POST navigation action. It does **not** establish that LinkedIn serves schemas only after an application is started, nor that no legacy GET exists. No GET schema endpoint was observed, so there is no evidenced GET to replay for other jobs. `--questions` remains explicitly unavailable.

Private proof: `logs/followup/dialog-once.json`, `dialog-network.jsonl` (including all data-call attempts and blocked POST bodies), `dialog-screen-1.json`, `dialog-report.json`. The one-dialog marker prevents an accidental repeat. This live probe also recorded the standalone description component's POST; that evidence is used in challenge 3.
