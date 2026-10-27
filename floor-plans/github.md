# GitHub floor plan — drawn 2026-10-26, signed in as gugosf114, 2 doors deep, 45 pages

Drawn by a read-only crawler (scripts/floorplan.cjs) in the box Chromium on port 9222. It only loads pages by GET. It never clicks and never submits.
Never touched (deny list, by URL): logout, signout, login, signup, join, anything with "settings", delete, /new, edit, upload, remove, archive, transfer, billing, sponsors, marketplace, security/advisories, codespaces/new, /apps/, oauth, /sessions, /account, password, 2fa, invitations, unsubscribe, star, fork, watch, subscribe, follow, block, report, /compare, and image/zip/pdf files.

## Front door (home page) https://github.com/

Top bar (same on every signed-in page, left to right):
- Dashboard / home: https://github.com/
- Copilot: https://github.com/copilot
- Issues: https://github.com/issues
- Pull requests: https://github.com/pulls
- Repositories: https://github.com/repos
- Notifications: https://github.com/notifications
- Search: button "Open quick search dialog, type / to search". Press / to open it. The full search page is https://github.com/search.
- Buttons "Open Copilot…" and "Open agents panel" sit next to it.

Account switcher (the "gugosf114" menu on the dashboard):
- gugosf114 (personal): https://github.com/
- abrahamyants (organization dashboard): https://github.com/orgs/abrahamyants/dashboard
- Manage organizations: https://github.com/settings/organizations (settings, not crawled)
- Create organization: https://github.com/account/organizations/new (not crawled)

Main areas of the dashboard:
- Home tab: https://github.com/  and Feed tab: https://github.com/feed
- Banner "Save your seat" (Universe 2026) and "Go to GitHub Education": ads, ignore.
- Changelog list on the side, links to https://github.blog/changelog
- "Dashboard preview options" with a "Switch to classic dashboard" button, and a feedback form (4 radio buttons VERY_NEGATIVE to VERY_POSITIVE, a textarea "content", Cancel, Send feedback).
- Footer, listed once here: Terms https://docs.github.com/site-policy/github-terms/github-terms-of-service, Privacy https://docs.github.com/site-policy/privacy-policies/github-privacy-statement, Security https://github.com/security, Status https://www.githubstatus.com/, Docs https://docs.github.com/, Contact https://support.github.com/?tags=dotcom-footer, Manage cookies (button), Do not share my personal information (button).
- Profile menu items (avatar menu) did not show up in the crawl; it opens by click only. Known standard paths: profile https://github.com/gugosf114, settings https://github.com/settings/profile (standard path, not crawled).

## Rooms, one per page

### Home dashboard, https://github.com/
Doors: Copilot /copilot, Issues /issues, Pull requests /pulls, Repositories /repos, Notifications /notifications, Feed /feed, org dashboard /orgs/abrahamyants/dashboard, Security https://github.com/security.
Signs: Open quick search dialog; Open Copilot…; Open agents panel; Dashboard preview options; Switch to classic dashboard; Give feedback; Send feedback; Cancel; Close; Dismiss error. Inputs: 4 sentiment radios, textarea "content".

### Copilot chat, https://github.com/copilot
Doors: New chat /copilot; Agents https://github.com/copilot/agents; Spaces https://github.com/copilot/spaces; View all sessions https://github.com/copilot/agents?q=is%3Aopen; Plans https://github.com/features/copilot/plans; Copilot app https://github.com/features/ai/github-app; 4 task pages (see below) and PRs mbcpartyco/pull/1 and drift-auditor/pull/1.
Signs: "gugosf114, Copilot Student"; Condense sidebar; Model: Auto; Optimized for: Balance. Inputs: textarea "Ask anything or type @ to add context"; file input "image-uploader".

### Copilot Agents, https://github.com/copilot/agents  and Spaces, https://github.com/copilot/spaces
Small pages. 13 and 14 links. Agents has 12 buttons, Spaces has 9. One textarea-style input each.

