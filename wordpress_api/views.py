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
        try:  # pragma: no cover
            allow_language = settings.WP_API_ALLOW_LANGUAGE
            if allow_language:
                self.blog_language = str(get_language())
            else:
                self.blog_language = 'en'
        except AttributeError:
            self.blog_language = 'en'
        self.connector = WPApiConnector(lang=self.blog_language)

    def dispatch(self, *args, **kwargs):
        authors = self.connector.authors
        tags = self.connector.tags
        categories = self.connector.categories
        if 'server_error' in tags or\
           'server_error' in categories or\
           'server_error' in authors:
            messages.add_message(
                self.request, messages.ERROR,
                'The server is not reachable this moment. \
                Please try again later')
            raise Http404
        return super(ParentBlogView, self).dispatch(*args, **kwargs)

    def get_wp_api_kwargs(self, **kwargs):
        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:  # pragma: no cover
            page = 1
        wp_api = {
            'page_number': page
        }
        return wp_api

    def get_context_data(self, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        search = api_kwargs.get('search', '')
        blogs = self.connector.get_posts(**api_kwargs)
        tags = self.connector.tags
        categories = self.connector.categories
        if 'server_error' in blogs:
            messages.add_message(self.request, messages.ERROR,
                                 blogs['server_error'])
            raise Http404
        if not blogs['body']:
            raise Http404
        for blog in blogs['body']:
            blog['slug'] = str(blog['slug'])
            blog['bdate'] = iso8601.parse_date(blog['date']).date()
            featured_media = blog.get(
                '_embedded', {}).get('wp:featuredmedia', [])
            authors = blog.get(
                '_embedded', {}).get('author', [])
            if featured_media:
                blog['featured_image'] = featured_media[0]
            if authors:
                blog['authors'] = authors
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

    def get_context_data(self, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        context = cache.get(
            "blog_list_cache" + self.blog_language + "_page_" + str(page))
        context = super(BlogListView, self).get_context_data(**kwargs) if\
            context is None else context
        cache.add(
            "blog_list_cache" + self.blog_language + "_page_" + str(page),
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
        blog = cache.get("blog_cache_detail_{}_{}".format(
            kwargs.get('slug'), self.blog_language))
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        blog = self.connector.get_posts(
            **api_kwargs) if blog is None else blog
        tags = self.connector.tags
        categories = self.connector.categories
        cache.add(
            "blog_cache_detail_{}_{}".format(
                kwargs.get('slug'), self.blog_language),
            blog, cache_time)
        if 'server_error' in blog or\
           'server_error' in tags:
            messages.add_message(self.request, messages.ERROR,
                                 blog['server_error'])
            raise Http404

        if not blog['body']:
            raise Http404
        bdate = iso8601.parse_date(blog['body'][0]['date'])

        blog = blog['body'][0]
        blog_categories = []
        blog['slug'] = str(blog['slug'])
        blog['bdate'] = iso8601.parse_date(blog['date']).date()
        featured_media = blog.get(
            '_embedded', {}).get('wp:featuredmedia', [])
        authors = blog.get(
            '_embedded', {}).get('author', [])
        if featured_media:
            blog['featured_image'] = featured_media[0]
        if authors:
            blog['authors'] = authors
        if 'categories' in blog:
            for category in categories:
                if category['id'] in blog['categories']:
                    blog_categories.append(category)
        blog_tags = []
        if 'tags' in blog:
            for tag in tags:
                if tag['id'] in blog['tags']:
                    blog_tags.append(tag)
            if blog_tags:
                related_blogs = cache.get(
                    "blog_cache_detail_related_{}_{}".format(
                        kwargs.get('slug'), self.blog_language))
                tag_query = ",".join([str(tag['id']) for tag in blog_tags])
                related_blogs = self.connector.get_posts(
                    wp_filter={'tag': tag_query},
                    page_number=1,
                    orderby='date')['body'] if related_blogs is None else\
                    related_blogs
                for related_blog in related_blogs:
                    related_blog['slug'] = str(related_blog['slug'])
                    related_blog['bdate'] = iso8601.parse_date(
                        related_blog['date']).date()
                    featured_media = related_blog.get(
                        '_embedded', {}).get('wp:featuredmedia', [])
                    authors = related_blog.get(
                        '_embedded', {}).get('author', [])
                    if featured_media:
                        related_blog['featured_image'] = featured_media[0]
                    if authors:
                        related_blog['authors'] = authors
                cache.add(
                    "blog_cache_detail_related_{}_{}".format(
                        kwargs.get('slug'), self.blog_language),
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
            'blog_tags': blog_tags,
            'blog_categories': blog_categories,
            'bdate': bdate.date(),
        }
        return context


class CategoryBlogListView(ParentBlogView):
    """
    View to display all blogs in wp blog by category
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        slug = kwargs.get('slug')
        self.category = None
        for category in self.connector.categories:
            if category['slug'] == slug:
                self.category = category
                break
        if self.category is None:
            raise Http404
        wp_api = super(CategoryBlogListView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'categories': self.category['id']}
        return wp_api

    def get(self, request, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        context = cache.get(
            "blog_category_context_" +
            kwargs.get('slug') + self.blog_language + '_page_' + str(page))
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add(
            "blog_category_context_" +
            kwargs.get('slug') + self.blog_language + '_page_' + str(page),
            context, cache_time)
        category_name = None
        context['category'] = self.category
        category_name = self.category['name']
        context['category_name'] = category_name
        return render(request, self.template_name, context)


class TagBlogListView(ParentBlogView):
    """
    View to display all blogs in wp blog by tag
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        slug = kwargs.get('slug')
        self.tag = None
        for tag in self.connector.tags:
            if tag['slug'] == slug:
                self.tag = tag
                break
        if self.tag is None:
            raise Http404
        wp_api = super(TagBlogListView, self).get_wp_api_kwargs(**kwargs)
        wp_api['wp_filter'] = {'tags': self.tag['id']}
        return wp_api

    def get(self, request, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        context = cache.get("blog_tag_context_" + kwargs.get('slug') +
                            self.blog_language + '_page_' + str(page))
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_tag_context_" + kwargs.get('slug') +
                  self.blog_language + '_page_' + str(page),
                  context, cache_time)
        category_name = None
        context['tag'] = self.tag
        category_name = self.tag['name']
        context['tag_name'] = category_name
        return render(request, self.template_name, context)


class BlogByAuthorListView(ParentBlogView):
    """
    View to display all blogs written by given author
    """
    template_name = 'wordpress_api/blog_list.html'

    def get_wp_api_kwargs(self, **kwargs):
        wp_api = super(BlogByAuthorListView, self).get_wp_api_kwargs(**kwargs)
        slug = kwargs.get('slug')
        authors = self.connector.authors
        if slug in authors:
            wp_api['wp_filter'] = {'author': authors[slug]['id']}
        else:
            raise Http404
        return wp_api

    def get(self, request, **kwargs):
        api_kwargs = self.get_wp_api_kwargs(**kwargs)
        page = api_kwargs.get('page_number', 1)
        context = cache.get("blog_author_context_" + kwargs.get('slug') +
                            self.blog_language + '_page_' + str(page))
        context = self.get_context_data(**kwargs) if\
            context is None else context
        cache.add("blog_author_context_" + kwargs.get('slug') +
                  self.blog_language + '_page_' + str(page),
                  context, cache_time)
        author_name = None
        if context['blogs']:
            for blog in context['blogs']:
                authors = blog.get(
                    '_embedded', {}).get('author', [])
                for author in authors:
                    if str(author['slug']) == kwargs.get('slug'):
                        author_name = kwargs.get('slug')
                        context['author_name'] = author_name
                        return render(
                            request, self.template_name, context)
