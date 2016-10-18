import iso8601
from django.shortcuts import render
from django.views.generic import View
from django.contrib import messages
from django.http import Http404
from django.utils.translation import get_language
from django.conf import settings
from .utils import WPApiConnector
# Create your views here.


class ParentBlogView(View):
    """
    Class that defines a method to calculate args for the wp_api
    on the fly. Most of the code of the other views is the same.
    """
    def __init__(self, *args, **kwargs):
        super(ParentBlogView, self).__init__(*args, **kwargs)
        try:
            allow_language = settings.WP_API_ALLOW_LANGUAGE
            if allow_language:
                self.blog_language = str(get_language())
            else:
                self.blog_language = 'en'
        except AttributeError:
            self.blog_language = 'en'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = {
            'page_number': int(self.request.GET.get('page', 1)),
            'lang': self.blog_language}
        return wp_api

    def get_context_data(self, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        search = api_kwargs.get('search', '')
        if page is None:
            page = 1
        blogs = WPApiConnector().get_posts(**api_kwargs)
        tags = WPApiConnector().get_tags()
        categories = WPApiConnector().get_categories()

        if 'server_error' in blogs or\
           'server_error' in tags:
            messages.add_message(self.request, messages.ERROR,
                                 blogs['server_error'])
            raise Http404
        for blog in blogs['body']:
            position = blog['excerpt'].find(
                'Continue reading <span class="screen-reader-text">')
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

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)


class BlogListView(ParentBlogView):
    """
    View to display all blogs in wp blog
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(BlogListView, self).get_wp_api_kwargs(**kwargs)
        search_term = self.request.GET.get('q', None)
        if search_term is not None:
            wp_api['search'] = search_term
        return wp_api


class BlogView(ParentBlogView):
    """
    View to display blog detail in wp blog
    """
    template_name = 'wordpress_api/blog_detail.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(BlogView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'name': str(kwargs.get('slug'))}
        return wp_api

    def get_context_data(self, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        blog = WPApiConnector().get_posts(**api_kwargs)
        tags = WPApiConnector().get_tags()
        categories = WPApiConnector().get_categories()

        try:
            blog['body']
            if not blog['body']:
                raise Http404
        except KeyError:
            raise Http404
        if 'server_error' in blog['body'] or\
           'server_error' in tags:
            messages.add_message(self.request, messages.ERROR,
                                 blog['body']['server_error'])
            raise Http404
        bdate = iso8601.parse_date(blog['body'][0]['date'])

        blog = blog['body'][0]
        blog_tags = ''
        if 'post_tag' in blog['terms']:
            for tag in blog['terms']['post_tag']:
                blog_tags = blog_tags + tag['slug'] + ','
            if blog_tags:
                related_blogs = WPApiConnector().get_posts(
                    wp_filter={'tag': blog_tags},
                    page_number=1, orderby='date')['body']
                for related in related_blogs:
                    related_bdate = iso8601.parse_date(related['date_gmt'])
                    related['bdate'] = related_bdate.date()
            else:
                related_blogs = []
        else:
            related_blogs = []
        if blog in related_blogs:
            related_blogs.remove(blog)
        context = {
            'tags': tags,
            'categories': categories,
            'related_blogs': related_blogs[:3],
            'blog': blog,
            'bdate': bdate.date(),
        }
        return context


class CategoryBlogListView(ParentBlogView):
    """
    View to display all blogs in wp blog by category
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(CategoryBlogListView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'category_name': kwargs.get('slug')}
        return wp_api

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        category_name = None
        if context['blogs']:
            for category in context['blogs'][0]['terms']['category']:
                if str(category['slug']) == kwargs.get('slug'):
                    category_name = category['name']

        context['category_name'] = category_name
        return render(request, self.template_name, context)


class TagBlogListView(ParentBlogView):
    """
    View to display all blogs in wp blog by tag
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(TagBlogListView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'tag': kwargs.get('slug')}
        return wp_api

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['blogs']:
            for tag in context['blogs'][0]['terms']['post_tag']:
                if str(tag['slug']) == kwargs.get('slug'):
                    category_name = tag['name']
        else:
            category_name = None
        context['tag_name'] = category_name
        return render(request, self.template_name, context)
