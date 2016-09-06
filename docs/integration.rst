Integration
===========

This section describes step by step integration of django_wordpress_api with your application.


Configure django-wordpress_api inside your aplication
-----------------------------------------------------

Add this app to your ``INSTALLED_APPS`` in your settings file::

    INSTALLED_APPS += ('wordpress_api',)


You need two settings variables to be able to use the package:

::

    WP_URL = http://your-wordpress-app.com/
    BLOG_POSTS_PER_PAGE = <number-of-blogs-to-display-per-page>

Remmember to add [WP REST API v1](http://wp-api.org/index-deprecated.html) to http://your-wordpress-app.com/ or this package will be useless.


Add django-wordpress-api
------------------------
Add django-plans urls to your URL general configuration::

    url(r'^blog/', include('wordpress_api.urls')),
