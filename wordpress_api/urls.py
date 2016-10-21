# -*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.BlogListView.as_view(),
        name='wordpress_api_blog_list'),
    url(r'^category/(?P<slug>[-\w]+)/$',
        views.CategoryBlogListView.as_view(),
        name='wordpress_api_blog_category_list'),
    url(r'^(?P<slug>[-\w]+)/$', views.BlogView.as_view(),
        name='wordpress_api_blog_detail'),
    url(r'^tag/(?P<slug>[-\w]+)/$',
        views.TagBlogListView.as_view(),
        name='wordpress_api_blog_tag_list'),
    url(r'^author/(?P<slug>[-\w]+)/$',
        views.BlogByAuthorListView.as_view(),
        name='wordpress_api_blog_by_author_list'),
]
