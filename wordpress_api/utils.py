import requests
import six
from django.conf import settings
from requests.exceptions import ConnectionError, Timeout
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
try:
    cache_time = settings.WP_API_BLOG_CACHE_TIMEOUT
except AttributeError:
    cache_time = 0

try:
    blog_per_page = settings.BLOG_POSTS_PER_PAGE
except AttributeError:  # pragma: no cover
    blog_per_page = 10


class WPApiConnector(object):

    def __init__(self, lang='en', auth=None, load_meta_data=True):
        self.lang = lang
        self.wp_url = settings.WP_URL
        self.blog_per_page = blog_per_page
        if not self.wp_url:
            raise ImproperlyConfigured("Missing wordpress url")
        self.auth = None
        if load_meta_data:
            authors = cache.get("blog_cache_authors_detail_{}".format(
                self.lang))
            self.authors = self.get_authors() if authors is None else authors
            tags = cache.get("blog_cache_tags_{}".format(self.lang))
            self.tags = self.get_tags() if tags is None else tags
            categories = cache.get("blog_cache_categories_{}".format(
                self.lang))
            self.categories = self.get_categories()\
                if categories is None else categories
        else:
            self.authors = {}
            self.categories = []
            self.tags = []

    def get_authors(self):
        """
        In order to be able to search by authors, we need
        the authors id. This method returns a dict with authors
        slug: author_data as key, value.
        """
        query = self.wp_url + 'wp-json/wp/v2/users/'
        params = {'per_page': '100'}
        page = 1
        if self.lang is not None:
            params['lang'] = self.lang
        try:
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}
        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}
        authors = {}
        data = response.json()
        for author in data:
            authors[author['slug']] = author
        total_pages = response.headers.get('X-WP-TotalPages', 1)
        try:
            total_pages = int(total_pages)
        except ValueError:  # pragma: no cover
            total_pages = 1
        for i in range(0, total_pages - 1):
            page += 1
            params['page'] = page
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
            data = response.json()
            for author in data:
                authors[author['slug']] = author

        cache.add(
            "blog_cache_authors_detail_{}".format(self.lang),
            authors, cache_time)
        return authors

    def get_posts(self, wp_filter=None, search=None,
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
        auth = self.auth
        params = {'_embed': 'true'}
        query = self.wp_url + 'wp-json/wp/v2/posts/'
        if orderby == 'title':
            params['order'] = 'asc'
        else:
            params['order'] = 'desc'

        params['orderby'] = orderby

        if page_number is not None:
            params['per_page'] = str(self.blog_per_page)
            params['page'] = str(page_number)
        if custom_type is not None:
            params['type'] = custom_type
        if wp_filter is not None:
            for filter_type, filter_content in six.iteritems(wp_filter):
                key = filter_type
                params[key] = filter_content
        if search is not None:
            params['search'] = search
        if self.lang is not None:
            params['lang'] = self.lang
        try:
            response = requests.get(
                query, params=params, timeout=30, auth=auth)
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

    def get_tags(self):
        """
        Gets all the tags inside the wordpress application
        """
        params = {'per_page': '100'}
        page = 1
        tags = []
        query = self.wp_url + "wp-json/wp/v2/tags/"
        if self.lang is not None:
            params['lang'] = self.lang
        try:
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}
        tags += response.json()
        total_pages = response.headers.get('X-WP-TotalPages', 1)
        try:
            total_pages = int(total_pages)
        except ValueError:  # pragma: no cover
            total_pages = 1
        for i in range(0, total_pages - 1):
            page += 1
            params['page'] = page
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
            tags += response.json()
        cache.add(
            "blog_cache_tags_{}".format(self.lang),
            tags, cache_time)
        return tags

    def get_categories(self):
        """
        Gets all the categories inside the wordpress application
        """
        params = {'per_page': '100'}
        page = 1
        categories = []
        query = self.wp_url + "wp-json/wp/v2/categories/"
        if self.lang is not None:
            params['lang'] = self.lang
        try:
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
        except (ConnectionError, Timeout):
            return {'server_error': 'The server is not reachable this moment\
                    please try again later'}

        if response.status_code != 200:
            return {
                'server_error': 'Server returned status code %i' % response.
                status_code}

        categories += response.json()
        total_pages = response.headers.get('X-WP-TotalPages', 1)
        try:
            total_pages = int(total_pages)
        except ValueError:  # pragma: no cover
            total_pages = 1
        for i in range(0, total_pages - 1):
            page += 1
            params['page'] = page
            response = requests.get(
                query, params=params, timeout=30, auth=self.auth)
            categories += response.json()
        cache.add(
            "blog_cache_categories_{}".format(self.lang),
            categories, cache_time)
        return categories
