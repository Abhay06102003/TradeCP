# TradeCP - Trading Command Protocol

TradeCP is an advanced MCP (Model Context Protocol) server that provides comprehensive stock market analysis tools powered by AI. It combines real-time financial data with intelligent analysis to deliver professional-grade trading insights.

## 🚀 Features

### Core Trading Tools
- **Stock Price Analysis**: Real-time stock prices, historical data, earnings history, and analyst estimates
- **Company Intelligence**: Comprehensive company information including sector, industry, and business details
- **News Aggregation**: Latest news and market sentiment analysis for any stock
- **Technical Analysis**: Financial patterns and technical indicators
- **Ticker Resolution**: Smart company name to ticker symbol conversion

### AI-Powered Analysis
- **Professional Summaries**: AI-generated financial analysis in professional analyst style
- **Data Integration**: Seamless combination of multiple data sources
- **Interactive Chat**: Natural language interface for stock market queries
- **Contextual Understanding**: Sequential tool execution based on conversation context

## 📁 Project Structure

```
TradeCP/
├── mcp_sever.py           # Main MCP server implementation
├── calling_mcps.py        # Interactive chat client with automatic tool calling
├── requirement.txt        # Project dependencies
├── tools/                 # Trading analysis tools
│   ├── find_ticker.py     # Company name to ticker conversion
│   ├── price_details.py   # Stock price and financial data
│   ├── news.py           # News aggregation and analysis
│   ├── patterns.py       # Technical analysis and patterns
│   └── sheets_details.py  # Extended company details
└── README.md             # Project documentation
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Ollama with qwen3:4b model (for AI analysis)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TradeCP
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirement.txt
   ```

3. **Install and setup Ollama**
   ```bash
   # Install Ollama (visit https://ollama.ai for platform-specific instructions)
   ollama pull qwen3:4b
   ```

## 🚀 Usage

### Running the MCP Server

Start the MCP server to expose trading tools:

```bash
python mcp_sever.py
```

The server provides the following MCP tools:
- `get_stock_price(ticker)` - Get comprehensive price analysis
- `get_stock_financial_data(ticker)` - Get technical analysis and patterns
- `get_stock_details(ticker)` - Get detailed company information
- `get_stock_news(ticker)` - Get latest news and sentiment
- `get_ticker_from_name(name)` - Convert company name to ticker

### Interactive Chat Interface

Launch the intelligent chat interface:

```bash
python calling_mcps.py
```

#### Chat Commands
- Type any stock-related question naturally
- `tools` - View available tools
- `clear` - Clear conversation history
- `quit` - Exit the application

#### Example Interactions
```
👤 You: What's the current price of Apple?
🤖 Assistant: [AI provides comprehensive Apple stock analysis]

👤 You: Get me news about Tesla
🤖 Assistant: [AI provides latest Tesla news with analysis]

👤 You: Analyze Microsoft's financial patterns
🤖 Assistant: [AI provides technical analysis of Microsoft]
```

## 🔧 Configuration

### AI Model Configuration
The system uses Ollama's qwen3:4b model by default. You can modify the model in:
- `mcp_sever.py` - Line 15: `model="qwen3:4b"`
- `calling_mcps.py` - Class initialization parameter

### Data Sources
- **Yahoo Finance**: Primary data source for stock information
- **Real-time APIs**: Live market data and news feeds

## 📊 Tool Details

### Price Analysis (`get_stock_price`)
- Current stock price and targets
- Historical price data
- Earnings history and estimates
- AI-generated professional analysis

### Financial Data (`get_stock_financial_data`)
- Technical indicators
- Chart patterns
- Market trends analysis

### Company Details (`get_stock_details`)
- Business fundamentals
- Financial statements
- Company metrics

### News Analysis (`get_stock_news`)
- Latest market news
- Sentiment analysis
- Impact assessment

## 🤖 AI Integration

TradeCP leverages advanced AI to:
- Summarize complex financial data
- Provide professional analyst-style insights
- Extract key figures and trends
- Maintain conversation context
- Execute sequential analysis workflows

## 📝 Development Notes

- Built with FastMCP for efficient tool serving
- Uses Pydantic for robust data validation
- Implements automatic retry logic for API calls
- Supports multi-currency financial data
- Includes comprehensive error handling

## 🔮 Future Improvements

1. I am planning to add a robust Technical analysis logic, ressistance levels weigthed on time and frequency. also Triangle patterns.
2. Plan to add Financial Analysis like company future projects and Managment.
3. Planning to add the all Ratios like PE, ROCE and all these.
4. also add mcp.resources to get the checking factor of all these ratios make context better and good to have with llms so that it can give better results.
5. Make prompting good and clear.
6. Focus on all other aspects like company product performance and seasonal demands and pattern recognizing using codes and logic.
7. Add a web search, first it should do a search and extract titles of each site and LLM will call another and decide which one to open and after that extract only selected once and feed by summarise them.