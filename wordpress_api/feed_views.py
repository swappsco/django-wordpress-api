import iso8601
from django.contrib.syndication.views import Feed
from django.conf import settings
from django.utils.translation import get_language
from django.http import Http404
from django.urls import reverse
from .utils import WPApiConnector


class LatestEntriesFeed(Feed):

    title = "Latest blog entries"
    description = "Latest blog entries"
    link = '/blog/'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = {
            'page_number': 1
        }
        return wp_api

    def get_context_data(self, **kwargs):
        connector = WPApiConnector(lang=self.blog_language)
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        search = api_kwargs.get('search', '')
        if not isinstance(page, int):
            page = 1
        blogs = connector.get_posts(**api_kwargs)
        tags = connector.tags
        categories = connector.categories

        if 'server_error' in blogs or\
           'server_error' in tags:
            raise Http404
        if not blogs['body']:
            raise Http404
        for blog in blogs['body']:
            if blog['excerpt'] is not None:
                position = blog['excerpt'].find(
                    'Continue reading')
                if position != -1:
                    blog['excerpt'] = blog['excerpt'][:position]
            blog['slug'] = str(blog['slug'])
            blog['bdate'] = iso8601.parse_date(blog['date']).date()
        context = {
            'blogs': blogs['body'],
            'tags': tags,
            'categories': categories,
            'search': search,
            'total_posts': int(blogs['headers']['X-WP-Total']),
            'total_pages': int(blogs['headers']['X-WP-TotalPages']),
            'current_page': page,
            'previous_page': page - 1,
            'next_page': page + 1,
        }
        return context

    def items(self):
        try:
            allow_language = settings.WP_API_ALLOW_LANGUAGE
            if allow_language:
                self.blog_language = str(get_language())
            else:
                self.blog_language = 'en'
        except AttributeError:
            self.blog_language = 'en'
        return self.get_context_data()['blogs']

    def item_title(self, item):
        return item['title']

    def item_description(self, item):
        return item['excerpt']

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return reverse(
            'wordpress_api_blog_detail', args=[item['slug']])
