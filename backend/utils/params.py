import pathlib

trades_dump = pathlib.Path("source/trades")

# backend.trade_actions.active_trades.cache
pickle_cache = pathlib.Path("source/cache.pickle")

# Na
pickle_context = pathlib.Path("source/context.pickle")
similarity_threshold = 0.85

# backend.trade_actions.exit_model
exit_model_path = pathlib.Path("source/models/exit_xgb/xgboost_model_10_c.json")

# backend.trade_actions.exit_model
stop_loss = (0.99, 1.01)
