========
Usage
========

To use Django Wordpress API in a project::

    import wordpress_api

The django-wordpress-api has two main features:
the WPApiConnector and the Views that uses it.
If you want to use the pre defined views, just add wordpress-api-urls to your project.


The basic django-wordpress-api urls are::

    http://localhost:8000/blog/; display the blog list

    http://localhost:8000/(?P<slug>[-\w]+)/; displays the detail of a blog identified with the given slug

    http://localhost:8000/category/(?P<slug>[-\w]+)/; displays the blogs in the category identified with the given slug

    http://localhost:8000/tag/(?P<slug>[-\w]+)/; displays the blogs in the tag identified with the given slug

Else, If you want to retreive the blog posts in your custom views, you can use directly the WPApiConnector and its methods. You can check them at wordpress_api/utils.py
