Deploying to AWS with autoscaling
=================================

This deploy system makes heavy use of
`Fabulaws <http://fabulaws.readthedocs.org/en/latest/index.html>`_.
Please at least skim those docs first.

Note that there are a few changes in this project from the
default architecture described in the Fabulaws docs:

* We use django-pipeline instead of django-compressor.
* We serve the static files from the Django processes in
  our web servers instead of using S3.

Terms
-----

These are some terms that'll be used in the deploy files.

*Deployment:* The project. In this case, ``opendebates``.

*Environment:* A configuration and set of one or more systems that
make the project available on the network with a unique domain and
set of data.  For example, we might have testing, staging,
and production environments.

*Role:* Each system in an environment plays one or more roles, meaning
that it provides some service to the environment. Example roles include
db-master, db-slave, cache, web, worker, etc.

From scratch
------------

AWS console
~~~~~~~~~~~

Currently there's some manual setup required in the AWS console
before we can start using the automation.

Please work *carefully and thoroughly* through the
`Fabulaws initial setup documentation <http://fabulaws.readthedocs.org/en/latest/initial-setup.html>`_, changing
``myproject`` to ``opendebates``.  This will include creating security groups,
creating a load balancer, and creating an autoscaling group.

You can skip most of the *Project Configuration* section because that's
already been done for this project, but review it to be sure.

Autoscaling policies
~~~~~~~~~~~~~~~~~~~~

This part isn't covered in the Fabulaws docs. These are example policies
to start with for the autoscaling group.

Notifications
+++++++++++++

These alarms are configured on the load balancer,
actually.

Alarm: Backend Connection Errors
* Threshold: BackendConnectionErrors >= 1 for 5 minutes
* Actions:
  * in ALARM:
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
* Namespace: AWS/ELB
* Metric name: BackendConnectionErrors
* Dimensions: LoadBalancerName = xxxxxxxxxxxx
* Statistic: Sum
* Period: 5 minutes

Alarm: Healthy Hosts
* Description: Production healthy hosts <.95
* Threshold: HealthHostCount < 0.95 for 5 minutes
* Actions:
  * in ALARM:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in OK:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in INSUFFICIENT DATA:
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
* Namespace: AWS/ELB
* Metric name: HealthHostCount
* Dimensions: LoadBalancerName = xxxxxxxxxxxx
* Statistic: Average
* Period: 1 minute

Alarm: Project Production Latency
* Description: Latency >= .5 seconds
* Threshold: Latency >= 0.5 for 10 minutes
* Actions:
  * in ALARM:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in OK:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in INSUFFICIENT DATA:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
* Namespace: AWS/ELB
* Metric name: Latency
* Dimensions: LoadBalancerName = xxxxxxxxxxxx
* Statistic: Average
* Period: 5 minutes

Alarm: Prod RequestCount
* Description: Prod RequestCount > 95000
* Threshold: RequestCount > 25,000 for 5 minutes
* Actions:
  * in ALARM:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in OK:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
  * in INSUFFICIENT DATA:
    * Send message to topic "client" (foo@lists.example.com)
    * Send message to topic "caktus" (xxx-team@caktusgroup.com)
* Namespace: AWS/ELB
* Metric name: RequestCount
* Dimensions: LoadBalancerName = xxxxxxxxxxxx
* Statistic: Sum
* Period: 5 minutes

Scale up/scale down actions
+++++++++++++++++++++++++++

These are on the autoscaling group.

Scale down:
* Threshold: CPUUtilization <= 5 for 30 minutes
* Actions:
  * in ALARM:
     * For group THIS_AUTOSCALING_GROUP use policy Decrease Group Size (Remove 2 instances)
* Namespace: AWS/ELB
* Metric name: CPUUtilization
* Dimensions: AutoScalingGroupName = THIS_AUTOSCALING_GROUP
* Statistic: Average
* Period: 5 minutes

Scale up:
* Threshold: CPUUtilization >= 40 for 5 minutes
* Actions:
  * in ALARM:
     * For group THIS_AUTOSCALING_GROUP use policy Increase Group Size (Add 2 instances)
     * Send message to topic "XCGVDFSDFSDFS" (xxxx-team@caktusgroup.com)
  * In INSUFFICIENT DATA:
     * Send message to topic "XCGVDFSDFSDFS" (xxxx-team@caktusgroup.com)
* Namespace: AWS/ELB
* Metric name: CPUUtilization
* Dimensions: AutoScalingGroupName = THIS_AUTOSCALING_GROUP
* Statistic: Average
* Period: 5 minutes


Changes to project files
~~~~~~~~~~~~~~~~~~~~~~~~

In ``fabulaws-config.yml`` in this project, find the section that
looks like this::

    site_domains_map:
      production:
      - dualstack.myproject-production-1-12345.us-east-1.elb.amazonaws.com
      staging:
      - dualstack.myproject-staging-1-12345.us-east-1.elb.amazonaws.com
      testing:
      - dualstack.myproject-testing-1-12345.us-east-1.elb.amazonaws.com

