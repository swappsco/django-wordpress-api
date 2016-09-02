from django.test import TestCase, override_settings
import responses
from wordpress_api.utils import WPApiConnector
from django.conf import settings


class TestUtils(TestCase):
    """
    Tests for 508.wp_api.utils
    """

    def setUp(self):
        self.connector = WPApiConnector()
        self.default_response_kwargs = {
            'json': {'success': 'something found'},
            'status': 200,
            'content_type': 'application/json',
        }

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

    @override_settings(WP_URL='http://this_is_some_unvalid_url/')
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
        responses.add(responses.GET, settings.WP_URL + 'wp-json/posts',
                      body={'error': 'not found'}, status=404,
                      content_type='application/json')

        posts = self.connector.get_posts()
        self.assertTrue('response_error' in posts.keys())

    @responses.activate
    def test_connector_uses_orderby(self):
        """
        By default orderby is defined to be date.
        It can be something else (like title) and the query should be changed
        accordingly.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/posts',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue(
            'filter[orderby]=date' in posts['headers']['request_url'])
        posts = self.connector.get_posts(orderby='title')
        self.assertTrue(
            'filter[orderby]=title' in posts['headers']['request_url'])

    @responses.activate
    def test_page_number_is_used(self):
        """
        Page number is 1 by default. If it is an int it gets used.
        If it is None it gets ignored.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/posts',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue('&page=1' in posts['headers']['request_url'])
        posts = self.connector.get_posts(page_number=10)
        self.assertTrue('&page=10' in posts['headers']['request_url'])
        posts = self.connector.get_posts(page_number=None)
        self.assertTrue('&page=' not in posts['headers']['request_url'])

    @responses.activate
    def test_extra_filters(self):
        """
        If filter_type and filter_content are passed as arguments,
        they are taken in account for the query to the server.
        Otherwise ignored.
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/posts',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts(
            wp_filter={'some_filter': 'some_content'})
        self.assertTrue(
            '&filter[some_filter]=some_content' in posts[
                'headers']['request_url'])

    @responses.activate
    def test_custom_types(self):
        """
        If custom type is defined, it should be used, otherwise ignored
        """
        responses.add(responses.GET, settings.WP_URL + 'wp-json/posts',
                      **self.default_response_kwargs)
        posts = self.connector.get_posts()
        self.assertTrue('&type=' not in posts['headers']['request_url'])
        posts = self.connector.get_posts(custom_type='glossary')
        self.assertTrue('&type=glossary' in posts['headers']['request_url'])
