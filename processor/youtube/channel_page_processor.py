import json
import re

from bs4 import BeautifulSoup
import requests

url_queue = []


def channel_data_dump(url):
    channel = {}
    # Make a GET request to fetch the raw HTML content
    html_content = requests.get(url).text

    # Reading data from a file.
    # with open('examples/sample_channel_get.html', 'r') as file:
    #     data = file.read().replace('\n', '')
    # html_content = data

    # Parse the html content
    soup = BeautifulSoup(html_content, "lxml")
    subscribers_pattern = re.compile(r'[0-9 | .]*\w subscribers')
    subscribers_text = str(soup.find("script", text=subscribers_pattern))

    yt_initial_data_start_index = html_content.index('window["ytInitialData"] =')
    yt_initial_data_end_index = html_content.index('window["ytInitialPlayerResponse"]')
    yt_data_json = str((html_content[yt_initial_data_start_index:yt_initial_data_end_index]))
    yt_data_json = json.loads(yt_data_json.replace('window["ytInitialData"] =', '') \
                              .replace('window["ytInitialPlayerResponse"]', '') \
                              .replace(';', ''))
    metadata_json = yt_data_json['metadata']['channelMetadataRenderer']
    channel[metadata_json['externalId']] = {}
    channel[metadata_json['externalId']]['description'] = (metadata_json['description'])
    channel[metadata_json['externalId']]['title'] = (metadata_json['title'])
    channel[metadata_json['externalId']]['keywords'] = (metadata_json['keywords'])
    channel[metadata_json['externalId']]['avatar'] = (metadata_json['avatar'])
    channel[metadata_json['externalId']]['isFamilySafe'] = (metadata_json['isFamilySafe'])
    channel[metadata_json['externalId']]['ownerUrls'] = (metadata_json['ownerUrls'])
    channel[metadata_json['externalId']]['subscribers'] = subscribers_pattern.findall(subscribers_text)
    channel[metadata_json['externalId']]['video_data'] = {}

    print('*******************************************************************************************')

    tabs_count = len(yt_data_json['contents']['twoColumnBrowseResultsRenderer']['tabs'])
    for tab_id in range(tabs_count):
        try:
            # print("TABS ID " + str(tab_id))
            section_list_count = len(
                yt_data_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][tab_id]['tabRenderer']['content'][
                    'sectionListRenderer']['contents'])
        except:
            continue
        # print("SECTION COUNT " + str(section_list_count))
        for section_id in range(section_list_count):
            try:
                # print("SELECTION ID " + str(section_id))
                item_section_list_count = len(
                    yt_data_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][tab_id]['tabRenderer'][
                        'content'][
                        'sectionListRenderer']['contents'][section_id]['itemSectionRenderer']['contents'])
            except:
                continue
            # print("ITEM SECTION COUNT " + str(item_section_list_count))
            for item_section_id in range(item_section_list_count):
                try:
                    # print("ITEM SECTION ID " + str(item_section_id))
                    shelf_render_list_count = len(
                        yt_data_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][tab_id]['tabRenderer'][
                            'content'][
                            'sectionListRenderer']['contents'][section_id]['itemSectionRenderer']['contents'][
                            item_section_id]['shelfRenderer'] \
                            ['content']['horizontalListRenderer']['items'])
                except:
                    continue
                # print("SHELF RENDER COUNT " + str(shelf_render_list_count))
                for shelf_render_id in range(shelf_render_list_count):
                    try:
                        # print("SHELF RENDER ID " + str(shelf_render_id))
                        shelf_render_list = (
                            yt_data_json['contents']['twoColumnBrowseResultsRenderer']['tabs'][tab_id]['tabRenderer'][
                                'content'][
                                'sectionListRenderer']['contents'][section_id]['itemSectionRenderer']['contents'][
                                item_section_id]['shelfRenderer'] \
                                ['content']['horizontalListRenderer']['items'][shelf_render_id]['gridVideoRenderer'])
                        extracted_data = {'title': (shelf_render_list['title']['simpleText']),
                                          'published_time': (shelf_render_list['publishedTimeText']['simpleText']),
                                          'views': (shelf_render_list['viewCountText']['simpleText']),
                                          'thumbnail': (shelf_render_list['thumbnail']['thumbnails'][0]['url']),
                                          'video_id': (shelf_render_list['videoId'])}
                        channel[metadata_json['externalId']]['video_data'][
                            shelf_render_list['videoId']] = extracted_data

                    except:
                        continue

    with open('output_data/' + str(metadata_json['externalId']) + '.json', 'w') as fp:
        json.dump(channel, fp)


def channel_url_retrieval(url):
    with open('master_url_list.json', 'r') as fp:
        master_url_list = json.load(fp)
    url_queue.append(url)

    while url_queue is not None:
        url = url_queue.pop()
        # Make a GET request to fetch the raw HTML content
        html_content = requests.get(url).text

        # Parse the html content
        soup = BeautifulSoup(html_content, "lxml")
        base_url_pattern = re.compile(r'\"canonicalBaseUrl\"\:\"\/\w*\/\w*\"')
        urls_text = str(soup.find(text=base_url_pattern))
        url_list = (base_url_pattern.findall(urls_text))

        # Using for loop
        for url in url_list:
            url = url.split("\"")[3]

            master_url_list_set = set(master_url_list)
            if url not in master_url_list_set:
                try:
                    channel_data_dump('https://www.youtube.com' + str(url))
                    print("SUCCESS URL : " + 'https://www.youtube.com' + str(url))
                except:
                    print("ERROR URL : " + 'https://www.youtube.com' + str(url))

                master_url_list.append(url)
                with open('master_url_list.json', 'w') as fp:
                    json.dump(master_url_list, fp)
                url_queue.append('https://www.youtube.com' + str(url))


with open('input_data/channel_list.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        channel_url_retrieval(line.replace('\n', ''))
