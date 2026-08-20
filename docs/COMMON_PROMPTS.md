This document lists down sample prompts that you can try.

**Developer — after any tool change**

Paste the contents of `[prompts/compliance_check.md](../prompts/compliance_check.md)` into Cursor so the agent checks the diff against `[docs/STANDARDS.md](STANDARDS.md)` (fast pass; not a full audit).

Live-status note: prompts under **Tasks / exports**, **Configuration**, and the newer BML/datatable write flows use tools that are **untested against live CPQ** (offline contracts only). Prefer dry-run / read-only exploration until they are smoke-tested. See [README.md](../README.md#testing-status-live-cpq).

**Users**
Which users have not logged in for a long time?
Make a list of all the users which have email id in the gmail domain

Give a list of all  the users who have not logged in the past 90 days

Which all users are common in both the dev and test environments? Unique user is identified via the email ID

**Groups**

Give me a table that shows how many users are there in each group

Help me identify redundant user groups. If two (or more) user groups have exactly the same users one of them is redundant
**BML**
Get all the BML code and list all BML files

Which are the 10 biggest BML files? Give me the bml code for them

List built-in BML common functions (untested live)

Search BML scripts for a string and list util library folders (untested live)

**Commerce**
make a list of 20 commerce attributes which were recently modified along with thir last modified date

Give me details of the save_t action, owner_t attribute

**Parts**

how many parts are there in the system? give me details of the most recently created 10 parts



**Data Tables**
make a list of all the data tables, when they were deployed and how many rows in each of the tables

Create a new data table (dry-run only) — untested live

**Tasks / exports** (untested live)
Start a data table export for ModelMaster (dry-run first), then poll get_task and download the result file

**Configuration** (untested live)
List product families, then list attributes for the first family at scope=family

List models under a product family/line and fetch the layout cache attributes for one model

**Performance logs**  
List the 5 slowest performance log events by serverTime  
Show performance log details for event id 12345

What is the average time save action has taken in the past 5 days?

**Transaction**

give me details of the t ransaction with bsid 91920137

Can you share the details of all the lines from that quote in a table?i want all the attributes

Give me the list of 10 most recently updated quotes along with who created them, when it was created, who last udpated it and their status

**Transaction Layout**
What attributes are visible on the quote header layout?

Can you give me details of the quote CPQ-16553-1? List down the values of all the attributes that are visible on the header and line level layout

Export the attachment for quote transaction id 92299647 using attribute proposalAttachment_t
