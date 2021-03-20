import csv
import isodate
from googleapiclient.discovery import build
from config import CHANNEL_ID, API_KEY


class Parser:
    playlists = list()
    data = list()

    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=API_KEY)

    def send_playlist_request(self, page_token=None) -> dict:
        """
        Функция отправки запроса для получения плейлистов

        :param page_token: токен нужной страницы
        :return: основная информация о плейлистах
        """
        request = self.youtube.playlists().list(
            part="snippet",
            channelId=CHANNEL_ID,
            maxResults=50,
            pageToken=page_token
        )
        response = request.execute()
        return response

    def get_all_playlists(self):
        """
        Функция собирает массив всех плейлистов с канала
        :return: None
        """
        response = self.send_playlist_request();
        while True:
            self.playlists += response.get('items')
            if 'nextPageToken' in response:
                response = self.send_playlist_request(response.get('nextPageToken'))
            else:
                break

    def get_all_videos_from_playlist(self, playlist_id, page_token=None) -> dict:
        """
        Функция отправки запроса для получения видео
        :param playlist_id: id плейлиста
        :param page_token: токен страницы
        :return: список видео с информацией о них
        """
        request = self.youtube.playlistItems().list(
            part="snippet",
            maxResults=50,
            playlistId=playlist_id,
            pageToken=page_token
        )
        response = request.execute()
        return response

    def get_video_info(self, video_id):
        """
        Функция отправки запроса для получения информации о видео
        :param video_id: id видео
        :return: информаия о видео
        """
        request = self.youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_id
        )
        response = request.execute()
        return response

    def get_info_about_all_videos(self):
        """
        Функция сбора всей информации по каждому видео
        :return: None
        """
        for playlist in self.playlists:
            playlist_id = playlist.get('id')
            playlist_title = playlist.get('snippet').get('title')
            response = self.get_all_videos_from_playlist(playlist_id)

            while True:
                playlist_videos = response.get('items')
                for video in playlist_videos:
                    video_id = video.get('snippet').get('resourceId').get('videoId')

                    video_response = self.get_video_info(video_id)
                    params = video_response.get('items')[0]

                    video_title = params.get('snippet').get('title')
                    video_publishedAt = params.get('snippet').get('publishedAt')
                    video_duration = params.get('contentDetails').get('duration')
                    parsed_video_duration = int(isodate.parse_duration(video_duration).total_seconds())

                    statistics = params.get('statistics')
                    view_count = statistics.get('viewCount')
                    like_count = statistics.get('likeCount')
                    dislike_count = statistics.get('dislikeCount')
                    favorite_count = statistics.get('favoriteCount')
                    comment_count = statistics.get('commentCount')

                    self.data.append([video_id, playlist_title, video_title, video_publishedAt, view_count, like_count,
                                      dislike_count, favorite_count, comment_count, parsed_video_duration])

                if 'nextPageToken' in response:
                    response = self.get_all_videos_from_playlist(playlist_id, response.get('nextPageToken'))
                else:
                    break

    def write_data(self):
        """
        Функция записи в csv файл
        :return: None
        """
        with open('data.csv', 'w', encoding='utf8', newline='') as File:
            csv_writer = csv.writer(File, delimiter=';')
            csv_writer.writerow(
                ['id', 'Название плейлиста', 'Название видео', 'Дата публикации видео', 'Количество просмотров видео',
                 'Количество лайков под видео', 'Количество дизлайков под видео', 'Количество добавлений видео '
                                                                                  'в избранное',
                 'Количество комментариев под видео', 'Продолжительность видео в секундах'])
            for elem in self.data:
                csv_writer.writerow(elem)

    def parse(self):
        self.get_all_playlists()
        self.get_info_about_all_videos()
        self.write_data()


parser = Parser()
parser.parse()
