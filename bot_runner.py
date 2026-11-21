# bot_runner.py (замените start_bot.py)
import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# НАСТРОЙКА ДЛЯ RAILWAY
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def run_bot_forever():
    """Запускает бота с бесконечным перезапуском при ошибках"""
    
    print("=" * 60)
    print("🚀 TELEGRAM BOT - RAILWAY DEPLOYMENT")
    print("=" * 60)
    
    # Загружаем переменные
    load_dotenv()
    
    # Проверяем токен
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не найден!")
        print("Установите BOT_TOKEN в переменных окружения Railway")
        return
    
    logger.info(f"🤖 Токен: {BOT_TOKEN[:10]}...")
    
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            restart_count += 1
            logger.info(f"🔄 Запуск бота (попытка {restart_count}/{max_restarts})")
            
            # Импортируем здесь, чтобы переимпортировать при перезапуске
            import importlib
            import main
            
            # Перезагружаем модуль при перезапуске
            importlib.reload(main)
            
            # Запускаем основную функцию
            await main.main()
            
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            break
            
        except Exception as e:
            logger.error(f"❌ Бот упал с ошибкой: {e}")
            import traceback
            traceback.print_exc()
            
            # Ждем перед перезапуском
            wait_time = min(30, restart_count * 5)  # Экспоненциальная задержка
            logger.info(f"⏳ Перезапуск через {wait_time} секунд...")
            await asyncio.sleep(wait_time)
    
    logger.error(f"🚨 Достигнут лимит перезапусков ({max_restarts})")

if __name__ == "__main__":
    # Настройка для Windows (если локально)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(run_bot_forever())
    except KeyboardInterrupt:
        print("\n👋 Бот завершен")
