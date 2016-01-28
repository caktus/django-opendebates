Setting up Cloudflare
=====================

* Create or get access to a cloudflare account

* You'll need control of a domain that you can change the name servers on.
  (Your website can be a subdomain of it though.)
  E.g. this is a domain that's hosted by some domain name provider like
  GoDaddy, and not a subdomain of such a domain. We'll call this the
  "root" domain, to distinguish it from the "web site domain" (though
  they could actually be the same if you want).

* Click "Add site" at the top of the cloudflare page

* Enter the root domain name.

* It'll take it a minute to look up your current DNS records.

* It'll tell you a couple of name server names. Go to your domain's settings
  (in GoDaddy or wherever) and update your domain's nameservers to the cloudflare
  ones.

It might take a while before queries for your domain are going to Cloudflare instead
of your old nameservers, but you can keep setting things up meanwhile.

* If you haven't already, add your website domain to the DNS. If this is
  going through Amazon ELB, you can make it a CNAME to the LB's hostname.

* Be sure the cloud icon next to your website domain is orange, indicating that
  requests to that domain will go through Cloudflare.

* Click "Page rules" at the top.

* Add a page rule, pattern "http://websitedomain/*", and choose "Always
  use https".

* Add another page rule, pattern "websitedomain/*", and choose SSL Mode:
  Full SSL.

Now wait for the DNS to update.