### Copilot task pages (4)
- https://github.com/gugosf114/mbcpartyco/tasks/93df7331-f16e-4b7b-99eb-42c7c5438615 (Troubleshooting HTTPS enforcement toggle)
- https://github.com/gugosf114/bakers-agent/tasks/adeed354-c604-4c80-b4a2-096971c5b7ce (New task)
- https://github.com/gugosf114/bakers-agent/tasks/26542abb-29b2-44a0-a465-f98bc7c95403 (New task)
- https://github.com/gugosf114/drift-auditor/tasks/538dbf05-0daa-498e-8782-3a858b089239 (drift auditor review, 49 buttons)

### Copilot marketing pages
Plans https://github.com/features/copilot/plans (184 links) and app https://github.com/features/ai/github-app (131 links). Marketing nav only. Skip.

### Issues (yours, all repos), https://github.com/issues/assigned
Doors: Assigned to me /issues/assigned; Created by me /issues/created; Mentioning me /issues/mentioned; Recently updated /issues/recent; saved view https://github.com/issues/SSC_kgDOACDbBg.
Signs: Open 0 / Closed 0 tabs; "New issue" button; "Collapse sidebar". Input: text box with the query `is:issue state:open archived:false assignee:@me sort:updated-desc`. All five views looked empty (0 open).

### Pull requests inbox, https://github.com/pulls/inbox
Doors: Inbox /pulls/inbox; Authored by me /pulls/authored; Assigned to me /pulls/assigned; Involves me /pulls/involves; Review requests /pulls/reviews. Lists 5 open PRs: heirloom-android#18, gugosf114.github.io #350 to #353.
Signs: Select repositories; "Filter by age: Last month"; section toggles Needs your review, Needs your teams' review, Your drafts, Waiting for review or checks, Needs action, Ready to merge. No text input on inbox.

