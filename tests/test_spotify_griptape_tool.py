from griptape.artifacts import TextArtifact
from spotify_griptape_tool.tool import SpotifyClient


class TestReverseStringTool:
    def test_reverse_string(self):
        value = "some_value"

        tool = SpotifyClient()

        params = {"values": {"input": value}}
        result = tool.reverse_string(params)

        assert isinstance(result, TextArtifact), "Expected TextArtifact instance"
        assert result.value == value[::-1]
