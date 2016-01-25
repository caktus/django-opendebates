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

(These might change, especially the not using S3 part, but they're
correct at the time this is written.)

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
already been done for this project, except for
`SSH Keys <http://fabulaws.readthedocs.org/en/latest/initial-setup.html#ssh-keys>`_.

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

Now you can run this command to set up everything else::

    fab create_environment:opendebates,<environment>

It'll take a while (30 minutes? an hour?) but you only need to do it
once per environment.

Updating code
-------------

This is what to do when the code changes and you want the servers in
an environment to switch to the newer code.

Read through this whole section before starting to update anything,
please!

Step 1: Create a new launch configuration. This is a saved EC2 instance image
that the autoscaler uses to spin up new web servers::

     fab create_launch_config_for_deployment:opendebates,<environment>

On an m1.small instance, this'll take just over 20 minutes. It might be faster
if your web servers are using a faster server.

At the end of the output of that command, it'll print out a long string that
is the name of the new launch configuration. Save that somewhere.

Now, which order you do steps 2 and 3 in might depend on whether you
have migrations and whether it's okay for the migration to run before
the web servers have been updated, or for the web servers to be updated
before the migrations are run, or whether they really really need to happen
at the same time.

If you can run migrations first, or don't have any, do step 2, then step 3.

If you have to update webservers first, do step 3, then step 2.

If you really have to update things all together, skip down a bit
to "Updating everything at once".

Step 2: Update your worker(s)::

    fab <environment> deploy_worker

This will also run migrations.

Step 3: If the changes are minor, such that it's okay if some servers are
temporarily running the newer code while others are still running the older,
then you can update the web servers without downtime::

    fab deploy_serial:opendebates,<environment>,<launch config name>

This will take the web servers down one at a time and bring up a replacement,
waiting each time until the replacement is healthy before doing the next. It'll
take quite a while if there are many servers, but no downtime is needed.

If you need to update things all at the same time, some downtime will be needed.
On the bright side, this command will run much faster than the other one.
Here it is::

    fab deploy_full:opendebates,<environment>,<launch config name>

This'll put up an "upgrade in progress" notice on the site, take down all the
webservers, create new ones using the new launch config, and take down the
upgrade notice again once everything looks okay. In my testing it took about
4 minutes each time.

Updating everything at once
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you really have to take it all down, run migrations, update all the code,
and only then bring things back up, do this::

    fab <environment> begin_upgrade

That'll stop sending requests to the Django web processes.  Wait a minute
to let any requests in progress complete. Next::

    fab <environment> deploy_worker

That'll update the code on the workers and run the migrations.  Finally::

    fab deploy_full:opendebates,<environment>,<launch config name>

which will update the web servers and take down the upgrade page.

Shortcuts
~~~~~~~~~

For test purposes, you can skip creating the new launch configuration and
just update the servers in place::

    fab <environment> begin_upgrade deploy_worker deploy_web end_upgrade

Just be aware that if the autoscaling group starts any new web servers,
they'll be running the code from the old launch configuration, which could
break things. You can suspend the autoscaling group to avoid that though::

    fab suspend_autoscaling_processes:opendebates,<environment>
    fab resume_autoscaling_processes:opendebates,<environment>

Of course, don't do this in production.

Help
----

There's lots of good information in the Fabulaws
`Maintenance <http://fabulaws.readthedocs.org/en/latest/maintenance.html>`_
and
`Troubleshooting <http://fabulaws.readthedocs.org/en/latest/troubleshooting.html>`_
pages.

To be determined
----------------

* How do we control the autoscaling?