### Pull requests, Authored by me, https://github.com/pulls/authored
Doors: tabs Open 22 and Closed 825 (https://github.com/pulls/authored?q=is%3Apr+author%3A%40me+state%3Aclosed+archived%3Afalse+sort%3Aupdated-desc); 22 PR links across repos gugosf114.github.io, abrahamyants/lavrentiy, abrahamyants/wim-android, collaboration-inception, conversation-corpus, heirloom-android.
Signs: Filter by repository; Filter by author. Input: query `is:pr author:@me state:open archived:false sort:updated-desc`.
Other PR views (same layout, one query box each): /pulls/assigned, /pulls/involves, /pulls/reviews.

### Repositories, https://github.com/repos
Doors: My contributions /repos?q=contributed-by:@me; My repositories /repos?q=owner:@me; My forks /repos?q=owner:@me%20fork:true; Admin access /repos?q=admin:@me; New repository https://github.com/new (not crawled). About 221 links: per repo a link, a "commit activity" link, forks, stargazers, issues, pulls, settings.
Repos seen: gugosf114/gugosf114.github.io, gugosf114/bakers-agent, abrahamyants/wim-calls, abrahamyants/wim-android, abrahamyants/lavrentiy, gugosf114/bakers-agent-2, gugosf114/noisefile-android, and more.
Signs: Collapse sidebar; Show 4 more topics. Input: text box with `contributed-by:@me`.

### Notifications, https://github.com/notifications?query=is%3Aunread
Doors: Notification settings /settings/notifications; Watched repositories /watching; Subscriptions /notifications/subscriptions; Inbox /notifications; Saved ?query=is%3Asaved; Done ?query=is%3Adone; by reason: Assigned reason%3Aassign, Participating reason%3Aparticipating, Mentioned reason%3Amention, Team mentioned reason%3Ateam-mention, Review requested reason%3Areview-requested; per repo `?query=repo%3Aowner%2Fname` (14 repos, for example bakers-agent 123 unread). Each notification links to a PR or an actions run.
Signs: Filter; Customize filters; All; Unread; Sort by (Newest to oldest, Oldest to newest); Group by (Repository, Date); Done; Unsubscribe; More options; Mark as read; Mark as unread; Select all 310 notifications; Select all; Clear selection; Move to inbox; Subscribe; Save; Unsave; Previous. Inputs: query box `is:unread`; one checkbox per notification (name is the notification id, starts with NT_); a select-all checkbox.
Inbox count at draw time: 310.

### Search, https://github.com/search
Doors: advanced search https://github.com/search/advanced.
Signs: button "prefixes". Input: text box named "Search GitHub".
Result URLs look like https://github.com/search?q=TEXT&type=Repositories (seen on /repos topic links).

### Org dashboard, https://github.com/orgs/abrahamyants/dashboard
Doors: View organization https://github.com/abrahamyants; Browse repositories https://github.com/orgs/abrahamyants/repositories; activity entries link to wim-android branches, commits, PRs (#39 to #45), and the release https://github.com/abrahamyants/wim-android/releases/tag/v1.0.0-2026-10-13-full.
Signs: Filter; reaction buttons (thumbs up, heart, rocket…); Undo; Dismiss.

### Feed, https://github.com/feed
Doors: your repos list on the left (gugosf114.github.io, bakers-agent, wim-calls, wim-android, lavrentiy, bakers-agent-2, noisefile-android, agent-bridge, glm-george-recipe, signal); Trending https://github.com/trending ("See more"); starred-by-others repo cards.
Signs: Show more; Filter; Create list; "Starred, click to unstar this repository" (do not click).

### Security landing, https://github.com/security
Marketing page (132 links): features, solutions, resources. Skip. Search box is "Search or jump to".

### Community discussions, https://github.com/orgs/community/discussions/
Public forum. Doors: Overview /community; Discussions /orgs/community/discussions; Packages; People; categories /orgs/community/discussions/categories/<name>; filters Open, Closed, Locked, Answered, Unanswered via `?discussions_q=`.
Signs: Sort by: Latest activity; Filter labels; Filter: Open; "New discussion" /orgs/community/discussions/new/choose (not crawled). Inputs: `is:open` text; "filter" search box.

### A repo home page, https://github.com/gugosf114/gugosf114.github.io  (same layout for bakers-agent)
Doors (repo tab bar): Code (repo root); Issues /issues; Pull requests /pulls; Agents /agents?author=gugosf114; Actions /actions; Projects /projects; Wiki /wiki; Security /security; Insights /pulse; Settings /settings (listed, never opened). Also: /branches (99), /tags, /commits/main/ (1,415 commits), /activity, /stargazers, /watchers, /forks, /graphs/commit-activity, /tree/main/<folder>, /commit/<sha>, topics /topics/<name>, site link https://mybakingcreations.com/. About 400 links, most are file and folder links ("N repo links like /tree/main/<dir>, /blob/main/<file>").
Signs: Go to file; Add file; main branch; Code; Watch; Star; Unpin; Edit repository metadata; View all files; Outline. Input: "Go to file" text box.

### Repo issues, https://github.com/gugosf114/gugosf114.github.io/issues
Doors: filters via `?q=` (assigned, author, mentions), Views /issues/views, Milestones /milestones, Labels /labels, New issue /issues/new/choose (not crawled).
Signs: Filter by author; labels; projects; milestones; Issues type menu. Input: `is:issue state:open`.

### Repo pull requests, https://github.com/gugosf114/gugosf114.github.io/pulls
Doors: Open 14 `?q=is%3Apr+state%3Aopen`; Closed 341 `?q=is%3Apr+state%3Aclosed`; Authored /pulls/gugosf114; Assigned /pulls/assigned/gugosf114; Involves /pulls/involves/gugosf114; Review requests /pulls/review-requested/gugosf114; Milestones; Labels; Stacks /stacks; New pull request /compare (not crawled); 14 PR links /pull/<n>.
Signs: Filter by author, label, projects, milestones, reviews, assignee; Sort by Newest descending; Filter by review: Review required; Feedback. Inputs: `is:pr state:open`; one checkbox per PR ("Select: <title>"); select-all "default".

### A pull request page, example https://github.com/gugosf114/gugosf114.github.io/pull/353 (also .../pull/350 to 352, heirloom-android/pull/18, mbcpartyco/pull/1, drift-auditor/pull/1)
Doors: tabs Conversation /pull/N; Commits /pull/N/commits; Checks /pull/N/checks; Files changed /pull/N/changes; branch links /tree/<branch>; commit links; Open in github.dev; Open in codespace (do not open).
Signs: Copy code; reaction buttons; Positive/Negative feedback; many form controls: Reason (select), comment textarea "new_comment_field", file input, "Find a user", reviewer/assignee/label checkboxes. These are write controls. A reader should not touch them.

### Repo small pages
Commit graph (…/graphs/commit-activity), Forks (…/forks), Stargazers (…/stargazers): repo tab bar plus a few links, 7 buttons, no inputs.

## Fastest routes

- Pull requests page, all repos: https://github.com/pulls  (inbox: https://github.com/pulls/inbox; mine: https://github.com/pulls/authored)
- Notifications: https://github.com/notifications  (unread only: https://github.com/notifications?query=is%3Aunread)
- List my repos: https://github.com/repos?q=owner:@me  (also https://github.com/gugosf114?tab=repositories, standard path, not crawled)
- A repo's settings page: https://github.com/OWNER/REPO/settings  (pattern seen as a link on /repos, never opened)
- Search code: https://github.com/search?q=YOUR+TEXT&type=code  (standard path, not crawled)
- My issues: https://github.com/issues/assigned  (created by me: https://github.com/issues/created)
- My PRs: https://github.com/pulls/authored
- Create a new repo: https://github.com/new  (seen as the "New repository" link on /repos; not opened)
- Bonus: one repo's PR list https://github.com/OWNER/REPO/pulls ; one PR https://github.com/OWNER/REPO/pull/N ; one repo's Actions https://github.com/OWNER/REPO/actions

## What a dumb script needs to know

- Every signed-in page has the same six top links, in this order: /, /copilot, /issues, /pulls, /repos, /notifications. Their text is empty (icons). Key on the href, not the text.
- Quick search: the button's accessible name is "Open quick search dialog, type / to search". Pressing "/" opens it. The real search page is /search and its input is named "Search GitHub".
- Query boxes on list pages are plain text inputs whose value is the current filter, for example `is:pr author:@me state:open archived:false sort:updated-desc`. Edit the value and press Enter, or just build the URL with `?q=`.
- Most state lives in the URL: `/notifications?query=...`, `/repos?q=...`, `/OWNER/REPO/pulls?q=...`, `/orgs/community/discussions?discussions_q=...`. Prefer URLs over clicking.
- Tab names on a repo: Code, Issues, "Pull requests N" (count is inside the link text), Agents, Actions, Projects, Wiki, Security, Insights (/pulse), Settings.
- Counts are baked into link text: "Open 22 (22)", "Closed 825 (825)", "Inbox 310". Strip digits before matching names.
- Notification rows have one checkbox each; its name is the notification id (starts with NT_). Bulk buttons appear after ticking: Done, Mark as read, Unsubscribe, Save.
- Pagination: the notifications page has a "Previous" button (a "Next" button was not seen in the crawl). `?page=N` is the standard way on list pages (standard path, not crawled).
- Popups to expect: "Dismiss error" button, cookie buttons "Manage cookies" and "Do not share my personal information", and the Universe banner. They are on nearly every page and are safe to ignore.
- Do not touch: Star, Unpin, Watch, Open in codespace, Switch to classic dashboard, any comment box. These change things.
- Copilot chat input is a textarea with placeholder "Ask anything or type @ to add context".
