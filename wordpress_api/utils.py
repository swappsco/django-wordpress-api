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
        if orderby == 'title':
            order = '&filter[order]=ASC'
        else:
            order = '&filter[order]=DESC'
        if page_number is None:
            query = self.wp_url + 'wp-json/posts?filter[orderby]=' + orderby +\
                order + '&filter[posts_per_page]=-1'
        else:
            query = self.wp_url + 'wp-json/posts?filter[posts_per_page]=' +\
                str(settings.BLOG_POSTS_PER_PAGE) + '&page=' +\
                str(page_number) + '&filter[orderby]=' + orderby +\
                order
        if custom_type is not None:
            query += '&type=%s' % custom_type
        if wp_filter is not None:
            for filter_type, filter_content in six.iteritems(wp_filter):
                query += '&filter[' + filter_type + ']=' +\
                    filter_content
            query += '&filter[orderby]=' + orderby + order
        if search is not None:
            query += '&filter[s]=' + search
        if lang is not None:
            query += '&lang=' + lang
        try:
            response = requests.get(query, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}
        headers = response.headers or {}
        headers.update({'request_url': query})
        return {'body': response.json(), 'headers': headers, }

    def get_tags(self):
        """
        Gets all the tags inside the wordpress application
        """

        query = self.wp_url + "wp-json/taxonomies/post_tag/terms"
        try:
            response = requests.get(query, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}

        return response.json()

    def get_categories(self):
        """
        Gets all the categories inside the wordpress application
        """
        query = self.wp_url + "wp-json/taxonomies/category/terms"
        try:
            response = requests.get(query, timeout=30)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}

        return response.json()
