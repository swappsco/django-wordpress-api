# !/usr/bin/env python
#  -*- coding: utf-8 -*-
from django.test import TestCase, override_settings, Client
from django.urls import reverse
import responses
from wordpress_api.utils import WPApiConnector
from django.conf import settings


"""
test_django-wordpress-api
------------

Tests for `django-wordpress-api` models module.
"""


class TestUtils(TestCase):
    """
    Tests for wordpress_api.utils
    """
    @responses.activate
    def setUp(self):
        responses.add(
            responses.GET, settings.WP_URL + 'wp-json/wp/v2/users/',
            status=200,
            json=[{
                "id": 2,
                "name": "test-slug",
                "url": "",
                "description": "",
                "link": "https://example.com/blog/author/test-slug/",
                "slug": "test-slug",
                "avatar_urls": {
                    "24": "https://example.com/test-avatar",
                },
                "meta": [],
                "_links": {
                    "self": [
                        {
                            "href": "https://example.com/wp-json/wp/v2/users/2"
                        }
                    ],
                    "collection": [
                        {
                            "href": "https://example.com/wp-json/wp/v2/users"
                        }
                    ]
                }
            }],
            content_type='application/json')
        self.connector = WPApiConnector()
        self.default_response_kwargs = {
            'json': {'success': 'something found'},
            'status': 200,
            'content_type': 'application/json',
        }

    def test_connector_gets_all_authors(self):
        """
        connector object should have the authors as one
        of its properties
        """
        self.assertTrue(self.connector.authors is not None)
        self.assertTrue('test-slug' in self.connector.authors)
        self.assertEqual(self.connector.authors['test-slug']['id'], 2)

    @override_settings(WP_URL='')
    def test_raises_error_if_no_api_url(self):
        """
        If the wp_api url is not defined, utils should
        return a message with configuration error.
        TODO: This should raise an exception, not just return a message.
        """
        connector = WPApiConnector()
        posts = connector.get_posts()
        self.assertTrue('configuration_error' in posts.keys())

    @responses.activate
    def test_connection_returns_error(self):
        """
        If server cannot be reached a message with server error
        should be returned
        """
        connector = WPApiConnector()
        posts = connector.get_posts()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_error_status_propagates(self):
        """
        When we get a non 200 status from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      status=404,
                      content_type='application/json')

        posts = self.connector.get_posts()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_connection_error_propagates(self):
        """
        When we get a connection error from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        posts = self.connector.get_posts()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_error_status_propagates_get_tags(self):
        """
        When we get a non 200 status from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        responses.add(responses.GET,
                      settings.WP_URL + 'wp-json/wp/v2/tags/',
                      status=404,
                      content_type='application/json')

        posts = self.connector.get_tags()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_connection_error_propagates_get_tags(self):
        """
        When we get a connection error from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        posts = self.connector.get_tags()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_error_status_propagates_get_categories(self):
        """
        When we get a non 200 status from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        responses.add(responses.GET,
                      settings.WP_URL + 'wp-json/wp/v2/categories/',
                      status=404,
                      content_type='application/json')

        posts = self.connector.get_categories()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_connection_error_propagates_get_categories(self):
        """
        When we get a connection error from the server,
        an error indicating that something happened along with the
        status code is required.
        """
        posts = self.connector.get_categories()
        self.assertTrue('server_error' in posts.keys())

    @responses.activate
    def test_connector_uses_orderby(self):
        """
        By default orderby is defined to be date.
        It can be something else (like title) and the query should be changed
        accordingly.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue(
            'orderby=date' in posts['headers']['request_url'])
        posts = self.connector.get_posts(orderby='title')
        self.assertTrue(
            'orderby=title' in posts['headers']['request_url'])

    @responses.activate
    def test_page_number_is_used(self):
        """
        Page number is 1 by default. If it is an int it gets used.
        If it is None it gets ignored.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue('page=1' in posts['headers']['request_url'])
        posts = self.connector.get_posts(page_number=10)
        self.assertTrue('page=10' in posts['headers']['request_url'])
        posts = self.connector.get_posts(page_number=None)
        self.assertTrue('page=' not in posts['headers']['request_url'])

    @responses.activate
    def test_extra_filters(self):
        """
        If filter_type and filter_content are passed as arguments,
        they are taken in account for the query to the server.
        Otherwise ignored.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts(
            wp_filter={'some_filter': 'some_content'})
        self.assertTrue(
            'some_filter=some_content' in posts[
                'headers']['request_url'])

    @responses.activate
    def test_custom_types(self):
        """
        If custom type is defined, it should be used, otherwise ignored
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue('type=' not in posts['headers']['request_url'])
        posts = self.connector.get_posts(custom_type='glossary')
        self.assertTrue('type=glossary' in posts['headers']['request_url'])


class TestViews(TestCase):
    """
    Tests for wordpress_api.views
    """

    def setUp(self):
        self.default_response_kwargs = {
            'json': [{
                'excerpt': 'test blog',
                'slug': 'test-blog',
                'date': '2007-01-25T12:00:00Z',
                'author': {'name': 'test', 'slug': 'test-slug'},
                'terms': {
                    'post_tag': [{'slug': 'test-tag',
                                  'name': 'test tag'}],
                    'category': [{'slug': 'test-category',
                                  'name': 'test category'}]
                },
                'date_gmt': '2007-01-25T12:00:00Z',
            }],
            'status': 200,
            'content_type': 'application/json',
            'adding_headers': {'X-WP-Total': '1', 'X-WP-TotalPages': '1'},
        }
        self.client = Client()

    # BlogListView
    @responses.activate
    def test_blog_list_view_return_200(self):
        """
        If the wp client gets information, it should return a 200
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/tags/',
            **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/categories/',
            **self.default_response_kwargs)
        response = self.client.get(reverse('wordpress_api_blog_list'))
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_blog_list_view_return_404_if_server_error(self):
        """
        If there is a problem with the wp server, it should
        return 404
        """
        response = self.client.get(reverse('wordpress_api_blog_list'))
        self.assertEqual(response.status_code, 404)

    # BlogView
    @responses.activate
    def test_blog_view_return_200(self):
        """
        If the wp client gets information, it should return a 200
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/tags/',
            **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/categories/',
            **self.default_response_kwargs)
        response = self.client.get(
            reverse('wordpress_api_blog_detail', args=('test-blog',)))
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_blog_view_return_404_if_server_error(self):
        """
        If there is a problem with the wp server, it should
        return 404
        """
        response = self.client.get(
            reverse('wordpress_api_blog_detail', args=('test-blog',)))
        self.assertEqual(response.status_code, 404)

    @responses.activate
    def test_blog_view_return_404_if_no_blog(self):
        """
        If the wordpress server returns an empty array, it should
        raise 404
        """
        data = {
            'json': [],
            'status': 200,
            'content_type': 'application/json',
            'adding_headers': {'X-WP-Total': '1', 'X-WP-TotalPages': '1'},
        }
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **data)
        responses.add(responses.GET,
                      settings.WP_URL + 'wp-json/wp/v2/tags/',
                      **data)
        response = self.client.get(
            reverse('wordpress_api_blog_detail', args=('test-blog',)))
        self.assertEqual(response.status_code, 404)

    # CategoryBlogListView
    @responses.activate
    def test_category_view_return_200(self):
        """
        If the wp client gets information, it should return a 200
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/tags/',
            **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/categories/',
            **self.default_response_kwargs)
        response = self.client.get(
            reverse('wordpress_api_blog_category_list',
                    args=('test-category',)))
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_category_view_return_404_if_server_error(self):
        """
        If there is a problem with the wp server, it should
        return 404
        """
        response = self.client.get(
            reverse('wordpress_api_blog_category_list',
                    args=('test-category',)))
        self.assertEqual(response.status_code, 404)

    # TagBlogListView

    @responses.activate
    def test_tag_view_return_200(self):
        """
        If the wp client gets information, it should return a 200
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/tags/',
            **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/categories/',
            **self.default_response_kwargs)
        response = self.client.get(
            reverse('wordpress_api_blog_tag_list',
                    args=('test-tag',)))
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_tag_view_return_404_if_server_error(self):
        """
        If there is a problem with the wp server, it should
        return 404
        """
        response = self.client.get(
            reverse('wordpress_api_blog_tag_list',
                    args=('test-tag',)))
        self.assertEqual(response.status_code, 404)

    # BlogByAuthorListView

    @responses.activate
    def test_author_view_return_200(self):
        """
        If the wp client gets information, it should return a 200
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/wp/v2/posts/',
                      **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/tags/',
            **self.default_response_kwargs)
        responses.add(
            responses.GET, settings.WP_URL +
            'wp-json/wp/v2/categories/',
            **self.default_response_kwargs)
        response = self.client.get(
            reverse('wordpress_api_blog_by_author_list',
                    args=('test-slug',)))
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_author_view_return_404_if_server_error(self):
        """
        If there is a problem with the wp server, it should
        return 404
        """
        response = self.client.get(
            reverse('wordpress_api_blog_by_author_list',
                    args=('test-slug',)))
        self.assertEqual(response.status_code, 404)
