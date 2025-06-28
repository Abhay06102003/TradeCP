import asyncio
import json
import ollama
from fastmcp import Client
from typing import List, Dict, Any, Optional

class MCPChatSystem:
    def __init__(self, mcp_server_path: str, ollama_model: str = "llama3.2"):
        self.mcp_server_path = mcp_server_path
        self.ollama_model = ollama_model
        self.conversation_history = []
        
    async def start_chat(self):
        """Start the interactive chat session with automatic tool calling"""
        print("🤖 MCP Chat Assistant Started!")
        print("Type 'quit' to exit, 'clear' to clear history, 'tools' to see available tools")
        print("-" * 60)
        
        async with Client(self.mcp_server_path) as mcp_client:
            # Get available tools
            tools = await mcp_client.list_tools()
            tool_descriptions = self._format_tools_for_model(tools)
            
            print(f"📋 Loaded {len(tools)} MCP tools")
            print("-" * 60)
            
            while True:
                try:
                    user_input = input("\n👤 You: ").strip()
                    
                    if user_input.lower() == 'quit':
                        print("👋 Goodbye!")
                        break
                    elif user_input.lower() == 'clear':
                        self.conversation_history = []
                        print("🧹 Conversation history cleared!")
                        continue
                    elif user_input.lower() == 'tools':
                        print("\n🛠️ Available Tools:")
                        for tool in tools:
                            print(f"  • {tool.name}: {tool.description}")
                        continue
                    
                    if not user_input:
                        continue
                    
                    # Process the user input with automatic tool calling
                    response = await self._process_query_automatically(user_input, mcp_client, tool_descriptions)
                    if response and '<think>' in response and '</think>' in response:
                        start = response.find('<think>')
                        end = response.find('</think>') + len('</think>')
                        response = response[:start] + response[end:] 
                    print(f"\n🤖 Assistant: {response}")
                    
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
    
    def _format_tools_for_model(self, tools) -> str:
        """Format tools information for the model"""
        tool_info = []
        for tool in tools:
            # Get parameter info
            params = []
            if hasattr(tool, 'input_schema') and tool.input_schema:
                properties = tool.input_schema.get('properties', {})
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', '')
                    params.append(f"{param_name} ({param_type}): {param_desc}")
            
            tool_desc = f"- {tool.name}: {tool.description}"
            if params:
                tool_desc += f"\n  Parameters: {', '.join(params)}"
            tool_info.append(tool_desc)
        
        return "\n".join(tool_info)
    
    async def _process_query_automatically(self, user_query: str, mcp_client, tool_descriptions: str) -> str:
        """Automatically process query and use all relevant tools with sequential execution"""
        
        # Add user query to history
        self.conversation_history.append({"role": "user", "content": user_query})
        
        # Start with the original query and execute tools sequentially
        return await self._execute_tools_sequentially(user_query, mcp_client, tool_descriptions)
    
    async def _execute_tools_sequentially(self, current_query: str, mcp_client, tool_descriptions: str, executed_tools: Optional[List[Dict[str, Any]]] = None) -> str:
        """Execute tools sequentially, using results from previous tools as input for next ones"""
        
        if executed_tools is None:
            executed_tools = []
        
        # Build context from previously executed tools
        context = ""
        if executed_tools:
            context = "\n\nPrevious tool results:\n"
            for tool in executed_tools:
                context += f"- {tool['tool_name']}: {tool['result']}\n"
        
        # Determine next tool to use
        planning_prompt = f"""You are a helpful assistant with access to various tools through MCP (Model Context Protocol).

Available tools:
{tool_descriptions}

The user originally asked: "{current_query}"{context}

ANALYZE THE SITUATION:
- What is the user asking for?
- What tools have already been executed?
- What information is still missing to fully answer the user's question?

RULES:
1. If the user asks for stock price and you don't have a ticker symbol, use get_ticker_from_name first
2. If you have a ticker symbol from previous results, use get_stock_price next
3. If the user asks for news and you have a ticker, use get_stock_news
4. If you have all the information needed, return empty array []

Respond with ONLY a JSON array with ONE tool (or empty array), in this exact format:
[{{"tool": "tool_name", "params": {{"param1": "value1"}}}}]

Examples:
- Need ticker first: [{{"tool": "get_ticker_from_name", "params": {{"name": "Apple Inc"}}}}]
- Have ticker, need price: [{{"tool": "get_stock_price", "params": {{"ticker": "AAPL"}}}}]
- Have ticker, need news: [{{"tool": "get_stock_news", "params": {{"ticker": "AAPL"}}}}]
- All done: []

Do not include any explanation, just the JSON array."""

        try:
            # Get tool planning from model
            planning_response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": planning_prompt}],
                stream=False
            )
            
            planning_text = planning_response['message']['content'].strip()
            # print("--------------------------------")
            # print("Planning text: ", planning_text)
            if planning_text and '<think>' in planning_text and '</think>' in planning_text:
                start = planning_text.find('<think>')
                end = planning_text.find('</think>') + len('</think>')
                planning_text = planning_text[:start] + planning_text[end:] 
            print(f"🧠 Planning: {planning_text}")
            
            # Parse the tool request
            try:
                # prnt("--------------------------------")
                # print("Plainning text: ", planning_text)
                if planning_text:
                    # print("Trying to parse tool requests")
                    tool_requests = json.loads(planning_text)
                    print(f"🔍 Parsed tool requests: {tool_requests}")
                    
                    if tool_requests and len(tool_requests) > 0:  # If a tool is needed
                        tool_request = tool_requests[0]  # Take the first (and should be only) tool
                        tool_name = tool_request.get('tool')
                        parameters = tool_request.get('params', {})
                        
                        print(f"🔧 Using tool: {tool_name} with parameters: {parameters}")
                        
                        try:
                            # Call the MCP tool
                            tool_result = await mcp_client.call_tool(tool_name, parameters)
                            tool_output = tool_result[0].text if tool_result else "No result"
                            
                            # Add this tool result to executed tools
                            executed_tools.append({
                                'tool_name': tool_name,
                                'parameters': parameters,
                                'result': tool_output
                            })
                            print(f"✅ Tool {tool_name} completed with result: {tool_output}")
                            
                            # Special logic for sequential tool execution
                            # If we just got a ticker, we should continue to get price/news
                            if tool_name == 'get_ticker_from_name' and tool_output and 'Error' not in tool_output:
                                print("🔄 Got ticker, continuing to get stock data...")
                            
                            # Check if we need to execute more tools (recursive call)
                            print(f"🔄 Checking for more tools needed after {tool_name}...")
                            return await self._execute_tools_sequentially(current_query, mcp_client, tool_descriptions, executed_tools)
                            
                        except Exception as e:
                            print(f"❌ Error with tool {tool_name}: {str(e)}")
                            executed_tools.append({
                                'tool_name': tool_name,
                                'parameters': parameters,
                                'result': f"Error: {str(e)}"
                            })
                            # Continue to final response even with error
                            print("🔄 Continuing despite error...")
                            return await self._execute_tools_sequentially(current_query, mcp_client, tool_descriptions, executed_tools)
                    
                    # No more tools needed - generate final response
                    print(f"🏁 No more tools needed. Executed {len(executed_tools)} tools total.")
                    if executed_tools:
                        final_response = await self._generate_comprehensive_response(current_query, executed_tools)
                        self.conversation_history.append({"role": "assistant", "content": final_response})
                        return final_response
                    else:
                        # No tools were executed, generate direct response
                        print("⚠️ No tools were executed, generating direct response")
                        return await self._generate_direct_response(current_query)
                        
                else:
                    # If parsing fails and we have executed tools, generate response based on them
                    if executed_tools:
                        final_response = await self._generate_comprehensive_response(current_query, executed_tools)
                        self.conversation_history.append({"role": "assistant", "content": final_response})
                        return final_response
                    else:
                        return await self._generate_direct_response(current_query)
                    
            except json.JSONDecodeError:
                print("❌ Failed to parse tool planning")
                if executed_tools:
                    final_response = await self._generate_comprehensive_response(current_query, executed_tools)
                    self.conversation_history.append({"role": "assistant", "content": final_response})
                    return final_response
                else:
                    return await self._generate_direct_response(current_query)
                
        except Exception as e:
            if executed_tools:
                final_response = await self._generate_comprehensive_response(current_query, executed_tools)
                self.conversation_history.append({"role": "assistant", "content": final_response})
                return final_response
            else:
                return f"Error in query processing: {str(e)}"
    
    async def _generate_direct_response(self, user_query: str) -> str:
        """Generate a direct response without using tools"""
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Respond naturally to the user's query."},
                    {"role": "user", "content": user_query}
                ],
                stream=False
            )
            
            direct_response = response['message']['content'].strip()
            self.conversation_history.append({"role": "assistant", "content": direct_response})
            return direct_response
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    async def _generate_comprehensive_response(self, user_query: str, tool_results: List[Dict]) -> str:
        """Generate a comprehensive response based on multiple tool results"""
        
        # Format all tool results
        results_summary = []
        for i, result in enumerate(tool_results, 1):
            results_summary.append(f"Tool {i} ({result['tool_name']}): {result['result']}")
        
        results_text = "\n\n".join(results_summary)
        
        prompt = f"""The user asked: "{user_query}"

I used {len(tool_results)} tool(s) and got these results:

{results_text}

Please provide a comprehensive, natural response to the user based on ALL this information. 
Combine and synthesize the data from all tools to give a complete answer. 
Don't mention the technical details about using tools, just give a conversational response that addresses the user's query."""

        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            return response['message']['content'].strip()
        except Exception as e:
            # Fallback response
            return f"Based on the collected information: {' '.join([r['result'] for r in tool_results])}"

async def main():
    # Initialize the chat system
    chat_system = MCPChatSystem(r"/home/abhay06102003/Desktop/Proj/TradeCP/backend/mcp_sever.py", "qwen3:8b")
    
    # Start the interactive chat
    await chat_system.start_chat()

if __name__ == "__main__":
    asyncio.run(main())