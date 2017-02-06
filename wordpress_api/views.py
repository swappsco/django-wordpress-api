import iso8601
from django.core.cache import cache
from django.shortcuts import render
from django.views.generic import View
from django.contrib import messages
from django.http import Http404
from django.utils.translation import get_language
from django.conf import settings
from .utils import WPApiConnector

# Create your views here.
try:
    cache_time = settings.WP_API_BLOG_CACHE_TIMEOUT
except AttributeError:
    cache_time = 0


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
        if not isinstance(page, int):
            page = 1
        blogs = WPApiConnector().get_posts(**api_kwargs)
        tags = WPApiConnector().get_tags(lang=self.blog_language)
        categories = WPApiConnector().get_categories(lang=self.blog_language)

        if 'server_error' in blogs or\
           'server_error' in tags:
            messages.add_message(self.request, messages.ERROR,
                                 blogs['server_error'])
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

    def get(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def dispatch(self, *args, **kwargs):
        return super(ParentBlogView, self).dispatch(*args, **kwargs)


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

    def get_context_data(self, **kwargs):
        context = cache.get("blog_list_cache" + self.blog_language)
        context = super(BlogListView, self).get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_list_cache" + self.blog_language,
                  context, cache_time)
        return context


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
        blog = cache.get("blog_cache_detail_" + kwargs.get('slug') +
                         self.blog_language)
        tags = cache.get("blog_cache_detail_tags_" + kwargs.get('slug') +
                         self.blog_language)
        categories = cache.get(
            "blog_cache_detail_categories_" + kwargs.get('slug') +
            self.blog_language)

        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        blog = WPApiConnector().get_posts(
            **api_kwargs) if blog is None else blog
        tags = WPApiConnector().get_tags(
            lang=self.blog_language) if tags is None else tags
        categories = WPApiConnector().get_categories(
            lang=self.blog_language) if categories is None else categories

        cache.add(
            "blog_cache_detail_" + kwargs.get('slug') + self.blog_language,
            blog, cache_time)
        cache.add(
            "blog_cache_detail_tags_" + kwargs.get('slug') +
            self.blog_language,
            tags, cache_time)
        cache.add(
            "blog_cache_detail_categories_" + kwargs.get('slug') +
            self.blog_language,
            categories, cache_time)

        if 'server_error' in blog or\
           'server_error' in tags:
            messages.add_message(self.request, messages.ERROR,
                                 blog['server_error'])
            raise Http404

        if not blog['body']:
            raise Http404
        bdate = iso8601.parse_date(blog['body'][0]['date'])

        blog = blog['body'][0]
        blog_tags = ''
        if 'post_tag' in blog['terms']:
            for tag in blog['terms']['post_tag']:
                blog_tags = blog_tags + tag['slug'] + ','
            if blog_tags:
                related_blogs = cache.get(
                    "blog_cache_detail_related" + kwargs.get('slug') +
                    self.blog_language)

                related_blogs = WPApiConnector().get_posts(
                    wp_filter={'tag': blog_tags},
                    page_number=1,
                    orderby='date')['body'] if related_blogs is None else\
                    related_blogs
                cache.add(
                    "blog_cache_detail_related" + kwargs.get('slug') +
                    self.blog_language,
                    related_blogs, cache_time)

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
        context = cache.get("blog_category_context_" + kwargs.get('slug') +
                            self.blog_language)
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_category_context_" + kwargs.get('slug') +
                  self.blog_language,
                  context, cache_time)
        category_name = None
        if context['blogs']:
            for item in context['blogs'][0]['terms']['category']:
                if str(item['slug']) == kwargs.get('slug'):
                    context['category'] = item
                    category_name = item['name']

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
        context = cache.get("blog_tag_context_" + kwargs.get('slug') +
                            self.blog_language)
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_tag_context_" + kwargs.get('slug') +
                  self.blog_language,
                  context, cache_time)
        category_name = None
        if context['blogs']:
            for item in context['blogs'][0]['terms']['post_tag']:
                if str(item['slug']) == kwargs.get('slug'):
                    context['tag'] = item
                    category_name = item['name']

        context['tag_name'] = category_name
        return render(request, self.template_name, context)


class BlogByAuthorListView(ParentBlogView):
    """
    View to display all blogs written by given author
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(BlogByAuthorListView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'author_name': kwargs.get('slug')}
        return wp_api

    def get(self, request, **kwargs):
        context = cache.get("blog_author_context_" + kwargs.get('slug') +
                            self.blog_language)
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_author_context_" + kwargs.get('slug') +
                  self.blog_language,
                  context, cache_time)
        author_name = None
        if context['blogs']:
            if str(context[
                    'blogs'][0]['author']['slug']) == kwargs.get('slug'):
                author_name = kwargs.get('slug')

        context['author_name'] = author_name
        return render(request, self.template_name, context)
