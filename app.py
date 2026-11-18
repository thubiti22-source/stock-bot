import os
import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# إعدادات تيليجرام من متغيرات البيئة في Render
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9039693992:AAEl_8PyjkcPSfXaxkW2kPfd8EKyIYgd40o")
CHAT_ID = os.environ.get("CHAT_ID", "20949590")

# قائمة الأسهم المستهدفة (أسهم زخم ومنخفضة السعر بين 1 و 20 دولار بالإضافة للأسهم الكبرى)
STOCKS_LIST = [
    "SOFI", "PLTR", "NIO", "MARA", "RIOT", "AMC", "GME", "SNDL", "FCEL", 
    "PLUG", "TLRY", "HBAN", "F", "VALE", "AAL", "CCL", "ZIM", "NVDA", "TSLA"
]

def send_telegram_message(message):
    """إرسال الإشعارات إلى تيليجرام"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def analyze_stock(ticker):
    """تحليل الأسهم بناءً على استراتيجيات الزخم، الفوليوم، والتماسك"""
    try:
        # جلب البيانات التاريخية اليومية
        stock = yf.Ticker(ticker)
        df = stock.history(period="60d")
        
        if df.empty or len(df) < 30:
            return None
            
        current_price = df['Close'].iloc[-1]
        
        # تصفية الأسهم ضمن النطاق المطلوب ($1 إلى $20) أو الأسهم الكبرى المحددة
        if current_price > 20.0 and ticker not in ["NVDA", "TSLA"]:
            return None
        if current_price < 1.0:
            return None

        # حساب المتوسطات المتحركة للنمط الكلاسيكي (EMA 21, SMA 50)
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # حساب متوسط حجم التداول لآخر 20 يوم
        df['Vol_SMA_20'] = df['Volume'].rolling(window=20).mean()
        
        last_volume = df['Volume'].iloc[-1]
        avg_volume = df['Vol_SMA_20'].iloc[-1]
        
        ema_21 = df['EMA_21'].iloc[-1]
        sma_50 = df['SMA_50'].iloc[-1]
        
        # شروط الانفجار السعري واختراق الفوليوم (>= 1.5x متوسط الحجم)
        is_volume_spike = last_volume >= (1.5 * avg_volume)
        is_uptrend = current_price > ema_21 > sma_50
        
        # حساب مستويات المخاطر وإدارة الصفقة (1:2.5 Risk-to-Reward)
        stop_loss = round(current_price * 0.95, 2)  # وقف الخسارة 5%
        take_profit = round(current_price + (current_price - stop_loss) * 2.5, 2)
        
        if is_uptrend and is_volume_spike:
            message = (
                f"🚨 **فرصة صفقات زخم جديدة تم رصدها!** 🚨\n\n"
                f"📌 **الرمز:** `{ticker}`\n"
                f"💵 **السعر الحالي:** `${current_price:.2f}`\n"
                f"📈 **الاتجاه:** صاعد قوي (EMA21 > SMA50)\n"
                f"📊 **حجم التداول:** مرتفع ({last_volume:,.0f} سهم)\n\n"
                f"🎯 **توصية الإدارة المالية:**\n"
                f"🛑 **وقف الخسارة (Stop Loss):** `${stop_loss}`\n"
                f"💰 **هدف الربح (Take Profit):** `${take_profit}`\n"
                f"⚖️ **العائد للمخاطرة:** 1:2.5"
            )
            return message
            
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        
    return None

def main():
    """حلقة التشغيل المستمرة على مدار الساعة"""
    startup_msg = "🤖 **تم تشغيل بوت مراقبة الأسهم والزخم بنجاح سحابياً (24/7)!**"
    send_telegram_message(startup_msg)
    print("Bot started successfully and monitoring market...")
    
    while True:
        try:
            for ticker in STOCKS_LIST:
                alert = analyze_stock(ticker)
                if alert:
                    send_telegram_message(alert)
                time.sleep(5)  # فاصل زمني بين فحص كل سهم لتجنب حظر الطلبات
                
            # الانتظار لفترة قبل دورة الفحص التالية (مثلاً كل 15 دقيقة)
            time.sleep(900)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
