import pathlib

source_root = pathlib.Path(__file__).parent.parent.parent
trades_dump = source_root / "source/trades"

# backend.transformer_model
sentiment_model = source_root / "source/models/labse"
tokenizer_model = "cointegrated/LaBSE-en-ru"
token_max_len = 100

# backend.telegram_bot
tg_token = source_root / "source/configs/tg_bot.yaml"

# backend.trade_actions.active_trades.cache
pickle_cache = source_root / "source/cache.pickle"

# Na
pickle_context = source_root / "source/context.pickle"
similarity_threshold = 0.85

# backend.trade_actions.exit_model
exit_model_path = source_root / "source/models/exit_xgb/xgboost_model_10_c.json"

# backend.trade_actions.exit_model
stop_loss = (0.99, 1.01)

# backend.tinvest_api
tinvest_api_token = source_root / "source/configs/token.yaml"
