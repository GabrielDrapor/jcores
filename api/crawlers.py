from typing import TypedDict
import time
import requests
from urllib.parse import urlencode
from loguru import logger


class QueryParams(TypedDict, total=False):
    page_limit: str
    page_offset: str
    sort: str
    include: str
    filter_list_all: str
    fields_radios: str
    meta_categories: str
    meta_users: str


def fetch_user_episodes(user_id: int, limit: int = 12, offset: int = 0):
    """Fetch user radio data from the API with given limit and offset."""
    base_url = f'https://www.gcores.com/gapi/v1/users/{user_id}/radios'

    # Define query parameters
    query_params: QueryParams = {
        "page_limit": str(limit),
        "page_offset": str(offset),
        "sort": "-published-at",
        "include": "category,user,djs",
        "filter_list_all": "1",
        "fields_radios": "title,desc,excerpt,is-published,thumb,app-cover,cover,"
                         "comments-count,likes-count,bookmarks-count,is-verified,published-at,"
                         "option-is-official,option-is-focus-showcase,duration,draft,audit-draft,"
                         "user,comments,category,tags,entries,entities,similarities,"
                         "latest-collection,collections,operational-events,portfolios,"
                         "catalog-tags,djs,media,latest-album,albums,is-free,is-require-privilege",
        "meta_categories": ",",
        "meta_users": ",",
    }

    # Convert to query string
    query_string = urlencode({
        "page[limit]": query_params["page_limit"],
        "page[offset]": query_params["page_offset"],
        "sort": query_params["sort"],
        "include": query_params["include"],
        "filter[list-all]": query_params["filter_list_all"],
        "fields[radios]": query_params["fields_radios"],
        "meta[categories]": query_params["meta_categories"],
        "meta[users]": query_params["meta_users"],
    }, doseq=True)

    # Construct final URL
    url = f"{base_url}?{query_string}"

    time.sleep(1)
    # Send the request
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()  # Raise an error for bad responses


def fetch_album(album_id: int):
    base_url = f'https://www.gcores.com/gapi/v1/albums/{album_id}'
    time.sleep(1)
    response = requests.get(base_url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def fetch_episode_albums(album_id: int):
    base_url = f'https://www.gcores.com/gapi/v1/albums/{album_id}/published-audiobooks'
    time.sleep(1)
    response = requests.get(base_url)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


# Example usage
if __name__ == "__main__":
    user_id = 13701
    limit = 20
    offset = 0

    try:
        data = fetch_user_episodes(user_id, limit, offset)
        # print(data)
        logger.info("data length: {}", len(data['data']))

    except requests.HTTPError as e:
        print(f"HTTP Error: {e}")
