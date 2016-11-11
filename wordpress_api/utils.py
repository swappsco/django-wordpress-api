import requests
import six
from django.conf import settings
from requests.exceptions import ConnectionError, Timeout


class WPApiConnector():

    def __init__(self):
        self.wp_url = settings.WP_URL
        self.blog_per_page = settings.BLOG_POSTS_PER_PAGE

    def get_posts(self, wp_filter=None, search=None, lang=None,
                  page_number=1, orderby='date', custom_type=None):
        """
        get latests post from a wordpress blog.
        if number_of_posts is not defined or not an int,
        it will get all posts. Else,
        it will get the latests posts according to
        number_of_posts.
        wp_filter must be a dict with key = filter_type
        and value filter_content.
        filter_type must be a valid filter from
        wp-api

        http://wp-api.org/index-deprecated.html#posts_retrieve-posts
        """
        if not self.wp_url or not self.blog_per_page:
            return {'configuration_error': 'External url is not defined'}
        params = {}
        query = self.wp_url + 'wp-json/posts/'
        if orderby == 'title':
            params['filter[order]'] = 'ASC'
        else:
            params['filter[order]'] = 'DESC'

        params['filter[orderby]'] = orderby

        if page_number is None:
            params['filter[posts_per_page]'] = '-1'
        else:

            params['filter[posts_per_page]'] = str(
                settings.BLOG_POSTS_PER_PAGE)
            params['page'] = str(page_number)
        if custom_type is not None:
            params['type'] = custom_type
        if wp_filter is not None:
            for filter_type, filter_content in six.iteritems(wp_filter):
                key = 'filter[%s]' % filter_type
                params[key] = filter_content
        if search is not None:
            params['filter[s]'] = search
        if lang is not None:
            params['lang'] = lang
        try:
            response = requests.get(query, params=params, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}
        headers = response.headers or {}
        headers.update({'request_url': response.url})
        return {'body': response.json(), 'headers': headers, }

    def get_tags(self, lang=None):
        """
        Gets all the tags inside the wordpress application
        """
        params = {}
        query = self.wp_url + "wp-json/taxonomies/post_tag/terms/"
        if lang is not None:
            params['lang'] = lang
        try:
            response = requests.get(query, params=params, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}

        return response.json()

    def get_categories(self, lang=None):
        """
        Gets all the categories inside the wordpress application
        """
        params = {}
        query = self.wp_url + "wp-json/taxonomies/category/terms/"
        if lang is not None:
            params['lang'] = lang
        try:
            response = requests.get(query, params=params, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}

        return response.json()
