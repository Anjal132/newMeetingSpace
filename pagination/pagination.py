from rest_framework.pagination import PageNumberPagination


class SmallResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 50
