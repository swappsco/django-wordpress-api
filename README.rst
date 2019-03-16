=============================
Django Wordpress API
=============================

.. image:: https://badge.fury.io/py/django-wordpress-api.png
    :target: https://badge.fury.io/py/django-wordpress-api

.. image:: https://travis-ci.org/swappsco/django-wordpress-api.png?branch=master
    :target: https://travis-ci.org/swappsco/django-wordpress-api

.. image:: https://coveralls.io/repos/github/swappsco/django-wordpress-api/badge.svg?branch=master
	:target: https://coveralls.io/github/swappsco/django-wordpress-api?branch=master

.. image:: https://readthedocs.org/projects/django-wordpress-api/badge/?version=latest
	:target: http://django-wordpress-api.readthedocs.io/en/latest/?badge=latest


Easily Install your Wordpress blog in your Django project

This package  allows to communicate easily with any wordpress project that is using wordpress core >= 4.7.0.

Even though the WP REST API package is already on the 2 version; it is still on beta so it was decided that this package will only support v1 until v2 is out of beta.

Documentation
-------------

The full documentation is at https://django-wordpress-api.readthedocs.org.

Quickstart
----------

Install Django Wordpres API::

    pip install django-wordpress-api

Then use it in a project::

    import wordpress_api

Features
--------

* Connect to an external wordpress application
* Retrieves all the blog posts ordered by pages
* Filter blog posts using several of the `available filters in WP REST API <http://wp-api.org/index-deprecated.html#posts_retrieve-posts>`_
* Search blog posts using a keyword
* order the blog posts by several attributes like author, title, type, etc; ascending and descending order (default order is descending date)
* Retrieve posts with a different type than "post"
* Four Views to display the blog page, The Post detail, The Posts filtered by category and the Posts filtered by tag; All of this with the search by keyword option

Running Tests
--------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements.txt
    (myenv) $ pip install -r requirements_test.txt
    (myenv) $ python manage.py test

Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
