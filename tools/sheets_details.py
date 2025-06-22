import sys
import yfinance as yf
import pydantic
from typing import Any
import pandas as pd

class SheetsDetails(pydantic.BaseModel):
    company_information: dict[Any, Any]
    balance_sheet: dict[Any, Any] | pd.DataFrame
    cashflow: dict[Any, Any] | pd.DataFrame
    income_statement: dict[Any, Any] | pd.DataFrame
    cash_flow_statement: dict[Any, Any] | pd.DataFrame
    earnings: dict[Any, Any] | pd.DataFrame
    
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

def get_sheets_details(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    company_information = ticker_obj.info
    balance_sheet = ticker_obj.get_balance_sheet(as_dict=True)
    cashflow = ticker_obj.get_cashflow(as_dict=True)
    income_statement = ticker_obj.get_income_stmt(as_dict=True)
    cash_flow_statement = ticker_obj.get_cash_flow(as_dict=True)
    earnings = ticker_obj.get_financials(as_dict=True)
    return SheetsDetails(
        company_information=company_information,
        balance_sheet=balance_sheet,
        cashflow=cashflow,
        income_statement=income_statement,
        cash_flow_statement=cash_flow_statement,
        earnings=earnings
    )

