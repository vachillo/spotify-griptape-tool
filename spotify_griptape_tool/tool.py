from __future__ import annotations
import os
from textwrap import dedent
from griptape.artifacts import TextArtifact, ErrorArtifact, ListArtifact
from griptape.tools import BaseTool
from griptape.utils.decorators import activity
from schema import Schema, Literal, Or, Optional
from attr import define, field, Factory
from spotipy import Spotify, SpotifyClientCredentials, SpotifyOAuth, SpotifyException, MemoryCacheHandler
from urllib.parse import quote as url_encode
from json import loads as to_dict


@define
class SpotifyClient(BaseTool):
    client_id = field(type=str)
    client_secret = field(type=str)
    authorization_code = field(type=str, default=None)
    authorization_state = field(type=str, default=None)
    authorization_redirect_uri = field(type=str, default=None)
    authorization_scopes = field(type=str, default=None)
    oauth_manager = field(type=SpotifyOAuth, default=None)
    user_token = field(type=str, default=None)
    client = field(
        type=Spotify,
        default=Factory(
            lambda self: Spotify(
                auth=self.user_token, 
                client_credentials_manager=SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    cache_handler=MemoryCacheHandler()
                )
            ), 
            takes_self=True
        )
    )

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        if self.client_id is None or self.client_secret is None:
            raise ValueError("client_id and client_secret must be set")
        self.oauth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.authorization_redirect_uri,
            state=self.authorization_state,
            scope=self.authorization_scopes,
        )
        if self.authorization_code is not None:
            self.client.set_auth(self.oauth_manager.get_access_token(self.authorization_code, as_dict=False))
        
    ####################
    ###    ALBUMS    ###
    ####################
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for a single album.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the album.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code. If a country code is specified, only content that is playable in that market is returned. Note: Playlist results are not affected by the market parameter.
                    Examples: market=US
                """)): str,
            }),
        }
    )
    def get_album(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        market: str = vals.get("market", "US")

        try:
            result = self.client.album(id, market=market)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for several albums.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the albums. Maximum: 20 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code. If a country code is specified, only content that is playable in that market is returned. Note: Playlist results are not affected by the market parameter.
                    Examples: market=US
                """)): str,
            }),
        }
    )
    def get_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")
        market: str = vals.get("market", "US")

        try:
            result = self.client.albums(ids, market=market)
            artifacts = list()
            for album in result["albums"]:
                artifacts.append(TextArtifact(str(album)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for tracks on an album.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the album.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code. If a country code is specified, only content that is playable in that market is returned. Note: Playlist results are not affected by the market parameter.
                    Examples: market=US
                """)): str,
            }),
        }
    )
    def get_album_tracks(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        market: str = vals.get("market", "US")

        try:
            result = self.client.album_tracks(id, market=market)
            artifacts = list()
            for track in result["items"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
   
    @activity(
        config={
            "description": "Can be used to get the current user's saved albums.",
            "schema": Schema({
                Literal("limit", description=dedent("""
                    The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first object to return. Default: 0 (i.e., the first object). Use with limit to get the next set of objects.
                """)): int,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                    Because min_*, max_* and market are applied to the results but not considered when determining the number of returned objects, it is possible that the response will contain less than limit items. In this case, the response will contain a next link to continue paging.
                """)): str,
            }),
        }
    )
    def get_current_user_saved_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)
        market: str = vals.get("market", "US")

        try:
            result = self.client.current_user_saved_albums(limit=limit, offset=offset, market=market)
            artifacts = list()
            for album in result["items"]:
                artifacts.append(TextArtifact(str(album)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))

    @activity(
        config={
            "description": "Can be used to add one or more albums to the current user's library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the albums. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def add_to_current_user_saved_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            self.client.current_user_saved_albums_add(ids)
            artifacts = list()
            for id in ids:
                artifacts.append(TextArtifact(f"Successfully added album with id: {id}"))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to remove one or more albums from the current user's library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the albums. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def remove_from_current_user_saved_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            self.client.current_user_saved_albums_delete(ids)
            artifacts = list()
            for id in ids:
                artifacts.append(TextArtifact(f"Successfully removed album with id: {id}"))
            return ListArtifact(artifacts)
        
        except Exception as e:
            return ErrorArtifact(str(e))

    @activity(
        config={
            "description": "Can be used to check if one or more albums is already saved in the current Spotify user's 'Your Music' library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the albums. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def check_current_user_saved_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            result = self.client.current_user_saved_albums_contains(ids)
            artifacts = list()
            for id in ids:
                artifacts.append(TextArtifact(f"Album with id: {id} is saved: {result[ids.index(id)]}"))
            return ListArtifact(artifacts)
        
        except Exception as e:
            return ErrorArtifact(str(e))
    
    @activity(
        config={
            "description": "Can be used to get a list of new album releases featured in Spotify (shown, for example, on a Spotify player's “Browse” tab).",
            "schema": Schema({
                Literal("country", description=dedent("""
                    An ISO 3166-1 alpha-2 country code.
                    Provide this parameter to ensure that the returned items will show releases available in the specified country.
                    If omitted, the releases will be shown for all countries.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (i.e., the first track). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_new_releases(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        country: str = vals.get("country")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.new_releases(country=country, limit=limit, offset=offset)
            artifacts = list()
            for album in result["albums"]["items"]:
                artifacts.append(TextArtifact(str(album)))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    ####################
    ###    ARTISTS   ###
    ####################
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for a single artist identified by their unique Spotify ID.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the artist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
            }),
        }
    )
    def get_artist(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")

        try:
            result = self.client.artist(id)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for several artists based on their Spotify IDs.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the artists. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def get_artists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            result = self.client.artists(ids)
            artifacts = list()
            for artist in result["artists"]:
                artifacts.append(TextArtifact(str(artist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))

    
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information about an artist's albums.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the artist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("include_groups", description=dedent("""
                    A list of keywords that will be used to filter the response. If not supplied, all album types will be returned. Valid values are:
                    - album
                    - single
                    - appears_on
                    - compilation
                    For example: include_groups=album,single.
                    A maximum of 20 album groups can be queried in one request.
                """)): list,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                    Because min_*, max_* and market are applied to the results but not considered when determining the number of returned objects, it is possible that the response will contain less than limit items. In this case, the response will contain a next link to continue paging.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of objects to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first object to return. Default: 0 (i.e., the first object). Use with limit to get the next set of objects.
                """)): int,
            }),
        }
    )
    def get_artist_albums(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        include_groups: list = vals.get("include_groups")
        market: str = vals.get("market", "US")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.artist_albums(id, include_groups=include_groups, market=market, limit=limit, offset=offset)
            artifacts = list()
            for album in result["items"]:
                artifacts.append(TextArtifact(str(album)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information about an artist's top tracks by country.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the artist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("country", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
            }),
        }
    )
    def get_artist_top_tracks(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        country: str = vals.get("country", "US")

        try:
            result = self.client.artist_top_tracks(id, country=country)
            artifacts = list()
            for track in result["tracks"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information about artists similar to a given artist. Similarity is based on analysis of the Spotify community’s listening history.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the artist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 20.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (i.e., the first track). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_artist_related_artists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.artist_related_artists(id, limit=limit, offset=offset)
            artifacts = list()
            for artist in result["artists"]:
                artifacts.append(TextArtifact(str(artist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    ########################
    ###    AUDIOBOOKS    ###
    ########################
    
    # TODO
    
    ########################
    ###    CATEGORIES    ###
    ########################
    
    # TODO
        
    #####################
    ###    CHAPTERS   ###
    #####################
        
    # TODO
        
    #####################
    ###    EPISODES   ###
    #####################
    
    # TODO
        
    ####################
    ###    GENRES    ###
    ####################
    
    @activity(
        config={
            "description": "Can be ued to get a list of available genres seed parameter values for recommendations.",
        }
    )
    def get_available_genre_seeds(self, params: dict) -> TextArtifact | ErrorArtifact:
        try:
            result = self.client.recommendation_genre_seeds()
            artifacts = list()
            for genre in result["genres"]:
                artifacts.append(TextArtifact(str(genre)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))

    #####################
    ###    MARKETS    ###
    #####################
    
    @activity(
        config={
            "description": "Can be used to get the list of markets where Spotify is available, in ISO 3166-1 alpha-2 format."
        }
    )
    def get_available_markets(self, params: dict) -> TextArtifact | ErrorArtifact:
        try:
            result = self.client.available_markets()
            artifacts = list()
            for market in result["markets"]:
                artifacts.append(TextArtifact(str(market)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    #####################
    ###    PLAYER    ####
    #####################
        
    # TODO
        
    #####################
    ##    PLAYLISTS   ###
    #####################
        
    @activity(
        config={
            "description": "Can be used to get a playlist owned by a Spotify user.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
                Literal("fields", description=dedent("""
                    Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned. For example, to get just the playlist’s description and URI: fields=description,uri. A dot separator can be used to specify non-reoccurring fields, while parentheses can be used to specify reoccurring fields within objects. For example, to get just the added date and user ID of the adder: fields=tracks.items(added_at,added_by.id). Use multiple parentheses to drill down into nested objects, for example: fields=tracks.items(track(name,href,album(name,href))).
                    Fields can be excluded by prefixing them with an exclamation mark, for example: fields=tracks.items(track(name,href,album(!name,href))).
                    Note: You can't use parentheses to exclude fields. 
                """)): str,
                Literal("additional_types", description=dedent("""
                    A comma-separated list of item types that your client supports besides the default track type. Valid types are: track and episode.
                    Note: This parameter was introduced to allow existing clients to maintain their current behaviour and might be deprecated in the future. In addition to providing this parameter, make sure that your client properly handles cases of new types in the future by checking against the type field of each object.
                """)): str,
            }),
        }
    )
    def get_playlist(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        market: str = vals.get("market", "US")
        fields: str = vals.get("fields")
        additional_types: str = vals.get("additional_types")

        try:
            result = self.client.playlist(id, market=market, fields=fields, additional_types=additional_types)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Change a playlist's name and public/private state. (The user must, of course, own the playlist.)",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("name", description=dedent("""
                    The new name for the playlist, for example "My New Playlist Title".
                """)): str,
                Literal("public", description=dedent("""
                    If true the playlist will be public, if false it will be private.
                    To be able to create private playlists, the user must have granted the playlist-modify-private scope.
                """)): bool,
                Literal("collaborative", description=dedent("""
                    If true , the playlist will become collaborative and other users will be able to modify the playlist in their Spotify client.
                    Note: You can only set collaborative to true on non-public playlists.
                """)): bool,
                Literal("description", description=dedent("""
                    Value for playlist description as displayed in Spotify Clients and in the Web API.
                """)): str,
            }),
        }
    )
    def change_playlist_details(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        name: str = vals.get("name", None)
        public: bool = vals.get("public", None)
        collaborative: bool = vals.get("collaborative", None)
        description: str = vals.get("description", None)

        try:
            result = self.client.playlist_change_details(id, name=name, public=public, collaborative=collaborative, description=description)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))

    # playlist-read-private
    @activity(
        config={
            "description": "Can be used to get full details of the items of a playlist owned by a Spotify user.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
                Literal("fields", description=dedent("""
                    Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned. For example, to get just the total number of tracks and the request limit: fields=total,limit. A dot separator can be used to specify non-reoccurring fields, while parentheses can be used to specify reoccurring fields within objects. For example, to get just the added date and user ID of the adder: fields=items(added_at,added_by.id). Use multiple parentheses to drill down into nested objects, for example: fields=items(track(name,href,album(name,href))).
                    Fields can be excluded by prefixing them with an exclamation mark, for example: fields=items.track.album(!external_urls,images).
                    Note: You can't use parentheses to exclude fields. 
                """)): str,
                Literal("additional_types", description=dedent("""
                    A list of item types that your client supports besides the default track type. Valid types are: track and episode.
                    Note: This parameter was introduced to allow existing clients to maintain their current behaviour and might be deprecated in the future. In addition to providing this parameter, make sure that your client properly handles cases of new types in the future by checking against the type field of each object.
                """)): list,
            }),
        }
    )
    def get_playlist_items(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        market: str = vals.get("market", "US")
        fields: str = vals.get("fields", None)
        additional_types: str = vals.get("additional_types", ["track", "episode"])

        try:
            result = self.client.playlist_items(id, market=market, fields=fields, additional_types=additional_types)
            artifacts = list()
            for track in result["items"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))


    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Can be used to reorder items in a playlist.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("range_start", description=dedent("""
                    The position of the first item to be reordered.
                """)): int,
                Literal("insert_before", description=dedent("""
                    The position where the items should be inserted.
                """)): int,
                Literal("range_length", description=dedent("""
                    The amount of items to be reordered. Defaults to 1 if not set.
                    The range of items to be reordered begins from the range_start position, and includes the range_length subsequent items.
                """)): int,
                Literal("snapshot_id", description=dedent("""
                    The playlist's snapshot ID against which you want to make the changes.
                    The API will validate that the specified items exist and in the specified positions and make the changes, even if more recent changes have been made to the playlist.
                    If omitted, the API will create a new snapshot of the playlist you are modifying.
                """)): str,
            }),
        }
    )
    def playlist_reorder_items(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        range_start: int = vals.get("range_start", None)
        insert_before: int = vals.get("insert_before", None)
        range_length: int = vals.get("range_length", None)
        snapshot_id: str = vals.get("snapshot_id", None)

        try:
            result = self.client.playlist_reorder_items(id, range_start=range_start, insert_before=insert_before, range_length=range_length, snapshot_id=snapshot_id)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Can be used to replace all the items in a playlist, overwriting its existing items. This powerful request can be useful for replacing items, re-ordering existing items, or clearing the playlist.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("uris", description=dedent("""
                    A list of Spotify URIs to set, can be track or episode URIs.
                    A maximum of 100 items can be set in one request.
                """)): list,
            }),
        }
    )
    def replace_playlist_items(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        uris: list = vals.get("uris")

        try:
            result = self.client.playlist_replace_items(id, uris)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Can be used to add one or more items to a playlist.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                """)): str,
                Literal("uris", description=dedent("""
                    A list of Spotify URIs for the items to add. Maximum: 100 track URIs.
                """)): list,
                Literal("position", description=dedent("""
                    The position to insert the tracks, a zero-based index. For example, to insert the tracks in the first position: position=0; to insert the tracks in the third position: position=2. If omitted, the tracks will be appended to the playlist. Tracks are added in the order they are listed in the query string or request body.
                """)): int,
            }),
        }
    )
    def add_items_to_playlist(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        tracks: list = vals.get("uris")
        position: int = vals.get("position", 0)

        try:
            result = self.client.playlist_add_items(id, tracks, position=position)
            return TextArtifact(str(result))

        except SpotifyException as se:
            if se.http_status == 403 or se.http_status == 401:
                auth_response = self.get_auth_response()
                return ErrorArtifact(auth_response)
            return ErrorArtifact(str(se))
        
    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Remove one or more items from a user's playlist.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("uris", description=dedent("""
                    A list of Spotify URIs to remove, can be track or episode URIs.
                    A maximum of 100 items can be removed in one request.
                """)): list,
                Literal("snapshot_id", description=dedent("""
                    The playlist's snapshot ID against which you want to make the changes.
                    The API will validate that the specified items exist and in the specified positions and make the changes, even if more recent changes have been made to the playlist.
                    If omitted, the API will create a new snapshot of the playlist you are modifying.
                """)): str,
            }),
        }
    )
    def remove_playlist_items(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        uris: list = vals.get("uris")
        snapshot_id: str = vals.get("snapshot_id", None)

        try:
            result = self.client.playlist_remove_all_occurrences_of_items(id, uris, snapshot_id=snapshot_id)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))

    # playlist-read-private
    @activity(
        config={
            "description": "Can be used to get a list of the playlists owned or followed by the current Spotify user.",
            "schema": Schema({
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (the first object). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_current_user_playlists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.current_user_playlists(limit=limit, offset=offset)
            artifacts = list()
            for playlist in result["items"]:
                artifacts.append(TextArtifact(str(playlist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # playlist-read-private
    # playlist-read-collaborative
    @activity(
        config={
            "description": "Can be used to get a list of the playlists owned or followed by a Spotify user.",
            "schema": Schema({
                Literal("user_id", description=dedent("""
                    The user's Spotify user ID.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (the first object). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_user_playlists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        user_id: str = vals.get("user_id")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.user_playlists(user_id, limit=limit, offset=offset)
            artifacts = list()
            for playlist in result["items"]:
                artifacts.append(TextArtifact(str(playlist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))

    @activity(
        config={
            "description": "Can be used to create a Spotify playlist",
            "schema": Schema({
                Literal("name", description=dedent("""
                    The name for the new playlist, for example "Your Coolest Playlist". This name does not need to be unique; a user may have several playlists with the same name.
                """)): str,
                Literal("public", description=dedent("""
                    Defaults to true. If true the playlist will be public, if false it will be private.
                    To be able to create private playlists, the user must have granted the playlist-modify-private scope.
                """)): bool,
                Literal("collaborative", description=dedent("""
                    Defaults to false. If true the playlist will be collaborative. Note that to create a collaborative playlist you must also set public to false. To create collaborative playlists you must have granted playlist-modify-private and playlist-modify-public scopes.
                """)): bool,
                Literal("description", description=dedent("""
                    Value for playlist description as displayed in Spotify Clients and in the Web API.
                """)): str,
            }),
        }
    )
    def create_playlist(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        name: str = vals.get("name")
        public: bool = vals.get("public", True)
        collaborative: bool = vals.get("collaborative", False)
        description: str = vals.get("description", "")

        try:
            result = self.client.user_playlist_create(self.client.me()["id"], name, public=public, collaborative=collaborative, description=description)
            return TextArtifact(str(result))

        except SpotifyException as se:
            if se.http_status == 403 or se.http_status == 401:
                auth_response = self.get_auth_response()
                return ErrorArtifact(auth_response)
            return ErrorArtifact(str(se))
        
    @activity(
        config={
            "description": "Can be used to get a list of Spotify featured playlists (shown, for example, on a Spotify player's 'Browse' tab).",
            "schema": Schema({
                Literal("locale", description=dedent("""
                    The desired language, consisting of an ISO 639-1 language code and an ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)". Provide this parameter if you want the results returned in a particular language (where available). Note that, if locale is not supplied, or if the specified language is not available, all strings will be returned in the Spotify default language (American English). The locale parameter, combined with the country parameter, may give odd results if not carefully matched. For example country=SE&locale=de_DE will return a list of categories relevant to Sweden but as German language strings.
                """)): str,
                Literal("country", description=dedent("""
                    A country: an ISO 3166-1 alpha-2 country code. Provide this parameter to ensure that the category exists for a particular country.
                """)): str,
                Literal("timestamp", description=dedent("""
                    A timestamp in ISO 8601 format: yyyy-MM-ddTHH:mm:ss. Use this parameter to specify the user's local time to get results tailored for that specific date and time in the day. If not provided, the response defaults to the current UTC time. Example: "2014-10-23T09:00:00" for a user whose local time is 9AM.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (the first object). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_featured_playlists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        locale: str = vals.get("locale")
        country: str = vals.get("country")
        timestamp: str = vals.get("timestamp")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.featured_playlists(locale=locale, country=country, timestamp=timestamp, limit=limit, offset=offset)
            artifacts = list()
            for playlist in result["playlists"]["items"]:
                artifacts.append(TextArtifact(str(playlist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get a list of Spotify playlists tagged with a particular category.",
            "schema": Schema({
                Literal("category_id", description=dedent("""
                    The Spotify category ID for the category.
                """)): str,
                Literal("country", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
                Literal("limit", description=dedent("""
                    The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first item to return. Default: 0 (the first object). Use with limit to get the next set of items.
                """)): int,
            }),
        }
    )
    def get_category_playlists(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        category_id: str = vals.get("category_id")
        country: str = vals.get("country")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)

        try:
            result = self.client.category_playlists(category_id, country=country, limit=limit, offset=offset)
            artifacts = list()
            for playlist in result["playlists"]["items"]:
                artifacts.append(TextArtifact(str(playlist)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
    
    @activity(
        config={
            "description": "Can be used to get a playlist cover image.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
            }),
        }
    )
    def get_playlist_cover_image(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")

        try:
            result = self.client.playlist_cover_image(id)
            artifacts = list()
            for image in result:
                artifacts.append(TextArtifact(str(image)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # ugc-image-upload
    # playlist-modify-public
    # playlist-modify-private
    @activity(
        config={
            "description": "Can be used to upload a custom playlist cover image and assign it to a playlist owned by a Spotify user.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the playlist.
                """)): str,
                Literal("image", description=dedent("""
                    Base64 encoded JPEG image data, maximum payload size is 256 KB.
                """)): str,
            }),
        }
    )
    def upload_custom_playlist_cover_image(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        image: str = vals.get("image")

        try:
            result = self.client.playlist_upload_cover_image(id, image)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
    
    #####################
    ###    SEARCH     ###
    #####################

    @activity(
        config={
            "description": "Can be used to search for albums, artists, playlists, tracks, shows or episodes.",
            "schema": Schema({
                Literal("q", description=dedent("""
                    Your search query.
                    You can narrow down your search using field filters. The available filters are album, artist, track, year, upc, tag:hipster, tag:new, isrc, and genre. Each field filter only applies to certain result types.
                    The artist and year filters can be used while searching albums, artists and tracks. You can filter on a single year or a range (e.g. 1955-1960).
                    The album filter can be used while searching albums and tracks.
                    The genre filter can be used while searching artists and tracks.
                    The isrc and track filters can be used while searching tracks.
                    The upc, tag:new and tag:hipster filters can only be used while searching albums. The tag:new filter will return albums released in the past two weeks and tag:hipster can be used to return only albums with the lowest 10% popularity.
                    Example: 'remaster track:Doxy artist:Miles Davis'
                """)): str,
                Literal("type", description=dedent("""
                    A list of item types to search across. Search results include hits from all the specified item types.
                    Allowed values: "album", "artist", "playlist", "track", "show", "episode", "audiobook"
                """)): list,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code. If a country code is specified, only content that is playable in that market is returned. Note: Playlist results are not affected by the market parameter.
                    Examples: market=US
                """)): str,
            }),
        }
    )
    def search(self, params: dict) -> ListArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        q: str = vals.get("q")
        type: list(str) = vals.get("type")
        market: str = vals.get("market", "US")

        try:
            res = self.client.search(q=url_encode(q), type=",".join(type), market=market)
            artifacts = list()
            for key in res.keys():
                for item in res[key]["items"]:
                    artifacts.append(TextArtifact(f"{key}: {item}"))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    #####################
    ###    SHOWS      ###
    #####################
    
    # TODO
    
    #####################
    ###    TRACKS     ###
    #####################
    
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for a single track identified by its unique Spotify ID.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the track.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
            }),
        }
    )
    def get_track(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")
        market: str = vals.get("market", "US")

        try:
            result = self.client.track(id, market=market)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
    
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information for multiple tracks based on their Spotify IDs.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the tracks. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
            }),
        }
    )
    def get_tracks(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")
        market: str = vals.get("market", "US")

        try:
            result = self.client.tracks(ids, market=market)
            artifacts = list()
            for track in result["tracks"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    # user-library-read
    @activity(
        config={
            "description": "Get a list of the songs saved in the current Spotify user's 'Your Music' library.",
            "schema": Schema({
                Literal("limit", description=dedent("""
                    The maximum number of tracks to return. Default: 20. Minimum: 1. Maximum: 50.
                """)): int,
                Literal("offset", description=dedent("""
                    The index of the first track to return. Default: 0 (the first object). Use with limit to get the next set of tracks.
                """)): int,
                Literal("market", description=dedent("""
                    An ISO 3166-1 alpha-2 country code or the string from_token.
                    Provide this parameter if you want to apply Track Relinking.
                """)): str,
            }),
        }
    )
    def get_current_users_saved_tracks(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        limit: int = vals.get("limit", 20)
        offset: int = vals.get("offset", 0)
        market: str = vals.get("market", "US")

        try:
            result = self.client.current_user_saved_tracks(limit=limit, offset=offset, market=market)
            artifacts = list()
            for track in result["items"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
    
    # user-library-modify
    @activity(
        config={
            "description": "Can be used to save one or more tracks to the current user's 'Your Music' library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the tracks. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def save_tracks_for_user(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            self.client.current_user_saved_tracks_add(ids)
            artifacts = list()
            for id in ids:
                artifacts.append(TextArtifact(f"Sucessfully saved track: {id} to user's library"))
            return ListArtifact(artifacts)
        
        except Exception as e:
            return ErrorArtifact(str(e))
        
    # user-library-modify
    @activity(
        config={
            "description": "Can be used to remove one or more tracks from the current user's 'Your Music' library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the tracks. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def remove_tracks_for_user(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            self.client.current_user_saved_tracks_delete(ids)
            artifacts = list()
            for id in ids:
                artifacts.append(TextArtifact(f"Sucessfully removed track: {id} from user's library"))
            return ListArtifact(artifacts)
        
        except Exception as e:
            return ErrorArtifact(str(e))
        
    # user-library-read
    @activity(
        config={
            "description": "Can be used to check if one or more tracks is already saved in the current Spotify user's 'Your Music' library.",
            "schema": Schema({
                Literal("ids", description=dedent("""
                    A list of the Spotify IDs for the tracks. Maximum: 50 IDs.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def check_current_users_saved_tracks(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            result = self.client.current_user_saved_tracks_contains(ids)
            artifacts = list()
            for is_saved in result:
                artifacts.append(TextArtifact(str(is_saved)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
        
    @activity(
        config={
            "description": "Can be used to get audio features for multiple tracks based on their Spotify IDs.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify IDs for the track.
                    Spotify IDs are 22-character strings that start with sp.
                """)): list,
            }),
        }
    )
    def get_audio_features(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        ids: list = vals.get("ids")

        try:
            result = self.client.audio_features(ids)
            artifacts = list()
            for track in result["audio_features"]:
                artifacts.append(TextArtifact(str(track)))
            return ListArtifact(artifacts)

        except Exception as e:
            return ErrorArtifact(str(e))
    
    @activity(
        config={
            "description": "Can be used to get Spotify catalog information about a track's audio analysis.",
            "schema": Schema({
                Literal("id", description=dedent("""
                    The Spotify ID for the track.
                    Spotify IDs are 22-character strings that start with sp.
                """)): str,
            }),
        }
    )
    def get_audio_analysis(self, params: dict) -> TextArtifact | ErrorArtifact:
        vals: dict = params.get("values")
        id: str = vals.get("id")

        try:
            result = self.client.audio_analysis(id)
            return TextArtifact(str(result))

        except Exception as e:
            return ErrorArtifact(str(e))
