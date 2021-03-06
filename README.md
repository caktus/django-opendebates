django-opendebates
=============

# Installation

(See below if you prefer to run locally using Docker, or hit the big time with Kubernetes.)

Install python 2.7, virtualenv, postgres.

```
$ createdb opendebates
$ mkvirtualenv opendebates -p `which python2.7`
(opendebates)$ pip install -r requirements/dev.txt
(opendebates)$ python manage.py migrate
(opendebates)$ python manage.py load_zipcode_database zips.csv
(opendebates)$ npm install bower less
(opendebates)$ cp .env.sample .env
(opendebates)$ echo "export PATH=$PWD/node_modules/.bin:$PATH" >> $VIRTUAL_ENV/bin/postactivate
(opendebates)$ deactivate
$ workon opendebates
(opendebates)$
```

Edit .env:

```
DATABASE_URL=postgres://@/opendebates
DJANGO_DEBUG=1
SITE_DOMAIN=0.0.0.0:8000
ALLOWED_HOSTS=0.0.0.0
```


Create a Site object:

```
(opendebates)$ python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.create(domain='0.0.0.0:8000', name='0.0.0.0:8000')
>>> ^D
```

Create a superuser:

```
(opendebates)$ python manage.py createsuperuser
Username: rnixon
Email address: rnixon@not-white-house.gov
Password:
Password (again):
Superuser created successfully.
```

Note, that any user created in the shell (or the admin) will not have a `Voter`
object associated with it, so it won't function properly on the frontend until
a `Voter` is created for it, which can be done through the admin.

Then you can start the development server:

```
(opendebates)$ python manage.py runserver 0.0.0.0:8000
```

Go to the *admin*: http://0.0.0.0:8000/admin/

Login as the superuser

Add a new Debate object:

* Be sure to use the site 0.0.0.0:8000
* Make note of the prefix you set, e.g. "nyc2019".

Create a `Voter` object (at the /admin/opendebates/voter/ URL) for the superuser
you created for yourself.

Now you can visit the site at http://0.0.0.0:8000/nyc2019/.

# To run locally using docker

* Install docker-compose and its dependencies.
* Your user needs to belong to group 'docker'. If not, add that group to your user,
  then log out and log in again to make that take effect. (Sorry, no other
  way that I know of to make user group changes take effect).
* Clone this repo and change to its directory.
* Create a virtualenv (using Python 2.7, sorry)

    ```$ mkvirtualenv opendebates -p `which python2.7` ```

* Activate virtualenv

    ```$ workon opendebates```

* Install the project requirements

    ```pip install -r requirements/dev.txt```

* Build the docker container

    ```docker-compose up --build -d```

* Run migrations in the docker container

    ```docker-compose run web python manage.py migrate --noinput```

* Create a superuser (so you can log into the admin)

    ```docker-compose run web python manage.py createsuperuser``` (answer prompts to create superuser)

    Note, that any user created in the shell (or the admin) will not have a `Voter`
    object associated with it, so it won't function properly on the frontend until
    a `Voter` is created for it, which can be done through the admin.

* Visit http://localhost:8000/admin/ and log in as the new superuser
* Create a new Debate and note its prefix
* Create a `Voter` object (at the /admin/opendebates/voter/ URL) for the superuser
you just created for yourself
* Visit http://localhost:8000/<prefix of the debate you just created>/
* When ready to shut the server down,

    ```docker-compose stop```

# Kubernetes

* Create a python virtualenv, activate, and install requirements for dev

    pip install -r requirements/dev.txt

  (Python 2 or 3 should work equally well, but of course 3 is better :-).)

* Get the opendebates ansible vault password from Lastpass and put it in a file
  ".vault_password" at the top level of the local directory where you have checked
  out this project.
