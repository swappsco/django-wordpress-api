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

At version 0.1.8 multilingual support was added. To use it, you need to install `WPML <https://wpml.org>`_ and `wpml wp rest api adapter plugin by aaltomeri <https://github.com/aaltomeri/wpml-wp-rest-api-adapter>`_ inside your wordpress site and set the following variable inside your settings.

::

    WP_API_ALLOW_LANGUAGE = True

Inside the views, the language is supported using ``django.utils.translation.get_language``. If you are not using django translation, you can use the WPApiConnector.get_posts method directly and pass the language as the lang parameter. You can check how this work at ``wordpress_api/utils.py``


Page cache
------------------------

At version 0.1.18 cache support was added to all django wordpress api related pages. To activate it, just set the following setting.

::

    WP_API_BLOG_CACHE_TIMEOUT = 60 * 60 * 24


RSS Feed
------------------------

At version 0.1.23 a RSS Feed was added. You may use it importing LatestEntriesFeed from wordpress_api.feed_views and adding it to your
urls configuration.

::

        url(r'^feed/$', LatestEntriesFeed()),

If you want to modify the title or the description, just create your own class and inherit LatestEntriesFeed.
