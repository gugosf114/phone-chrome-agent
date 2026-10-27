# Thursday — the bakery's order and customer book · WEIGHT: FULL (in daily use by Yana and George)

**What it is.** George's own order-management app for My Baking Creations, the thing other bakeries buy Monday.com or
HoneyBook for. A password-protected web app at mybakingcreations.com/thursday, installable on the phone (PWA), synced live
across devices (Firebase Realtime Database + Firebase Storage for attachments and sketches). Built by George, used by Yana as
head baker.
**What it does.** Dashboard with overdue and due-today alerts, counts (active orders, due this week, unpaid invoices, sketches
pending), revenue paid and outstanding, average order value, a due-date list and a calendar. Active Orders and Archive tables:
customer, due date and time, item (cake, cookies, cupcakes, cake pops, macarons), components and sub-items, description,
flavor, quantity, invoice status (paid / sent / number), pickup or delivery with a map link, sketch status and sketch file,
contact, assigned person, attachments, order date; sort by due date, order date, or customer; mark complete, restore, delete;
CSV export. New Order form: assigned to, item type, customer, email, phone, flavor, quantity, pickup/delivery, components,
dates, price, description. "New from Email": paste a customer email and it extracts the order fields. An "Emotional Support"
button for the baker on a hard day.
**Live, 2026-10-27.** 53 active orders, 14 due this week, 29 unpaid invoices, 39 sketches pending; $17,013 paid, $14,293
outstanding; corporate orders due this week for American Express, BNY, Accel, Willkie Farr & Gallagher, ServiceNow (756 cake
pops in 63 boxes).
**What it proves.** He built the operations tool a real business runs on every day, with the data model, alerts, and
workflow a small shop actually needs, and it has held up through hundreds of orders.
**The sentence.** "I built Thursday, the order and customer management app my family's bakery runs on every day: live-synced
orders, due-date alerts, invoices, sketches, delivery, and an email-to-order parser."
**Cite when:** internal tools, CRM / order management, operations software, small-business systems, Firebase, PWAs, "built
what the business needed instead of buying it".
**Rule.** Customer names and dollar figures stay out of letters; describe the tool.
**Proof.** mybakingcreations.com/thursday (password in thursday/index.html, repo gugosf114/gugosf114.github.io)
