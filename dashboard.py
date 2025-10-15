import streamlit as st
import requests

st.title("Ultimate SMC/ICT AI Trading Dashboard")

product_id = st.sidebar.text_input("Product ID", "101")
size = st.sidebar.number_input("Order Size", 1)
side = st.sidebar.selectbox("Side", ["buy", "sell"])
entry = st.sidebar.number_input("Entry Price")
stop = st.sidebar.number_input("Stop Loss")
target = st.sidebar.number_input("Target")

if st.button("Send Signal"):
    data = {"product_id": product_id, "size": size, "side": side, "entry": entry, "stop": stop, "target": target}
    resp = requests.post("https://your-railway-app-url/webhook", json=data)
    st.write("Trade Response:", resp.json())
