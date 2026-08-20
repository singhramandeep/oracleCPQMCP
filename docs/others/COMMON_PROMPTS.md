This document lists sample prompts you can try.

**Developer — after any tool change**

Paste the contents of [`prompts/compliance_check.md`](../../prompts/compliance_check.md) into Cursor so the agent checks the diff against [`docs/STANDARDS.md`](../STANDARDS.md) (fast pass; not a full audit).

Canonical prompt list (kept up to date): [`docs/COMMON_PROMPTS.md`](../COMMON_PROMPTS.md). Tasks / configuration / newer BML+datatable export tools are **untested live** — see [README testing status](../../README.md#testing-status-live-cpq).

**Users**
Which users have not logged in for a long time?
Make a list of all the users which have email id in the gmail domain

**BML**
Get all the BML code and list all BML files

**Commerce**
make a list of 20 commerce attributes which were recently modified along with thir last modified date

**Data Tables**
make a list of all the data tables, when they were deployed and how many rows in each of the tables

**Tasks / exports** (untested live)
Start a data table export dry-run, then explain get_task / download_task_file

**Configuration** (untested live)
List product families and attributes at scope=family

**Performance logs**
List the 5 slowest performance log events by serverTime
Show performance log details for event id 12345
What is the average time save action has taken in the past 5 days?

**users**
Set the first name of the user xyz to "New Name"
help me with usernames of 10 users which were modified recently. List down their last modified date
How many users exist in both test and dev environment? identify a user by its email id
