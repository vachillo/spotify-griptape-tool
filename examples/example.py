from griptape.structures import Agent
from spotify_griptape_tool import ReverseStringTool


agent = Agent(tools=[ReverseStringTool()])

agent.run("Use the ReverseStringTool to reverse 'Griptape'")
