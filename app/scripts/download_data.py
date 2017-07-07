import wikipedia


def download_single(wiki_page_name, only_summary=False, language='en'):
    """
    Download the content of a wikipedia page

    :param wiki_page_name: the name
    :param only_summary:
    :return:
    """

    wikipedia.set_lang(language)
    if only_summary:
        page = wikipedia.page(wiki_page_name)
        return page.content
    else:
        return wikipedia.summary(wiki_page_name)


def download_all(wiki_page_names, only_summary=False, language='en'):
    contents = {}
    for pn in wiki_page_names:
        contents[pn] = download_single(pn, only_summary=only_summary, language=language)

    return contents


# TODO if starts with http or www get only the page name

