from .antiflood import AntiFloodMiddleware, RawMessageAntiFloodMiddleware

middlewares = (AntiFloodMiddleware, )
raw_middlewares = (RawMessageAntiFloodMiddleware, )
