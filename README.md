earwig
======
A unified contact engine powered by Open Civic Data

Project Definition
------------------

Goals:

* Enable meaningful and direct communication between constituents and their government.
* Enable representatives to more easily handle flow of contacts and make timely responses.
* Keep project data-source agnostic, OCD is primary data source but backend could be switched.
* Provide API through which other applications can leverage system to add contact-your-rep functionality.
* Learn optimal ways to ensure communication reaches legislator, employing wide range of approaches to maximize successful contacts.

Non-Goals:

* Provide platform for political groups to send bulk-emails.
* Provide mechanism for harvesting emails / list-building.

Infrastructure
--------------

Contact Engine

* API-driven for easy integration into multiple system (web, mobile, etc.)
* given components of a message (from, to, contents) enter it into a queue
* send messages by processing queue and determining optimal method(s) of contact
* analytics component analyzing/predicting response rates, gather data from day 1

Public Site

* front page "find your location"
* list of jurisdictions & reps
    * messages to individuals
    * messages to groups (V2)
* legislator pages (V2)
* point people to anthropod where there are gaps in knowledge

Anthropod+

* use MagicScraper(tm) technology to get options for user
* make Anthro more userfriendly

Open Questions
--------------

* public vs private contact?
* how do we handle people being out of session?
* allowing officials to claim accounts?
* GIS uncertainity (we have city but not wards)
    * leverage Google API?
    * present w/ entire ward
    * "I know my ward" -> heatmap?

API
---
POST /sender/
    Get or create a sender object.  Useful for pre-authorization/looking up an existant key.
    params: email, name, ttl

POST /message/
    Create a message to be delivered by the earwig.
    params: type, subject, message, sender (key or JSON payload), app_key
    return: message body

GET /message/<message_id>/
    get message body
    return: message body
