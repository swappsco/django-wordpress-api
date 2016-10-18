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

Remember to add `WP REST API v1 <http://wp-api.org/index-deprecated.html>`_ to http://your-wordpress-app.com/ or this package will be useless.


Add django-wordpress-api
------------------------
Add django-wordpress-api urls to your URL general configuration::

    url(r'^blog/', include('wordpress_api.urls')),


Multilingual support
------------------------

At version 0.1.8 language support was added. To use it, you need to install inside your wordpress site `WPML <https://wpml.org>`_ and `wpml wp rest api adapter plugin by aaltomeri <https://github.com/aaltomeri/wpml-wp-rest-api-adapter>`_ and set the following variable inside your settings.

::

    WP_API_ALLOW_LANGUAGE = True

Inside the views, the language is supported using ``django.utils.translation.get_language``. If you are not using django languages, you can use the WPApiConnector.get_posts method directly and pass the language as the lang parameter. You can check how this work at ``wordpress_api/utils.py``
