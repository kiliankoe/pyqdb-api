import requests
import json


def get_all_quotes():
    """Makes an API request for all quotes"""
    r = requests.get(
        url='',
        headers={
            'Authorization': 'Basic '
        }
    )
    return json.loads(r.content.decode('utf-8'))


def get_author_quotes(search_author):
    """Makes an API request for a list of all quotes from a specific author"""
    r = requests.get(
        url='',
        params={
            'author': search_author
        },
        headers={
            'Authorization': 'Basic '
        }
    )
    return json.loads(r.content.decode('utf-8'))


def author_list(quotes, min_rating=0):
    """Takes a list of quotes and returns a set of all present authors with an optional minimum quote rating"""
    authors = []
    for quote in quotes:
        if quote['rating'] >= min_rating:
            for single_author in quote['authors']:
                authors.append(single_author)
    return set(authors)


def author_count(quotes):
    """Takes a list of quotes and returns a dictionary for the number of quotes each author is attributed with"""
    authors = {}
    for quote in quotes:
        for single_author in quote['authors']:
            if single_author in authors:
                authors[single_author] += 1
            else:
                authors[single_author] = 1
    return authors


def mean_rating(quotes):
    """Takes a list of quotes and returns the mean rating, especially useful with get_author_quotes()"""
    ratings = [quote['rating'] for quote in quotes]
    if len(ratings) != 0:
        return sum(ratings) / float(len(ratings))
    else:
        # This really shouldn't be happening... But apparently the API fails on umlauts. Why?!
        return -10


# print a list of all authors with at least 3 quotes in the database
for author, count in author_count(get_all_quotes()).items():
    if not count < 3:
        print(author + ': ' + str(count))

# print a list of authors together with their respective average rating
for author in author_list(get_all_quotes()):
    # print(author)
    print(author + ': %.2f' % mean_rating(get_author_quotes(author)))
