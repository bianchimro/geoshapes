from django.core.paginator import InvalidPage, EmptyPage


def get_page_or_1(request):
    """
    Gets the page argument from request. defaults to 1 if not given or not an integer
    """

    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    return page


def get_paginator_page(paginator, page):
    """
    Gets paginator page given a Paginator object and a page. Gets the last page if num page is
    incompatible with paginator
    """

    # If page request is out of range, deliver last page of results.
    try:
        objects_page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        objects_page = paginator.page(paginator.num_pages)

    return objects_page
