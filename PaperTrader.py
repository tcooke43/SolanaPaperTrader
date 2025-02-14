import asyncio
import json
import websockets
import tkinter as tk
from tkinter import ttk
import ssl
from threading import Thread
import time

# PumpPortal WebSocket Endpoint
PUMP_FUN_WS = "wss://pumpportal.fun/api/data"

class PumpFunPriceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Pump.fun Live Price Tracker")

        # Label for Instructions
        self.label = tk.Label(root, text="Enter Token Mint Address:", font=("Arial", 12))
        self.label.pack(pady=10)

        # Entry for Token Mint Address
        self.token_entry = tk.Entry(root, width=50)
        self.token_entry.pack(pady=5)

        # Button to Start Tracking
        self.track_button = tk.Button(root, text="Start Tracking", command=self.start_tracking)
        self.track_button.pack(pady=10)

        # Label to Display Price Updates
        self.price_label = tk.Label(root, text="Waiting for price updates...", font=("Arial", 14, "bold"))
        self.price_label.pack(pady=20)

        # Scrollable Frame for Trades
        self.canvas = tk.Canvas(root)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.trade_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.trade_frame, anchor="nw")

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Track data
        self.token_address = None
        self.websocket_thread = None

    def start_tracking(self):
        self.token_address = self.token_entry.get().strip()
        if not self.token_address:
            self.price_label.config(text="Please enter a valid token address.", fg="red")
            return

        self.price_label.config(text="Connecting to Pump.fun...", fg="black")

        # Start WebSocket in a separate thread
        self.websocket_thread = Thread(target=self.run_websocket, daemon=True)
        self.websocket_thread.start()

    def update_price(self, price):
        self.price_label.config(text=f"Latest Price: ${price}", fg="green")

    def update_trade(self, ticker, order_size, price, trade_time):
        # Display a new trade in the scrollable frame
        trade_info = f"Ticker: {ticker} | Size: {order_size} SOL | Price: ${price} | Time: {trade_time}"
        trade_label = tk.Label(self.trade_frame, text=trade_info, font=("Arial", 10))
        trade_label.pack(fill="x", pady=2)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))  # Update scrollable region

    def run_websocket(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.websocket_handler())

    async def websocket_handler(self):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Temporarily disable SSL verification

        try:
            async with websockets.connect(PUMP_FUN_WS, ssl=ssl_context) as websocket:
                print(f"Connected to {PUMP_FUN_WS}")

                # Subscribe to trade updates for the given token using the correct method
                subscribe_msg = {
                    "method": "subscribeTokenTrade",  # This method streams trade data
                    "keys": [self.token_address]
                }
                await websocket.send(json.dumps(subscribe_msg))
                print(f"Sent subscription request: {subscribe_msg}")

                while True:
                    response = await websocket.recv()
                    print(f"Received: {response}")  # Debugging

                    data = json.loads(response)

                    if "data" in data and len(data["data"]) > 0:
                        for trade in data["data"]:
                            ticker = trade.get("symbol", "N/A")
                            order_size = trade.get("solAmount", "N/A")
                            price = trade.get("initialBuy", "N/A")
                            trade_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())  # Using current time as placeholder

                            # Update the Tkinter UI
                            self.root.after(0, self.update_trade, ticker, order_size, price, trade_time)

        except Exception as e:
            print(f"WebSocket Error: {e}")
            self.root.after(0, self.price_label.config, {"text": "Error connecting to Pump.fun", "fg": "red"})

# Run the Tkinter UI
if __name__ == "__main__":
    root = tk.Tk()
    app = PumpFunPriceTracker(root)
    root.mainloop()