* Install the Google Cloud SDK (https://cloud.google.com/sdk/install). Depending on how you
  install this, `kubectl` might not be included by default. You'll need it so be sure to install it too.
  That's at https://kubernetes.io/docs/tasks/tools/install-kubectl/.
* Run `gcloud auth login` once to login to the Google Compute Cloud with
  your Google account.  (If you get auth errors later, the first thing to try is
  doing this again.)
* Each environment uses a particular project on Google Compute Cloud.
  You can see these in the fabfile near the top.  Find out from another developer
  which environment or environments you will need to access, and how to get
  someone to give you that access.
* Run `fab testing` (or other environment name) to check your auth is working.

  *(Be sure to get this right, because whatever cluster you've set up this way is the one that's going to have all this stuff deployed to it.)*

* Run ```fab testing up``` - this will create or update the complete deploy.
* Wait for things to get going. (FIXME: what's a good provider-independent way to tell?)
  - some things might fail because previous steps aren't done yet. You can
    wait a minute then just run the whole thing again.
* See what the "EXTERNAL_IP" of the load balancer is:
  ```kubectl get ingress --namespace=opendebates-ENVIRONMENT```
* Pick a HOSTNAME.
* Go make a DNS entry for HOSTNAME pointing at that IP address
* ```fab testing createsuperuser```

    Note, that any user created in the shell (or the admin) will not have a `Voter` object
    associated with it, so it won't function properly on the frontend until a `Voter` is
    created for it, which can be done through the admin.

* Visit http://HOSTNAME/admin/ and log in as the new superuser
* Create a new Debate and note its prefix
* Create a `Voter` object (at the /admin/opendebates/voter/ URL) for the superuser
you just created for yourself

* Visit http://HOSTNAME/PREFIX/

To update the docker image used by Kubernetes:

* IF you want to use a different docker hub account than "caktus", change
  `fab` to`fab docker_hub:accountname` in the following commands; e.g.
  `fab docker_hub:dpoirier build`.
* Build a new image: ```fab build```
  In the output, note the tag assigned to the new image. It will have the
  format YYYYMMDDhhmmss, e.g. 20191008110643
* Publish your latest image: ```fab publish```. Notice where the push is
  going to in the output, e.g. ```The push refers to repository [docker.io/caktus/opendebates]```
* Update the ENVIRONMENT_vars.yml file for the environment you want to use the new
  image (e.g. kubernetes/testing_vars.yml),
  changing OPENDEBATES_IMAGE to the full name from the push,
  e.g. ```"docker.io/caktus/opendebates"```, and OPENDEBATES_VERSION to
  the tag that was assigned to this image.
* Deploy, e.g. ```fab testing up```.

To create a new environment for Kubernetes:

* Pick a name for the new environment, e.g. "staging" or "nov19debate". We'll
  refer to that as ENVIRONMENT.
* Add it to the list "ENVIRONMENTS" in fabfile.py.
* Create a new task for it in fabfile.py (just copy and edit the 'testing' task).
* Find out where the Postgres server is.
* Create or get the password for a postgres user named "opendebates_ENVIRONMENT"
* Create (if it doesn't exist) a database named  "opendebates_ENVIRONMENT" owned
  by  "opendebates_ENVIRONMENT"
* Create file kubernetes/ENVIRONMENT_vars.yml
  looking at the corresponding file for other environments to fill those in.
* To encrypt values, use "fab encrypt_string:STRING_TO_ENCRYPT".  Put the
  result (starting with "!vault") into the vars file in place of the unencrypted
  value.
  
To get backups working for a new environment, it's a bit fiddly:

* Create a Google Compute Platform service account by going to
  https://console.cloud.google.com/iam-admin/serviceaccounts,
  selecting the right project, then clicking "Create Service Account" at the top.
  Just pick a meaningful name. It doesn't need any permissions or access added
  here so if you're prompted, just decline.

* In the list of service accounts, you should now see your new one. Click the "three dots"
  in that account's row in the "Actions" column.  Select "Create Key".
  Download the resulting JSON file into the kubernetes directory.
  Use "fab encrypt_file:kubernetes/FILENAME" to encrypt it.

* In your ENVIRONMENT_vars.yml file, set "GS_CREDENTIALS_FILE" to the filename of the
  json file, without any path.

* Create a Google Storage bucket by going to https://console.cloud.google.com/storage/browser and
  clicking "Create Bucket".

* Click on the new bucket in the bucket list, go to its permissions tab, "Add Members",
  and add the service account you just created by entering its email address (or enough
  for it to autocomplete).

* Give the service account both "Storage Object Viewer" and "Storage Object Creator"
  roles.

# Site copy and content

We're relying on Django's i18n system for managing site copy.  An "English translation"
should be generated and used to provide installation-specific text, rather than updating
messages directly in the codebase.

To that end, all user-visible strings
in the Python and Django template files are wrapped in Django's i18n functions, and can
be collected into a .PO file with Django's built-in manage.py commands:

```
sudo apt-get install gettext
cd opendebates
workon opendebates
python manage.py makemessages -l en
```

This will give you an up-to-date file in
`opendebates/locale/en/LC_MESSAGES/django.po`
which you can edit with installation-appropriate text overrides.  To use it, then run:

```
python manage.py compilemessages -l en
```

You can visit the view at `/test/` to confirm that text overrides are working properly.

# Deployment

There is a management command `python manage.py update_trending_scores` --
in production, you'll want a cronjob
to run that every ten minutes (or more, or less) and may want to adjust
the "trending algorithm" which is expressed in SQL.

Deployment-specific environment variables can be stored in a `opendebates/.env` file.
See `opendebates/.env.sample` for relevant variables that you might want to set.

To install front-end packages and then collect static files:

```
python manage.py bower install
python opendebates/manage.py collectstatic --noinput
```

Files will be collected into `opendebates/static/` -- in production mode (DJANGO_DEBUG=False)
all static files will be served from this directory.  Do not make edits to files directly
in `opendebates/static` -- instead, make edits to the source files (usually that's in opendebates/opendebates/static) and then re-run collectstatic
to update the served copies.


### Deployment on Heroku

Should be straightforward.  Only one catch -- run these as one command:

```
heroku run 'python manage.py makemigrations registration && python manage.py migrate'
```


## Using Vagrant to create dev VM

### Installation
Install virtualbox. This will be fairly OS specific, but we recommend using some package manager (apt/aptitude, rpm, brew, etc). Unless you're on windows, in which case ???

Install vagrant: http://docs.vagrantup.com/v2/installation/index.html

Install vagrant plugin vagrant-ansible-local
   vagrant plugin install vagrant-ansible-local

### Setup
All you should need is `vagrant up`. This will bring up a VM with all of the appropriate setup/installation.

In order to get into the VM, you can use `vagrant ssh`. This will log you in as the 'vagrant' user, which has sudo priveleges. If you'd like root, you can use `sudo su -` which will log you in as root. All of the files in repo will be placed in /vagrant.

Therefore, in order to start the webserver, you can do the following:
```
/vagrant/ve/bin/python opendebates/manage.py runserver 0.0.0.0:8000
```

Similarly, to collect static files you can use:
```
/vagrant/ve/bin/python /vagrant/opendebates/manage.py bower install
/vagrant/ve/bin/python opendebates/manage.py collectstatic --noinput
```

HOWEVER, you don't actually need to ssh into the VM in order to run these commands!
```
vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py runserver 0.0.0.0:8000'
```
or
```
vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py bower install'
vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py collectstatic --noinput'
```


You do not need to edit any of the server files in the virtual machine. It is perfectly fine to do all of your normal development work in this repo as you would normally.

### Create a Superuser
```
vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py createsuperuser'
```
or if already inside the VM:
```
/vagrant/ve/bin/python manage.py createsuperuser
```

# Developing

## Front-End

One of the key principles we'd like to keep in mind across the site is separation of concerns.
We want to make each piece as much dedicated to one concern as possible.

One example where this is particularly relevant is javascript in django template files.
We want to keep javascript out of our django template files as much as possible.
There may be some situations in which it may be necessary to have some small amount of js, particularly if we need to pass python variables to the front end,
but if you find yourself doing any logic work in an inline javascript snippet in a django template file, please please put that into its own js file.

Similarly, we want to keep html templating out of any javascript files.
If you find yourself doing something like this:
```
$('.some-container').append('<h1>A header</h1><p>A message</p><p>Another message</p>');
```
Move that html into a javascript template!

### Structuring

We're using LESS compiled to CSS, Handlebars templates, and a handful of third-party libraries including jquery, lodash, momentjs, and bootstrap amongst some others.

We use django templates to hand off any server configs to javascript. We can do this by creating a javascript namespace which can be accessed from any other included JS files.

See /opendebates/templates/base.html for an example of how this works. Similarly, we can then access that namespace in any of our javascript files.
An example of loading that namespace is in /opendebates/static/js/base/helpers.js

With our javascript namespace, we can order all of our submodules, with their properties and functions, and any of their sub-modules.
Our namespace is `ODebates`, so we might have: `ODebates.paths`, `ODebates.configs`, `ODebates.login`, etc.

If we had a login page, we could have an object `ODebates.login`, which could then have a function `ODebates.login.init()`, an object `ODebates.login.helpers` for helpers that
are specific to that login page, `ODebates.login.handlers` for any handlers which are specific to that login page, etc.

### Bower

Bower is a front-end package manager:
http://bower.io/
https://github.com/nvbn/django-bower

It makes keeping track of front-end libraries/dependencies much simpler and less error-prone. Instead of randomly saving js or css files from 3rd party websites, bower lets us
keep all of our dependencies in one place, track versions and handle updates.

In our settings.py file, we have the following:
```
BOWER_INSTALLED_APPS = (
    'jquery',
    'lodash',
    'bootstrap',
    'moment',
    'handlebars',
)
```
These are bower packages with their names as they might appear here: http://bower.io/search/

If you'd like to add an additional package, search for it on bower, add a line here to our settings file, and then run:
`vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py bower install'`
`vagrant ssh -c '/vagrant/ve/bin/python /vagrant/opendebates/manage.py collectstatic --noinput'`

In order to use one of these libraries in a django template, you can use the following:
```
  {% load static %}
  <script type="text/javascript" src='{% static 'jquery/dist/jquery.min.js' %}'></script>
  <script type="text/javascript" src='{% static 'handlebars/handlebars.min.js' %}'></script>
```

### LESS Stylesheets

We're using django-pipeline for LESS->CSS compilation.
http://django-pipeline.readthedocs.org/en/latest/index.html

In our settings.py file, there is a variable PIPELINE_CSS = {} which sets up the stylesheet pipeline.
An example might look like:
```
PIPELINE_CSS = {
    'base': {
        'source_filenames': (
          'less/base.less',
        ),
        'output_filename': 'css/base.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}
```

What this does is takes base.less, compiles it, minify/uglifies it (if not in DEBUG), and put the result into /static/css/base.css.
You can then load that stylesheet with the following:
```
  {% load pipeline %}
  {% stylesheet 'base' %}
```

Which leads us into
### Bootstrap

Ideally, we'd like to work with Bootstrap, not fight against it.
Bootstrap provides for the setting and accessing of a variety of LESS variables, which we would ideally match with our graphic design palette.

For example, in static/bower_components/bootstrap/less/modals.less, there is the following code:
```
// Actual modal
.modal-content {
  position: relative;
  background-color: @modal-content-bg;
  border: 1px solid @modal-content-fallback-border-color; //old browsers fallback (ie8 etc)
  border: 1px solid @modal-content-border-color;
  border-radius: @border-radius-large;
  .box-shadow(0 3px 9px rgba(0,0,0,.5));
  background-clip: padding-box;
  // Remove focus outline from opened modal
  outline: 0;
}
```
By setting `@modal-content-bg` in our variables.less file, we can change the modal background color in the most bootstrap-compatible (read: least hacky) way.

For any page that we'd like to import bootstrap styles (and our bootstrap variables), you can add the following to the top of the page:
`@import "bootstrap_import";`
### Handlebars

Similarly to how the css pipeline works, the javascript pipeline is set up like so:
```
PIPELINE_JS = {
    'base': {
        'source_filenames': (
          'js/base/*.js',
          'templates/base/*.handlebars',
        ),
        'output_filename': 'js/base.js',
    }
}
```

Then in the django template, we just need to call the following to load our compiled js
```
  {% load pipeline %}
  {% javascript 'base' %}
```

This will load any of the javascript files in static/js/base/ and will load and compile any handlebars templates in static/templates/base/

In our javascript, we could then access any of our named handlebars templates with `Handlebars.templates['template_name']` where template_name.handlebars
was a template file.


# Misc Vagrant+Ansible

## Useful Commands
see http://docs.vagrantup.com/v2/cli/index.html

`vagrant provision` - runs the ansible playbook set in the Vagrantfile
`vagrant ssh` - ssh into the VM
`vagrant reload` - reloads the Vagrantfile and makes any changes necessary. Adding `--provision` will run the ansible provisioner after reload

## Watch mode

The following will run the ansible provisioner in "watch" mode so that you can see if any changes would be made:
```
vagrant ssh -c "ansible-playbook /tmp/vagrant-ansible-local/django_server.yml --connection=local -i 'localhost,' --check --diff"
```
