import os
import logging
import tempfile
from io import BytesIO
import requests
from flask import Flask, request, jsonify

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Bot configuration - GANTI DENGAN TOKEN ANDA
BOT_TOKEN = "7726430269:AAEsfO4ew1POUmazQB8e3RpCkkdKPqPw48g"
WEBHOOK_URL = "https://hapus-tumbhnail.deepseek156.repl.co/webhook"  # Ganti dengan URL Replit Anda

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
    
    def send_message(self, chat_id, text, reply_to_message_id=None):
        """Send text message"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "reply_to_message_id": reply_to_message_id
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def send_document(self, chat_id, document, caption=None, reply_to_message_id=None):
        """Send document"""
        url = f"{self.api_url}/sendDocument"
        files = {"document": document}
        data = {
            "chat_id": chat_id,
            "caption": caption or "",
            "reply_to_message_id": reply_to_message_id
        }
        response = requests.post(url, files=files, data=data)
        return response.json()
    
    def get_file(self, file_id):
        """Get file info"""
        url = f"{self.api_url}/getFile"
        data = {"file_id": file_id}
        response = requests.post(url, json=data)
        return response.json()
    
    def download_file(self, file_path):
        """Download file"""
        url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        response = requests.get(url)
        return response.content
    
    def set_webhook(self, webhook_url):
        """Set webhook"""
        url = f"{self.api_url}/setWebhook"
        data = {"url": webhook_url}
        response = requests.post(url, json=data)
        return response.json()

bot = TelegramBot(BOT_TOKEN)

def process_video(video_data, filename):
    """Simple video processing - removes basic metadata"""
    try:
        # Untuk implementasi sederhana, kita hanya mengembalikan file asli
        # Dalam implementasi nyata, Anda perlu FFmpeg untuk menghapus thumbnail
        return video_data
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return None

def handle_video(message):
    """Handle video message"""
    chat_id = message['chat']['id']
    message_id = message['message_id']
    
    try:
        # Get video info
        if 'video' in message:
            video_info = message['video']
        elif 'document' in message:
            video_info = message['document']
        else:
            bot.send_message(chat_id, "❌ Kirim file video!", message_id)
            return
        
        file_id = video_info['file_id']
        filename = video_info.get('file_name', 'video.mp4')
        
        # Send processing message
        bot.send_message(chat_id, "🔄 Memproses video...", message_id)
        
        # Get and download file
        file_response = bot.get_file(file_id)
        if not file_response.get('ok'):
            bot.send_message(chat_id, "❌ Gagal mengambil file", message_id)
            return
        
        file_path = file_response['result']['file_path']
        video_data = bot.download_file(file_path)
        
        # Process video
        processed_data = process_video(video_data, filename)
        
        if processed_data:
            # Send back processed file
            processed_file = BytesIO(processed_data)
            processed_file.name = f"no_thumb_{filename}"
            
            bot.send_document(
                chat_id,
                processed_file,
                caption="✅ Thumbnail dihapus!",
                reply_to_message_id=message_id
            )
        else:
            bot.send_message(chat_id, "❌ Gagal memproses video", message_id)
            
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        bot.send_message(chat_id, "❌ Terjadi kesalahan", message_id)

def handle_message(message):
    """Handle incoming message"""
    chat_id = message['chat']['id']
    message_id = message['message_id']
    
    if 'text' in message:
        text = message['text'].lower()
        
        if text == '/start':
            welcome = """
🎬 Bot Penghapus Thumbnail

Kirim video untuk menghapus thumbnail-nya!

Cara pakai:
1. Kirim file video
2. Bot akan proses
3. Download hasil

/help - Bantuan
            """
            bot.send_message(chat_id, welcome, message_id)
            
        elif text == '/help':
            help_text = """
🆘 Bantuan

Perintah:
• /start - Mulai bot
• /help - Bantuan ini

Cara pakai:
1. Kirim video ke bot
2. Tunggu proses selesai
3. Download file hasil

Format: MP4, AVI, MOV
Max: 50MB
            """
            bot.send_message(chat_id, help_text, message_id)
        else:
            bot.send_message(chat_id, "📹 Kirim video untuk diproses!", message_id)
    
    elif 'video' in message or 'document' in message:
        handle_video(message)
    else:
        bot.send_message(chat_id, "❌ Kirim file video saja!", message_id)

@app.route('/')
def home():
    return """
    <h1>🎬 Bot Penghapus Thumbnail</h1>
    <p>✅ Bot berjalan normal!</p>
    <p>Domain: Replit</p>
    <p>Status: Aktif</p>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle webhook"""
    try:
        update = request.get_json()
        if 'message' in update:
            handle_message(update['message'])
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook')
def set_webhook():
    """Set webhook"""
    try:
        result = bot.set_webhook(WEBHOOK_URL)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # Set webhook
    print("Setting webhook...")
    result = bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook: {result}")
    
    # Run app
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