and change the domain under the environment you're setting up to the
full hostname of the load balancer you just created.

Also look for this section::

      auto_scaling_groups:
        opendebates:
          production: opendebates-production-ag
          staging: opendebates-staging-ag
          testing: opendebates-testing-ag

and change the appropriate value to the name of the autoscaling group you
created.  (Or create it with that name to begin with.)

Automation commands
~~~~~~~~~~~~~~~~~~~

If you are creating a new environment and no servers exist
yet, you can run this command to set them all up at once::

    fab create_environment:opendebates,<environment>

This took 17 minutes the last time I tried it, which doesn't seem bad
at all (with system sizes like c3.large and m3.large or faster).

You only need to do it once per environment.  After that, you can follow
the instructions below for updating things.  You'll need to do at least one
deploy to get web servers(s) up and running.

Manual steps
------------

These are more things that should probably be automated, but aren't yet.

Enable unaccent extension: See comments at https://caktus.atlassian.net/browse/OP-105

Load zip code database: See comments at https://caktus.atlassian.net/browse/OP-104

Updating code
-------------

This is what to do when the code changes and you want the servers in
an environment to switch to the newer code.

Read through this whole section before starting to update anything,
please!

Step 1: Make sure secrets are updated. Review your ``fabsecrets_<environment>.py`` file and update
any secrets that need updating. (Run ``fab <environment> update_local_fabsecrets`` to first pull a
copy from the current worker server, if needed). If any have changed, or you just want to be sure
that everything is in sync on the web and worker servers, run the following command::

     fab <environment> update_server_passwords

NOTE: While this will also update the secrets file on the database, cache, and queue servers, there
is no mechanism for that file to be re-read on those roles. Those roles will continue using old
secrets.

Step 2: Create a new launch configuration. This is a saved EC2 instance image
that the autoscaler uses to spin up new web servers::

     fab create_launch_config_for_deployment:opendebates,<environment>

On an m1.small instance, this'll take just over 20 minutes. It might be faster
if your web servers are using a faster server.

At the end of the output of that command, it'll print out a long string that
is the name of the new launch configuration. Save that somewhere.

Step 3: Update the servers

There are two ways to do this, and it's important to choose the right
one.

A "full" deployment should be used any time there are backwards-incompatible
updates to the application, i.e., when having two versions of the code running
simultaneously on different servers might have damaging results or raise errors
for users of the site.  Note that this type of deployment requires downtime,
which needs to be scheduled ahead of time.

To perform a full deployment, including downtime::

    fab deploy_full:opendebates,<environment>,<launch config name>

This'll put up an "upgrade in progress" notice on the site, take down all the
webservers, create new ones using the new launch config, and take down the
upgrade notice again once everything looks okay. In my testing a successful
full deploy took about 4 minutes.

A “serial” deployment can be used any time the changes being deployed are minimal enough that
having both versions of the code running simultaneously will not cause problems. This is usually
the case any time there are minor, code-only (non-schema) updates.

To perform a serial deployment::

    fab deploy_serial:opendebates,<environment>,<launch config name>

This will take the web servers down one at a time and bring up a replacement,
waiting each time until the replacement is healthy before doing the next. It'll
take quite a while if there are many servers, but no downtime is needed.

Shortcuts
~~~~~~~~~

For test purposes, you can skip creating the new launch configuration and
just update the servers in place::

    fab <environment> begin_upgrade deploy_worker deploy_web end_upgrade

or::

    fab deploy_full_without_autoscaling:opendebates,<environment>

Just be aware that if the autoscaling group starts any new web servers,
they'll be running the code from the old launch configuration, which could
break things. You can suspend the autoscaling group to avoid that though::

    fab suspend_autoscaling_processes:opendebates,<environment>
    fab resume_autoscaling_processes:opendebates,<environment>

Of course, don't do this in production.

Also - *don't forget to resume*!  Even a full deploy won't completely
undo a suspend - actually, having the AG processes suspended will break
deploys.

Help
----

There's lots of good information in the Fabulaws
`Maintenance <http://fabulaws.readthedocs.org/en/latest/maintenance.html>`_
and
`Troubleshooting <http://fabulaws.readthedocs.org/en/latest/troubleshooting.html>`_
pages.

Monitoring
----------

After initial server setup and after deploys, be sure that you see servers for all roles in the
'running' state in the `Amazon EC2 console
<https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:tag:environment=staging;tag:Name=opendebates;sort=desc:launchTime>`_.

You should also be able to view more detailed monitoring info at `NewRelic
<https://rpm.newrelic.com/accounts/343744/applications>`_.

To be determined
----------------

* How do we control the autoscaling?
