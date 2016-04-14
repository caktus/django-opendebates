Release Notes
=============

v0.0.6 on 2016-04-14
--------------------

* Incorporate SITE_THEMES for customization of Florida static content (#133)
* More style polish from Ethan (#135)
* Track and sort by local vote counts (#136)
* Add Facebook/Twitter meta tags (#137)
* Coverage / gitignore improvements (#132, #134)

v0.0.5 on 2016-04-07
--------------------

* Add runtime settings for disabling voting, submissions, sorting
  by votes, displaying submission votes, and displaying total votes,
  as well as setting the debate date/time. (#125, #129)
* Styles and popups (#128, #126, #120)
* Fix 500 error on bad category (#124)
* Set email_from addresses (#122)
* Clean up Django settings for tests (#121)

v0.0.4 on 2016-04-05
--------------------

* Add deploy for florida debate server (#113)
* Track using mixpanel (#114)
* Many style updates, including modals and responsive behavior, footer
* Allow anonymous user to reused a user account's email address (#107)
* Don't require a logged-in user to fill in the captcha on first vote (#107)
* Return to homepage after logout (#108)
* Hide merged duplicates on page load
* Lazy pagination
* Search fixes (#99, #96)

v0.0.3 on 2016-02-17
--------------------

* Implement design, including but not limited to header, logo,
  social sharing sidebar, question form, mobile layout,
  layout of "you may be interested in" questions, total votes
  counter, countdown time remaining
* Implement flagging questions for removal or merge
* Implement "forgot password" flow from login page link
* Fraud prevention:
  * Add re-CAPTCHA for registration and a user's first vote
* Changes for performance:
  * cache fragments of pages
  * remove unused code for comments
  * template caching
  * query optimizations in multiple views
  * send transactional emails from background tasks
  * move to larger servers than we had been testing with (but still within
    the sizes from the original proposal)
  * route read-only requests' queries to the database replica rather
    than the master database'
  * deploy behind CloudFlare
* Move testing servers to testing.demopenquestions.com
* Run trending questions update task every ten minutes

Some known issues/tasks not yet done:

* No social meta tags
* No about, changelog, partners pages or nav for them
* No popups
* No readonly DB connection
* Miscellaneous little UI issues to clean up
* BP would still like to improve "random" and "trending" algorithms

Plus things that can't be done until the schedule is set.

v0.0.2 on 2016-02-04
--------------------

* Add relations to router.
* Run trending score task.
* Larger web instances
* Implement site header design.

v0.0.1 on 2016-02-04
--------------------

* DO NOT USE. Bug fixed in 0.0.2
* Initial release of Caktus modifications
