# bot_runner.py
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

def check_railway_environment():
    """Проверка окружения для Railway"""
    print("=" * 60)
    print("🚀 TELEGRAM BOT - RAILWAY DEPLOYMENT")
    print("=" * 60)
    
    # 1. На Railway переменные окружения устанавливаются автоматически
    # НЕ нужно проверять файлы .env
    
    print("🔍 Проверка переменных окружения Railway...")
    
    # Ключевые переменные
    required_vars = ['BOT_TOKEN']
    optional_vars = ['DATABASE_URL', 'ENVIRONMENT']
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Отсутствуют обязательные переменные: {', '.join(missing)}")
        print("   Установите их в Railway: Settings → Variables")
        return False
    
    # Показываем что есть
    print("✅ Найдены переменные:")
    for var in required_vars + optional_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else "***"
            print(f"   {var}: {masked}")
    
    # Определяем тип БД
    db_url = os.getenv("DATABASE_URL")
    if db_url and 'postgresql://' in db_url:
        print("🗄️  Используется: PostgreSQL (Railway)")
    else:
        print("🗄️  Используется: SQLite (по умолчанию)")
    
    return True

async def run_bot_forever():
    """Запускает бота с бесконечным перезапуском при ошибках"""
    
    if not check_railway_environment():
        return
    
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            restart_count += 1
            logger.info(f"🔄 Запуск бота (попытка {restart_count}/{max_restarts})")
            
            # Импортируем основной модуль
            import start_bot
            
            # Запускаем основную функцию
            await start_bot.main()
            
        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            break
            
        except Exception as e:
            logger.error(f"❌ Бот упал с ошибкой: {e}")
            import traceback
            logger.error("Трейсбэк ошибки:")
            
            # Для отладки: печатаем полный трейсбэк
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_tb)
            for line in tb_lines:
                logger.error(line.strip())
            
            # Ждем перед перезапуском
            wait_time = min(30, restart_count * 5)
            logger.info(f"⏳ Перезапуск через {wait_time} секунд...")
            await asyncio.sleep(wait_time)
    
    logger.error(f"🚨 Достигнут лимит перезапусков ({max_restarts})")

async def simple_bot_test():
    """Простой тест бота для Railway"""
    print("\n🧪 Запуск простого теста бота...")
    
    try:
        # Пробуем импортировать и запустить main.py
        import start_bot
        
        # Создаем таск
        task = asyncio.create_task(start_bot.main())
        
        # Ждем немного
        await asyncio.sleep(5)
        
        # Проверяем работает ли
        if task.done():
            print("❌ Бот завершился слишком быстро")
            try:
                await task  # Чтобы увидеть исключение
            except Exception as e:
                print(f"Ошибка: {e}")
                import traceback
                traceback.print_exc()
            return False
        else:
            print("✅ Бот работает")
            task.cancel()
            return True
            
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🤖 ЗАПУСК БОТА НА RAILWAY")
    print("=" * 60)
    
    # Настройка для Windows (если локально)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        # Запускаем основной цикл
        asyncio.run(run_bot_forever())
    except KeyboardInterrupt:
        print("\n👋 Бот завершен")
    except Exception as e:
        print(f"\n🚨 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
