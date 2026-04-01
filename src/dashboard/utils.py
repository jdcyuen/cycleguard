import streamlit as st
import pandas as pd
import json
from src.config.config_loader import load_config
from src.utils.market_data import MarketData

# Load config once globally to be used by helpers
config = load_config()
PORTFOLIO_FILE = config["system"]["files"]["portfolio"]
STATE_FILE = config["system"]["files"]["rebalance"]
RECOVERY_FILE = config["system"]["files"]["recovery"]
TRADE_LOG = config["system"]["files"]["trades"]


@st.cache_data
def load_portfolio():
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


@st.cache_data
def load_trade_log():
    try:
        df = pd.read_csv(TRADE_LOG)
        df["date"] = pd.to_datetime(df["date"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["date", "type", "asset", "amount", "reason"])


@st.cache_data
def load_rebalance_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_run_date": None, "executed_levels": []}


@st.cache_data
def load_recovery_state():
    try:
        with open(RECOVERY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"bottom": None, "recovered": False}


@st.cache_data
def load_market_data():
    market = MarketData()
    df = market.run()
    return df
